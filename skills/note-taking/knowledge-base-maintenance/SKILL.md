---
name: knowledge-base-maintenance
description: Audit an Obsidian/Markdown knowledge base for notes that can be merged, deduplicated, renamed, or linked.
platforms: [linux, macos, windows]
---

# Knowledge Base Maintenance

Use this skill when the user asks to scan notes, clean up an Obsidian vault, find merge candidates, identify duplicate notes, find orphan notes, or suggest wikilinks/backlinks. This complements the protected `obsidian` skill: use `obsidian` for basic vault path resolution and file operations, then use this skill for graph-maintenance analysis.

## Principles

- Default to **reporting recommendations, not editing notes**. Merges, deletes, and bulk link insertion are destructive enough that they should be confirmed separately.
- If the user or cron prompt explicitly asks to merge/link/remove notes, treat that as edit authorization for the stated scope. Still be conservative, keep a diff report, and verify the result.
- Prefer **class-level cleanup findings** over dumping every low-confidence similarity match.
- Separate findings by confidence:
  1. exact raw/body duplicates,
  2. same normalized title / duplicate IDs,
  3. stub-to-full-note merge candidates,
  4. explicit unlinked title mentions,
  5. thematic/similarity-only link candidates.
- Watch for nested mirror directories, e.g. `Archive/Foo/Archive/Foo`, where many files are body-identical. Report whether mirrored pairs diverge before recommending deletion.
- Treat false positives conservatively: generic titles such as `Index`, `Delete`, `Monitoring`, `Extra costs`, `Untitled`, or personal/work cross-domain homonyms should be manually reviewed, not auto-linked.
- Do not delete notes just because they are short. Only remove notes that are clearly empty, frontmatter-only, scratch/trash, or old orphan stubs with little standalone meaning and no in/out wikilinks/backlinks.

## Workflow

1. Resolve the vault path using the `obsidian` skill convention: `OBSIDIAN_VAULT_PATH`, else current working directory if it is the vault, else the documented fallback.
2. Inventory markdown notes excluding `.git`, `.obsidian`, `node_modules`, and sync/system folders. Exclude `.trash` by default for analysis, but include `.trash` only when the user explicitly asks to remove old/meaningless notes or clean trash-like stubs.
3. Parse frontmatter aliases/IDs, wikilinks, tags, title tokens, body text, and hashes.
4. Produce duplicate groups:
   - exact raw hash duplicates,
   - body hash duplicates after frontmatter removal,
   - same normalized title,
   - duplicate frontmatter `id` values if present.
5. Produce merge candidates using conservative signals: identical body, same ID, high content similarity, high title overlap, or a short/stub note overlapping a larger note.
6. Produce link candidates using two buckets:
   - explicit title/alias mention in another note body without an existing wikilink,
   - thematic similarity pairs that are not already linked.
7. Read representative high-ranking notes before making the final recommendation so the final answer can filter obvious false positives.
8. For authorized edits:
   - merge duplicates by preserving the richer/canonical note, adding source aliases/IDs when useful, and deleting the source only after verifying the destination contains the useful content,
   - add only high-confidence wikilinks; avoid generic homonyms and personal/work cross-domain collisions,
   - remove only notes that satisfy the conservative deletion criteria above,
   - leave a root note named like `Knowledge Base Maintenance Diff YYYY-MM-DD HHMMSS.md` containing the summary, file list/name-status, and representative unified diff.
9. Final answer should include:
   - vault path and note count,
   - highest-confidence duplicate/merge groups,
   - concrete wikilink opportunities,
   - what was edited or explicitly not edited,
   - path to any structured report and/or root diff note.

## Cron-job notes

- Cron jobs may run without an interactive approval path; prefer `terminal` or file tools over `execute_code` if `execute_code` is blocked in cron mode.
- If `skills.external_dirs` creates a skill-name collision, `skill_view` may fail as ambiguous. Diagnose by reading the concrete `SKILL.md` path from the collision message or by removing the stale duplicate; do not loop on the same ambiguous skill name.
- After making edits in a Git-backed vault, verify with `git status`, confirm expected deletions are absent, confirm modified targets exist, and include the root diff note path in the final report.
- In vaults with auto-backup/auto-commit hooks, `git status` may become clean while your changes were committed during the run. If that happens, inspect recent commits (`git log --oneline -6`, `git show --name-status <commit>`) and build the root diff note from the relevant commit range rather than from the now-empty working tree.
- When embedding the diff in the root report note, exclude the report note itself from the embedded unified diff to avoid recursive/self-referential diffs. If unrelated non-markdown files changed concurrently, scope the embedded cleanup diff to markdown pathspecs and mention only the markdown cleanup in the note.
- In report-note action summaries, avoid raw wikilinks for target notes unless you intentionally want the report note to add backlinks/noise. Prefer code-form paths such as `` `Folder/Note` (alias) `` in summaries, while the actual edited notes should contain the real `[[wikilinks]]`.

## Reusable script

A reusable conservative scanner is provided at `scripts/scan_merge_link_candidates.py`. Run it with:

```bash
OBSIDIAN_VAULT_PATH=/path/to/vault python scripts/scan_merge_link_candidates.py
# or
python scripts/scan_merge_link_candidates.py /path/to/vault
```

By default the scanner excludes `.trash`. If the user explicitly asked to clean trash-like stubs, include trash notes with:

```bash
INCLUDE_TRASH=1 python scripts/scan_merge_link_candidates.py /path/to/vault
# or
python scripts/scan_merge_link_candidates.py /path/to/vault --include-trash
```

It writes `/tmp/obsidian_note_scan.json` and prints a human-readable summary. The script is read-only.

## Pitfalls

- Similarity based on one shared token, URLs, or very short notes is noisy. Suppress or label these as low confidence.
- Excalidraw `.excalidraw.md` files often contain generated text; exact duplicates are useful, but thematic similarity is often less meaningful.
- Frontmatter IDs and aliases can cause self-mentions; search only the body when looking for missing wikilinks.
- For link insertion, match explicit title/alias mentions case-insensitively but preserve the matched surface text in the wikilink alias, e.g. `contracts` -> `[[Folder/Contracts|contracts]]`. Mask existing wikilinks, URLs, and fenced code blocks before replacement.
- When detecting old orphan notes, remember that code-fenced diagrams, JSON, Mermaid, sheet blocks, and Excalidraw content may tokenize to zero or few words. Do not delete these as meaningless solely because word count is low; review representative content and prefer reporting/no deletion unless they are clearly empty/trash.
- In sync-backed vaults, file mtimes may reflect sync/backup activity rather than note age; for date-titled daily/log notes, use the title/path date or frontmatter date when judging whether a note is old.
- If archive mirrors exist, de-duplicate mirror copies in the report so the user sees one actionable recommendation instead of dozens of repeated pairs.
