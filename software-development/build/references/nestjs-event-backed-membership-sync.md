# NestJS event-backed membership sync pitfalls

Use this when a feature changes local membership/assignment state that is mirrored into an external provider (for example organization monitoring lists mapped to Creditsafe portfolios).

## Failure pattern

A handler updates the local assignment field (for example `monitoringListId`) but only emits side-effect events for newly upserted rows. Existing rows that gain a list, or move from list A to list B, then look correct locally while the external provider remains stale.

A related saga/command bug is choosing the external target by re-reading mutable current DB state instead of using the immutable list/bucket ID carried by the event/command. If the entity moves again before the saga executes, it can add/remove the wrong external target.

## Implementation checklist

1. Validate the target list/bucket belongs to the caller/client before mutating local state.
2. Read the previous local state before the update with enough fields for event payloads (`_id`, provider remote ID, client ID, previous list/bucket ID).
3. Mutate local state.
4. Emit side-effect events based on the transition:
   - no previous list -> target list: emit add-to-target.
   - same previous list -> same target: emit nothing.
   - previous list A -> target list B: emit remove-from-A and add-to-B.
   - replace/delete from a list: emit remove-from-that-list for every removed entity.
5. Saga command handlers should use the command/event's target list ID to resolve external provider metadata, not the entity's current assignment field.
6. If new provider-backed records are required by the ticket (named lists, portfolios, tenant mappings, defaults), add a durable provisioning path: migration, seed/bootstrap, admin setup command, or explicit operational doc. Schema alone is not enough.

## Test checklist

- Existing entity without an assignment receives the add event.
- Existing entity moving between assignments receives remove-old and add-new events.
- Existing entity already in the target assignment emits no duplicate external sync event.
- New upserted entity receives add event.
- Replace/delete emits remove events scoped to the old assignment.
- Saga command resolves provider metadata from the command/event assignment ID, even when the entity's current assignment differs.
- Provisioning path creates or verifies required named records/default mappings.