# Hermes _SANE_PATH missing NixOS system directories

## Origin

Discovered while debugging a `Cleanup notes` cron job on NixOS that kept
failing or exhausting its tool-call budget without applying edits.

## The bug

Hermes Agent's terminal tool builds PATH from the agent process's PATH plus
a static fallback (`_SANE_PATH` in `tools/environments/local.py`). The
original `_SANE_PATH` only included macOS/Homebrew and standard FHS Linux
dirs:

```python
_SANE_PATH = (
    "/opt/homebrew/bin:/opt/homebrew/sbin:"
    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
)
```

On NixOS, `ls`, `find`, `head`, `grep`, `rg` live in
`/run/current-system/sw/bin`, which was absent from both the cron process's
PATH and the `_SANE_PATH` fallback.

## Why search_files broke too

The `search_files` tool (in `tools/file_operations.py`) internally pipes
ripgrep output through `head -n <limit>`:

```python
cmd_parts.extend(["|", "head", "-n", str(fetch_limit)])
```

Since `head` was not on PATH, every `search_files` call returned:

```
(eval):1: command not found: head
```

instead of search results. This affected both filename and content searches.

## How it manifested in cron runs

The cron agent (running `minimax/minimax-m3` or `openai/gpt-oss-120b`)
would:

1. Try `ls -la /path | head -50` → `command not found: ls` + `command not found: head`
2. Try `search_files` → `command not found: head`
3. Try `find /path | head -50` → `command not found: find` + `command not found: head`
4. Try `/bin/ls` → `no such file or directory: /bin/ls` (NixOS has no `/bin/ls`)
5. Eventually fall back to `python3 << 'EOF'` heredocs
6. Run out of tool-call budget before completing the actual task

Each run wasted 4–7 tool calls on PATH diagnostics.

## The fix

Patched `_append_missing_sane_path_entries()` in
`tools/environments/local.py` to append NixOS system dirs when they exist:

```python
# After the existing _SANE_PATH loop, before the return:
import os as _os
for nix_dir in (
    "/run/current-system/sw/bin",
    "/etc/profiles/per-user/" + _os.environ.get("USER", ""),
    "/nix/var/nix/profiles/default/bin",
):
    if nix_dir and nix_dir not in seen and _os.path.isdir(nix_dir):
        ordered_entries.append(nix_dir)
```

The `isdir` guard ensures this is a no-op on non-NixOS systems (macOS,
standard Linux, Windows).

## Verification

- 139 tests in the three PATH-related test files: all pass
- 190 tests across the broader local-env/terminal suite: all pass
- Total: 329 passed, 0 failed

```
tests/tools/test_browser_homebrew_paths.py     ✓ (48 tests)
tests/tools/test_local_env_blocklist.py         ✓ (51 tests)
tests/tools/test_windows_native_support.py      ✓ (58 tests)
+ 10 more local-env/terminal test files          ✓ (142 tests)
```

## Test runner note

`scripts/run_tests.sh` probes `.venv` first, which may exist as a stripped
install without pip/pytest. The `venv/` directory (also in the probe list)
had pip but no pytest either. Fix:

```bash
venv/bin/pip install pytest pytest-asyncio pytest-timeout
```

Then run pytest directly with `venv/bin/python -m pytest` instead of the
runner script, which insists on `.venv` first.
