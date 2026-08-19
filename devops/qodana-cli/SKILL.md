---
name: qodana-cli
description: Install, configure, run, and troubleshoot JetBrains Qodana CLI for local static analysis, SARIF reports, quality gates, baselines, fixes, and Qodana Cloud uploads. Use when requests mention `qodana`, `qodana.yaml`, Qodana linters, or Qodana CLI scan results.
license: MIT
compatibility: Requires the Qodana CLI. Container mode requires Docker or a Docker-compatible Podman context. Native mode supports only selected Qodana linters.
metadata:
  author: Roy Hermens
  version: "1.0.0"
---

# Qodana CLI

Use `qodana` for local Qodana analysis and report operations. Prefer project configuration in `qodana.yaml` over long repeated commands.

Check live command help when flags matter. Qodana CLI and linter behavior changes between releases.

## Workflow

1. Identify the project root, requested scope, linter, execution mode, and cloud requirement.
2. Read `qodana.yaml` and related bootstrap scripts before running analysis.
3. Verify the CLI and the container engine or native-mode requirements.
4. Run the smallest analysis that satisfies the request.
5. Read the SARIF output and preserve the Qodana exit status.
6. Report findings, output paths, execution mode, linter, and verification result.

## Safety

- Treat ordinary scans as read-oriented, but expect dependency downloads, caches, and generated reports.
- Inspect `bootstrap`, plugins, mounted volumes, and custom images before scanning an untrusted repository.
- A `bootstrap` command can execute arbitrary code and modify the project.
- Do not use `--apply-fixes` or `--cleanup` without an explicit request.
- Before applying fixes, require a clean worktree or another recoverable snapshot.
- Review the diff after applying fixes. Run the project's tests and formatters when available.
- Do not use `qodana init --force` without authorization to replace the existing configuration.
- A cloud-connected scan binds its report to a Qodana Cloud project.
- Before cloud upload, confirm the intended project and authorization to send analysis data.
- Never print, commit, or place `QODANA_TOKEN` in shell history.
- Treat `QODANA_ENDPOINT` as sensitive infrastructure information when it identifies a private instance.

## Verify Requirements

```bash
qodana --version
qodana --help
```

For container mode:

```bash
docker version
```

Qodana uses the active Docker context. For Podman, use Docker compatibility mode or a Docker context targeting the Podman socket.

For native mode, verify support with current documentation and command help:

```bash
qodana scan --help
```

Native mode supports selected linters only. It may download the corresponding JetBrains IDE.

## Install

Prefer the user's existing package manager.

```bash
# macOS or Linux
brew install jetbrains/utils/qodana

# macOS or Linux installer
curl -fsSL https://jb.gg/qodana-cli/install | bash

# Windows
winget install -e --id JetBrains.QodanaCLI

# Windows alternatives
choco install qodana
scoop bucket add jetbrains https://github.com/JetBrains/scoop-utils
scoop install qodana
```

After installation, run `qodana --version`. Do not upgrade an established CI version unless the user requests it.

## Discover or Initialize Configuration

Read existing configuration first:

```bash
if [ -f qodana.yaml ]; then
  printf '%s\n' 'Existing qodana.yaml found'
else
  qodana init
fi
```

`qodana init` detects the project and creates `qodana.yaml`. Use `--project-dir` when the current directory is not the target root.

```bash
qodana init --project-dir path/to/project
qodana init --help
```

Do not guess a linter when detection is ambiguous. Check the current linter list in `qodana scan --help` and the Qodana linter documentation.

Since Qodana 2025.2, `--linter` names a logical linter. Use `--image` to select a specific container image.

## Configure `qodana.yaml`

Keep reusable settings in the project-root `qodana.yaml`:

```yaml
version: "1.0"
linter: qodana-js
profile:
  name: qodana.recommended
failThreshold: 0
exclude:
  - name: All
    paths:
      - dist
      - coverage
```

Validate keys against the current Qodana schema and documentation:

- Schema: `https://www.schemastore.org/qodana-1.0.json`
- Reference: `https://www.jetbrains.com/help/qodana/qodana-yaml.html`

Use `--config relative/path/to/config.yaml` for a non-default configuration. Relative paths resolve from the project directory.

Before adding exclusions, identify whether generated paths are already excluded. Broad exclusions can hide real findings.

## Run Analysis

Use project configuration by default:

```bash
qodana scan
```

Show problems in terminal output when the result size is manageable:

```bash
qodana scan --print-problems
```

Serve the report after scanning:

```bash
qodana scan --show-report
# Or serve the latest saved report
qodana show
```

Open only the latest report directory:

```bash
qodana show --dir-only
```

Use deterministic artifact paths in automation:

```bash
qodana scan \
  --results-dir .qodana/results \
  --cache-dir .qodana/cache \
  --report-dir .qodana/results/report
```

If these paths are repository-local, confirm `.gitignore` policy before creating or changing it.

### Select execution mode

Container mode:

