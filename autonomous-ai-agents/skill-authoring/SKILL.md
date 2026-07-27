---
name: skill-authoring
description: Create, revise, validate, consolidate, and audit portable Agent Skills containing SKILL.md instructions, scripts, references, or assets. Use when the user asks to author a skill, improve skill triggers or structure, merge overlapping skills, or check Agent Skills specification compliance.
license: MIT
compatibility: Agent Skills-compatible harnesses, including Pi, Claude Code, Codex, and Hermes Agent.
metadata:
  author: Roy Hermens
  version: "1.0.1"
---

# Skill Authoring

Create focused skills that reliably change agent behavior without duplicating general instructions or consuming unnecessary context.

## When to use

Use this skill to:

- create or scaffold a reusable Agent Skill,
- revise a `SKILL.md` description, workflow, or supporting files,
- merge redundant skills,
- audit a skill for portability, safety, and specification compliance,
- decide whether instructions belong in a skill, project guidance, or a one-off prompt.

Do not create a skill for a single task, generic advice the agent already follows, or project rules that should always apply. Put always-on repository conventions in `AGENTS.md` or the harness equivalent.

## Workflow

1. **Establish scope.** Identify the desired behavior, triggering requests, non-triggering requests, target harnesses, canonical skill root, and whether the work is creation, revision, merge, or audit. Ask only for decisions that cannot be inferred safely.
2. **Survey existing skills.** Inspect skill names and descriptions before drafting. Read the full bodies of the closest matches. Prefer extending or merging an existing skill over adding a competing trigger.
3. **Design the behavior change.** Define the inputs, ordered actions, safety boundaries, completion criteria, and expected report. Remove instructions that merely restate default agent behavior.
4. **Choose the content boundary.** Keep always-needed instructions in `SKILL.md`; move branch-specific detail to `references/`, deterministic operations to `scripts/`, and reusable output material to `assets/`.
5. **Implement narrowly.** Preserve local conventions when editing. Use portable relative paths, document dependencies, and avoid hard-coded user or repository paths unless the skill is intentionally private and environment-specific.
6. **Validate.** Run [`python scripts/validate_skill.py <skill-directory>`](scripts/validate_skill.py), inspect every warning, and perform any harness-specific validation available.
7. **Exercise the trigger.** Test at least one request that should activate the skill and one nearby request that should not. Confirm the instructions are sufficient without loading unrelated references.
8. **Report the result.** State the created, changed, merged, or removed paths; validation performed; assumptions; and any harness restart or session reload needed for discovery.

## Decide whether a skill is appropriate

Create a skill when all of these are true:

- The task class is likely to recur.
- Specialized process or domain knowledge materially improves the result.
- The behavior can be described with a stable trigger and completion condition.
- The content can remain sufficiently self-contained or reference local support files.

Prefer another mechanism when:

- **Always-on project rule:** use `AGENTS.md` or equivalent project instructions.
- **One-off request:** use the user prompt or a plan.
- **Large external documentation:** reference or index the source instead of copying it into `SKILL.md`.
- **Independent execution role:** use the harness's agent/delegation mechanism rather than pretending a skill creates a separate agent.

## Portable structure

Use the standard directory shape:

```text
skill-name/
├── SKILL.md
├── scripts/       # optional executable helpers
├── references/    # optional on-demand documentation
└── assets/        # optional templates or static resources
```

Resolve relative paths from the skill directory. Keep supporting files inside the skill so the directory can be moved or shared intact.

## Frontmatter

Use portable Agent Skills fields by default:

```yaml
---
name: skill-name
description: Describe what the skill does and the specific requests that should trigger it.
license: MIT
compatibility: Optional environment or dependency requirements.
metadata:
  author: Your Name
  version: "1.0.0"
---
```

Requirements:

- `name` is 1–64 characters, lowercase ASCII letters, digits, and hyphens only.
- `name` has no leading, trailing, or consecutive hyphens.
- The directory name matches `name` for cross-harness portability.
- `description` is non-empty, at most 1024 characters, and explains both capability and trigger.
- `compatibility` is at most 500 characters when present.
- Optional metadata must not be required for correct behavior.
- Treat `allowed-tools` as experimental and harness-specific; omit it unless the target environment explicitly supports it.

## Write effective descriptions

The description is always visible during skill discovery, so optimize it for accurate routing.

A strong description contains:

1. concrete actions or outputs,
2. recognizable user terminology,
3. explicit trigger conditions,
4. enough distinction from neighboring skills.

Prefer:

```yaml
description: Inspect and repair TypeScript import paths after files or domain types move. Use for unresolved-module errors caused by a refactor or bounded-context migration.
```

Avoid:

```yaml
description: Helps with TypeScript.
```

