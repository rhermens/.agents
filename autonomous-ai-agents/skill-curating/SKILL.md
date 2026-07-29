---
name: skill-curating
description: Reflect on completed agent sessions to identify reusable lessons, assess skill coverage, and recommend or apply targeted skill improvements. Use after work settles, after repeated friction or user corrections, or when asked for a skill retrospective. Use skill-authoring instead for implementing a predefined skill change without session reflection.
license: MIT
compatibility: Agent Skills-compatible harness with access to the current session. Skill edits require filesystem access and explicit authorization.
metadata:
  author: Roy Hermens
  version: "1.1.0"
---

# Skill Curating

Review a settled session for reusable guidance. Improve the skill library without recording incidental details or duplicating existing instructions.

## Operating modes

Select one mode before reviewing candidates.

- **Recommendation mode:** Report proposed changes without editing files.
- **Improvement mode:** Edit skill files within the authorized scope.

Use recommendation mode for automatic end-of-session triggers. Use improvement mode only when the user explicitly authorizes skill edits.

Never delete, merge, publish, or relocate skills without authorization for that exact operation.

## Session boundary

Start curation only when the primary task is complete, stopped, or explicitly handed off.

If active work remains, defer curation. Do not interrupt implementation, debugging, or verification.

Use only available session evidence. Do not invent missing events or claim access to unavailable session history.

## Reflection workflow

1. **Summarize the outcome.** Record the request, result, verification state, and unresolved blockers.
2. **Extract evidence.** Find user corrections, repeated friction, failed approaches, safeguards, and successful non-obvious workflows.
3. **Form candidates.** Convert each observation into one transferable behavior change. Remove project, framework, tool, and job-specific terms.
4. **Test formalization.** Formalize declarative rules only when this reduces tokens and valid interpretations.
5. **Classify each candidate.** Choose a broadly applicable existing skill, a new skill, or no durable change.
6. **Inspect nearby skills.** Read the full text of likely destination skills and overlapping descriptions.
7. **Evaluate each candidate.** Apply the acceptance rules below and reject weak candidates.
8. **Recommend or improve.** Follow the selected operating mode.
9. **Verify the result.** Check scope, consistency, links, triggers, and authorization.
10. **Report concisely.** State the outcome, evidence, changed paths, checks, and deferred recommendations.

## Evidence to inspect

Prefer concrete session events:

- the user corrected behavior or terminology,
- the same obstacle occurred more than once,
- an initial approach failed for a general reason,
- a missing safeguard caused risk or rework,
- a non-obvious command or sequence consistently succeeded,
- an existing skill triggered incorrectly or failed to trigger,
- guidance was duplicated across skills,
- deterministic logic would be safer as a script.

Treat a single event as sufficient only when the lesson is clear, reusable, and high impact.

## Candidate acceptance rules

Use this rule:

```text
accept(c) ⇔ evidenced(c) ∧ improves_behavior(c) ∧ recurring(c) ∧ stable(c)
            ∧ domain_neutral(c) ∧ destination_owns(c) ∧ novel(c)
            ∧ sanitized(c) ∧ trigger_preserving(c)
```

- `domain_neutral`: Applies across projects, frameworks, languages, and non-programming work.
- `sanitized`: Contains no secrets, private data, or incidental identifiers.
- `trigger_preserving`: Does not make a broad skill trigger less accurately.

Reject a candidate when any conjunct is false.

## Formalization review

Apply `skill-authoring`'s formalization rule while forming candidates. Keep a formula only when it preserves every condition and reduces tokens and ambiguity.

## Choose the destination

Use this order:

1. Improve a broadly applicable existing skill that already owns the behavior.
2. Add broadly applicable support material to that skill.
3. Recommend a new skill when no existing skill has the correct trigger.
4. Make no change when the lesson is not durable.

Prefer revising one destination over copying guidance into several skills.

If skills overlap, recommend consolidation only when their trigger boundaries or workflows are materially duplicated.

## Improvement mode

Before editing, activate or read `skill-authoring` and follow its authoring, safety, and validation workflow.

Make the smallest change that alters future behavior. Preserve valid frontmatter, terminology, structure, and portability.

Keep session-specific evidence out of the skill. Write the generalized rule that the evidence supports.

Do not modify product code, project configuration, or unrelated documentation during curation.

For each edited skill:

1. Validate the skill with the validator documented by `skill-authoring`.
2. Test one request that should trigger the skill.
3. Test one similar request that should not trigger the skill.
4. Review the diff for unsupported or duplicated guidance.

If validation fails, keep the curation incomplete and report the blocker.

## Recommendation mode

For each accepted candidate, report:

- destination skill or proposed skill name,
- evidence from the session,
- exact behavior to add, remove, or clarify,
- expected benefit,
- confidence as high, medium, or low.

Write each recommendation as domain-neutral behavior that applies to programming and non-programming work.

Do not name the session's project, framework, language, tool, role, or job in the proposed action.

Do not produce a patch unless the user requests one. Limit the report to the highest-value candidates.

If no candidate passes the acceptance rules, report: `No skill changes recommended.`

## Final report

Use this compact structure:

```markdown
## Skill curation

Outcome: no change | recommendations | improved

- Evidence: <session event>
- Action: <destination and behavior change>
- Benefit: <future improvement>
- Confidence: high | medium | low

Changed paths: <paths or none>
Checks: <validation and trigger tests, or not run>
```

Mention required harness reloads after creating or renaming a skill.
