#!/usr/bin/env bash
# Paste a message from stdin into a tmux pane and submit it.
# Usage: send.sh <pane_id> < message.txt
set -euo pipefail

pane="${1:?usage: send.sh <pane_id> < message}"
buffer="delegate-$$"

tmux display-message -p -t "$pane" '#{pane_id}' >/dev/null

# Vim-mode prompts treat pasted text as commands in NORMAL mode.
if tmux capture-pane -p -t "$pane" | tail -n 5 | grep -q -- '-- NORMAL --'; then
  tmux send-keys -t "$pane" i
  sleep 0.2
fi

tmux load-buffer -b "$buffer" -
# -p uses bracketed paste so newlines do not submit early.
tmux paste-buffer -p -d -b "$buffer" -t "$pane"
sleep 0.5
tmux send-keys -t "$pane" Enter
