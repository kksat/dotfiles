import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ZSHRC = Path(__file__).resolve().parents[1] / "dot-zshrc"
ZSH = shutil.which("zsh")


@unittest.skipUnless(ZSH, "zsh is required")
class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles completion ")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.bin = self.home / "bin"
        self.bin.mkdir()
        (self.home / ".config").mkdir()
        (self.home / ".config/alias").touch()
        self.env = {
            "HOME": str(self.home),
            "ZDOTDIR": str(self.home),
            "PATH": f"{self.bin}:/usr/bin:/bin",
            "HOMEBREW_PREFIX": str(self.home / "brew"),
            "XDG_CACHE_HOME": str(self.home / "cache"),
            "XDG_DATA_HOME": str(self.home / "data"),
            "TERM": "xterm-256color",
            "ZSHRC_UNDER_TEST": str(ZSHRC),
            "TEST_LOG": str(self.home / "calls"),
        }
        self.yc_source = self.home / "yandex-cloud/completion.zsh.inc"
        self.yc_source.parent.mkdir()
        self.yc_source.write_text("""
__yc_convert_bash_to_zsh() {
  print -r -- yc-generate >> "$TEST_LOG"
  [[ ! -f "$HOME/yc-fail" ]] || return 1
  cat <<'COMPLETION'
print -r -- yc-source >> "$TEST_LOG"
__start_yc() { :; }
complete -o default -F __start_yc yc
# Substitute the ZLE-only entry point after bashcompinit defines it.
_bash_complete() { print -r -- "yc-dispatch:$*"; }
COMPLETION
}
""")
        ydb_path = self.home / "ydb/path.bash.inc"
        ydb_path.parent.mkdir()
        ydb_path.write_text('export YDB_PATH_LOADED=1\n')
        self.ydb_source = self.home / "data/ydb/completion.zsh.inc"
        self.ydb_source.parent.mkdir(parents=True)
        self.ydb_source.write_text("""
print -r -- ydb-source >> "$TEST_LOG"
_ydb() { print -r -- "ydb-dispatch:$*"; }
compdef _ydb ydb
""")
        for name in ("yc", "ydb"):
            self.executable(name, '#!/bin/sh\nprintf "%s\\n" "$*"\n')
        self.entire = self.executable("entire", """#!/bin/sh
if [ "$1 $2" != "completion zsh" ]; then
  printf '%s\n' "$*"
  exit 0
fi
printf '%s\n' entire-generate >> "$TEST_LOG"
if [ -f "$HOME/entire-fail" ]; then exit 1; fi
if [ -f "$HOME/entire-empty" ]; then exit 0; fi
cat <<'COMPLETION'
print -r -- entire-source >> "$TEST_LOG"
_entire() { print -r -- "entire-dispatch:$*"; }
compdef _entire entire
COMPLETION
""")

    def executable(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)
        return path

    def shell(self, script, check=True):
        result = subprocess.run(
            [ZSH, "-dfi", "-c", 'source "$ZSHRC_UNDER_TEST"\n' + script],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")
        return result

    def calls(self):
        log = self.home / "calls"
        return log.read_text().splitlines() if log.exists() else []

    def complete(self, command):
        return self.shell(f"""
${{=_comps[{command}]}} first
${{=_comps[{command}]}} second
""")

    def test_startup_defers_all_three_completions(self):
        self.shell("""
[[ -n $_comps[yc] && -n $_comps[ydb] && -n $_comps[entire] ]] || exit 1
[[ $YDB_PATH_LOADED = 1 ]] || exit 2
(( ! $+functions[__start_yc] && ! $+functions[_ydb] && ! $+functions[_entire] ))
""")
        self.assertEqual(self.calls(), [])

    def test_commands_run_without_loading_completions(self):
        result = self.shell("yc --version; ydb --version; entire --version")
        self.assertEqual(result.stdout.splitlines(), ["--version"] * 3)
        self.assertEqual(self.calls(), [])

    def test_yc_loads_once_and_forwards_bash_completion_arguments(self):
        result = self.complete("yc")
        self.assertEqual(result.stdout.splitlines(), [
            "yc-dispatch:-o default -F __start_yc first",
            "yc-dispatch:-o default -F __start_yc second",
        ])
        self.assertEqual(self.calls(), ["yc-generate", "yc-source"])
        self.complete("yc")
        self.assertEqual(self.calls().count("yc-generate"), 1)

    def test_yc_cache_refreshes_after_source_changes(self):
        self.complete("yc")
        future = (self.home / "cache/zsh/yc_completion.zsh").stat().st_mtime + 5
        os.utime(self.yc_source, (future, future))
        self.complete("yc")
        self.assertEqual(self.calls().count("yc-generate"), 2)

    def test_failed_yc_conversion_can_retry_in_same_shell(self):
        self.shell("""
touch "$HOME/yc-fail"
${=_comps[yc]} && exit 1
[[ ! -f "$XDG_CACHE_HOME/zsh/yc_completion.zsh" ]] || exit 2
rm "$HOME/yc-fail"
${=_comps[yc]} retry
""")
        self.assertEqual(self.calls(), ["yc-generate", "yc-generate", "yc-source"])

    def test_ydb_loads_once_and_dispatches_first_completion(self):
        result = self.complete("ydb")
        self.assertEqual(result.stdout.splitlines(), [
            "ydb-dispatch:first", "ydb-dispatch:second",
        ])
        self.assertEqual(self.calls(), ["ydb-source"])

    def test_entire_cache_is_reused_across_shells(self):
        for _ in range(2):
            result = self.complete("entire")
            self.assertEqual(result.stdout.splitlines(), [
                "entire-dispatch:first", "entire-dispatch:second",
            ])
        self.assertEqual(self.calls(), [
            "entire-generate", "entire-source", "entire-source",
        ])

    def test_entire_cache_refreshes_after_binary_replacement(self):
        self.complete("entire")
        # Installers can preserve an older binary mtime; identity must also
        # invalidate the cache, not just a newer modification timestamp.
        original_mtime = self.entire.stat().st_mtime
        replacement = self.executable("entire-new", self.entire.read_text())
        os.utime(replacement, (original_mtime - 60, original_mtime - 60))
        replacement.replace(self.entire)
        self.complete("entire")
        self.assertEqual(self.calls().count("entire-generate"), 2)

    def test_failed_or_empty_generation_can_retry(self):
        for marker in ("entire-fail", "entire-empty"):
            with self.subTest(marker=marker):
                flag = self.home / marker
                flag.touch()
                self.shell("${=_comps[entire]} && exit 1; exit 0")
                self.assertFalse((self.home / "cache/zsh/entire_completion.zsh").exists())
                flag.unlink()
        self.complete("entire")
        self.assertEqual(self.calls().count("entire-source"), 1)

    def test_failed_entire_generation_can_retry_in_same_shell(self):
        self.shell("""
touch "$HOME/entire-fail"
${=_comps[entire]} && exit 1
rm "$HOME/entire-fail"
${=_comps[entire]} retry
""")
        self.assertEqual(self.calls(), [
            "entire-generate", "entire-generate", "entire-source",
        ])

    def test_failed_refresh_preserves_previous_cache(self):
        self.complete("entire")
        cache = self.home / "cache/zsh/entire_completion.zsh"
        previous = cache.read_bytes()
        with self.entire.open("a") as executable:
            executable.write("\n# new version\n")
        (self.home / "entire-fail").touch()
        self.shell("${=_comps[entire]} && exit 1; exit 0")
        self.assertEqual(cache.read_bytes(), previous)
        self.assertEqual(self.calls().count("entire-source"), 1)

    def test_missing_optional_tools_do_not_break_startup(self):
        self.yc_source.unlink()
        self.ydb_source.unlink()
        self.entire.unlink()
        self.shell("""
[[ -z $_comps[yc] && -z $_comps[ydb] && -z $_comps[entire] ]]
""")
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
