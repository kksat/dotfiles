# Session windows

Press **Ctrl-b, then i** to open tmux's native window picker filtered to the
session you are using. Move with the arrow keys, press **Enter** to select a
window, or **q** / **Escape** to cancel. The pane is temporarily zoomed while
choosing a window.

This replaces the default `prefix + i` pane-information binding. The standard
`prefix + w` picker is unchanged. Like the standard picker, this uses tmux's
native filtering UI; pressing `f` lets you edit or remove the filter.

The plugin captures the session ID when the key is pressed, not when the config
loads. Session groups are supported, and names containing shell or tmux format
characters do not need escaping because the filter uses IDs, not names.

## Installation

`dot-tmux.conf` loads this local plugin after TPM. Stowing the dotfiles makes it
available at `~/.tmux/local-plugins/session-windows/session-windows.tmux`. It is
kept outside TPM's managed `plugins` directory so TPM cleanup cannot delete it.
No download or dependency beyond tmux is required.

To load just this binding in a running tmux server:

```sh
tmux run-shell '~/.tmux/local-plugins/session-windows/session-windows.tmux'
```

## Checks

From the dotfiles repository:

```sh
sh -n dot-tmux/local-plugins/session-windows/session-windows.tmux
shellcheck dot-tmux/local-plugins/session-windows/session-windows.tmux
python3 dot-tmux/local-plugins/session-windows/test_session_windows.py -v
```

The integration tests use separate temporary tmux sockets and a pseudo-terminal
to exercise the actual Ctrl-b, i binding without modifying your running server.
They cover session filtering, grouped sessions, special characters in session
names, switching sessions after plugin load, repeated loading, and selecting a
window. Tested with tmux 3.5a.
