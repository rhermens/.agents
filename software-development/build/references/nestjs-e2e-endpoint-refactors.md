# NestJS E2E Endpoint Refactor Pitfalls

Use this when a NestJS CQRS endpoint/DTO/handler refactor breaks e2e tests.

## Tight repro

- Run the smallest affected e2e project first, not the whole monorepo:
  ```bash
  OAUTH_ISSUER_URI=https://debitroomsoftware-test.eu.kinde.com \
  OAUTH_AUDIENCE=https://software.debitroom.com \
  CREDITSAFE_URL=https://connect.sandbox.creditsafe.com/v1/ \
  CREDITSAFE_USERNAME=test \
  CREDITSAFE_PASSWORD=test \
  pnpm exec jest --config ./jest-e2e.config.ts \
    --selectProjects ./apps/organization-information-collector \
    --runInBand --forceExit
  ```
- For the full e2e suite, include dummy values required by validation and feature flags for route modules tested by the suite, for example `SANDBOX_ENABLED=true` for transaction-collector sandbox routes.
- If setup fails before the app initializes, ignore cascading `global.__APP__`/`.close()` errors and fix the first config/module initialization error.

## Fix pattern after DTO/semantic changes

1. Read the DTO and controller before editing the e2e spec. Validation failures often mean the request body no longer matches required fields.
2. If a new domain entity is required by validation or handler lookup, create it in the e2e fixture through the real Mongoose model rather than bypassing the endpoint.
3. Update assertions to the new domain semantics, not just status codes. Example: a bulk “delete” endpoint may now remove list membership by unsetting `monitoringListId` while preserving organization documents.
4. Assert both sides of isolation after membership changes:
   - target client/list membership changed as expected;
   - other-client records or other-list records are untouched.
5. For Mongo lean docs, an unset optional field may be absent rather than present as `undefined`; prefer `expect(doc).not.toHaveProperty('monitoringListId')` for `$unset` assertions.
6. If two e2e specs intentionally share setup because they exercise paired endpoint semantics, first extract small fixture helpers under `test/utils/` (for example monitoring-list creation). If Qodana still reports intentional `DuplicatedCode`, add the exact spec paths under the existing `DuplicatedCode` `exclude` block in `qodana.yaml`, then parse the YAML and verify the paths are present.

## Verification

- Rerun the affected e2e project.
- Run targeted unit specs around the changed handler/service.
- Run scoped ESLint for touched e2e specs, then full `pnpm run lint` and `pnpm run build`.
