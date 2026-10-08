---
name: pr-watch
description: Watch a GitHub pull request during an active agent session. Report new comments by severity and investigate newly failed CI/CD checks. Use when asked to monitor or watch a remote PR for feedback or failures.
license: MIT
compatibility: Requires an authenticated GitHub CLI (`gh`); `jq` is useful for filtering. Monitoring stops when the agent session ends.
metadata:
  author: Roy Hermens
  version: "1.0.0"
---

# PR Watch

Watch one remote GitHub PR in the active agent session. Report findings in the agent response; do not post to GitHub.

`gh pr checks --watch` watches checks until completion, but does not watch comments. Poll both channels independently instead.

## Workflow

1. Resolve the full PR URL or `OWNER/REPO` and PR number. If ambiguous, ask for the target.
2. Check `gh auth status`. If authentication fails, ask the user to authenticate without printing credentials.
3. Read `gh pr view PR_NUMBER -R OWNER/REPO --json number,title,url,state,headRefOid`.
4. Take an initial snapshot using the commands below. Record existing comment IDs and check identities in session memory.
5. Report existing failed checks after investigating them. Do not repeat existing comments unless the user requests a baseline summary.
6. Every 60 seconds, refresh PR metadata, all three comment sources, and checks. Use a bounded sleep between passes; do not use `gh pr checks --watch` as the only watcher.
7. Compare each successful snapshot against the last successful snapshot. Report new comments and newly failed checks promptly after that pass.
8. Continue until the user stops the watch or the PR closes. On interruption or API failure, state when monitoring stopped; a skill cannot notify after the session ends.

If a request fails, do not advance its snapshot or treat its missing records as deleted. Retry with a reasonable delay; report persistent authentication or rate-limit failures.

## Collect comments and checks

Use distinct keys `(source, id)` for comments. Fetch all pages so older records never disappear at pagination boundaries:

```bash
gh api "repos/OWNER/REPO/issues/PR_NUMBER/comments?per_page=100" --paginate
gh api "repos/OWNER/REPO/pulls/PR_NUMBER/comments?per_page=100" --paginate
gh api "repos/OWNER/REPO/pulls/PR_NUMBER/reviews?per_page=100" --paginate
gh pr checks PR_NUMBER -R OWNER/REPO --json name,state,bucket,link,workflow,startedAt,completedAt
```

Include nonempty formal review bodies, top-level issue comments, and inline review comments. Do not duplicate inline comments through their parent review. Keep author, body, created time, URL, and inline path/line when available. Note when an inline comment points to an outdated diff; do not silently discard it.

`gh pr checks` can return nonzero for failed or pending checks. Parse its JSON output before treating that exit status as a retrieval error. Match a check across polls by head SHA, check name, run URL, and start time. A failure means a new check entered `bucket == "fail"` or a new failed run appeared. On a new head SHA, track its checks separately. Do not repeat an unchanged failure.

## Investigate failed CI/CD

1. Inspect the failed check URL and its associated job, step, and error. Confirm the run's head SHA matches the PR head being reported.
2. For GitHub Actions, use `gh run view RUN_ID -R OWNER/REPO --json headSha,attempt,conclusion,jobs,url` and `gh run view RUN_ID -R OWNER/REPO --log-failed`.
3. For a rerun, include its attempt number in the failure identity. Use `gh run view RUN_ID --attempt ATTEMPT -R OWNER/REPO --log-failed` when needed.
4. If logs are missing, inspect the check URL or provider's accessible logs. State what is unavailable instead of guessing.
5. Trace the earliest relevant failure to its cause. Distinguish a failing test or build step from a downstream cancellation or deployment block.
6. Report the failing workflow/check, confirmed cause with log evidence, affected SHA/run URL, and a next diagnostic step. Label unconfirmed explanations as hypotheses.

Use the `systematic-debugging` skill for deeper source investigation when the logs alone do not establish the cause. Do not change code, rerun workflows, or mutate remote state without explicit authorization.

## Report new comments

Rank actionable comments by potential impact: **critical** (security, data loss, production outage), **high** (blocking correctness or broken behavior), **medium** (maintainability or nonblocking functional issue), **low** (style or minor improvement), then **informational** (question, approval, or status). Treat this as an inferred priority, not a reviewer-assigned severity. If impact is unclear, say so rather than inventing certainty.

For each new comment, include severity, concise summary, author, location if inline, and a direct link. Within each severity tier, use oldest-first order. Group related comments without hiding their links. Do not claim a comment is valid, resolved, or blocking without inspecting current-head code; use `pr-review-comment-assessment` if the user requests a verdict.

Report CI/CD failures in a separate section after comments, including evidence and any investigation limits. If neither channel changed, remain quiet until the next pass unless the user asks for status.

## Verification and limits

- Confirm the PR target and latest head SHA on each pass.
- Confirm all comment pages and check data were retrieved before reporting a clean pass.
- Include a timestamp with each reported update and state explicitly when monitoring stops.
- This skill monitors only while the agent session and polling loop remain active. For unattended alerts, use a separate scheduler or webhook integration.
