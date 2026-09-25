---
name: type-driven-development
description: Design and implement statically typed domain logic from types outward. Use for explicit type-driven development requests or domain-heavy features where entities, invariants, state transitions, and function contracts should precede implementation. Apply the order: domain entities, domain properties, function signatures, then implementation.
license: MIT
compatibility: Statically typed languages with a compiler or type checker.
metadata:
  author: Roy Hermens
  version: "1.0.0"
---

# Type-Driven Development

Build domain logic by making the type system describe valid data and valid operations before writing behavior.

## Activation

Use this skill when:

- the user explicitly requests type-driven development,
- domain entities or state transitions are central to the work,
- invalid states can be excluded through types,
- public contracts need design before implementation.

Do not use it for documentation, configuration, generated code, or untyped languages without a useful static checker.

Do not force domain wrappers onto trivial local values. A new type must express a domain distinction or prevent a real mistake.

## Core Rule

Follow this order for each vertical behavior slice:

```text
Domain entities → domain properties → function signatures → implementation
```

Do not write implementation logic while an earlier phase remains unresolved.

Types define possible values and operations. Tests still define observable examples and runtime behavior.

## Workflow

### 1. Select One Domain Slice

Choose one end-to-end capability. State its input, result, errors, and state changes in domain language.

Keep the slice small enough to complete all four phases before starting another slice.

Do not model the entire domain upfront. Later implementation feedback may change earlier type choices.

### 2. Define Domain Entities

Identify concepts with distinct identity, lifecycle, or meaning.

- Use domain names instead of transport or framework names.
- Separate entities that obey different rules.
- Give identifiers distinct types when accidental substitution is possible.
- Reuse an existing entity when it already owns the concept.
- Keep persistence and wire formats outside the domain model.

Completion condition: every value in the slice belongs to a named domain concept or a justified primitive.

### 3. Define Function Signatures

Write contracts without implementation logic.

For each operation, specify:

- accepted domain state,
- returned domain state,
- expected failure variants,
- effect requirements,
- asynchronous behavior,
- generic constraints where they preserve information.

Prefer signatures that expose valid transitions:

```typescript
function submitOrder(
  order: DraftOrder,
): Result<SubmittedOrder, SubmitError> {
}
```

Avoid weak contracts such as `any`, broad `string`, boolean success flags, unchecked casts, or exceptions for expected domain outcomes.

If the language requires bodies, use interfaces, declarations, protocols, traits, or compile-failing placeholders. Do not hide behavior in a stub.

Run the narrowest type-check command. Confirm callers can use the contract and invalid calls fail to type-check.

Completion condition: the type checker accepts the contract surface without weakening it.

### 5. Add Behavioral Examples

If the project has tests, write focused tests against the typed contract before implementation.

When `test-driven-development` also applies, preserve its RED-GREEN-REFACTOR cycle. The type phases precede RED:

```text
entities → properties → signatures → failing test → implementation → refactor
```

Do not treat successful type-checking as proof of runtime behavior.

### 6. Implement Last

Write the smallest implementation that satisfies the signatures and behavioral examples.

- Exhaustively handle each domain variant.
- Keep casts and unchecked assertions out of domain logic.
- Keep I/O at explicit boundaries.
- Preserve information carried by input types.
- Do not widen return types to make implementation easier.

If implementation pressure exposes a bad contract, return to the relevant type phase. Change the type deliberately, then update callers and tests.

Completion condition: implementation type-checks without contract weakening and satisfies the required behavior.

### 7. Refine the Slice

After verification:

- remove duplicate types that express the same concept,
- simplify types that add no safety,
- improve names that do not match domain language,
- extract shared constructors or parsers,
- keep exhaustive checks intact.

Then repeat the workflow for the next domain slice.

## Boundary Rules

Static types do not validate network, database, file, or user input.

Use this boundary flow:

```text
unknown input → parse and validate → domain type → domain operations → serialized output
```

Never cast untrusted input directly into a domain type. Validation must construct the domain value.

Do not expose persistence records as domain entities when their valid states differ.

## Type Design Checks

Ask these questions before implementation:

1. Can two identifiers or units be accidentally exchanged?
2. Can flags or optional fields create contradictory states?
3. Does each function accept only the state it can process?
4. Are expected failures represented in the return type?
5. Does an unchecked boundary bypass domain construction?
6. Can the type checker verify every state transition exhaustively?
7. Does each abstraction prevent a real defect or clarify the domain?

If a type adds ceremony without safety or clarity, remove it.

## Anti-Patterns

- Writing implementation first and annotating it afterward.
- Designing all entities before selecting a vertical slice.
- Encoding every domain concept as `string`, `number`, or `boolean`.
- Adding optional properties to merge incompatible lifecycle states.
- Using `any`, unchecked casts, or non-null assertions to silence the checker.
- Hiding expected domain failures behind generic exceptions.
- Confusing transport schemas, persistence records, and domain entities.
- Treating type-check success as a replacement for tests.
- Creating complex generic machinery without a domain requirement.

## Verification

Before completion:

- [ ] Domain entities use domain names.
- [ ] Domain properties express valid variants and invariants.
- [ ] Function signatures preceded implementation.
- [ ] Invalid state transitions fail to type-check where practical.
- [ ] Untrusted inputs pass through runtime validation.
- [ ] Expected failures have explicit representations.
- [ ] Implementations do not weaken contracts with escape hatches.
- [ ] The project type-check command passes.
- [ ] Existing tests and relevant new tests pass.

## Final Report

Report:

- entities and properties introduced or changed,
- function contracts introduced or changed,
- invariants enforced by types,
- invariants that still require runtime checks,
- type-check and test commands with results.
