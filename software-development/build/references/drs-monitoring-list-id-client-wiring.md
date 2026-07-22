# DRS monitoring-list id client wiring

When the DRS/SaaS monitoring endpoints require a monitoring list id, update the caller-side contract all the way through instead of only changing the HTTP request body.

## Discovery pattern

1. Inspect the upstream SaaS PR/controller and DTOs for the exact parameter names.
   - Bulk monitor endpoint (`POST /organization-information-collector/monitoring/bulk-organizations`) expects `addToMonitoringListId` in the body.
   - Events endpoint (`GET /organization-information-collector/monitoring/organizations/events`) expects `monitoringListId` in query params.
2. Search the backend for every DRS monitoring endpoint call, not just direct HTTP strings:
   - `monitorOrganizations(`
   - `fetchOrganizationEvents(`
   - `/organization-information-collector/monitoring/`
3. Trace through the domain service (`IOrganizationService` implementation) to the command handlers that call it, then decide where the environment-owned id belongs.

## Implementation pattern

For this backend, keep endpoint-specific HTTP parameter names in `DrsClient`, while the domain service owns reading the environment variable used by its domain flow.

- Add env validation for all configured ids, even if only one is currently used by existing call sites:
  - `DRS_MONITORING_LIST_ID_PARTNERS`
  - `DRS_MONITORING_LIST_ID_FINANCE_RECEIVERS`
- Validate these as 24-character hex strings / Mongo ids when the upstream DTO requires `@IsMongoId()`.
- Add them to `.env.example` near the other DRS settings.
- For finance receiver monitoring calls, read `DRS_MONITORING_LIST_ID_FINANCE_RECEIVERS` via `ConfigService.getOrThrow(...)` and pass it to:
  - bulk monitor calls as body field `addToMonitoringListId`
  - organization events calls as query field `monitoringListId`
- Update request types (`FetchOrganizationEventsRequest`) so missing ids become compile errors.
- Update unit tests at both levels:
  - `DrsClient` tests assert exact HTTP body/query string.
  - domain service tests mock `ConfigService.getOrThrow` and assert the id is passed to the client.

## Pitfalls

- Do not assume both configured env vars have current call sites. In DR-7536 the partners id had to be registered and validated, but no existing partner monitoring endpoint call existed in this backend to wire.
- Do not use the same field name for every endpoint. The bulk monitor DTO used `addToMonitoringListId`, while events used `monitoringListId`.
- If patching a TypeScript file repeatedly fails around broad/duplicated snippets, re-read the file and use a full-file `write_file` for the small service rather than looping stale patches.

## Verification

Run targeted tests for both the HTTP client and the domain service, then typecheck/build:

```bash
pnpm test -- src/shared/drs/drs.client.spec.ts src/company-information/drs/drs-organization.service.spec.ts
pnpm test:types
pnpm run build
```

Run scoped lint on touched files if full lint is expensive or noisy.
