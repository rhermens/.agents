#!/usr/bin/env bash
# List coding-agent panes in tmux sessions that match a query.
# Usage: find-agent.sh <query>
# Output (tab-separated): pane_id  session  window  agent  path
# A session matches when its name equals the query, starts with "<query> ",
# or a pane's working directory basename equals the query (case-insensitive).
set -euo pipefail

query="${1:?usage: find-agent.sh <query>}"
agents_re='^(claude|\.claude-wrapped|codex|opencode|pi|agent|cursor-agent|gemini|aider|hermes)$'
q=$(printf '%s' "$query" | tr '[:upper:]' '[:lower:]')

tmux list-panes -a -F '#{pane_id}	#{session_name}	#{window_index}	#{pane_tty}	#{pane_current_path}' |
while IFS=$'\t' read -r pane session window tty path; do
  s=$(printf '%s' "$session" | tr '[:upper:]' '[:lower:]')
  b=$(printf "%s" "${path##*/}" | tr '[:upper:]' '[:lower:]')
  if [[ "$s" != "$q" && "$s" != "$q "* && "$b" != "$q" ]]; then
    continue
  fi
  agent=""
  while read -r comm; do
    name="${comm##*/}"
    if [[ "$name" =~ $agents_re ]]; then agent="$name"; break; fi
  done < <(ps -t "${tty#/dev/}" -o comm= 2>/dev/null)
  if [[ -n "$agent" ]]; then
    printf '%s\t%s\t%s\t%s\t%s\n' "$pane" "$session" "$window" "$agent" "$path"
  fi
done
