"""Exercise the real prefix binding in an isolated tmux server and terminal."""

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


PLUGIN = Path(__file__).with_name("session-windows.tmux")


class SessionWindowsTest(unittest.TestCase):
    def tmux(self, *args):
        return subprocess.check_output(
            ["tmux", "-S", self.socket, *args], text=True
        ).strip()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="tmux-session-windows-")
        self.addCleanup(self.directory.cleanup)
        self.socket = str(Path(self.directory.name) / "socket")
        self.tmux(
            "-f", "/dev/null", "new-session", "-d", "-s", "main",
            "-n", "local-one", "-x", "120", "-y", "40", "sleep 300",
        )
        self.addCleanup(self.tmux, "kill-server")
        self.tmux("set-option", "-g", "automatic-rename", "off")
        self.tmux("new-window", "-d", "-t", "main:", "-n", "local-two", "sleep 300")
        self.tmux(
            "new-session", "-d", "-s", "other", "-n", "foreign-window", "sleep 300"
        )
        self.tmux("new-session", "-d", "-s", "grouped", "-t", "main")
        environment = dict(os.environ, TMUX=f"{self.socket},0,0")
        # Loading twice must not change the behavior or capture the load-time session.
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
        self.read_until(b"local-one")

    def stop_client(self):
        self.client.terminate()
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

    def open_picker(self):
        os.write(self.master, b"\x02i")
        output = self.read_until(b"sort: index")
        self.assertNotIn(b"no matches", output)
        return output

    def assert_local_windows(self, output):
        self.assertIn(b"local-one", output)
        self.assertIn(b"local-two", output)
        self.assertNotIn(b"foreign-window", output)

    def test_current_session_only(self):
        self.assert_local_windows(self.open_picker())

    def test_grouped_session_only(self):
        self.tmux("switch-client", "-t", "grouped")
        self.read_until(b"[grouped]")
        output = self.open_picker()
        self.assert_local_windows(output)
        self.assertIn(b"grouped: 2 windows", output)
        self.assertNotIn(b"main: 2 windows", output)

    def test_session_name_with_special_characters(self):
        self.tmux("rename-session", "-t", "main", "work's $HOME,#{session_id}")
        self.read_until(b"[work's")
        self.assert_local_windows(self.open_picker())

    def test_session_is_resolved_at_keypress(self):
        self.tmux("switch-client", "-t", "other")
        self.read_until(b"foreign-window")
        output = self.open_picker()
        self.assertIn(b"foreign-window", output)
        self.assertNotIn(b"local-one", output)
        self.assertNotIn(b"local-two", output)

    def test_select_window(self):
        self.open_picker()
        os.write(self.master, b"\x1b[B\r")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.tmux("display-message", "-p", "#{window_name}") == "local-two":
                break
            time.sleep(0.05)
        self.assertEqual(self.tmux("display-message", "-p", "#{window_name}"), "local-two")
        self.assertEqual(self.tmux("display-message", "-p", "#{session_name}"), "main")
        self.assertEqual(self.tmux("display-message", "-p", "#{pane_mode}"), "")


if __name__ == "__main__":
    unittest.main()
