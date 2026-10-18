# Keybindings

Press **Ctrl-b, then ?** (or **Ctrl-b, then k**) to browse all current tmux
keybindings in an `fzf` popup occupying **100% of the client width and height**.
Start typing to fuzzy-search key names, key tables, and commands.

- **Ctrl-n** / **Down**: next result.
- **Ctrl-p** / **Up**: previous result.
- **Enter** / **Escape** / **Ctrl-c**: close without executing a binding.

This replaces the default `prefix + ?` help view and keeps the existing
`prefix + k` shortcut as an alias. It follows the local `session-windows`
plugin's popup pattern and ignores `FZF_DEFAULT_OPTS` and
`FZF_DEFAULT_OPTS_FILE` to keep search and navigation predictable.

## Installation

Requires tmux with popup support and `fzf`. `dot-tmux.conf` loads this plugin
after TPM, outside TPM's managed directory. To load only these bindings into
the running server:

```sh
tmux run-shell '~/.tmux/local-plugins/keybindings/keybindings.tmux'
```

## Checks

From the dotfiles repository:

```sh
sh -n dot-tmux/local-plugins/keybindings/keybindings.tmux
sh -n dot-tmux/local-plugins/keybindings/list-keybindings.sh
shellcheck dot-tmux/local-plugins/keybindings/*.tmux dot-tmux/local-plugins/keybindings/*.sh
python3 dot-tmux/local-plugins/keybindings/test_keybindings.py -v
```

The tests use an isolated tmux server and a pseudo-terminal to exercise the real
prefix bindings, fuzzy matching despite conflicting global fzf options,
cancellation, safe dismissal, repeated loading, and full-size popup options.
