---
name: sentry-cli
description: Use when installing, configuring, or operating Sentry CLI for releases, deploys, commits, source maps, debug files, events, logs, or CI automation. Provides exact command patterns, authentication setup, verification checks, and common pitfalls for sentry-cli usage.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sentry, sentry-cli, releases, sourcemaps, ci, deploys, observability]
    related_skills: [github-cli, github-pr-workflow, build]
---

# Sentry CLI Usage

## Overview

Use `sentry-cli` for release automation, source map uploads, debug information file uploads, deploy tracking, commit association, ad-hoc event/log operations, and CI integration with Sentry. The CLI is stateful through project/org config and credentials, so the safest workflow is: verify auth and target project first, compute a release identifier once, run the operation, then verify the result in Sentry or with a read/list CLI command.

Sentry docs move quickly; when behavior matters, check the live docs at `https://docs.sentry.io/cli/` and the command help with `sentry-cli <command> --help`. Treat this skill as the operational checklist and command pattern library.

## When to Use

- Installing or verifying `sentry-cli` locally or in CI.
- Creating/finalizing Sentry releases.
- Associating commits with releases.
- Creating deploy records for environments such as `production` or `staging`.
- Uploading JavaScript source maps or artifact bundles.
- Uploading native/mobile debug information files.
- Troubleshooting auth, org/project targeting, missing artifacts, or release mismatch issues.

Don't use this skill for SDK instrumentation or application code setup except where SDK release/dist values must match CLI-created releases.

## Prerequisite Discovery

Before mutating Sentry state, identify these values and record them in the command block or CI environment:

| Value | Common source | Notes |
| --- | --- | --- |
| `SENTRY_AUTH_TOKEN` | Sentry user/org auth token or CI secret | Must have the scopes needed for the command, often project/release write permissions. Never print it. |
| `SENTRY_ORG` | Sentry organization slug | Org slug, not display name. |
| `SENTRY_PROJECT` | Sentry project slug | Project slug, not display name. Some release operations are org-wide but project targeting still matters for artifact/source-map behavior. |
| `VERSION` / release | `sentry-cli releases propose-version`, git SHA, package version, or app version | Must exactly match the release value used by the SDK at runtime. |
| `DIST` | Build number / bundle identifier when used | Must exactly match SDK `dist` if artifacts are dist-scoped. |
| `ENVIRONMENT` | `production`, `staging`, etc. | Used for deploy records. |

Completion criterion: do not run create/upload commands until auth, org, project, and release name are explicit.

## Installation and Authentication

### Install

Prefer the project/CI's established package manager. Common options:

```bash
# macOS
brew install getsentry/tools/sentry-cli

# npm/npx, useful for JS repos and CI
npm install --save-dev @sentry/cli
npx sentry-cli --version

# direct binary install, common in CI images
curl -sL https://sentry.io/get-cli/ | bash
sentry-cli --version
```

### Authenticate and target org/project

Prefer environment variables in CI and `.env.local` or shell exports locally:

```bash
export SENTRY_AUTH_TOKEN='***'
export SENTRY_ORG='my-org-slug'
export SENTRY_PROJECT='my-project-slug'
sentry-cli info
```

Alternative local config:

```bash
sentry-cli login
sentry-cli config set defaults.org my-org-slug
sentry-cli config set defaults.project my-project-slug
sentry-cli info
```

Verification criterion: `sentry-cli info` succeeds and shows the intended server/org/project context without exposing the token.

## Release Workflow

A safe default release workflow:

```bash
set -euo pipefail

VERSION="$(sentry-cli releases propose-version)"
ENVIRONMENT="production"

sentry-cli releases new "$VERSION"
sentry-cli releases set-commits "$VERSION" --auto
# build and upload artifacts here
sentry-cli deploys new --release "$VERSION" -e "$ENVIRONMENT"
sentry-cli releases finalize "$VERSION"
```

Useful variants:

```bash
# Create and immediately finalize if no later artifact/build step is needed
sentry-cli releases new "$VERSION" --finalize

# If automatic commit association cannot find a provider commit but fallback is acceptable
sentry-cli releases set-commits "$VERSION" --auto --ignore-missing

# List deploys for a release
sentry-cli deploys list --release "$VERSION"
```

Release names are organization-wide enough to collide across projects. If multiple projects share the same semantic version but should be separate releases, make the version unique, for example `frontend-1.2.3` and `backend-1.2.3`.

Completion criterion: the release exists, commits are associated when intended, deploy record exists for the intended environment, and the app SDK will send the exact same `release` value.

## JavaScript Source Maps

For modern Sentry JavaScript SDKs and CLI versions, prefer Debug ID based artifact bundles when possible.

Manual Debug ID flow:

```bash
# Build first so the directory contains generated JS and .map files
npm run build

# Inject Debug IDs into minified artifacts and source maps
sentry-cli sourcemaps inject /path/to/build-output

# Upload artifact bundle
sentry-cli sourcemaps upload /path/to/build-output
```

Release-based or path-prefix upload flow, useful for older setups:

```bash
sentry-cli sourcemaps upload /path/to/sourcemaps \
  --release "$VERSION" \
  --dist "$DIST" \
  --url-prefix '~/static/js' \
  --strip-common-prefix
```

