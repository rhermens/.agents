---
name: type-driven-development
description: Shape statically typed domain logic so data models, invariants, and contracts guide implementation. Use for explicit type-driven development requests or domain-heavy features where types should reveal valid states, operations, and design constraints.
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

- domain entities or state transitions are central to the work,
- public contracts need design before implementation.

Do not use it for documentation, configuration, generated code, or untyped languages without a useful static checker.

Do not force domain wrappers onto trivial local values. A new type must express a domain distinction or prevent a real mistake.

## Core Principle

Let the domain shape constrain the implementation. Model what values exist, which states are valid, and which transitions are allowed.

Types and implementation can evolve together. Do not infer the domain model only from code that has already been written.

If implementation resists the shape, inspect the domain assumption. Do not immediately weaken the contract or bypass the checker.

Types define possible values and operations. Tests still define observable examples and runtime behavior.

## Workflow

### Choose a Domain Slice

Choose one end-to-end capability. State its inputs, results, failures, and state changes in domain language.

Keep the slice small. Do not model the entire domain upfront.

### Shape the Domain

Identify concepts with distinct identity, lifecycle, or meaning. Describe their valid properties, variants, and relationships.

- Use domain names instead of transport or framework names.
- Separate concepts that obey different rules.
- Distinguish identifiers or units when accidental substitution is possible.
- Use explicit variants when flags or optional fields permit contradictory states.
- Reuse an existing entity when it already owns the concept.
- Keep persistence and wire formats outside the domain model.

Every new type should clarify the domain or prevent a realistic mistake.

### Shape Operations

Use function signatures to express what operations accept, produce, and reject.

Consider:

- accepted domain states,
- returned domain states,
- expected failure variants,
- effect and asynchronous requirements,
- generic constraints that preserve information.

Prefer signatures that expose valid transitions:

```typescript
function submitOrder(
  order: DraftOrder,
): Result<SubmittedOrder, SubmitError> {
}
```

Avoid weak contracts such as `any`, broad `string`, boolean success flags, unchecked casts, or exceptions for expected domain outcomes.

Run the narrowest type-check command while shaping the contract. Confirm valid callers work and invalid calls fail to type-check.

### Implement Within the Shape

Let the established shapes guide control flow and data transformations.

- Exhaustively handle each domain variant.
- Keep casts and unchecked assertions out of domain logic.
- Keep I/O at explicit boundaries.
- Preserve information carried by input types.
- Do not widen types only to make implementation easier.

Implementation can reveal missing states or incorrect assumptions. Refine the types deliberately, then update callers and tests.

### Verify Behavior

If the project has tests, add focused behavioral examples against the typed contract.

When `test-driven-development` also applies, preserve its RED-GREEN-REFACTOR cycle. Type design shapes the API exercised by each test.

Do not treat successful type-checking as proof of runtime behavior.

### Refine the Model

After verification:

- remove duplicate types that express the same concept,
- simplify types that add no safety,
- improve names that do not match domain language,
- extract shared constructors or parsers,
- keep exhaustive checks intact.

Repeat with the next domain slice.

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

- Treating types as annotations for an implementation that already determined the design.
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
- [ ] Domain shapes and function contracts meaningfully constrain implementation.
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
