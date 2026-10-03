---
name: obsidian-design-notes
description: "Author design, architecture, and project documentation notes in the Obsidian vault. Covers format conventions, mermaid diagram usage, multi-note linking, and git-friendly data file patterns."
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [obsidian, design, architecture, documentation, mermaid]
    related_skills: [obsidian, knowledge-base-maintenance]
---

# Obsidian Design Notes

Use this skill when the user asks to write design notes, architecture notes, project documentation, or technical planning notes in the Obsidian vault. This covers *how* to format and structure the notes — for the mechanics of reading/writing files, load `obsidian` instead.

## Format conventions

1. **Concise text + mermaid diagrams.** Keep prose tight — tables and bullet points over paragraphs. Use mermaid diagrams for structure, data flow, and state transitions. Obsidian renders mermaid natively in preview mode.

2. **Mermaid diagram types by use case:**
   - `flowchart LR/TD` — component architecture, decision trees, pipelines.
   - `sequenceDiagram` — request/response flows, hook lifecycles, inter-process communication.
   - `stateDiagram-v2` — state machines, lifecycle transitions.
   - `erDiagram` — data models, entity relationships.

3. **Split multi-component topics into linked sub-notes.** An overview note with goals + an architecture diagram links to component-detail sub-notes via `[[Wikilinks]]`. One note per logical component, not one giant note. Example structure:
   ```
   ProjectName/
     ProjectName.md          ← overview, goals, architecture diagram, links
     Components.md           ← component breakdown
     Data Model.md           ← schemas, ER diagram
     Subsystem.md            ← per-subsystem detail
   ```

4. **Tables for structured comparisons.** Use markdown tables for rule matrices, field definitions, component lists — not prose.

## Git-friendly data files

When the user wants a usage log, tracker, or similar data file that is git-tracked and append-only, use a **single markdown file** (not per-month rotation, not one-file-per-event). Structure:

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

### Why single file (not rotated)

The user explicitly prefers one file with one git history over monthly rotation or per-event files. The tradeoff is slightly higher conflict risk, mitigated by the append-only log block format above.

## Pitfalls

1. **Don't write long prose paragraphs.** The user wants concise, scannable notes. If you find yourself writing a paragraph longer than 3 sentences, refactor into a table or bullet list.

2. **Don't create one giant note for a multi-component system.** Split into sub-notes and link them. The overview note should fit on one screen.

3. **Don't rotate data files by month.** Use a single file. The user finds file proliferation worse than merge conflict risk.

4. **Don't forget wikilinks between sub-notes.** Each sub-note should link back to the overview and to related siblings.
