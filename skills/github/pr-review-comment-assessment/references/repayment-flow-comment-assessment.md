# Example: PR comment assessment from repayment-flow review

A useful pattern emerged while assessing unresolved comments on a refactor PR:

- GitHub REST inline comments returned many old comments, but GraphQL `reviewThreads` showed only one currently unresolved thread.
- The latest formal review body still listed additional concerns that were not represented as unresolved threads, so both sources mattered.
- Some earlier comments had been addressed in the latest head by moving a public service into private methods on the owning service.
- A targeted local test run passed, but a correctness concern remained valid because the code recorded the full overdue amount instead of the actual allocated amount.

## Review lessons

- Treat “tests passed” as verification context, not as proof that a reviewer's business-logic concern is resolved.
- For accounting/payment allocation code, check whether recorded/audited amounts reflect the amount actually applied after caps and after successful side effects, not the pre-cap or intended amount.
- For production collections built from filtered data, validate upstream invariants but still flag brittle `assert` usage if one inconsistent record can crash a job. Prefer explicit domain errors, normalization, or report-and-skip behavior when appropriate.
- When a user asks about “my latest comments”, include comments summarized in the latest review body even if GitHub's unresolved-thread list is shorter.