```bash
qodana scan --linter qodana-js --within-docker true
```

Native mode:

```bash
qodana scan --linter qodana-js --within-docker false
```

Pinned container image:

```bash
qodana scan --image jetbrains/qodana-js:<version>
```

Pin CLI, linter, or image versions in CI for reproducible analysis. Do not copy an example version without checking compatibility.

### Scope analysis

Analyze one project within a repository:

```bash
qodana scan \
  --repository-root . \
  --project-dir path/to/project
```

Analyze one directory while retaining project context:

```bash
qodana scan --only-directory path/inside/project
```

Analyze a commit range:

```bash
qodana scan --diff-start "$(git merge-base HEAD origin/main)" --diff-end HEAD
```

Fetch enough Git history before a diff scan. Missing history can produce incorrect scope or failure.

## Quality Gates and Baselines

Prefer committed quality-gate policy in `qodana.yaml`. Use CLI overrides for one run only.

```bash
qodana scan --fail-threshold 0
```

Use an existing SARIF report as a baseline:

```bash
qodana scan --baseline path/to/qodana.sarif.json
```

Add `--baseline-include-absent` only when the report must include baseline findings absent from the current run.

Do not hide new findings by replacing a baseline without review. Compare old and new SARIF files before committing a new baseline.

Preserve nonzero exits in CI. Qodana uses exit `255` for a failed quality gate and may use `137` for out-of-memory termination.

## Read Reports

The results directory contains `qodana.sarif.json`, logs, and analysis artifacts. The report directory contains the generated HTML report.

View a SARIF file in the terminal:

```bash
qodana view --sarif-file path/to/qodana.sarif.json
```

Extract a compact finding list with `jq`:

```bash
jq '[
  .runs[]?.results[]?
  | {
      ruleId,
      level,
      message: .message.text,
      file: .locations[0].physicalLocation.artifactLocation.uri,
      line: .locations[0].physicalLocation.region.startLine
    }
]' path/to/qodana.sarif.json
```

Do not treat an empty terminal summary as proof of a clean scan. Check the exit status and SARIF contents.

## Apply Quick-Fixes

Only after explicit authorization:

```bash
git status --short
qodana scan --apply-fixes
# Or run cleanup when explicitly requested
qodana scan --cleanup

git diff --check
git diff
```

Afterward, rerun Qodana without mutation flags. Run relevant project tests before reporting completion.

## Qodana Cloud

Paid linters generally require a Qodana Cloud project token. Store it in the environment or a masked CI secret:

```bash
: "${QODANA_TOKEN:?missing QODANA_TOKEN}"
qodana scan
```

The token identifies the Qodana Cloud project, verifies licensing, and binds the report to that project.

For a private Qodana Cloud instance:

```bash
export QODANA_ENDPOINT='https://qodana.example.invalid/'
qodana scan
```

Send an existing report only after cloud-upload authorization:

```bash
: "${QODANA_TOKEN:?missing QODANA_TOKEN}"
qodana send --results-dir path/to/results
```

Never put the token value in `qodana.yaml` or a command example. Redact it from logs and summaries.

## Container Inputs

Qodana CLI does not pass the full host environment into containers. Pass only required variables:

```bash
qodana scan --env NAME=value
```

Mount only required files or directories:

```bash
qodana scan --volume host/path:/container/path
```

Do not mount credential directories broadly. Prefer a single read-only credential file when the workflow supports it.

## Troubleshooting

1. Run `qodana --version` and the failing subcommand with `--help`.
2. Re-run with a suitable `--log-level` only when more detail is needed.
3. Open the results directory with `qodana show --dir-only`.
4. Inspect `log/idea.log`, `projectStructure/Modules.json`, and the SARIF file.
5. Verify the selected linter, execution mode, project root, repository root, and configuration file.
6. For container failures, verify the active Docker context and available memory.
7. For exit `137`, increase container memory or reduce analysis scope.
8. For unresolved dependencies, inspect project import and `bootstrap` behavior.
9. For incorrect diff results, fetch Git history and verify both commit identifiers.
10. Use `--clear-cache` only after evidence suggests stale cache state.

Do not solve import failures by adding arbitrary dependency installation commands. Use the project's lockfile and established setup command.

## Completion Checklist

- [ ] The CLI and execution mode were verified.
- [ ] `qodana.yaml`, bootstrap commands, plugins, and mounts were reviewed.
- [ ] The intended linter and project scope were used.
- [ ] The command exit status was preserved and interpreted.
- [ ] The SARIF or HTML report was located and inspected.
- [ ] No token or private endpoint was exposed.
- [ ] Cloud upload or source mutation had explicit authorization.
- [ ] Applied fixes were reviewed and verified with a clean follow-up scan.

Use these official references when current behavior matters:

- CLI: `https://github.com/JetBrains/qodana-cli`
- Documentation: `https://www.jetbrains.com/help/qodana/`
- Configuration: `https://www.jetbrains.com/help/qodana/configuration-reference.html`
