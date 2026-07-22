---
name: jira-acli
description: Work with Jira Cloud from the terminal using Atlassian CLI (`acli`) instead of the Jira MCP server. Use for Jira issues/work items, projects, boards, sprints, fields, filters, dashboards, JQL searches, and safe Jira automation.
---

# Jira ACLI Skill

Use this skill for Jira tasks. Prefer Atlassian's official CLI, `acli`, over MCP.

## Requirements

- `acli` must be installed.
- Jira Cloud access must be authenticated with `acli jira auth`.
- For JSON-heavy processing, use `jq` when available.

Check installation and auth:

```bash
acli --version
acli jira auth status
```

If not authenticated, ask the user for their Jira Cloud site and email, then have them run one of:

```bash
# OAuth/browser auth, if supported by your acli version
acli jira auth login --site "your-site.atlassian.net"

# API token auth
# Create a token at https://id.atlassian.com/manage-profile/security/api-tokens
echo "$ATLASSIAN_API_TOKEN" | acli jira auth login --site "your-site.atlassian.net" --email "you@example.com" --token
```

Do not ask the user to paste secrets into chat. Do not print tokens.

## Safety

- Read operations are fine without confirmation.
- Before mutating Jira state, summarize the exact action and ask for confirmation unless the user explicitly requested it.
- Mutating operations include: create, edit, assign, transition, comment, link, delete, bulk changes, sprint changes, field changes, project/board/admin changes.
- For bulk updates, first run the exact JQL/search and show the affected keys/count.
- Avoid making assumptions about issue type names, workflows, custom field IDs, or transition names. Query them first.

## Discover Commands

`acli` command names can vary a little by version. Use help when unsure:

```bash
acli jira --help
acli jira workitem --help
acli jira project --help
acli jira board --help
acli jira sprint --help
acli jira field --help
```

Prefer `--help` over guessing.

## Common Read Operations

### Search issues / work items with JQL

```bash
acli jira workitem search --jql 'project = ABC ORDER BY created DESC'
```

Useful JQL examples:

```jql
assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated DESC
project = ABC AND text ~ "login" ORDER BY updated DESC
project = ABC AND sprint in openSprints() ORDER BY rank
key in (ABC-123, ABC-456)
```

### View one issue / work item

```bash
acli jira workitem view ABC-123
```

### List projects

```bash
acli jira project list
```

### Inspect project details

```bash
acli jira project view ABC
```

### Boards and sprints

```bash
acli jira board list
acli jira sprint list --board-id BOARD_ID
```

### Fields

```bash
acli jira field list
```

Use this before referencing custom fields in scripts.

## Common Mutations

Only run after explicit user request/confirmation.

### Create a work item

```bash
acli jira workitem create --project ABC --type Task --summary "Summary here"
```

If the body/description is long, put it in a temp file and use the relevant `--from-file` or description flag shown by `acli jira workitem create --help`.

### Add a comment

First check the exact comment flag for your version:

```bash
acli jira workitem --help
```

Then use the comment subcommand if available, or fall back to REST API via `acli`/`curl`.

### Transition / assign / edit

Always inspect available operations first:

```bash
acli jira workitem view ABC-123
acli jira workitem --help
```

Then run the version-specific transition/assign/edit command shown by `--help`.

## REST API Fallback

If `acli` lacks a command, use Jira REST API. Prefer `acli` auth/session helpers if your version exposes an API command; otherwise use `curl` with environment variables.

Required env vars for curl fallback:

```bash
export JIRA_SITE="your-site.atlassian.net"
export ATLASSIAN_EMAIL="you@example.com"
export ATLASSIAN_API_TOKEN="..."
```

Search with JQL:

```bash
curl -sS \
  -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" \
  -H 'Accept: application/json' \
  --get \
  --data-urlencode 'jql=project = ABC ORDER BY created DESC' \
  --data-urlencode 'maxResults=20' \
  "https://$JIRA_SITE/rest/api/3/search/jql" | jq .
```

Get an issue:

```bash
curl -sS \
  -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" \
  -H 'Accept: application/json' \
  "https://$JIRA_SITE/rest/api/3/issue/ABC-123" | jq .
```

Create a comment:

```bash
curl -sS \
  -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -X POST \
  --data @comment.json \
  "https://$JIRA_SITE/rest/api/3/issue/ABC-123/comment" | jq .
```

Use Atlassian Document Format for rich-text fields when calling REST directly.

## MCP Replacement Map

Use these CLI equivalents instead of Jira MCP tools:

- auth/connect: `acli jira auth status`, `acli jira auth login`
- list/search issues: `acli jira workitem search --jql '...'`
- view issue: `acli jira workitem view KEY`
- create issue: `acli jira workitem create ...`
- projects: `acli jira project list/view`
- boards: `acli jira board list`
- sprints: `acli jira sprint list`
- fields/custom fields: `acli jira field list`
- unsupported endpoints: Jira REST API via `curl` fallback
