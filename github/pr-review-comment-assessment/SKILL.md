---
name: pr-review-comment-assessment
description: Assess unresolved or latest PR review comments and tell the user whether you agree, with current-head code evidence.
---

# PR Review Comment Assessment

Use this when the user asks you to review a pull request and specifically asks for your opinion on unresolved comments, latest comments, review threads, or whether existing reviewer feedback is valid.

## Workflow

1. Gather PR metadata and confirm the exact tree under review:
   - PR title/body, base/head refs, `headRefOid`, changed files, checks.
   - Check out the PR locally and confirm local `HEAD` matches the GitHub `headRefOid`.
2. Fetch comments from multiple sources:
   - Top-level issue comments.
   - Inline pull request comments.
   - Formal reviews and review bodies.
   - GitHub GraphQL `reviewThreads` for authoritative resolved/unresolved state.
3. For GitHub unresolved state, do not rely only on REST inline comments or `gh pr view --json comments,reviews`. Use GraphQL `reviewThreads` and filter `isResolved == false`.
4. Read the current PR-head file around each unresolved or latest substantive comment with line numbers. Diff hunks can be stale after force-pushes or follow-up commits.
5. For each substantive comment, classify it directly:
   - agree / still valid and blocking
   - partly agree / valid but should be narrowed or rephrased
   - disagree / not a real issue, with evidence
   - addressed in current head
   - obsolete/outdated because the code moved
6. Run targeted verification when feasible, but keep it separate from review judgement. Green CI or targeted tests do not resolve a logic/design concern by themselves.
7. Final response should include:
   - Scope / Checks run.
   - Verdict: approve/comment/changes requested.
   - Dedicated “Opinion on unresolved/latest comments” section, comment-by-comment.
   - Any additional findings discovered while checking the comments.

## GraphQL unresolved-thread query

```bash
gh api graphql \
  -f owner="$OWNER" \
  -f repo="$REPO" \
  -F number="$PR_NUMBER" \
  -f query='query($owner:String!, $repo:String!, $number:Int!) {
    repository(owner:$owner, name:$repo) {
      pullRequest(number:$number) {
        reviewThreads(first:100) {
          nodes {
            id
            isResolved
            isOutdated
            path
            line
            originalLine
            comments(first:20) {
              nodes {
                author { login }
                body
                createdAt
                url
                path
                line
                originalLine
                outdated
                diffHunk
              }
            }
          }
        }
      }
    }
  }'
```

## Pitfalls

- REST `/pulls/{n}/comments` lists inline comments but does not provide the review-thread resolved state.
- A latest formal review body can summarize still-blocking concerns even if only one inline thread is currently unresolved.
- Do not dismiss style/design comments as mere preference until checking the closest sibling implementation or repo pattern.
- When a comment points at a past line, inspect current head before saying whether it is still valid.
- Respect explicit instructions not to post comments externally; provide the assessment to the user only.
