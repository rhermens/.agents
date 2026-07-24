# SSH agent sockets in Home Manager user services

When a systemd user service performs Git SSH operations, do not assume it sees the same `SSH_AUTH_SOCK` as the interactive shell. The user manager can retain an older socket such as GNOME Keyring/GCR while the shell points at 1Password or another agent.

Symptoms include libgit2/OpenSSH authentication failures mentioning the SSH socket or an agent with no identities, while `ssh-add -l` works in the user's shell.

## Durable module pattern

Expose a nullable per-service option rather than hard-coding a single environment assumption. Keep the default as `null` so the service can inherit the user's runtime `SSH_AUTH_SOCK`; use a concrete value only as an override:

```nix
sshAuthSock = lib.mkOption {
  type = lib.types.nullOr lib.types.str;
  default = null;
  description = "SSH agent socket path to pass to the service. When unset, inherit the user's SSH_AUTH_SOCK environment variable.";
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

## Verification

Evaluate the generated service, not just the flake package:

- default service's generated wrapper does not set a fixed socket and preserves inherited `SSH_AUTH_SOCK`
- default service's wrapper has a Darwin `launchctl getenv SSH_AUTH_SOCK` fallback
- explicit `sshAuthSock = "..."` appears in the wrapper and overrides the inherited socket
- `git diff --check` passes

For ad-hoc checks, create a temporary `/tmp/hermes-verify-*.sh` script with `mktemp`, run it via `terminal`, and remove it with a trap so verification evidence is visible to coding-session guards.