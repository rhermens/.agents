---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first vault work: reading, listing, searching, creating, appending, editing, and adding wikilinks.

## Vault path

Resolve the vault path before file operations.
Use `OBSIDIAN_VAULT_PATH` when set. Otherwise, check `~/Documents/Obsidian Vault`.
If neither resolves to an existing vault, ask for the path before creating or editing notes.

Resolve environment variables and `~` before passing absolute paths to file tools.
Quote vault paths in shell commands.

## Read a note

Use the available file-reading tool with the note's absolute path.
Prefer line numbers and pagination when available.

## List notes

List notes with file search or shell commands.
Restrict the search to the resolved vault or requested subfolder.
For example, `find "/absolute/vault/path" -type f -name '*.md'` lists Markdown notes.

## Search

Use available search tools for filenames and note content.
Restrict content searches to Markdown when appropriate.
With ripgrep available, `rg -n -g '*.md' 'pattern' "/absolute/vault/path"` searches note content.

## Create a note

Use the available file-writing tool with the absolute path and full Markdown content.
Before writing, check whether the target exists. Do not replace an existing note without authorization.

## Append to a note

1. Read the target note.
2. If stable context exists, use the targeted-editing tool to insert content at that anchor.
3. If no stable anchor exists, use a permitted append operation or a read-then-write workflow.
4. Re-read the changed section to verify existing content remains intact.

## Targeted edits

Read the current content before editing.
Use the targeted-editing tool with unique surrounding context.
Check the resulting content or diff for unintended changes.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, link related content with wikilinks.
