---
name: unattended-git-services
description: "Design, debug, and verify unattended Git synchronization services, including SSH-agent authorization and bounded network operations."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [git, systemd, launchd, ssh-agent, services, reliability]
    related_skills: [nix-user-services, systematic-debugging]
---

# Unattended Git Services

Design and troubleshoot background services that fetch, commit, and push Git repositories without assuming an interactive terminal or indefinitely reliable credentials.

## When to Use

- A Git synchronization daemon is active but stops committing or pushing.
- A systemd user service or LaunchAgent uses SSH credentials from 1Password or another desktop agent.
- A remote Git operation needs a hard timeout or reliable retry boundary.
- A long-lived Git process survives suspend, network changes, agent locking, or GUI authorization expiry.

## Procedure

1. Inspect the service's generated command, environment, PID, process state, CPU time, and recent logs. Do not equate `active (running)` with healthy progress.
2. Compare the last completed tick against repository status and file modification times. Establish whether change detection or the remote operation is stuck.
3. Inspect open SSH-agent and TCP sockets. Test the exact service socket with `ssh-add -l` and a bounded `ssh -o BatchMode=yes` probe.
4. For approval-oriented desktop agents, check their GUI for suppressed authorization requests. Do not add a TTY: the desktop agent owns the prompt.
5. Restart only the affected service as a diagnostic probe. Verify that pending changes are processed and that the process returns to sleeping or exits normally.
6. Confirm the deployed binary and unit match current source. Check branch/refspec behavior against each watched repository's actual branch.
7. Bound the entire remote operation at a process boundary. Prefer a one-shot service plus timer and service-level timeout over an immortal in-process loop.
8. Verify at least one subsequent interval, repository cleanliness, local/remote branch alignment, process state, and CPU behavior.

## Reliability Design

Prefer one synchronization per process:

- systemd: `Type=oneshot`, a finite `TimeoutStartSec`, and a user timer
- launchd: one bounded invocation per scheduled run, with explicit stdout/stderr paths
- long-lived coordinator: spawn a `--once` child, poll it, then kill and reap it after the deadline

Threads are not a safe cancellation boundary for native Git/SSH calls: Rust cannot forcibly terminate a thread stuck inside FFI.

## Pitfalls

- `Restart=on-failure` cannot recover a process that spins forever without exiting.
- A credential callback timeout may not bound authentication; many libraries use the returned credential later.
- Creating an SSH-agent credential successfully does not prove the later signature request will be approved.
- A fallback after constructing an agent credential may never run when authentication fails later.
- Desktop-agent prompts are GUI authorization, not terminal input; TTY and askpass flags are usually irrelevant.
- Hard-coded branch refspecs break repositories using a different default branch.
- Do not activate a full declarative system generation when unrelated uncommitted changes are present without understanding their scope.

## Verification

- A forced-hang fixture is terminated by the configured timeout.
- The next scheduled invocation starts with a fresh process and can succeed.
- Pending changes are committed once and pushed to the current branch.
- The repository is clean and aligned with its upstream afterward.
- The service is sleeping normally or has exited, with no sustained CPU spin.

## References

See `references/libgit2-ssh-agent-timeouts.md` for why libgit2 credential callbacks cannot reliably timeout desktop SSH-agent authorization and for recommended process-boundary designs.
