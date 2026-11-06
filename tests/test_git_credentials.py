import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


GITCONFIG = Path(__file__).resolve().parents[1] / "dot-gitconfig"
GIT = shutil.which("git")


@unittest.skipUnless(GIT, "git is required")
class CredentialHelperTests(unittest.TestCase):
    def test_homebrew_prefix_and_fallback(self):
        for host in ("github.com", "gist.github.com"):
            for prefix_state in ("set", "unset", "empty"):
                with self.subTest(host=host, prefix_state=prefix_state):
                    with tempfile.TemporaryDirectory(prefix="dotfiles credentials ") as temp:
                        home = Path(temp)
                        prefix = home / "Homebrew prefix"
                        (prefix / "bin").mkdir(parents=True)
                        gh = prefix / "bin/gh"
                        gh.write_text(
                            '#!/bin/sh\n'
                            '[ "$1" = auth ] && [ "$2" = git-credential ] '
                            '&& [ "$3" = get ] || exit 1\n'
                            'printf "username=test-user\\npassword=test-password\\n"\n'
                        )
                        gh.chmod(0o755)
                        bin_dir = home / "bin"
                        bin_dir.mkdir()
                        brew = bin_dir / "brew"
                        brew.write_text(
                            '#!/bin/sh\n'
                            '[ "$1" = --prefix ] || exit 1\n'
                            'printf called > "$BREW_LOG"\n'
                            'printf "%s\\n" "$TEST_PREFIX"\n'
                        )
                        brew.chmod(0o755)
                        brew_log = home / "brew-calls"
                        env = {
                            "HOME": str(home),
                            "PATH": os.pathsep.join((str(bin_dir), "/usr/bin", "/bin")),
                            "GIT_CONFIG_NOSYSTEM": "1",
                            "GIT_CONFIG_GLOBAL": str(GITCONFIG),
                            "GIT_TERMINAL_PROMPT": "0",
                            "TEST_PREFIX": str(prefix),
                            "BREW_LOG": str(brew_log),
                        }
                        if prefix_state != "unset":
                            env["HOMEBREW_PREFIX"] = str(prefix) if prefix_state == "set" else ""
                        result = subprocess.run(
                            [GIT, "credential", "fill"],
                            input=f"protocol=https\nhost={host}\n\n",
                            cwd=home,
                            env=env,
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertIn("username=test-user\n", result.stdout)
                        self.assertIn("password=test-password\n", result.stdout)
                        self.assertEqual(result.stderr, "")
                        self.assertEqual(brew_log.exists(), prefix_state != "set")


if __name__ == "__main__":
    unittest.main()