Do not stuff the workflow into the description. Do not make several skills claim broad phrases such as “use for coding” or “use for debugging.”

## Write effective instructions

- Start with the outcome and when the skill applies.
- Use an ordered workflow for sequencing and bullets for decision rules.
- Give each important step a checkable completion condition.
- Co-locate caveats with the action they constrain.
- State destructive-operation authorization boundaries explicitly.
- Include exact commands only when precision is valuable and the command is portable.
- Include examples for ambiguous inputs, outputs, or branching behavior.
- End with verification and reporting expectations.
- Delete no-op prose such as “be careful,” “be thorough,” or “follow best practices.”

Use strong rules sparingly. Reserve **must**, **always**, and **never** for genuine invariants; excessive absolutes make skills brittle or contradictory.

## Write clear technical instructions

Apply these ASD-STE100-inspired principles unless the skill's domain requires different terminology or sentence structure:

- Use one consistent term for each concept. Do not alternate between synonyms for stylistic variety.
- Use familiar words with one clear meaning. Define necessary domain-specific terms where readers first need them.
- Prefer active voice. Write agent actions in the imperative form, such as “Validate the file.”
- Put one instruction in each sentence or numbered step, except when actions must occur at the same time.
- Put a condition before its instruction and separate it clearly, such as “If validation fails, stop the workflow.”
- Keep instructions concise. As a practical target, use no more than 20 words for an instruction and 25 words for descriptive text.
- Give each paragraph one topic. Use short paragraphs, headings, and vertical lists to show structure.
- Use notes only for information. Do not hide required actions in notes or explanatory prose.
- State safety information explicitly: identify the hazard, its possible consequence, and the action that prevents it.
- Preserve exact commands, identifiers, API names, quotations, and required legal or domain terminology even when they exceed these targets.

These principles improve clarity but do not by themselves make a skill ASD-STE100 compliant. Claim compliance only after checking the complete text against the current writing rules and controlled dictionary.

## Progressive disclosure

The entire `SKILL.md` is loaded when the skill activates. Keep it focused.

Move content to `references/` when it is:

- needed only for one branch of the workflow,
- a long API or format reference,
- a catalog of examples,
- likely to change independently.

Move content to `scripts/` when a deterministic implementation is safer or cheaper than repeatedly generating commands. Scripts should be self-contained, validate inputs, fail with actionable errors, avoid destructive defaults, and document nonstandard dependencies.

Place templates and static resources in `assets/`. Link every support file from `SKILL.md` or remove it if unused.

## Merging and revising skills

When skills overlap:

1. Choose the skill with the clearer name, broader valid trigger, or more established support files as the destination.
2. Compare instructions by behavior, not wording.
3. Transfer only unique, still-correct rules and assets.
4. Reconcile contradictions explicitly; prefer safer and more evidence-backed behavior.
5. Remove duplicated prose and stale references.
6. Delete the redundant skill only after validating the destination contains all retained behavior.
7. Search configurations and documentation for references to the removed skill name.

For revisions, preserve useful local conventions but do not perpetuate invalid frontmatter, broken references, or harness-specific assumptions without documenting them.

## Safety and trust

Skills can instruct agents to execute code and perform destructive actions.

- Review third-party skills and scripts before enabling them.
- Never embed credentials, tokens, private URLs, or secrets.
- Require explicit authorization for deletion, publishing, deployments, remote mutations, or bulk edits unless the user's request already grants that exact scope.
- Prefer dry-run and read-only defaults.
- Bound filesystem and network scope.
- Verify generated scripts independently before presenting the skill as safe.

## Validation checklist

- [ ] `SKILL.md` starts with YAML frontmatter at byte zero.
- [ ] `name` and `description` satisfy the Agent Skills constraints.
- [ ] Directory name matches `name`.
- [ ] Description accurately separates this skill from neighboring skills.
- [ ] Body is non-empty and contains an actionable workflow.
- [ ] Referenced scripts, references, and assets exist.
- [ ] Relative paths resolve from the skill directory.
- [ ] Dependencies and compatibility constraints are documented.
- [ ] Destructive actions have authorization and verification rules.
- [ ] No secrets or machine-specific paths were accidentally included.
- [ ] Supporting scripts have been syntax-checked or exercised safely.
- [ ] One positive and one negative trigger scenario were considered.
- [ ] The target harness can discover the skill after any required reload.

## Harness notes

- **Pi:** recursively discovers directories containing `SKILL.md` from configured skill roots. The current session may require a restart before a newly created skill appears.
- **Cross-harness libraries:** keep one canonical copy and expose it through supported skill directories, settings, or symlinks rather than maintaining drifting copies.
- **Harness-specific metadata:** keep it optional and namespaced. The Markdown workflow must remain useful when another harness ignores that metadata.
