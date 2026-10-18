#!/bin/sh

plugin_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

# Resolve the invoking client at keypress, as in the session-windows plugin.
for key in '?' k; do
    tmux bind-key -T prefix "$key" run-shell \
        "tmux display-popup -E -c '#{client_name}' -w 100% -h 100% -T ' Keybindings ' \
            \"$plugin_dir/list-keybindings.sh\""
done
