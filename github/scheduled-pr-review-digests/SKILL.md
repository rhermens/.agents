---
name: scheduled-pr-review-digests
description: Produce scheduled GitHub PR review digests that rank non-draft open PRs by user-review need, importance, and size, with a quick targeted risk review.
---

# Scheduled PR Review Digests

Use this skill when a cron/scheduled job asks to scan repositories for open PRs the user may need to review and deliver a concise digest. It complements `github-cli`, `github-code-review`, and `review` by focusing on multi-repository triage rather than a full line-by-line review.

## Workflow

1. **Authenticate non-interactively.** Use `gh api user --jq .login`; if `gh auth status` is stale, source the GitHub auth env and set `GH_TOKEN` without printing it.
2. **List PRs for every requested repo.** Use `gh pr list -R OWNER/REPO --state open --limit 100 --json number,title,author,headRefName,baseRefName,isDraft,updatedAt,createdAt,url,additions,deletions,changedFiles,reviewDecision,statusCheckRollup` and filter out drafts exactly when requested.
3. **Fetch details for every candidate.** Use `gh pr view ... --json reviews,files,commits,headRefOid,statusCheckRollup` so you can determine the user's latest review state and whether new commits landed after it.
4. **Classify review need.** Compare timestamps in UTC.

   ```text
   needs_attention(p, u) ⇔ no_review(p, u) ∨ review_time(p, u) < commit_time(p)
                            ∨ (review_invalidated(p, u) ∧ decision(p) ∈ {REVIEW_REQUIRED, CHANGES_REQUESTED})
   ```

5. **Rank by importance and order-of-magnitude size.** Prioritize destructive/financial/auth/permission/external-provider/date/deadline changes above cosmetic/test-only/dependency-only changes. Use additions/deletions/changed files as rough size buckets, not as the only ordering signal.
6. **Do a targeted quick review for high-risk PRs.** Inspect PR body, changed files, CI, and targeted diffs/full files around risky behavior. For full file context at the PR head, fetch `headRefOid` and use `gh api "repos/OWNER/REPO/contents/PATH?ref=$HEAD_SHA" --jq .content | base64 -d`.
7. **Report only useful signal.** If nothing new genuinely needs the user's attention, return exactly `[SILENT]`. Otherwise start with the explicit count of PRs the user needs to review, followed by ranked items.

## Review checks to include in digests

- For paired frontend/backend feature PRs, trace permission changes end-to-end. If permissions are split or renamed (for example create vs update), check frontend route guards/buttons/form modes and backend endpoints used by both modes, especially quote/preview endpoints. Flag mode-agnostic guards such as `!can(CREATE) || !can(UPDATE)` that require both permissions when create-only or update-only users should be allowed.
- For nested resource routes, verify both query and mutation handlers enforce the parent/child relationship, not just the controller route shape.
- For event-driven or audited updates, note whether emitted events include the values downstream consumers need, especially derived amounts or provider target fields.
- For approved PRs that the user has not reviewed, still include them when the user asked to be pinged if they personally have not reviewed. Another approval does not satisfy the user's review reminder.
- For Dependabot or lockfile-only PRs, keep the review brief but call out failing CI and the highest-risk package groups. Do not recommend approval while required checks are red.

## Output shape

Begin with a scope/checks note listing repos scanned, filters applied, and whether the review was GitHub-only or locally verified. Then use concise ranked entries with:

- repo/PR number/title
- author
- size bucket and raw `+/-`/file count
- importance rationale
- user's review status, including stale review timestamps when relevant
- CI summary
- URL
- short “important things to watch” bullets with concrete files/functions when found

Close with a short summary of the most important actions. Keep the digest actionable; do not turn it into a full code review unless asked.
