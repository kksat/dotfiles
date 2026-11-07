import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "dot-local/bin/rex-pi-tunnel"
LABEL = "com.ksatarin.rex-pi-ssh"
PLIST = REPO / f"Library/LaunchAgents/{LABEL}.plist"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash is required")
class RexPiLaunchAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rex launch agent ")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        bin_dir = self.home / "bin"
        bin_dir.mkdir()
        mock = (
            f"#!{sys.executable}\n"
            "import json, os, pathlib, sys\n"
            "name = pathlib.Path(sys.argv[0]).name\n"
            "args = sys.argv[1:]\n"
            "home = pathlib.Path(os.environ['HOME'])\n"
            "with open(os.environ['COMMAND_LOG'], 'a') as log:\n"
            "    log.write(json.dumps([name, *args]) + '\\n')\n"
            "loaded = home / 'loaded'\n"
            "connected = home / 'connected'\n"
            "if name == 'launchctl':\n"
            "    if args[0] == 'print':\n"
            "        sys.exit(0 if loaded.exists() else 1)\n"
            "    if args[0] == 'bootstrap':\n"
            "        if os.environ.get('BOOTSTRAP_FAIL'):\n"
            "            sys.exit(5)\n"
            "        loaded.touch()\n"
            "    if args[0] == 'bootout':\n"
            "        loaded.unlink()\n"
            "        connected.unlink(missing_ok=True)\n"
            "else:\n"
            "    if '-O' in args:\n"
            "        operation = args[args.index('-O') + 1]\n"
            "        if operation == 'check':\n"
            "            sys.exit(0 if connected.exists() else 1)\n"
            "        if operation == 'exit':\n"
            "            connected.unlink()\n"
            "    elif os.environ.get('SSH_FAIL'):\n"
            "        print('Connection failed', file=sys.stderr)\n"
            "        sys.exit(255)\n"
        )
        for name in ("ssh", "launchctl"):
            command = bin_dir / name
            command.write_text(mock)
            command.chmod(0o755)
        self.log = self.home / "commands.jsonl"
        self.env = {
            "HOME": str(self.home),
            "PATH": os.pathsep.join((str(bin_dir), "/usr/bin", "/bin")),
            "COMMAND_LOG": str(self.log),
        }
        self.agent = self.home / f"Library/LaunchAgents/{LABEL}.plist"
        self.agent.parent.mkdir(parents=True)
        # The control commands only require the stowed file to exist.
        self.agent.write_text("test fixture\n")
        self.service = f"gui/{os.getuid()}/{LABEL}"

    def run_tunnel(self, *args):
        return subprocess.run(
            [BASH, str(SCRIPT), *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_plist_supervises_foreground_worker_at_login(self):
        with PLIST.open("rb") as file:
            config = plistlib.load(file)
        self.assertEqual(config["Label"], LABEL)
        self.assertIs(config["KeepAlive"], True)
        self.assertIs(config["RunAtLoad"], True)
        self.assertEqual(config["ThrottleInterval"], 10)
        self.assertEqual(
            config["ProgramArguments"],
            ["/bin/sh", "-c", 'exec "$HOME/.local/bin/rex-pi-tunnel" run'],
        )

    def test_start_loads_agent_without_backgrounding_another_ssh(self):
        result = self.run_tunnel("start")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(["launchctl", "enable", self.service], self.calls())
        self.assertIn(
            ["launchctl", "bootstrap", f"gui/{os.getuid()}", str(self.agent)],
            self.calls(),
        )
        self.assertFalse(any("-fNT" in args for args in self.calls()))

    def test_repeated_start_does_not_reload_the_job(self):
        self.assertEqual(self.run_tunnel().returncode, 0)
        result = self.run_tunnel("start")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already", result.stdout)
        self.assertEqual(
            sum(args[:2] == ["launchctl", "bootstrap"] for args in self.calls()), 1
        )

    def test_start_retires_the_old_unmanaged_tunnel_before_loading(self):
        (self.home / "connected").touch()
        result = self.run_tunnel("start")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        exit_index = next(i for i, args in enumerate(calls) if "exit" in args)
        bootstrap_index = next(
            i for i, args in enumerate(calls) if args[:2] == ["launchctl", "bootstrap"]
        )
        self.assertLess(exit_index, bootstrap_index)
        self.assertFalse((self.home / "connected").exists())

    def test_start_requires_stowed_agent(self):
        self.agent.unlink()
        result = self.run_tunnel("start")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stow", result.stderr.lower())
        self.assertEqual(self.calls(), [])

    def test_bootstrap_failure_does_not_report_success(self):
        self.env["BOOTSTRAP_FAIL"] = "1"
        result = self.run_tunnel("start")
        self.assertEqual(result.returncode, 5)
        self.assertNotIn("enabled", result.stdout)

    def test_run_executes_foreground_ssh_with_private_socket_and_keepalives(self):
        result = self.run_tunnel("run")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = self.calls()[-1]
        self.assertEqual(args[0], "ssh")
        self.assertIn("-NT", args)
        self.assertNotIn("-fNT", args)
        self.assertEqual(args[-1], "pi")
        self.assertEqual(
            args[args.index("-L") + 1],
            f"{self.home}/.ssh/rex-pi.sock:/run/user/1000/rex/server.sock",
        )
        self.assertIn(str(self.home / ".ssh/rex-pi-control.sock"), args)
        for option in (
            "ControlMaster=auto", "ControlPersist=no", "ForkAfterAuthentication=no",
            "RemoteCommand=none", "BatchMode=yes", "ConnectTimeout=10",
            "ExitOnForwardFailure=yes", "ServerAliveInterval=15",
            "ServerAliveCountMax=3", "StreamLocalBindUnlink=yes",
            "StreamLocalBindMask=0177",
        ):
            self.assertIn(option, args)
        self.assertEqual((self.home / ".ssh").stat().st_mode & 0o777, 0o700)
        self.assertTrue((self.home / "Library/Logs/rex-pi-ssh.log").exists())

    def test_run_propagates_ssh_failure_and_logs_it(self):
        self.env["SSH_FAIL"] = "1"
        result = self.run_tunnel("run")
        self.assertEqual(result.returncode, 255)
        self.assertIn(
            "Connection failed",
            (self.home / "Library/Logs/rex-pi-ssh.log").read_text(),
        )

    def test_status_reports_disconnected_while_job_retries(self):
        (self.home / "loaded").touch()
        result = self.run_tunnel("status")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("launchd", result.stdout)
        self.assertFalse(any("bootstrap" in args for args in self.calls()))
        (self.home / "connected").touch()
        self.assertEqual(self.run_tunnel("status").returncode, 0)

    def test_stop_disables_retries_and_login_startup_and_is_idempotent(self):
        (self.home / "loaded").touch()
        (self.home / "connected").touch()
        result = self.run_tunnel("stop")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertIn(["launchctl", "disable", self.service], calls)
        self.assertIn(["launchctl", "bootout", self.service], calls)
        self.assertFalse((self.home / "loaded").exists())
        self.assertEqual(self.run_tunnel("stop").returncode, 0)

    def test_invalid_arguments_do_not_contact_ssh_or_launchctl(self):
        for args in (("restart",), ("start", "extra")):
            with self.subTest(args=args):
                result = self.run_tunnel(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Usage:", result.stderr)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
