---
name: typescript-import-refactors
description: Fix TypeScript/NestJS import-path breakage after files or bounded-context types are moved, with typecheck and lint verification.
---

# TypeScript Import Refactors

Use this when a TypeScript repo has broken imports after files/types/classes were moved, especially NestJS code using absolute `src/...` imports.

## Workflow

1. Run the repo's typecheck first, e.g. `pnpm run test:types`, to get the complete list of missing modules and any follow-on type narrowing errors.
2. Locate the new definitions before editing. Search by filename/symbol, then read the moved files to confirm exported names and contracts.
3. Patch stale imports in both `src/` and `test/`; do not limit changes to production files when TypeScript includes tests.
4. If an old intermediary class/type no longer exists, adapt the consuming test/code to the new concrete contract after reading the replacement type. Do not invent a shim unless the project conventions call for compatibility exports.
5. Search for stale old paths/symbols after edits before declaring completion.
6. Rerun typecheck.
7. Run targeted lint on the touched TypeScript files. Import path rewrites often trigger `simple-import-sort/imports`; use targeted ESLint `--fix` or manually reorder imports, then rerun lint.

## Pitfalls

- A missing import can hide follow-on errors like `Property 'receiver' does not exist on type 'IEvent'`; fix the import first, then re-run typecheck before changing logic.
- Bulk replacement is appropriate for pure path moves, but only after confirming the new files export the same names.
- When a test imported a removed abstraction, update the fixture/test event to implement or extend the new moved abstraction's required members.
- Do not report ESLint as verified if the command failed on import sorting. Run autofix/scoped lint and report the passing command.

## Verification

Minimum evidence before final response:

```bash
pnpm run test:types
pnpm run lint -- <touched .ts files>
```

If full lint is too broad or fails on unrelated pre-existing files, provide a scoped passing lint command for the touched files and call out the broader blocker separately.
