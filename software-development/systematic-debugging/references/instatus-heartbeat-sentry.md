# Instatus heartbeat failures in Sentry

Use this when a Jira/Sentry production issue mentions `cron.instatus.com`, heartbeat monitors, or generic Axios `500`/`502`/`504` errors with no in-app frames.

## Investigation pattern

1. Start from every Jira-linked and comment-linked Sentry URL. Linked/commented issues may belong to different Sentry projects.
2. Fetch the issue summary plus latest/listed events via Sentry REST, not only the Sentry issue table:
   - `/api/0/issues/<issueId>/`
   - `/api/0/issues/<issueId>/events/latest/`
   - `/api/0/issues/<issueId>/events/`
   - For a specific event id in another project: `/api/0/projects/<org>/<project>/events/<eventId>/`
3. Inspect breadcrumbs for the actual failing outbound request. For heartbeat failures, the useful evidence is often a long run of `POST 200 https://cron.instatus.com/...` followed by one `POST 500/504` to the same URL.
4. Trace the code path that sends the heartbeat. In this repo the relevant path was:
   - `src/health/heartbeat/heartbeat.service.ts` cron `ping()`
   - `firstValueFrom(this.httpService.post(targetUrl))`
   - catch block logs and `Sentry.captureException(error)`
5. Distinguish two failure classes:
   - Normal heartbeat URL fails with `cron.instatus.com` `500/504`: Instatus ingestion/transient third-party monitor failure; app may be healthy.
   - Health check target fails and code posts to `<HEARTBEAT_URL>/fail`: app/dependency unhealthy; still worth Sentry capture.

## Pitfalls

- Sentry can group unrelated Axios errors together when stacks contain only Axios/Sentry/node frames and no in-app frames. Do not infer one root cause from a mixed Axios issue; compare event breadcrumbs, URLs, mechanisms, and projects per event.
- The latest event in a Sentry issue may not represent the Jira-relevant event. The commented issue can show a newer unrelated `400` while older events in the same group contain the `500/504` heartbeat failures.
- If failures occur at the same timestamp across multiple `cron.instatus.com/debitroom-*` URLs and projects, that points away from one app worker and toward Instatus or network/ingestion transient failures.

## Likely remediation pattern

Keep Sentry capture for actual internal health-check failures, but avoid capturing exceptions for failed POSTs to Instatus itself. These are monitor-ingestion noise and can be logged as warnings or filtered by target host (`cron.instatus.com`).