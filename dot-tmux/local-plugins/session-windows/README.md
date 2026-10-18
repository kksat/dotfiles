# Session windows

Press **Ctrl-b, then i** to open an `fzf` popup containing only the current
session's windows. Start typing to fuzzy-filter the list immediately.

- **Ctrl-n** / **Down**: next result.
- **Ctrl-p** / **Up**: previous result.
- **Enter**: switch to the selected window.
- **Escape** / **Ctrl-c**: cancel without switching.

Window indices, names, and flags are shown (`*` marks the active window). Window
IDs are hidden from display and search, but used to select the correct window.
Typing `q` or `f` searches normally; these are not special picker commands.

This replaces the default `prefix + i` pane-information binding. The standard
`prefix + w` picker is unchanged.

The plugin captures the client and session ID when the key is pressed, not when
the config loads. Session groups are supported. Selection uses IDs rather than
interpreting session or window names as shell commands. Only the invoking
session is listed; removing the search query cannot reveal other sessions.

## Installation

Requires tmux with popup support and `fzf` (already included in the dotfiles
Brewfiles). On macOS, install missing dependencies with `brew install tmux fzf`.
The picker ignores `FZF_DEFAULT_OPTS` and `FZF_DEFAULT_OPTS_FILE` so global fzf
settings cannot override its navigation or launch a nested popup.

`dot-tmux.conf` loads this local plugin after TPM. Stowing the dotfiles makes it
available at `~/.tmux/local-plugins/session-windows/session-windows.tmux`. It is
kept outside TPM's managed `plugins` directory so TPM cleanup cannot delete it.

To load just this binding in a running tmux server:

```sh
tmux run-shell '~/.tmux/local-plugins/session-windows/session-windows.tmux'
```

## Checks

From the dotfiles repository:

```sh
sh -n dot-tmux/local-plugins/session-windows/session-windows.tmux
sh -n dot-tmux/local-plugins/session-windows/select-window.sh
shellcheck dot-tmux/local-plugins/session-windows/*.tmux dot-tmux/local-plugins/session-windows/*.sh
python3 dot-tmux/local-plugins/session-windows/test_session_windows.py -v
```

The integration tests use separate temporary tmux sockets and a pseudo-terminal
to exercise the actual Ctrl-b, i binding without modifying your running server.
They cover live fuzzy filtering, Ctrl-n/Ctrl-p and arrow navigation, cancellation,
session scoping, grouped sessions, special characters in session names, switching
sessions after plugin load, repeated loading, and selecting a window. Tested with
tmux 3.5a and fzf 0.61.3.
