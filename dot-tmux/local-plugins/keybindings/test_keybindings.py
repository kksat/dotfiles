"""Exercise the real keybinding popup in an isolated tmux server and PTY."""

import fcntl
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import tempfile
import termios
import time
import unittest


PLUGIN = Path(__file__).with_name("keybindings.tmux")


class KeybindingsTest(unittest.TestCase):
    def tmux(self, *args):
        return subprocess.check_output(
            ["tmux", "-S", self.socket, *args], text=True, timeout=5
        ).strip()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="tmux-keybindings-")
        self.addCleanup(self.directory.cleanup)
        self.socket = str(Path(self.directory.name) / "socket")
        self.tmux(
            "-f", "/dev/null", "new-session", "-d", "-s", "main",
            "-x", "120", "-y", "40", "sleep 300",
        )
        self.addCleanup(self.tmux, "kill-server")
        # These options would break live fuzzy search if inherited by the picker.
        self.tmux("set-environment", "-g", "FZF_DEFAULT_OPTS", "--exact --filter=missing")
        self.tmux("set-environment", "-g", "FZF_DEFAULT_OPTS_FILE", "/nonexistent-fzf-options")
        self.tmux("bind-key", "-T", "prefix", "F12", "set-option", "-g", "@keybindings-executed", "yes")
        environment = dict(os.environ, TMUX=f"{self.socket},0,0")
        for _ in range(2):
            subprocess.run([str(PLUGIN)], env=environment, check=True)

        self.master, slave = pty.openpty()
        self.addCleanup(os.close, self.master)
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
        environment = dict(os.environ, TERM="xterm-256color")
        environment.pop("TMUX", None)
        try:
            self.client = subprocess.Popen(
                ["tmux", "-S", self.socket, "attach-session", "-t", "main"],
                stdin=slave, stdout=slave, stderr=slave, env=environment,
                start_new_session=True,
            )
        finally:
            os.close(slave)
        self.addCleanup(self.stop_client)
        self.read_until(b"[main]")

    def stop_client(self):
        self.tmux("display-popup", "-C")
        self.read_until(b"")
        self.client.terminate()
        try:
            self.client.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.client.kill()
            self.client.wait(timeout=5)

    def read_until(self, marker):
        output = b""
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if select.select([self.master], [], [], 0.1)[0]:
                output += os.read(self.master, 65536)
            elif marker in output:
                return output
        self.fail(f"Terminal did not show {marker!r}: {output!r}")

    def open_picker(self, key=b"?"):
        os.write(self.master, b"\x02" + key)
        return self.read_until(b"Ctrl-n/Ctrl-p")

    def test_full_size_and_alias(self):
        question = self.tmux("list-keys", "-T", "prefix", "?")
        alias = self.tmux("list-keys", "-T", "prefix", "k")
        self.assertIn("-w 100% -h 100%", question)
        self.assertEqual(question.split("run-shell", 1)[1], alias.split("run-shell", 1)[1])
        self.open_picker(b"k")

    def test_live_fuzzy_search_and_enter_does_not_execute(self):
        total = len(self.tmux("list-keys").splitlines())
        self.open_picker()
        # A subsequence, not an exact substring: proves fuzzy search is active.
        os.write(self.master, b"F12 kybndsxctd")
        self.read_until(f"1/{total}".encode())
        os.write(self.master, b"\x0e\x10\r")
        self.read_until(b"[main]")
        self.assertEqual(self.tmux("show-option", "-gqv", "@keybindings-executed"), "")
        self.assertEqual(self.tmux("display-message", "-p", "#{pane_mode}"), "")

    def test_escape_cancels(self):
        self.open_picker()
        os.write(self.master, b"\x1b")
        self.read_until(b"[main]")
        # Reopening confirms that cancellation actually closed the first popup.
        self.open_picker()


if __name__ == "__main__":
    unittest.main()
