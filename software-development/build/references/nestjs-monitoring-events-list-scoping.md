# NestJS monitoring events list scoping

When an organization-events endpoint gains `monitoringListId`, wire it through the full controller/query/service/client path and use the monitoring-list record to select the external provider portfolio.

## Implementation pattern

1. Controller DTO / query params
   - Add `monitoringListId` to the events query DTO.
   - Validate it with `@IsMongoId()` when it is a Mongo `_id`.
   - Preserve endpoint-specific naming: events query uses `monitoringListId`; bulk monitor bodies may use `addToMonitoringListId`.

2. CQRS query/handler
   - Keep `clientId` from identity/auth on the query.
   - In the query handler, load the monitoring list by both `_id` and `clientId`:
     ```ts
     const monitoringList = await monitoringListModel.findOne({
       _id: new Types.ObjectId(query.params.monitoringListId),
       clientId: query.clientId,
     }, null).lean();
     ```
   - Throw `NotFoundException('Monitoring list not found')` if absent.
   - Pass `monitoringList.portfolioId` downstream. Do not trust client-supplied portfolio ids or cached/default portfolio state for list-scoped events.

3. Domain/provider service
   - Add `portfolioId: number` to `notificationEventsFromPortfolio(...)` signatures at every layer: service, client interface, real client, mocks.
   - In the Creditsafe HTTP client, build `/monitoring/portfolios/${portfolioId}/notificationEvents?...` from the explicit argument.
   - Keep any existing provider flag behavior (`CREDITSAFE_FILTER_EVENTS_BY_PORTFOLIO=false`) intact; only the portfolio-scoped path should use the explicit `portfolioId`.

## Tests to update

- Query handler spec:
  - Mock monitoring-list lookup by `_id` + `clientId`.
  - Assert portfolio id forwarding to the monitoring service.
  - Add missing-list `NotFoundException` test and assert the provider service is not called.
- Service spec: assert client receives `{ page, pageSize }`, `asOf`, and `portfolioId`.
- HTTP client spec: assert endpoint uses the passed portfolio id, not cached/default `this.portfolioId`.
- Test mocks (`MockCreditsafeClient`) must accept the new parameter to keep e2e compile/runtime setup aligned.

## Pitfalls

- Do not only add the field to the DTO; the handler must enforce client isolation by looking up the list with `clientId`.
- Do not keep using a cached default provider portfolio for events once events are list-scoped.
- Search for all `notificationEventsFromPortfolio(` call sites after changing the signature; TypeScript may not surface mock-only mismatches until tests/build.
