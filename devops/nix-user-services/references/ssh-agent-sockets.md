# SSH agent sockets in Home Manager user services

When a systemd user service performs Git SSH operations, do not assume it sees the same `SSH_AUTH_SOCK` as the interactive shell. The user manager can retain an older socket such as GNOME Keyring/GCR while the shell points at 1Password or another agent.

Symptoms include libgit2/OpenSSH authentication failures mentioning the SSH socket or an agent with no identities, while `ssh-add -l` works in the user's shell. A service that times out on every sync cycle (with the `git-watch` supervisor killing the child after its timeout) is a strong indicator of this: the child's `git fetch`/`git push` hangs on SSH authentication against an agent with no usable identities, and the supervisor kills it at exactly the configured timeout.

## Durable module pattern

Expose a nullable per-service option rather than hard-coding a single environment assumption. **Default the option to `config.home.sessionVariables.SSH_AUTH_SOCK or null`** — not bare `null` — so the service picks up the user's declarative SSH agent (e.g. 1Password) rather than inheriting the systemd user manager's stale environment (e.g. GNOME Keyring/GCR). The systemd user manager environment is set at login and does NOT track `home.sessionVariables`; a bare `null` default means the service gets whatever socket the manager happened to capture, which may have no identities:

```nix
sshAuthSock = lib.mkOption {
  type = lib.types.nullOr lib.types.str;
  default = config.home.sessionVariables.SSH_AUTH_SOCK or null;
  description = "SSH agent socket path to pass to the service. Defaults to home.sessionVariables.SSH_AUTH_SOCK when set.";
};
```

For cross-platform Home Manager modules, prefer a small generated wrapper script as the service command. It preserves an inherited `SSH_AUTH_SOCK`, applies `sshAuthSock` when explicitly set, and can recover launchd's user environment on macOS:

```nix
serviceProgram = name: service: pkgs.writeShellScript "example-${name}" ''
  configured_ssh_auth_sock=${lib.escapeShellArg (if service.sshAuthSock == null then "" else service.sshAuthSock)}

  if [ -n "$configured_ssh_auth_sock" ]; then
    export SSH_AUTH_SOCK="$configured_ssh_auth_sock"
  elif [ -z "''${SSH_AUTH_SOCK:-}" ] && command -v launchctl >/dev/null 2>&1; then
    launchd_ssh_auth_sock="$(launchctl getenv SSH_AUTH_SOCK || true)"
    if [ -n "$launchd_ssh_auth_sock" ]; then
      export SSH_AUTH_SOCK="$launchd_ssh_auth_sock"
    fi
  fi

  exec ${package}/bin/example ...
'';
```

Use the wrapper as `systemd.user.services.<name>.Service.ExecStart` on Linux and as the sole `launchd.agents.<name>.config.ProgramArguments` entry on Darwin. On Linux, the systemd user manager environment is inherited when no override is set; on Darwin, `launchctl getenv SSH_AUTH_SOCK` is the practical fallback if the agent environment was imported into launchd.

**Key insight:** the wrapper's `elif [ -z "$SSH_AUTH_SOCK" ]` branch only fires when `SSH_AUTH_SOCK` is unset in the service environment. If `sshAuthSock` defaults to `null`, the wrapper script does NOT override the inherited (stale) socket — it keeps it. The module-level `sshAuthSock` default is what matters: it must resolve to the user's intended agent (`config.home.sessionVariables.SSH_AUTH_SOCK`) so the wrapper sets `configured_ssh_auth_sock` to that value and `export SSH_AUTH_SOCK` overwrites the stale inherited one.

## Verification

Evaluate the generated service, not just the flake package:

- default service's `sshAuthSock` resolves to `home.sessionVariables.SSH_AUTH_SOCK` (not `null`) when that variable is set
- default service's generated wrapper sets `configured_ssh_auth_sock` to the user's intended agent socket
- default service's wrapper has a Darwin `launchctl getenv SSH_AUTH_SOCK` fallback
- explicit `sshAuthSock = "..."` appears in the wrapper and overrides the inherited socket
- `git diff --check` passes

For ad-hoc checks, create a temporary `/tmp/hermes-verify-*.nix` script using `lib.evalModules` with stub `home`, `systemd`, and `launchd` options (plus `_module.args.pkgs`), assert `evaled.config.services.git-watch.<name>.sshAuthSock` equals the expected socket, and remove it after. This avoids needing a full Home Manager evaluation while still proving the option default resolves correctly. Report this explicitly as ad-hoc verification rather than suite green.

For live confirmation, compare the service process's `SSH_AUTH_SOCK` with the interactive shell's:

```bash
# Service environment
tr '\0' '\n' < /proc/<service-pid>/environ | grep '^SSH_AUTH_SOCK='
# Interactive shell
echo "$SSH_AUTH_SOCK"
# Test auth against each
SSH_AUTH_SOCK=<service-socket> ssh-add -l
SSH_AUTH_SOCK=<shell-socket> ssh-add -l
```

If the service socket reports "The agent has no identities" while the shell socket lists keys, the `sshAuthSock` default is the root cause.
