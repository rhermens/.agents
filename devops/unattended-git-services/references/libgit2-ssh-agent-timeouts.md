# libgit2 SSH-agent authentication and timeout boundaries

## The important call boundary

In git2-rs, `Cred::ssh_key_from_agent(username)` creates a credential object. It normally does not perform the later SSH-agent signing exchange while the Rust `RemoteCallbacks::credentials` callback is executing.

The actual sequence is:

1. libgit2 requests a credential through the Rust callback.
2. The callback returns an agent-backed credential object.
3. Later, libgit2's SSH transport connects to the agent, lists identities, and asks the agent to sign/authenticate.
4. libssh2 may return `LIBSSH2_ERROR_EAGAIN` while an approval-oriented agent is waiting, locked, or suppressing a background GUI prompt.
5. Some libgit2/libssh2 paths loop internally on `EAGAIN` without returning to the Rust credentials callback.

Consequences:

- A deadline checked inside `RemoteCallbacks::credentials` cannot interrupt the later wait/spin.
- `recv_timeout` around only `Cred::ssh_key_from_agent` usually times out nothing because construction returns immediately.
- A thread does not provide cancellation: native code can remain stuck after the caller gives up, and Rust cannot safely kill that thread.
- Returning an on-disk-key fallback only when `ssh_key_from_agent` construction fails does not handle later agent denial or waiting. Credential construction success is not authentication success.
- Generic server/connect timeout settings are not a dependable bound for this SSH-agent authorization path.

## Desktop authorization is not TTY input

1Password's SSH agent uses authorization controlled by the desktop application. Background Git requests may have prompts suppressed when their originating process is not foregrounded; the tray UI may show **SSH request waiting**. `StandardInput=tty`, `TTYPath`, SSH `-t`, and askpass configuration do not surface this desktop-owned prompt.

Approvals may be scoped by application/process and time, and may change when the desktop agent locks or quits. A service that worked earlier can therefore encounter a new authorization request later.

## Diagnostic signature

A likely wedged remote operation has several of these signs:

- unit reports `active (running)` but logs stop advancing
- process is single-threaded in `R` state rather than sleeping
- sustained CPU use or very high accumulated CPU time
- open TCP and desktop-agent Unix sockets remain attached
- repository has pending changes that ordinary `git status` sees
- restarting only the unit immediately processes those changes

Useful probes:

```bash
systemctl --user status <unit> --no-pager -l
systemctl --user show <unit> -p MainPID -p Environment -p ExecStart
ps -o pid,state,etime,time,pcpu,wchan:24,cmd -p <pid>
lsof -nP -p <pid>
SSH_AUTH_SOCK="$HOME/.1password/agent.sock" ssh-add -l
SSH_AUTH_SOCK="$HOME/.1password/agent.sock" timeout 10 \
  ssh -o BatchMode=yes -o ConnectTimeout=5 -T git@github.com
```

A successful current SSH probe proves current agent availability, not what happened at the original hang time. Preserve that distinction in the diagnosis.

## Reliable timeout patterns

### Preferred: one-shot service and timer

Run one synchronization per process. Let the service manager own cancellation:

```ini
[Service]
Type=oneshot
ExecStart=/absolute/path/git-watch --once --path /absolute/repository
TimeoutStartSec=30s
```

Schedule it with a systemd user timer. A wedged operation is killed, and the next invocation receives a fresh process, SSH session, and agent connection.

### Long-lived coordinator with bounded child

If orchestration must remain resident, move all Git/network work into a `--once` child process:

1. Spawn with `std::process::Command`.
2. Poll `Child::try_wait()` until completion or deadline.
3. On deadline, call `Child::kill()`.
4. Call `wait()` to reap the child.
5. Log a timeout and retry only on the next normal interval.

Do not perform the native Git operation in a worker thread and abandon the join handle.

### Coarse daemon mitigation

For an existing daemon, `RuntimeMaxSec` plus `Restart=always` limits how long a wedge survives. This is less precise because it restarts healthy daemons periodically and bounds total process lifetime rather than a single synchronization.

## Credential alternatives

For genuinely unattended operation, a dedicated on-disk SSH key or conventional agent avoids desktop approval waits, at the cost of a different security model. If using an on-disk key, choose it directly rather than pretending an agent-construction failure can catch later authorization failure.

## Verification recipe

1. Use a fixture child that deliberately blocks longer than the configured timeout.
2. Confirm the service manager kills it at the expected deadline.
3. Replace the fixture with the real one-shot command.
4. Trigger a run and verify commit/push behavior.
5. Trigger another run after the interval and verify a fresh PID and clean repository.
6. Confirm local HEAD equals its upstream branch and CPU does not accumulate in a permanent running loop.
