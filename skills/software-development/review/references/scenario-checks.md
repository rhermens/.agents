# Scenario-specific review checks

Apply the sections relevant to the changed behavior.

## Configuration-backed records and mappings

For required domain records or external-system mappings, verify a durable provisioning path:

- migration,
- seed or bootstrap,
- admin endpoint,
- documented operational step.

Examples include named lists, portfolios, tenants, provider IDs, and default mappings.
If requirements demand records or defaults, verify their creation as well as the schema.

## External-provider synchronization

Trace local mutations and emitted event payloads for new records, existing-record updates, and moves between lists or buckets.
Verify that assignment changes emit all effects needed to keep the external provider synchronized.
Use immutable command or event fields to select the external target; re-reading mutable state can select a different target.

## Membership removal

When deletion becomes membership removal, such as unsetting `listId`, `portfolioId`, or `groupId`, trace mutation and read endpoints.
Check that queries filter active membership or require the parent/list ID.
Ask for a regression that changes membership and then reads through the public endpoint.

## Destructive or administrative cleanup CLIs

Trace every action branch into the called service implementation.

- Verify service preconditions for each branch. A branch that proves an account is absent cannot require that account for revocation.
- Check dry-run behavior, confirmation, limits, per-item error handling, provider scope, and audit-friendly result totals.
- Apply eligibility predicates at the same granularity as the destructive action.
- Test parents with mixed active and inactive children; parent-level checks can incorrectly include or exclude individual children.
- Deduplicate organization-level revocations when iterating account-level reports.

## Date cutoffs

Verify explicit units and boundary behavior.
For Day.js, `subtract(30)` is milliseconds; use `subtract(30, 'days')` for a day cutoff.
Test just before and after the cutoff, missing dates, and equality.
Compare exclusive `isBefore`/`isAfter` checks with inclusive query operators.

## Business-day scheduling

For reminders with workday or bank-holiday offsets, establish whether the scheduler runs on calendar days or business days.
A daily cron computing “N workdays from today” can select the same date across weekends or holidays.
Verify an idempotency guard or a non-workday skip when repeated execution could send duplicate notifications.
Probe consecutive Friday/Saturday/Sunday and holiday-adjacent runs; request regression coverage for duplicate sends.

## Audit-field middleware

When replacing manual `createdBy`/`updatedBy` fields with plugins or middleware, trace every write mechanism.

1. Confirm hook coverage for `create`/`save`, `updateOne`, `updateMany`, and `findOneAndUpdate`.
2. Check bypass paths: `bulkWrite`, raw collection calls, `$push`ed nested subdocuments, `insertMany`, seeders, CLI commands, queues, cron jobs, sagas, and migrations.
3. Verify that each dispatch path has a CLS/request/processor audit actor.
4. Keep explicit nested-subdocument `createdBy` values when update-query middleware cannot stamp them.
