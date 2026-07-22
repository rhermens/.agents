---
name: github-cli
description: Work with GitHub repositories, issues, pull requests, reviews, Actions, releases, files, and code search using the GitHub CLI (`gh`) instead of the GitHub MCP server. Use when the user asks about GitHub data or wants GitHub operations from the terminal.
---

# GitHub CLI Skill

Use this skill for GitHub tasks. Prefer the local `gh` CLI and shell commands over MCP.

## Requirements

- `gh` must be installed.
- Authentication should be available through `gh auth status`. If not, ask the user to run `gh auth login`.
- For JSON-heavy tasks, use `jq` when available.

Check once if needed:

```bash
gh auth status
```

If `gh auth status` reports an invalid stored account but a valid token is available from the Hermes GitHub auth environment, prefer the token for non-interactive jobs instead of stopping:

```bash
source "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/gh-env.sh" >/dev/null 2>&1 || true
export GH_TOKEN="$GITHUB_TOKEN"
gh api user --jq .login
```

This is especially useful in cron/scheduled jobs where the user is not present to re-run `gh auth login`. Do not print the token.

## Safety

- Read operations are fine without confirmation.
- Before mutating GitHub state, summarize the exact action and ask if the user wants to proceed unless they explicitly requested the mutation.
- Mutating operations include: creating/editing/closing issues, commenting, merging PRs, approving/requesting changes, dispatching workflows, deleting releases/assets, changing labels/milestones, editing repo settings.
- Never print tokens. Do not run `gh auth token` unless strictly necessary; if used, do not echo it.

## Repository Context

Detect the current repository:

```bash
gh repo view --json owner,name,url,defaultBranchRef
```

Use an explicit repo with `-R owner/repo` when working outside a checked-out repository.

## Common Read Operations

### Repository info

```bash
gh repo view OWNER/REPO --json nameWithOwner,description,url,defaultBranchRef,isPrivate,repositoryTopics,licenseInfo
```

### Issues

```bash
gh issue list -R OWNER/REPO --state open --limit 50 --json number,title,author,labels,assignees,createdAt,updatedAt,url

gh issue view ISSUE_NUMBER -R OWNER/REPO --json number,title,body,author,labels,assignees,comments,state,url
```

### Pull requests

```bash
gh pr list -R OWNER/REPO --state open --limit 50 --json number,title,author,headRefName,baseRefName,isDraft,mergeable,reviewDecision,statusCheckRollup,url

gh pr view PR_NUMBER -R OWNER/REPO --json number,title,body,author,headRefName,baseRefName,files,commits,reviews,comments,checks,statusCheckRollup,mergeable,reviewDecision,url

gh pr diff PR_NUMBER -R OWNER/REPO --patch
```

### Actions and workflow runs

```bash
gh run list -R OWNER/REPO --limit 20 --json databaseId,displayTitle,event,status,conclusion,workflowName,createdAt,updatedAt,url

gh run view RUN_ID -R OWNER/REPO --json databaseId,displayTitle,status,conclusion,jobs,url

gh run view RUN_ID -R OWNER/REPO --log-failed
```

### Releases

```bash
gh release list -R OWNER/REPO --limit 20

gh release view TAG -R OWNER/REPO --json tagName,name,body,isDraft,isPrerelease,createdAt,publishedAt,assets,url
```

### Files and contents

```bash
gh api repos/OWNER/REPO/contents/PATH --jq .

gh api repos/OWNER/REPO/readme --jq .download_url
```

For source code in the current checkout, prefer local tools (`rg`, `git`, `read`) over GitHub API.

### Search

```bash
gh search repos "QUERY" --limit 20 --json fullName,description,url,stars,updatedAt

gh search issues "QUERY repo:OWNER/REPO" --limit 20 --json number,title,state,repository,url,updatedAt

gh search prs "QUERY repo:OWNER/REPO" --limit 20 --json number,title,state,repository,url,updatedAt

gh search code "QUERY repo:OWNER/REPO" --limit 20 --json repository,path,sha,url
```

## Mutating Operations

Only run after the user explicitly asks or confirms.

```bash
# Create issue
gh issue create -R OWNER/REPO --title "TITLE" --body "BODY" --label "label"

# Comment on issue or PR
gh issue comment ISSUE_NUMBER -R OWNER/REPO --body "COMMENT"
gh pr comment PR_NUMBER -R OWNER/REPO --body "COMMENT"

# Review PR
gh pr review PR_NUMBER -R OWNER/REPO --comment --body "COMMENT"
gh pr review PR_NUMBER -R OWNER/REPO --approve --body "COMMENT"
gh pr review PR_NUMBER -R OWNER/REPO --request-changes --body "COMMENT"

# Merge PR
gh pr merge PR_NUMBER -R OWNER/REPO --squash --delete-branch

# Trigger workflow
gh workflow run WORKFLOW_FILE_OR_NAME -R OWNER/REPO --ref BRANCH
```

## `gh api` Patterns

Use `gh api` for endpoints not covered by first-class commands.

```bash
# REST
 gh api repos/OWNER/REPO/pulls/PR_NUMBER/files --paginate --jq '.[] | {filename, status, additions, deletions}'

# GraphQL
 gh api graphql -f query='query($owner:String!, $repo:String!) { repository(owner:$owner, name:$repo) { name stargazerCount } }' -f owner=OWNER -f repo=REPO
```

Prefer `--json` and `--jq` to keep output compact. Use `--paginate` when the result can exceed one page.

## MCP Replacement Map

Use these CLI equivalents instead of GitHub MCP tools:

- get repository/file metadata: `gh repo view`, `gh api repos/.../contents/...`
- list/search issues and PRs: `gh issue list`, `gh pr list`, `gh search issues`, `gh search prs`
- inspect PRs and diffs: `gh pr view`, `gh pr diff`, `gh api repos/.../pulls/.../files`
- Actions runs/logs: `gh run list`, `gh run view`, `gh run view --log-failed`
- create/update/comment/review: `gh issue create/edit/comment`, `gh pr comment/review/merge`
