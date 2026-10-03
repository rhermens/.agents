---
name: github-code-review
description: Acquire GitHub pull request metadata, discussion, diffs, and source code for a code review. Use when a review needs GitHub-hosted PR context or a local checkout. Delegate all analysis and findings to the review skill.
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, Git, Code-Acquisition]
    related_skills: [github-cli, review]
---

# GitHub Code Review Acquisition

Acquire the exact GitHub PR tree and its context. Then use the `review` skill for analysis, verification, findings, and verdicts.

This skill does not define review criteria or review output. It never posts comments, submits reviews, approves, requests changes, or changes remote state.

## Requirements

- Run inside a Git repository when using local Git commands.
- Use an authenticated `gh` CLI for private repositories.
- Use an explicit `-R OWNER/REPO` when the current repository is not authoritative.

Check access without printing credentials:

```bash
gh auth status
gh repo view --json nameWithOwner,url,defaultBranchRef
```

## Workflow

### 1. Resolve the pull request

Identify the repository before resolving a PR number. PR numbers are repository-scoped.

```bash
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
gh pr view PR_NUMBER -R "$REPO" --json number,title,url
```

If the PR does not exist in the current repository, ask for the repository or full PR URL. If context suggests one likely alternative, present it for confirmation instead of assuming.

### 2. Gather immutable PR context

Fetch the base branch, head branch, head SHA, description, commits, files, and check state.

```bash
gh pr view PR_NUMBER -R OWNER/REPO \
  --json number,title,body,author,baseRefName,headRefName,headRefOid,url,isDraft,mergeable,reviewDecision,commits,files,statusCheckRollup

gh pr checks PR_NUMBER -R OWNER/REPO

gh pr diff PR_NUMBER -R OWNER/REPO --name-only
```

Record `headRefOid`. Use that SHA as the reviewed remote tree.

Fetch both discussion channels when prior feedback matters:

```bash
gh api repos/OWNER/REPO/issues/PR_NUMBER/comments --paginate
gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments --paginate
```

`gh pr view --json comments,reviews` does not include every inline review thread.

### 3. Compare the local tree with the PR head

Before using an existing checkout, inspect its state and SHA.

```bash
git status --short --branch
git rev-parse HEAD
gh pr view PR_NUMBER -R OWNER/REPO --json headRefOid --jq .headRefOid
```

If the SHAs differ, keep remote PR contents separate from local-only commits. Pass that distinction to the `review` skill.

Do not switch branches when the working tree contains uncommitted changes that checkout could overwrite.

### 4. Acquire the code locally

Prefer a local checkout when full repository context is required.

#### Checkout with GitHub CLI

```bash
gh pr checkout PR_NUMBER -R OWNER/REPO
git status --short --branch
git rev-parse HEAD
```

Confirm the resulting SHA equals `headRefOid`.

#### Fetch without switching the current branch

```bash
git fetch origin pull/PR_NUMBER/head:review/pr-PR_NUMBER
git diff BASE_REF...review/pr-PR_NUMBER --name-only
git diff BASE_REF...review/pr-PR_NUMBER
```

Use a distinct local branch name. Do not overwrite an existing branch.

#### Read remote files without checkout

Use the immutable head SHA when a local checkout is unavailable:

```bash
gh api "repos/OWNER/REPO/contents/PATH?ref=HEAD_SHA" --jq .content | base64 -d
```

Put `ref` in the query string. Passing it with `-f` can produce incorrect contents requests.

#### Fetch the remote patch

```bash
gh pr diff PR_NUMBER -R OWNER/REPO --patch
```

A patch alone may omit surrounding code. Acquire full files for any changed logic that requires context.

### 5. Hand off to the review skill

Provide the `review` skill with:

- repository and PR URL,
- base ref and immutable head SHA,
- local HEAD and dirty-tree state,
- changed file list and full diff,
- relevant full-file context,
- PR description and linked requirements,
- existing discussion when requested,
- remote check results.

The `review` skill owns code analysis, tests, diagnostics, severity, findings, and the final response.

## Completion criteria

```text
complete ⇔ target_unambiguous ∧ head_sha_recorded ∧ tree_delta_explicit
           ∧ review_context_available ∧ ¬remote_state_changed
```

`review_context_available` means the diff and required full-file context are available.
