---
name: obsidian-design-notes
description: "Author design, architecture, and project documentation notes in the Obsidian vault. Covers format conventions, mermaid diagram usage, multi-note linking, and git-friendly data file patterns."
metadata:
  platforms: "linux, macos, windows"
  hermes.tags: "obsidian, design, architecture, documentation, mermaid"
  hermes.related_skills: "obsidian, knowledge-base-maintenance"
---

# Obsidian Design Notes

Use this skill when the user asks to write design notes, architecture notes, project documentation, or technical planning notes in the Obsidian vault. This covers *how* to format and structure the notes — for the mechanics of reading/writing files, load `obsidian` instead.

## Format conventions

1. **Concise text + mermaid diagrams.** Keep paragraphs to three sentences or fewer. Use bullets for lists and mermaid diagrams for structure, data flow, and state transitions. Obsidian renders mermaid natively in preview mode.

2. **Mermaid diagram types by use case:**
   - `flowchart LR/TD` — component architecture, decision trees, pipelines.
   - `sequenceDiagram` — request/response flows, hook lifecycles, inter-process communication.
   - `stateDiagram-v2` — state machines, lifecycle transitions.
   - `erDiagram` — data models, entity relationships.

3. **Split multi-component topics into linked sub-notes.** Keep the overview to one screen, with goals, an architecture diagram, and component links. Use one note per logical component. Each sub-note links back to the overview and to related siblings via `[[Wikilinks]]`. Example structure:
   ```
   ProjectName/
     ProjectName.md          ← overview, goals, architecture diagram, links
     Components.md           ← component breakdown
     Data Model.md           ← schemas, ER diagram
     Subsystem.md            ← per-subsystem detail
   ```

4. **Tables for structured comparisons.** Use markdown tables for rule matrices, field definitions, and component lists.

## Git-friendly data files

For git-tracked usage logs and trackers, use a single append-only Markdown file.
This preserves the user's preference for one file history over rotation, accepting a higher merge-conflict risk.

Structure:

```markdown
# Skill Usage

| skill | invocations | success | failure | last_used | avg_tokens | notes |
|---|---|---|---|---|---|---|
| test-driven-development | 14 | 12 | 2 | 2026-07-25 | 1200 | |

<!-- log:append
{"ts":"2026-07-25T08:13Z","agent":"hermes","skill":"test-driven-development","session":"abc123","outcome":"success","duration_s":42,"tokens":1200}
-->
```

Two zones:
- **Summary table** at top — machine-regenerated, not hand-edited.
- **Raw log block** inside `<!-- log:append ... -->` — one JSON event per line, append-only.

### Conflict mitigation

- Table is derived data → on conflict, ignore both sides and regenerate.
- Log block appends on distinct lines → `git merge` auto-resolves most concurrent appends.
- Writer does atomic read-append-write (read full file → append line before `-->` → write back) to minimise the race window.
