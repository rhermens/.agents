---
name: skill-authoring
description: Create, revise, merge, validate, and audit portable Agent Skills. Use for SKILL.md instructions, triggers, structure, support files, or specification compliance.
license: MIT
compatibility: Agent Skills-compatible harnesses, including Pi, Claude Code, Codex, and Hermes Agent.
metadata:
  author: Roy Hermens
  version: "1.1.0"
---

# Skill Authoring

Create focused skills that change agent behavior reliably. Avoid duplicate guidance and unnecessary context.

## When to use

Use this skill to:

- create or scaffold a reusable Agent Skill,
- revise a skill description, workflow, or support file,
- merge skills that have overlapping triggers,
- audit portability, safety, or specification compliance,
- decide whether guidance belongs in a skill, project instructions, or a prompt.

Do not create a skill for one task or generic advice. Put permanent repository rules in `AGENTS.md` or its equivalent.

## Workflow

1. **Establish the scope.** Identify the intended behavior, trigger requests, exclusions, target harnesses, skill root, and work type. Ask only for decisions that you cannot infer safely.
2. **Survey existing skills.** Inspect nearby names and descriptions. Read the full text of the closest matches. Extend an existing skill when possible.
3. **Design the behavior.** Define inputs, ordered actions, safety limits, completion criteria, and the final report. Remove guidance that repeats default agent behavior.
4. **Choose content locations.** Keep essential guidance in `SKILL.md`. Put optional details, deterministic operations, and reusable material in their applicable directories.
5. **Implement the smallest change.** Preserve valid local conventions. Use portable paths and documented dependencies. Avoid machine-specific paths unless the skill requires them.
6. **Validate the skill.** Run [`python scripts/validate_skill.py <skill-directory>`](scripts/validate_skill.py). Review each warning. Run available harness checks.
7. **Test the trigger.** Test one request that must activate the skill. Test one similar request that must not activate it.
8. **Report the result.** List changed paths, checks, assumptions, and required reloads.

## Decide whether a skill is appropriate

Create a skill only when all these conditions are true:

- The task will probably occur again.
- Special process or domain knowledge improves the result.
- A stable trigger and completion condition can describe the behavior.
- The skill can contain its guidance or link to local support files.

Use another mechanism in these cases:

- **Permanent project rule:** Use `AGENTS.md` or equivalent project instructions.
- **One-time request:** Use the user prompt or a plan.
- **Large external document:** Link to or index the source. Do not copy it into `SKILL.md`.
- **Independent execution role:** Use the harness delegation system. Do not simulate another agent with a skill.

## Portable structure

Use this directory structure:

```text
skill-name/
├── SKILL.md
├── scripts/       # optional deterministic operations
├── references/    # optional guidance loaded when needed
└── assets/        # optional templates or static resources
```

Resolve relative paths from the skill directory. Keep support files inside this directory so users can move the skill safely.

## Frontmatter

Use portable Agent Skills fields by default:

```yaml
---
name: skill-name
description: Describe the skill output and the requests that activate it.
license: MIT
compatibility: Optional environment or dependency requirements.
metadata:
  author: Your Name
  version: "1.0.0"
---
```

Apply these requirements:

- Use 1–64 lowercase ASCII letters, digits, or hyphens for `name`.
- Do not put a hyphen first or last. Do not use consecutive hyphens.
- Match the directory name to `name` for cross-harness portability.
- Keep `description` non-empty and no longer than 1024 characters.
- State the skill capability and its trigger in `description`.
- Keep `compatibility` no longer than 500 characters.
- Do not require optional metadata for correct behavior.
- Treat `allowed-tools` as experimental and harness-specific. Omit it unless the target harness supports it.

## Write effective descriptions

The harness always reads the description during skill discovery. Write it for accurate routing.

Include:

1. concrete actions or outputs,
2. terms that users will probably use,
3. explicit trigger conditions,
4. a clear difference from nearby skills.

Prefer:

```yaml
description: Inspect and repair TypeScript import paths after files or domain types move. Use for unresolved-module errors caused by refactors or bounded-context migrations.
```

Avoid:

```yaml
description: Helps with TypeScript.
```

