# Sentry production issue investigation

Use this when a Jira bug references linked/commented Sentry issues or when production Sentry evidence is the main reproduction source.

## Practical workflow

1. Start from Jira and extract all issue keys, comments, attachments, and raw URLs. Jira comments may omit links in the rendered CLI output, so also inspect `--json --fields '*all'` when needed.
2. Use `sentry-cli info` to verify auth and discover the org/project with `sentry-cli projects list -o <org>`.
3. `sentry-cli issues list` is useful for search, but it only returns summary tables. Search broadly by exact error text, endpoint, ticket key, and domain terms:
   - `sentry-cli issues list -o <org> -p <project> --query '"exact error"' --max-rows 20`
   - Include resolved/ignored issues in searches; production hotfix investigations often involve already-resolved issues.
4. For root-cause work, fetch the Sentry REST API details for the issue and latest/listed events. The CLI debug log reveals the API shape (`/api/0/projects/<org>/<project>/issues/`, `/api/0/issues/<issueId>/events/latest/`, `/api/0/issues/<issueId>/events/`). Use the existing token from `~/.sentryclirc`; do not print the token.
5. Extract and compare:
   - title/error type and issue id/short id
   - culprit/transaction/endpoint
   - request URL and payload
   - release SHA(s), firstSeen/lastSeen, count
   - stack frames mapped back to source files
   - whether events changed release after a hotfix
6. Trace the Sentry stack frame to source with `search_files`/`read_file`, then trace upstream event/saga/command paths before proposing a fix.
7. For generic Axios issues with no in-app frames, compare individual event breadcrumbs before assigning one root cause. Sentry may group unrelated outbound HTTP failures together when the stack is only Axios/Sentry/node internals.

## Related references

- `references/instatus-heartbeat-sentry.md` — specific workflow for `cron.instatus.com` heartbeat failures and mixed Axios Sentry groups.

## Pitfalls

- A Sentry issue that persists after a hotfix may be residual corrupted production data rather than the original code bug still being present. Compare event release tags before and after the hotfix.
- If code appears to use a transaction, verify writes are actually bound to the session. In Mongoose, `session.withTransaction(...)` does not automatically attach the session to `model.create`, `updateOne`, etc.; pass `{ session }` to each write or use APIs that are explicitly session-bound.
- Avoid stopping at the first thrown error. A failed operation can leave a later symptom (for example, an orphaned foreign key/reference) that is what users now see.
- Sentry's latest event can be unrelated to the Jira-relevant event in the same issue group. Read the listed events and fetch specific event payloads when comments or timestamps point to a particular occurrence.