Common source map checks:

```bash
# Confirm debug IDs were injected
python3 - <<'PY'
from pathlib import Path
root = Path('/path/to/build-output')
for p in list(root.rglob('*.js'))[:20]:
    text = p.read_text(errors='ignore')
    if 'debugId=' in text:
        print('debugId in', p)
for p in list(root.rglob('*.map'))[:20]:
    text = p.read_text(errors='ignore')
    if 'debug_id' in text:
        print('debug_id in', p)
PY
```

Completion criterion: uploaded artifacts match the deployed files, `release`/`dist` match SDK runtime values when used, and minified stack traces resolve in a test event or a recent real event.

## Debug Information Files

For native, mobile, or compiled platforms, use the debug-files subcommands:

```bash
# Inspect files before upload
sentry-cli debug-files check /path/to/symbols-or-binaries

# Upload dSYM, ProGuard, Breakpad, ELF, PDB, or other supported debug files
sentry-cli debug-files upload /path/to/symbols-or-binaries
```

Use command help for platform-specific flags:

```bash
sentry-cli debug-files upload --help
```

Completion criterion: the upload command reports processed files and Sentry shows debug files available for the target project/org.

## Events, Logs, and Diagnostics

Ad-hoc event submission is useful for smoke tests:

```bash
sentry-cli send-event -m "sentry-cli smoke test for $VERSION"
```

General diagnostics:

```bash
sentry-cli --version
sentry-cli info
sentry-cli help
sentry-cli <subcommand> --help
```

When troubleshooting in CI, print versions and non-secret target values only:

```bash
echo "sentry-cli: $(sentry-cli --version)"
echo "SENTRY_ORG=$SENTRY_ORG SENTRY_PROJECT=$SENTRY_PROJECT VERSION=$VERSION ENVIRONMENT=${ENVIRONMENT:-}"
sentry-cli info
```

Never echo `SENTRY_AUTH_TOKEN`.

## CI Template

```bash
set -euo pipefail

: "${SENTRY_AUTH_TOKEN:?missing SENTRY_AUTH_TOKEN}"
: "${SENTRY_ORG:?missing SENTRY_ORG}"
: "${SENTRY_PROJECT:?missing SENTRY_PROJECT}"

VERSION="${SENTRY_RELEASE:-$(sentry-cli releases propose-version)}"
ENVIRONMENT="${SENTRY_ENVIRONMENT:-production}"

sentry-cli info
sentry-cli releases new "$VERSION" || true
sentry-cli releases set-commits "$VERSION" --auto || \
  sentry-cli releases set-commits "$VERSION" --auto --ignore-missing

# run build here
# npm ci && npm run build

# optional JS source maps
# sentry-cli sourcemaps inject dist
# sentry-cli sourcemaps upload dist --release "$VERSION"

sentry-cli deploys new --release "$VERSION" -e "$ENVIRONMENT"
sentry-cli releases finalize "$VERSION"
```

Make the release identifier available to the application build so the SDK sends matching events, for example `SENTRY_RELEASE=$VERSION` or the framework-specific release setting.

## Common Pitfalls

1. **Release mismatch between CLI and SDK.** If source maps or commits seem missing, first compare the CLI `VERSION` with the event's `release` tag in Sentry. They must match byte-for-byte.

2. **Wrong org/project slug.** Display names and slugs differ. Verify with `sentry-cli info` before uploads.

3. **Token leaked in logs.** Use masked CI secrets and never print `SENTRY_AUTH_TOKEN`.

4. **Source maps uploaded from the wrong directory.** Upload the final deployed build output, not stale intermediate files. For Debug ID flow, run `sentry-cli sourcemaps inject` after the final build and before upload/deploy.

5. **URL prefix mismatch.** In release/path based source-map uploads, `--url-prefix` must match the URL/path seen in stack frames. Debug ID flow reduces dependence on URL prefix matching.

6. **Commit association fails in shallow clones.** CI often checks out limited git history. Fetch enough history or use `--ignore-missing` when fallback behavior is acceptable.

7. **Release collision across projects.** Prefix release names when same version numbers should represent different projects.

8. **Finalizing too early.** If finalization is part of release ordering or commit association logic, finalize after artifacts and deploy records are in place unless the pipeline intentionally finalizes at creation.

9. **Assuming deploys can be deleted.** Sentry CLI docs state deploys can be listed but not deleted; avoid creating test deploys in production environments.

## Verification Checklist

- [ ] `sentry-cli --version` ran successfully.
- [ ] `sentry-cli info` confirmed the intended org/project/server.
- [ ] Token was provided through a secret/env var and was not printed.
- [ ] Release identifier was computed once and reused by CLI and app build/runtime.
- [ ] For releases: creation/finalization completed and commits/deploys were associated as intended.
- [ ] For source maps: artifacts are from the deployed build output; Debug IDs or release/dist/url-prefix match runtime events.
- [ ] For debug files: `debug-files check` or equivalent inspection was run before upload when possible.
- [ ] A read/list command, Sentry UI check, or smoke event verified the operation.
