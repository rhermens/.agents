---
name: adr-authoring
description: Write, supersede, and review Architecture Decision Records (ADRs). Use when the user asks to record, document, or update an architectural decision or ADR.
---

# ADR Authoring

Record one architectural decision per ADR. Capture the context, the options, the decision, and its consequences so future readers understand why.

Use `obsidian-design-notes` for other design notes in the Obsidian vault. Use `architect` or `plan` to make the decision itself.

## Workflow

1. **Find the ADR location.** Resolve the vault path as the `obsidian` skill describes. Then select the first match:
   1. If the vault exists, find the project folder that matches the repository or topic name. Use its existing ADR or decisions folder.
   2. If the project folder has no ADR folder, find an ADR or decisions folder elsewhere in the vault. Propose a project subfolder that follows that pattern.
   3. If the vault has no ADR folder, propose `<project folder>/Decisions/`.
   4. If there is no vault, look for `.adr-dir`, `docs/adr/`, `doc/adr/`, `docs/decisions/`, or `adr/` in the repository. If none exists, propose `docs/adr/`.
   5. Ask before you create a folder.
2. **Learn the local convention.** Read the two most recent ADRs and any template in the ADR directory. Match their filename pattern, headings, status values, and date format.
3. **Collect the decision inputs.** Read relevant code, issues, and discussion. Identify the problem, decision drivers, options, chosen option, and consequences.
4. **Ask for missing facts.** If the decision, its drivers, or the rejected options are unknown, ask the user. Never invent rationale or consensus.
5. **Assign the number.** Use the highest existing ADR number plus one. Keep the local zero-padding.
6. **Write the ADR.** If no local template exists, use [`assets/adr-template.md`](assets/adr-template.md).
7. **Handle supersession.** If the ADR replaces an earlier ADR, link both ways. Change only the earlier ADR's status line and add a link.
8. **Update the index.** If the ADR folder has an index, README, or project overview note, add the new entry. In the vault, use `[[Wikilinks]]`.
9. **Validate the ADR.** Confirm that the number is unique and that the filename matches the local pattern. Confirm that every relative link and `[[Wikilink]]` resolves.
10. **Report the result.** List created and changed paths, the status, and open questions.

## Content rules

Keep one decision in each ADR. If the input contains several decisions, propose several ADRs.

### Writing style

- Use one name for each option and concept. Use the same name in every section.
- Define each required domain term where readers first need it.
- Prefer familiar words, direct statements, and active voice.
- Target 25 words or fewer for each sentence.
- Give each paragraph one topic. Use headings, vertical lists, and tables to show structure.
- Preserve exact commands, identifiers, API names, and quotations from the sources.

### Sections

- **Title:** Write a short imperative phrase, such as "Use PostgreSQL for event storage".
- **Context:** State facts and constraints. Do not argue for the chosen option.
- **Considered options:** List at least two options. Include "do nothing" when it is a real option. Use a table to compare them.
- **Decision:** Write one or two sentences in the form "We will …, because …".
- **Consequences:** List positive and negative consequences separately.
- **Risks:** Identify each risk, its possible consequence, and the action that prevents it.
- **Follow-up:** Put one action in each item. State a condition before its action.
- **References:** Link to evidence such as issues, PRs, benchmarks, or documentation.

## Status rules

Use the local status values. If none exist, use `Proposed`, `Accepted`, `Rejected`, `Deprecated`, or `Superseded by ADR-NNNN`.

- Set new ADRs to `Proposed` unless the user confirms that the decision is accepted.
- Never rewrite the decision or rationale of an `Accepted` ADR. Write a new ADR that supersedes it.
- Correct typos and broken links in an existing ADR only when the user asks.
