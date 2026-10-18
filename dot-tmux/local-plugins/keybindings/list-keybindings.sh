#!/bin/sh
set -eu

if ! command -v fzf >/dev/null 2>&1; then
    tmux display-message 'Keybindings: fzf is required (brew install fzf)'
    exit 1
fi

# Ignore global options so fuzzy search and popup navigation stay predictable.
# This is a reference list: Enter closes the picker without executing anything.
tmux list-keys |
    FZF_DEFAULT_OPTS='' FZF_DEFAULT_OPTS_FILE='' fzf \
        --layout=reverse --no-multi --prompt='Keybind> ' \
        --header='Type to search | Ctrl-n/Ctrl-p: move | Enter/Esc: close' \
        --bind='ctrl-n:down,ctrl-p:up' >/dev/null || exit 0
