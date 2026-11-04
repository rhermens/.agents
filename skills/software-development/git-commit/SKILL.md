---
name: git-commit
description: Create Git commits with Conventional Commits messages. Use when the user asks to commit or save work.
---

# Git Commit

Commit staged work with a Conventional Commits message. Create a new commit each time so normal pushes work.

## Message format

Use this format:

```text
<type>[optional scope][!]: [TICKET-123: ]<description>

[optional body]

[optional footer(s)]
```

Apply these rules:

- Use one of these types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Use a lowercase noun for the scope, such as `feat(auth): ...`.
- If the branch name contains a Jira ticket key such as `DR-1234`, put it after the colon: `fix(auth): DR-1234: handle expired tokens`.
- If the branch name has no ticket key, omit the ticket segment.
- Write the description in the imperative mood, lowercase, without a final period. Keep the ticket key uppercase.
- Keep the header, including the ticket key, at 72 characters or fewer.
- Explain why the change exists in the body, not how.
- If the change breaks an API, add `!` after the type or scope and a `BREAKING CHANGE: <details>` footer.

A header is conventional when it matches this pattern:

```text
^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._/-]+\))?!?: ([A-Z][A-Z0-9]+-[0-9]+: )?.+
```

## Workflow

1. **Inspect the state.** Run `git status --short` and `git diff --cached --stat`.
2. **Confirm the staged content.** If nothing is staged, stage only the files that belong to the current task. Never stage secrets, build output, or unrelated changes. If the scope is unclear, ask the user.
3. **Write the message.** Describe the staged change only.
4. **Run the commit.** Run `git commit -m "<header>" -m "<body>"`.
5. **Verify the result.** Run `git log -1 --format='%H%n%B'` and `git status --short`.

## Hazards

- **Pre-commit hook failure.** Hazard: no commit is created, or hooks modify files. If a hook fails, fix the reported issue, stage the fix, and commit again. Never use `--no-verify` unless the user asks.
- **Detached `HEAD`.** Hazard: the commit is not on a branch. If `git branch --show-current` is empty, stop and ask the user.

## Report

State the commit hash and header.
