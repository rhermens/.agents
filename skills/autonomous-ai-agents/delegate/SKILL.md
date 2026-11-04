---
name: delegate
description: Hand a task to a coding agent running in another tmux session, such as a ticket worktree session. Use when asked to delegate, forward, or send work to tmux session DR-XXXX or another named session.
license: MIT
compatibility: Requires tmux and bash. Detects Claude Code, Codex, OpenCode, Pi, Cursor Agent, Gemini, Aider, and Hermes panes.
metadata:
  author: Roy Hermens
  version: "1.0.0"
---

# Delegate

Send a self-contained task to the agent running in another tmux session.

## Session layout

`wt` creates one tmux session per worktree:

- **Session name:** `<branch> (<repository>)`, for example `DR-8405 (dr-server-v2)`.
- **Working directory:** `~/.worktrees/<branch>`.
- **Windows:** `0` shell, `1` shell or dev server, `2` `nvim`, `3` shell, `4` agent.
- **Main checkouts:** Sessions such as `dr-server-v2` hold the main checkout, not a ticket.

The agent window is usually `4`. Detect it by process; the user can start an agent in any window.

## Workflow

1. **Resolve the target.** Run the finder with the session query from the request:

   ```sh
   scripts/find-agent.sh DR-8405
   ```

   Each line is `pane_id  session  window  agent  path`. Use the `pane_id`, such as `%42`, as the target. Session names contain spaces, so never target by session name.

2. **Handle the match count.**
   - If one pane matches, continue.
   - If several panes match, ask the user which one to use.
   - If no pane matches, check `tmux ls`. Report whether the session or only the agent is missing. Stop and ask before starting an agent or creating a worktree.

3. **Check the agent state.** Run `tmux capture-pane -p -t <pane_id> | tail -n 30`. If the agent is mid-task or waiting on a permission prompt, tell the user. Send only if they agree; most agents queue the message.

4. **Write the message.** Make it self-contained; the target agent has none of your context. Include:
   - the task and acceptance criteria,
   - relevant file paths, ticket keys, PR numbers, and findings,
   - constraints, such as "ask before force-pushing",
   - the origin: `Delegated from tmux session <your session>.`

   Get your session with `tmux display-message -p '#S'`.

5. **Send the message.** Write it to a temporary file, then run:

   ```sh
   scripts/send.sh <pane_id> < message.txt
   ```

   The script pastes with bracketed paste, so multi-line messages stay one prompt. It enters insert mode if a vim-mode prompt shows `-- NORMAL --`.

6. **Verify delivery.** Wait about two seconds. Run `tmux capture-pane -p -t <pane_id> | tail -n 30`. Confirm the agent started working or queued the message. If the text sits unsubmitted in the input box, run `tmux send-keys -t <pane_id> Enter` once.

## Hazards

- **Wrong session.** Hazard: another ticket's agent changes the wrong worktree. Confirm the matched `path` contains the requested ticket key before sending.
- **Interrupting an agent.** Hazard: `Escape` or `C-c` cancels the target's current work. Never send interrupt keys unless the user asks.
- **Secrets in transit.** Hazard: tmux buffers and agent transcripts store the message. Do not include credentials in the message.

## Report

State the target session, window, agent, and whether the agent accepted the message. Do not wait for the delegated task to finish unless the user asks.
