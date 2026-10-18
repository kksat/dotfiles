#!/bin/sh

plugin_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

# run-shell expands the invoking client/session at keypress, before the popup.
tmux bind-key -T prefix i run-shell \
    "tmux display-popup -E -c '#{client_name}' -w 80% -h 70% -T ' Session windows ' \
        \"$plugin_dir/select-window.sh\" '#{session_id}'"
