---
name: obsidian-cleanup-heuristics
description: Heuristics and reference scripts for automated cleanup of Obsidian vaults (duplicate removal, stub deletion, and link insertion).
platforms: [linux, macos, windows]
---

# Obsidian Cleanup Heuristics

This skill aggregates practical, reusable patterns for maintaining an Obsidian knowledge base.

## Short‑note deletion heuristic

- **Word count**: less than 10 words after stripping front‑matter.
- **No wikilinks**: the body does not contain any `[[...]]` patterns.
- **No backlinks**: no other note contains a wikilink to the file name.
- **Location**: not inside a `.trash` folder unless explicitly requested.

Such notes are typically placeholders or abandoned drafts and can be safely removed.

## Duplicate detection

- Compute a SHA‑256 hash of the full file content; identical hashes indicate exact duplicates.
- For body‑only duplicates, strip YAML front‑matter before hashing.
- Prefer keeping the note with the richer path (e.g., higher‑level folder) or the one with more backlinks.

## Link‑insertion heuristic

- Scan for plain‑text mentions of other note titles (case‑insensitive) that lack a corresponding `[[...]]` wikilink.
- Insert a wikilink preserving the original casing as an alias: `contracts` → `[[Folder/Contracts|contracts]]`.
- Exclude generic titles (Index, Untitled, etc.) and avoid cross‑domain homonyms.
- Wikilink insertion is allowed inside todo-bearing notes (`- [ ]` / `- [x]`) as long as the checkbox syntax is preserved byte-for-byte. The "never delete todo notes" rule is a deletion rule, not a modification rule.
- When using anchored find-and-replace (e.g. `patch`) to insert a wikilink on a list item, the `old_string` can match across a line boundary and silently swallow trailing characters from the next line. Always anchor on a unique surrounding context (e.g. include the line before and after, or the bullet plus a unique terminator), and re-read the file (or `git diff`) after every patch to confirm the surrounding lines are unchanged.

## Reference implementation

A Python script `scripts/scan_and_cleanup.py` is provided to run these heuristics on a vault path.

```bash
python scripts/scan_and_cleanup.py /path/to/vault
```

The script prints a JSON summary of actions (deletions, merges, link insertions) and can be run in dry‑run mode.

## Usage

1. Resolve the vault path (see the `obsidian` skill for `OBSIDIAN_VAULT_PATH` handling).
2. Run the reference script or implement the heuristics directly with the patterns above.
3. Review the generated summary before applying destructive changes.

---

*This skill is intended for automated cron jobs or manual maintenance runs. Adjust thresholds and exclusions to match your personal workflow.*
