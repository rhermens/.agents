# NestJS Mongoose migrations in this monorepo

Use this when adding a durable data backfill or one-time provisioning task in a NestJS service that uses `@dr/mongoose-migrations`.

## Implementation checklist

1. **Find the app's migration wiring before adding a class.** Existing migration support in this repo is provided by `MongooseMigrationsModule`; a migration class is not runnable just because it has `@Migration()`.
2. **Add the workspace dependency and TS project reference if the app does not already use migrations.**
   - `apps/<service>/package.json`: add `"@dr/mongoose-migrations": "workspace:*"`.
   - `apps/<service>/tsconfig.json`: add `../../libs/mongoose-migrations/tsconfig.lib.json` to `references` so `nest build -p tsconfig.app.json` resolves the library.
   - Run `pnpm install`/lockfile update so the app gets the workspace link and `pnpm-lock.yaml` reflects the dependency.
3. **Import `MongooseMigrationsModule` in the app module.** This provides the orchestrator and migration schema used by the CLI.
4. **Register the migration class as a provider in an imported feature module.** The orchestrator discovers providers decorated with `@Migration()`.
5. **Export cross-module injection tokens needed by the migration.** If a migration provider lives in module A and injects a token from module B (for example `ICreditsafeClient`), module B must export that token, not only the concrete service.
6. **Keep migrations idempotent.** Prefer unique natural filters plus `$setOnInsert`/`upsert` for durable records, then query the record back before backfilling references.
7. **Backfill by tenant/client scope.** For multi-tenant data, derive the set of affected clients (for example `organizationModel.distinct('clientId')`) and mutate one client scope at a time.
8. **Return structured migration stats.** Include IDs/counts useful for audit, such as `portfolioId`, migrated client count, and modified document count.

## Testing pattern

- Unit-test the migration class directly with mocked Mongoose models and external clients.
- Add at least two tests: normal backfill and empty/no-op input.
- Verify that external setup returns the remote ID the local record stores.
- Verify app startup/e2e after registration; DI can pass unit tests but fail e2e if a provider token was not exported from its module.

## Common pitfalls

- `@Migration()` without `MongooseMigrationsModule` import and provider registration will build but not run.
- Injecting an interface symbol from another module requires the source module to export the symbol provider.
- If the app did not previously depend on `@dr/mongoose-migrations`, TypeScript path aliases may pass in tests but `nest build` can still fail until package dependency, lockfile, and `tsconfig` reference are added.
- Avoid using only `findOneAndUpdate(..., { upsert: true, new: true })` when Mongoose typing gets in the way; an explicit `updateOne(..., { upsert: true })` followed by `findOne().lean()` is easier to type and keeps idempotence clear.
