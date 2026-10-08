---
name: git-commit
description: Create Git commits with Conventional Commits messages. Amend the existing conventional commit on ticket, feat/*, fix/*, or hotfix/* branches. Use when the user asks to commit, save, or amend work.
---

# Git Commit

Commit staged work with a Conventional Commits message. Keep one conventional commit per feature branch by amending it.

## Message format

Use this format:

```text
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

Apply these rules:

- Use one of these types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Use a lowercase noun for the scope, such as `feat(auth): ...`.
- Write the description in the imperative mood, lowercase, without a final period.
- Keep the header at 72 characters or fewer.
- Explain why the change exists in the body, not how.
- If the change breaks an API, add `!` after the type or scope and a `BREAKING CHANGE: <details>` footer.
- If the branch name contains an issue key such as `ABC-123`, add a `Refs: ABC-123` footer.

A header is conventional when it matches this pattern:

```text
^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._/-]+\))?!?: .+
```

## Workflow

1. **Inspect the state.** Run `git status --short` and `git diff --cached --stat`.
2. **Confirm the staged content.** If nothing is staged, stage only the files that belong to the current task. Never stage secrets, build output, or unrelated changes. If the scope is unclear, ask the user.
3. **Find the base branch.** Run `git symbolic-ref --short refs/remotes/origin/HEAD`. If that fails, use `main` or `master`, whichever exists.
4. **List the branch commits.** Run `git log --format='%H %s' <base>..HEAD`.
5. **Choose commit or amend.** Apply the amend rule below.
6. **Write the message.** Describe the full branch change, including earlier amended work.
7. **Run the commit.** Use the command from the matching case below.
8. **Verify the result.** Run `git log -1 --format='%H%n%B'` and `git status --short`.

### Amend rule

```text
amend ⇔ feature(current) ∧ ahead ≥ 1 ∧ conventional(HEAD) ∧ author(HEAD) = git config user.email
```

- `current`: output of `git branch --show-current`.
- `feature(current)`: `current` matches this pattern, case-insensitively:

  ```text
  ^(([A-Z][A-Z0-9]+-[0-9]+)([-_/].*)?|(feat|feature|fix|bugfix|hotfix)/.+)$
  ```

  Examples: `ABC-123`, `ABC-123-add-login`, `feat/login`, `hotfix/ABC-123`.
- `ahead`: number of commits in `<base>..HEAD`.
- `conventional(HEAD)`: the `HEAD` header matches the conventional pattern.

If any condition is false, create a new commit. Never amend on `main`, `master`, `develop`, `release/*`, `env/*`, or other shared branches.

### Commands

- **New commit:** `git commit -m "<header>" -m "<body>"`.
- **Amend:** `git commit --amend -m "<header>" -m "<body>"`. Update the message so it covers the old and new changes.
- **Amend with an unchanged message:** `git commit --amend --no-edit`.

## Hazards

- **Amended commit already pushed.** Hazard: the remote history differs from the local history. If `git status -sb` shows the branch diverged after the amend, tell the user to push with `git push --force-with-lease`. Do not push unless the user asks.
- **Pre-commit hook failure.** Hazard: no commit is created, or hooks modify files. If a hook fails, fix the reported issue, stage the fix, and commit again. Never use `--no-verify` unless the user asks.
- **Detached `HEAD`.** Hazard: the commit is not on a branch. If `git branch --show-current` is empty, stop and ask the user.

## Report

State these items:

- whether you created a new commit or amended one,
- the commit hash and header,
- whether a force push is necessary.