Do not put the workflow in the description. Do not let several skills claim broad triggers such as “coding” or “debugging.”

## Write effective instructions

- State the required outcome and the applicable requests first.
- Use numbered steps for sequences. Use bullets for decision rules.
- Give each important step a completion condition.
- Put each exception next to the action that it limits.
- State authorization requirements for destructive operations.
- Include exact commands when they add necessary precision and remain portable.
- Add examples when inputs, outputs, or branches can be ambiguous.
- End with verification and reporting requirements.
- Remove empty guidance such as “be careful” or “follow best practices.”

Use **must**, **always**, and **never** only for real invariants. Too many absolute rules make skills brittle or contradictory.

## Write clear technical instructions

Apply these ASD-STE100-inspired principles unless the domain requires different language:

- Use one consistent term for each concept. Do not change terms for stylistic variety.
- Use familiar words with one clear meaning. Define necessary domain terms where readers first need them.
- Prefer active voice. Write agent actions in the imperative form, such as “Validate the file.”
- Put one instruction in each sentence or numbered step. Combine actions only when they must occur together.
- Put a condition before its instruction. For example, write “If validation fails, stop the workflow.”
- Keep instructions concise. Target 20 words or fewer for instructions and 25 words or fewer for descriptions.
- Give each paragraph one topic. Use short paragraphs, headings, and vertical lists.
- Use notes only for information. Do not hide required actions in notes or explanations.
- Identify each hazard, its possible consequence, and the action that prevents it.
- Preserve exact commands, identifiers, API names, quotations, and required domain terms.

## Progressive disclosure

The harness loads all of `SKILL.md` when the skill activates. Keep this file focused.

Use `references/` for content that:

- applies to one workflow branch,
- contains a long API or format reference,
- contains many examples,
- can change independently.

Use `scripts/` when deterministic code is safer or cheaper than generated commands. Each script must:

- contain all required logic,
- validate its inputs,
- fail with an actionable message,
- avoid destructive defaults,
- document nonstandard dependencies.

Put templates and static resources in `assets/`. Link each support file from `SKILL.md`, or remove the unused file.

## Merge or revise skills

When skills overlap:

1. Select the skill with the clearest name, valid trigger, or established support files.
2. Compare the behaviors instead of the wording.
3. Transfer only unique and current guidance.
4. Resolve each conflict explicitly. Prefer safer guidance that has stronger evidence.
5. Remove duplicate text and stale links.
6. Validate the destination before deleting the redundant skill.
7. Find and update references to the removed skill name.

During revisions, preserve useful conventions. Correct invalid frontmatter, broken links, and undocumented harness assumptions.

## Safety and trust

Skills can direct agents to run code or perform destructive operations.

- Review third-party skills and scripts before enabling them.
- Do not store credentials, tokens, private URLs, or secrets.
- Require authorization for deletion, publication, deployment, remote changes, and bulk edits.
- Treat the user's request as authorization only when it grants the exact operation and scope.
- Prefer read-only operations and dry runs.
- Limit filesystem and network scope.
- Verify generated scripts before you describe the skill as safe.

## Validation checklist

- [ ] YAML frontmatter starts at byte zero.
- [ ] `name` and `description` meet Agent Skills requirements.
- [ ] The directory name matches `name`.
- [ ] The description distinguishes this skill from nearby skills.
- [ ] The body contains an actionable workflow.
- [ ] Each linked script, reference, and asset exists.
- [ ] Relative paths resolve from the skill directory.
- [ ] The skill documents dependencies and compatibility limits.
- [ ] Destructive actions include authorization and verification rules.
- [ ] The skill contains no secrets or accidental machine-specific paths.
- [ ] Support scripts pass syntax checks or safe tests.
- [ ] One positive and one negative trigger case were tested.
- [ ] The target harness can discover the skill after any required reload.

## Harness notes

- **Pi:** Pi finds `SKILL.md` files recursively in configured skill roots. Restart the session when a new skill does not appear.
- **Cross-harness libraries:** Keep one canonical copy. Use supported directories, settings, or symbolic links to expose it.
- **Harness metadata:** Keep harness-specific metadata optional and namespaced. The Markdown workflow must work when another harness ignores that metadata.
