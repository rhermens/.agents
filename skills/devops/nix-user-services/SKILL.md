---
name: nix-user-services
description: "Define and verify Home Manager user services."
license: MIT
metadata:
  version: "1.0.0"
  author: "Hermes Agent"
  platforms: "linux, macos"
  hermes.tags: "nix, home-manager, systemd, services"
  hermes.category: "devops"
---

# Nix User Services Skill

Define persistent per-user services through Home Manager, with systemd on Linux and no invalid configuration on Darwin. This covers service declaration and evaluation; it does not replace application-specific security, authentication, or deployment design.

## When to Use

- A user asks to run a CLI, local server, or dashboard persistently through their Nix configuration.
- A Home Manager module is shared by Linux and macOS and needs a Linux-only systemd service.
- A service must survive login-session changes and restart after failure.

## Prerequisites

The target repository is a Nix flake with a Home Manager configuration.

## Workflow

1. Read the service module, its imports, and existing service declarations.
2. Inspect the package output or supported wrapper to select the executable.
3. Set an absolute command path, required environment, working directory where appropriate, restart policy, and startup target.
4. For reusable flakes, expose `homeManagerModules.default` at top level. Use `home-manager.sharedModules` wrappers for NixOS/nix-darwin imports.
5. For shared modules, select platform-native services:
   - Linux: `systemd.user.services.<name>` with `Install.WantedBy = [ "default.target" ]`.
   - Darwin: `launchd.agents.<name>` with `config.ProgramArguments`, `config.KeepAlive`, and `config.RunAtLoad`.
   - Gate platform definitions with `lib.mkIf` inside `lib.mkMerge`.
   - Pass launchd arguments as a list, such as `[ exe "--flag" value ]`.
6. Follow the verification steps below before activation.

For reusable or cross-platform modules, read the [module patterns and evaluation guidance](references/home-manager-cross-platform-modules.md).

## Quick Reference

See `references/ssh-agent-sockets.md` for the durable pattern when systemd user services need Git SSH authentication through 1Password or another SSH agent socket.

See `references/darwin-launchd-git-ssh-logs.md` for diagnosing macOS LaunchAgents that commit but do not push because they lack the interactive SSH/1Password agent, and for adding stdout/stderr log files.

```nix
systemd.user.services.example-server = lib.mkIf pkgs.stdenv.isLinux {
  Unit = {
    Description = "Example local server";
    After = [ "network-online.target" ];
    Wants = [ "network-online.target" ];
  };

  Service = {
    ExecStart = "${config.home.homeDirectory}/.local/bin/example serve --host 127.0.0.1 --port 9119";
    WorkingDirectory = config.home.homeDirectory;
    Restart = "always";
    RestartSec = 5;
  };

  Install.WantedBy = [ "default.target" ];
};
```

Inspect a generated unit declaration without activating it:

```bash
nix eval --json .#nixosConfigurations.<host>.config.home-manager.users.<user>.systemd.user.services.<service>
```

## Service constraints

- Bind local dashboards to `127.0.0.1` unless remote access is explicitly requested and the authentication design has been reviewed.
- Do not add insecure bypass flags merely to make a service start.
- Source declarative service variables from Home Manager, for example `config.home.sessionVariables.SSH_AUTH_SOCK or null`.
  Omitted variables inherit the service manager's environment, which can contain a stale SSH agent socket.
- Use `--skip-build` only when the application's static assets are already available.
- Activate a full NixOS/Home Manager generation only when requested and the scope of unrelated pending changes is understood.

## Verification

- Evaluate the generated service with `nix eval --json`. Check service names and labels, executable, arguments, environment, working directory, restart policy, and startup target.
- For shared modules, evaluate representative Linux and Darwin configurations, including enabled and disabled services.
  Linux should produce the intended systemd services; Darwin should produce LaunchAgents without invalid systemd declarations.
  Cross-platform probes can select `nixpkgs.legacyPackages.x86_64-linux` and `nixpkgs.legacyPackages.x86_64-darwin` through `lib.evalModules`.
- `git diff --check` passes.
- If no repository check covers the module, use a safely created temporary `/tmp/hermes-verify-*` script to assert the generated configuration.
  Remove temporary scripts and output afterward. Report these checks as ad-hoc verification.
- After an explicitly requested activation, use `systemctl --user status <service>` on Linux, or `launchctl print gui/$UID/<label>` / launchd logs on Darwin, and inspect startup failures.

### Darwin launchd status and logs

When the user gives a friendly service name rather than the full LaunchAgent label, first discover the label before printing status:

```bash
launchctl print gui/$UID/<friendly-name> 2>&1 || \
launchctl print gui/$UID/com.<friendly-name> 2>&1 || \
launchctl print gui/$UID | grep -i -A5 -B5 '<friendly-name>'

grep -R '<friendly-name>' ~/Library/LaunchAgents /Library/LaunchAgents /Library/LaunchDaemons 2>/dev/null || true
```

Then print the actual label:

```bash
launchctl print gui/$UID/<actual.label>
# or for system daemons:
sudo launchctl print system/<actual.label>
```

In the output, report `state`, `pid`, `runs`, `last exit code`, the plist `path`, and the command from `program` / `arguments`. For Git/SSH services, also inspect the process environment and compare the service's agent socket with the interactive one:

```bash
ps eww -p <pid> -o command | tr ' ' '\n' | grep -E '^(HOME|SSH_AUTH_SOCK|PATH)='
SSH_AUTH_SOCK=<socket-from-service> ssh-add -l 2>&1 || true
SSH_AUTH_SOCK=$HOME/.1password/agent.sock ssh-add -l 2>&1 || true
```

If a LaunchAgent's generated config has `StandardOutPath = null` and `StandardErrorPath = null`, macOS Unified Logging may show only low-level system messages while the CLI's stderr tracing disappears. Add explicit log files in the LaunchAgent config before concluding the tool is silent:

```nix
launchd.agents.<name>.config = lib.mkIf pkgs.stdenv.isDarwin {
  StandardOutPath = "${config.home.homeDirectory}/Library/Logs/<name>.out.log";
  StandardErrorPath = "${config.home.homeDirectory}/Library/Logs/<name>.err.log";
};
```

For macOS Unified Logging, the portable `journalctl -xef` equivalent is:

```bash
/usr/bin/log stream --style compact --level debug
```

Use `/usr/bin/log` (or `command log`) when a user's shell reports `log: too many arguments`; that symptom usually means something named `log` is shadowing the system binary in the interactive shell. On newer macOS versions, prefer `--level debug` over older examples using separate `--info --debug` flags. For a specific launchd service/process:

```bash
/usr/bin/log stream --style compact --level debug --process <process-name>
/usr/bin/log stream --style compact --level debug --predicate 'process == "<process-name>" OR eventMessage CONTAINS "<launchd.label>"'
```
