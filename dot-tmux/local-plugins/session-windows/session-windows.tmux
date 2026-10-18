#!/bin/sh

# Freeze the invoking session ID at keypress; keep the per-row ID unexpanded.
# -G includes every grouped session so the current session is always available.
tmux bind-key -T prefix i run-shell \
    "tmux choose-tree -G -w -Z -t '#{pane_id}' -f '##{==:##{session_id},#{session_id}}'"
