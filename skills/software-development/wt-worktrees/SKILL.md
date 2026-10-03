---
name: wt-worktrees
description: Create, open, configure, verify, and clean up Git worktrees with rhermens/wt. Use when requests mention the `wt` CLI, `.wt.lua`, automated worktree setup, copied or linked worktree files, or wt-managed tmux sessions. Do not use for Windows Terminal's `wt.exe`.
license: MIT
compatibility: Requires Git and the rhermens/wt CLI. Lua configuration features depend on the installed wt release. tmux actions require tmux.
metadata:
  author: Roy Hermens
  version: "1.0.0"
---

# wt Worktrees

Use `wt` to create or reopen a Git worktree and apply its configured setup actions.

## Safety rules

- Run `wt` from the intended source checkout.
- Inspect both configuration files before execution.
- Treat every `wt.command` and `wt.tmux.window` value as executable shell input.
- Never pass untrusted text into Lua-generated shell commands.
- Confirm before adding secrets to `.wt.lua` or copying them into a worktree.
- Confirm before removing a worktree, branch, directory, or tmux session.
- Do not assume a successful `wt` exit means every setup action succeeded.

`wt` has no dry-run mode. It can create branches, directories, symlinks, processes, and tmux sessions.

## Workflow

Follow these steps before changing or opening a worktree.

### Inspect the environment

1. Confirm the dependency:

   ```sh
   command -v wt
   wt --help
   ```

2. Confirm the current checkout:

   ```sh
   git rev-parse --show-toplevel
   git status --short --branch
   git worktree list
   ```

3. Read the configuration files that exist:

   ```text
   ~/.config/wt/config.lua
   <source-checkout>/.wt.lua
   ```

Both scripts execute in that order. Scalar settings can change later. Copy, link, command, and tmux-window actions accumulate.

If configuration intent is unclear, stop and ask before running `wt`.

### Create or open a worktree

Use a short relative path whose basename is the intended worktree and branch name:

```sh
wt <path>
```

Examples:

```sh
wt feature-login
wt ../worktrees/feature-login
```

For a new target, `wt` creates a worktree and branch from the current `HEAD`. If the basename matches an existing branch, it checks out that branch.

If the target already exists, `wt` opens it and reapplies configured actions. Reapplication can overwrite copied files or report existing-link errors.

Pass configuration arguments after `--`:

```sh
wt feature-login -- "implement login flow"
```

Lua reads these arguments from zero-based `wt.args`, such as `wt.args[0]`.

### Configure setup actions

Edit the repository's `.wt.lua` only when the user requests repository-specific automation.

```lua
wt.worktrees_directory("../worktrees")

wt.copy({ src = ".env.example" })
wt.copy({ glob = "config/*.local", glob_ignore = "config/private*" })

wt.link({ src = "node_modules" })

wt.command("pnpm install")

wt.tmux.session(true)
wt.tmux.window("")
wt.tmux.window("nvim")
```

Apply these constraints:

- Keep `src` paths relative.
- Use `glob_ignore` to exclude nested worktree directories and private files.
- Quote shell values safely before constructing commands from `wt.args`.
- Use `wt.tmux.session(false)` when repository configuration must disable a global tmux setting.
- Do not expect local configuration to clear action lists added globally.

Use `~/.config/wt/config.lua` only for defaults the user wants across all repositories.

## Verification

After `wt` returns, verify each requested outcome:

```sh
git worktree list
git -C <resolved-worktree-path> status --short --branch
git -C <resolved-worktree-path> branch --show-current
```

Inspect copied files and symlink targets with read-only commands. If tmux is enabled, check its session:

```sh
tmux list-sessions
```

Review the complete `wt` output. Setup command failures can appear only as warnings while `wt` still exits successfully.

Report:

- the source checkout,
- the resolved worktree path and branch,
- the configuration files applied,
- the setup actions verified,
- every warning or failed action.

## Clean up

Use native Git commands because `wt` does not provide cleanup commands.

After explicit authorization, inspect before removal:

```sh
git -C <worktree-path> status --short
git worktree list
```

Then remove only the authorized resources:

```sh
git worktree remove <worktree-path>
git branch -d <branch>
tmux kill-session -t '<session-name>'
```

Do not use `--force` or `git branch -D` unless the user explicitly authorizes discarding the reported changes or commits.
