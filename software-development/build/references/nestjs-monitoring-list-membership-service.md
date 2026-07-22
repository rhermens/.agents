# NestJS monitoring-list membership service extraction

Use when multiple CQRS handlers perform the same monitoring-list membership side effects, including:

- removing organizations from a list by querying scoped organizations, unsetting `monitoringListId`, and publishing `OrganizationRemovedFromListEvent`;
- full add/remove membership operations when an organization is assigned or moved between lists: mutate `monitoringListId` and publish `OrganizationRemovedFromListEvent` for the previous list + `OrganizationAddedToListEvent` for the target list, or no-op if unchanged.

## Pattern

1. Extract side-effect and event-construction logic into an injectable domain/application service in the owning module, e.g. `monitoring/services/monitoring-list-membership.service.ts`.
2. Inject the Mongoose `Organization` model and `EventBus` into the service, not into every handler that only delegates this operation.
3. Expose intention-revealing methods for complete domain operations, for example:
   - `removeOrganizationsFromList(options)` for scoped removals: scoped read → unset membership → publish removal events;
   - `addOrganizationToList(options)` for one assignment/move: compare previous/target list → update membership → publish transition events;
   - `addOrganizationsToList(options)` for bulk assignment/move: bulk update selected organizations → publish add/move events.
   Do **not** expose methods whose only public contract is `publish...` or `create...Events`; publishing/event construction is a private implementation detail of the membership operation.
4. Keep handler call sites explicit and operation-level:
   - bulk replace/update passes `exceptRemoteIds` and the selected `monitoringListId` to remove missing members, then passes the resulting organizations to `addOrganizationsToList`;
   - bulk delete passes selected `organizationIds` and the selected `monitoringListId` to `removeOrganizationsFromList`;
   - single monitor passes the current organization and target `monitoringListId` to `addOrganizationToList`; the handler should not separately update membership;
   - create/upsert organization passes the organization plus explicit `previousMonitoringListId` to `addOrganizationToList`, because the returned document may not represent the pre-change list state.
5. Type removal options as a discriminated/union shape so callers cannot accidentally omit both selectors or pass both unless intended.
6. Register the service in the feature module providers. If handlers in another module need it, export the service from the owning module and import that module where needed.

## Query/update invariants

- Always scope reads by `clientId` and `monitoringListId` to preserve tenant/list isolation.
- Use the same found organizations as the event source so removal events reflect the previous membership.
- Unset with `{ $unset: { monitoringListId: '' } }` to match existing Mongoose conventions in this repo.
- Prefer updating only found IDs while retaining tenant/list scope (`{ clientId, monitoringListId, _id: { $in: organizations.map((o) => o._id) } }`) after the scoped read; this avoids mutating or publishing events for entities not actually selected.
- For list transitions, compare previous and target list IDs before mutating or emitting events; unchanged assignments are no-ops.
- Keep event publishing private inside the service. Handlers should request `add...ToList` or `remove...FromList`, not `publish...`, because publishing alone is only a partial membership abstraction and can leave DB state and external sync events inconsistent.
- If an upsert/update returned organization already has the target list, pass the separately captured previous list into the service. Do not infer previous state from the post-update entity.

## Tests

- Add a service spec that verifies exact query, update, and emitted `OrganizationRemovedFromListEvent` for both removal modes:
  - `$nin` / `exceptRemoteIds` replace cleanup;
  - `$in` / selected `organizationIds` deletion.
- Add service tests for complete transition operations:
  - no previous list → updates membership + add event only;
  - previous list differs → updates membership + remove + add events;
  - previous list equals target → no mutation and no events;
  - explicit `previousMonitoringListId` overrides the organization's current field.
- Update handler specs to assert delegation to complete service operations (`addOrganizationToList`, `addOrganizationsToList`, `removeOrganizationsFromList`) rather than duplicating service internals or asserting direct event publication in handler tests.
- When service extraction crosses module boundaries, add/verify module exports/imports as part of build verification.
- Run targeted Jest for the service and all touched handlers. If a large combined targeted Jest invocation segfaults after individual suites start passing, split the same suite set into smaller `pnpm run test -- ... --runInBand` invocations and report both the runner crash and the passing split evidence.
- Run scoped ESLint on touched files, then full build/lint when feasible.
