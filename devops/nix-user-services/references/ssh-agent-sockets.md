# SSH agent sockets in Home Manager user services

When a systemd user service performs Git SSH operations, do not assume it sees the same `SSH_AUTH_SOCK` as the interactive shell. The user manager can retain an older socket such as GNOME Keyring/GCR while the shell points at 1Password or another agent.

Symptoms include libgit2/OpenSSH authentication failures mentioning the SSH socket or an agent with no identities, while `ssh-add -l` works in the user's shell.

## Durable module pattern

Expose a nullable per-service option rather than hard-coding a single environment assumption. Default to the user's declarative Home Manager session variable when present, while still allowing a per-service override:

```nix
sshAuthSock = lib.mkOption {
  type = lib.types.nullOr lib.types.str;
  default = config.home.sessionVariables.SSH_AUTH_SOCK or null;
  description = "SSH agent socket path to pass to the service. Defaults to home.sessionVariables.SSH_AUTH_SOCK when set.";
};
```

Then add an explicit environment override only to Linux systemd services when the resolved option is set:

```nix
Service = {
  ExecStart = "...";
  Restart = "on-failure";
} // lib.optionalAttrs (service.sshAuthSock != null) {
  Environment = "SSH_AUTH_SOCK=${service.sshAuthSock}";
};
```

By default, the service uses `home.sessionVariables.SSH_AUTH_SOCK` if the user configured it declaratively. If that variable is absent, no service-level override is emitted. Set a concrete per-service socket path only when you want the unit to override the user's session variable.

## Verification

Evaluate the generated service, not just the flake package:

- default service with `home.sessionVariables.SSH_AUTH_SOCK` set includes `Service.Environment = "SSH_AUTH_SOCK=..."`
- default service without that user session variable omits `Service.Environment`
- explicit `sshAuthSock = "..."` overrides the user session variable
- `git diff --check` passes

For ad-hoc checks, create a temporary `/tmp/hermes-verify-*.sh` script with `mktemp`, run it via `terminal`, and remove it with a trap so verification evidence is visible to coding-session guards.