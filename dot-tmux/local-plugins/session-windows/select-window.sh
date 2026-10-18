#!/bin/sh
set -eu

session=$1
if ! command -v fzf >/dev/null 2>&1; then
    tmux display-message 'Session windows: fzf is required (brew install fzf)'
    exit 1
fi

tab=$(printf '\t')
# List only this session, including when its windows are shared with a group.
windows=$(tmux list-windows -t "$session" \
    -F "#{window_id}${tab}#{window_index}: #{window_name} #{window_flags}")

# Keep user-wide fzf options from changing selection, search, or popup behavior.
selection=$(printf '%s\n' "$windows" |
    FZF_DEFAULT_OPTS='' FZF_DEFAULT_OPTS_FILE='' fzf \
        --layout=reverse --no-multi --delimiter="$tab" --with-nth=2.. \
        --prompt='Window> ' \
        --header='Type to search | Ctrl-n/Ctrl-p: move | Enter: switch | Esc: cancel' \
        --bind='ctrl-n:down,ctrl-p:up') || exit 0

# Use the hidden window ID rather than interpreting any part of its name.
window=${selection%%"$tab"*}
tmux select-window -t "$session:$window"
