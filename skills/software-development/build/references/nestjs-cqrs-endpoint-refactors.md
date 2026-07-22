# NestJS CQRS endpoint refactor notes

Use when changing endpoint command semantics in this pnpm/NestJS monorepo.

## Rename a command flow cleanly

When a command name changes, update all layers together:

- command file/class: `commands/<verb>.command.ts`
- handler file/class/spec: `commands/handlers/<verb>.command-handler(.spec).ts`
- DTO file/classes if the public contract name changes
- controller imports and method return/body types
- module provider registration
- relative imports in specs
- search for stale old class/file names before verification

Prefer domain verbs over CRUD verbs when semantics are not creation. Example: `MonitorOrganizationCommand` is clearer than `CreateMonitoredOrganizationCommand` if it only attaches an existing organization to a monitoring list.

## Do not upsert when the requirement is "monitor existing"

If the user says the entity must already exist:

1. Validate related foreign/domain objects first if needed (e.g. monitoring list belongs to `clientId`).
2. `findOne({ clientId, domainKey })` for the target entity.
3. Throw `NotFoundException('<Entity> not found')` when missing.
4. `updateOne({ _id }, { $set: ... })` for the association/state change.
5. Publish the domain event only after the update path succeeds.
6. Add tests for both existing-target success and missing-target 404; assert no update/event on the 404 path.

Avoid `findOneAndUpdate(..., { upsert: true })` in these flows: it silently creates state the API contract says must pre-exist.

## Event payload sanity

When a saga needs a list/portfolio context later, include the stable list identifier on the domain event at publish time. Tests should assert constructor argument order using strings, not raw `ObjectId`s, when event classes expose string fields.
