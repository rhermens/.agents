---
name: nix-user-services
description: "Define and verify Home Manager user services."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [nix, home-manager, systemd, services]
    category: devops
---

# Nix User Services Skill

Define persistent per-user services through Home Manager, with systemd on Linux and no invalid configuration on Darwin. This covers service declaration and evaluation; it does not replace application-specific security, authentication, or deployment design.

## When to Use

- A user asks to run a CLI, local server, or dashboard persistently through their Nix configuration.
- A Home Manager module is shared by Linux and macOS and needs a Linux-only systemd service.
- A service must survive login-session changes and restart after failure.

## Prerequisites

- The target repository is a Nix flake with a Home Manager configuration.
- Inspect the module that imports the service and the application package or wrapper before choosing `ExecStart`.
- Use `read_file`, `search_files`, and `terminal` to establish the existing Nix style and the actual executable path.

## How to Run

1. Read the target `.nix` module and search the repository for existing `systemd.user.services` conventions.
2. Inspect the executable that will run in the service. Do not assume a package attribute exports a matching CLI binary.
3. Add a `systemd.user.services.<name>` declaration with a stable `ExecStart`, explicit working directory where appropriate, restart policy, and `Install.WantedBy = [ "default.target" ]`.
4. For reusable flakes, expose Home Manager modules at top level (`homeManagerModules.default`), not under `eachDefaultSystem`; if the module is meant to be imported from NixOS/nix-darwin module lists, add `nixosModules.default` / `darwinModules.default` wrappers that insert it through `home-manager.sharedModules`.
5. For a Home Manager module that should evaluate on both Linux and Darwin, emit platform-native service namespaces:
   - Linux: `systemd.user.services.<name>`
   - Darwin: `launchd.agents.<name>` with `config.ProgramArguments`, `config.KeepAlive`, and `config.RunAtLoad`
   Inside real Home Manager modules, prefer `lib.mkIf pkgs.stdenv.isLinux { ... }` / `lib.mkIf pkgs.stdenv.isDarwin { ... }` inside a surrounding `lib.mkMerge`; `mkIf` stays lazy enough to avoid forcing the `pkgs` module argument during option collection. Avoid `lib.optionalAttrs pkgs.stdenv...` in a module `config` value when `pkgs` is supplied by the module system — it forces `pkgs` too early and can cause `_module.args.pkgs` infinite recursion.
6. Evaluate the exact generated service configuration with `nix eval --json` before activation. For cross-platform modules, evaluate representative Linux and Darwin systems even from a Linux host by selecting `nixpkgs.legacyPackages.x86_64-linux` and `nixpkgs.legacyPackages.x86_64-darwin` in a targeted `lib.evalModules` expression.
7. Run `git diff --check`. Do not activate a full NixOS/Home Manager generation unless the user asked and the scope of unrelated pending changes is understood.

## Quick Reference

See `references/home-manager-cross-platform-modules.md` for the reusable flake output shape, NixOS/nix-darwin wrapper modules, platform gating pitfalls, and ad-hoc verification script pattern.

See `references/ssh-agent-sockets.md` for the durable pattern when systemd user services need Git SSH authentication through 1Password or another SSH agent socket.

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

## Procedure

### 1. Choose the executable deliberately

Check the package output or existing wrapper. Desktop packages and server CLIs often have different executable names. If a user-maintained wrapper is the supported entry point, use its absolute path and set any required service environment explicitly.

### 2. Expose reusable flake modules at the right level

When a flake exports a Home Manager module meant to be imported as `inputs.<name>.homeManagerModules.default`, do not define it inside `flake-utils.lib.eachDefaultSystem`; that shape becomes `homeManagerModules.<system>.default` and consumers get `attribute 'default' missing`. Define the module once in an outer `let`, reference the package as `self.packages.${pkgs.stdenv.hostPlatform.system}.default` from inside the module, then merge top-level module outputs after `eachDefaultSystem`:

```nix
outputs = { self, nixpkgs, flake-utils, crane }:
  let
    homeManagerModule = { config, lib, pkgs, ... }:
      let
        package = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      in {
        # options/config
      };
  in
  flake-utils.lib.eachDefaultSystem (system: {
    packages.default = ...;
  }) // {
    homeManagerModules.default = homeManagerModule;
    homeManagerModules.<name> = homeManagerModule;
  };
```

If users import from a NixOS/nix-darwin module list that already enables Home Manager, provide wrapper modules that add the HM module via `home-manager.sharedModules`:

```nix
nixosModules.default = { ... }: {
  home-manager.sharedModules = [ homeManagerModule ];
};

darwinModules.default = { ... }: {
  home-manager.sharedModules = [ homeManagerModule ];
};
```

### 3. Bind local admin surfaces safely

For dashboards intended for local use, bind to `127.0.0.1` unless the user explicitly needs remote access and the application authentication design has been reviewed. Do not add insecure bypass flags merely to make a service start.

### 3. Keep macOS evaluation valid

A shared Home Manager module may be imported by both Linux and Darwin configurations. If the service should run on both platforms, generate platform-native services: `systemd.user.services` on Linux and `launchd.agents` on Darwin. Use LaunchAgent `config.ProgramArguments` as a list rather than a shell string; no shell escaping is needed there because launchd calls the executable directly.

When gating these platform-specific service definitions in a real Home Manager module, prefer `lib.mkIf pkgs.stdenv.isLinux { ... }` / `lib.mkIf pkgs.stdenv.isDarwin { ... }` in a surrounding `lib.mkMerge`. Do not use `lib.optionalAttrs pkgs.stdenv...` in module `config` when `pkgs` comes from the module system; `optionalAttrs` is strict in its condition and can force `_module.args.pkgs`, causing infinite recursion in NixOS/Home Manager integration. For ad-hoc tests, define both `systemd.user.services` and `launchd.agents` dummy options if needed so `mkIf false` option trees can be type-checked safely.

### 4. Verify declaratively before activation

Use targeted `nix eval` for the exact service attribute. Confirm the generated `ExecStart`, environment, restart policy, and `WantedBy` values. `git diff --check` catches whitespace and patch errors, but is not a substitute for Nix evaluation.

## Pitfalls

- Do not assume `pkgs.<name>` exposes a same-named executable; inspect it first.
- Do not put `homeManagerModules.default` inside `flake-utils.lib.eachDefaultSystem` unless consumers are expected to import `homeManagerModules.<system>.default`; top-level `homeManagerModules.default` must be merged outside `eachDefaultSystem`.
- Do not import a Home Manager module directly into a NixOS or nix-darwin top-level module list unless it is explicitly valid there. When Home Manager is enabled by the system config, expose a wrapper `nixosModules.default` / `darwinModules.default` that sets `home-manager.sharedModules = [ homeManagerModule ];`.
- Do not place a Linux-only `systemd` service in a shared module without a Linux guard or omission.
- Do not use `lib.optionalAttrs pkgs.stdenv...` in a Home Manager module `config` value when `pkgs` is supplied by the module system; `optionalAttrs` forces its condition during module pushdown and can cause `_module.args.pkgs` infinite recursion. Use `lib.mkIf pkgs.stdenv.isLinux { ... }` / `lib.mkIf pkgs.stdenv.isDarwin { ... }` inside `lib.mkMerge` for platform-specific service definitions in real Home Manager modules.
- For launchd, prefer `ProgramArguments = [ exe "--flag" value ];` over a single shell command string; launchd does not need shell quoting for list arguments.
- Do not activate a system generation as incidental verification when the checkout contains unrelated changes.
- `--skip-build` is suitable only when the server's static assets are already available; otherwise use the application's documented build/deployment path.

## Verification

- `nix eval --json` returns the generated service object for the Linux configuration.
- If applicable, a Darwin configuration evaluates and returns generated `launchd.agents` with expected `ProgramArguments`, labels, and restart/load settings, without exposing an invalid `systemd` declaration.
- `git diff --check` passes.
- When there is no canonical repo test/lint/build command that exercises the Home Manager module change, create a focused temporary ad-hoc verification script under `/tmp` using an OS-safe `hermes-verify-` filename prefix. Have it evaluate the module with representative enabled/disabled services and assert exact generated names and command arguments. For cross-platform modules, evaluate both Linux and Darwin package sets in the script where possible, then clean up the temporary script/output. Report this explicitly as ad-hoc verification rather than suite green.
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

In the output, report `state`, `pid`, `runs`, `last exit code`, the plist `path`, and the command from `program` / `arguments`.

For macOS Unified Logging, the portable `journalctl -xef` equivalent is:

```bash
/usr/bin/log stream --style compact --level debug
```

Use `/usr/bin/log` (or `command log`) when a user's shell reports `log: too many arguments`; that symptom usually means something named `log` is shadowing the system binary in the interactive shell. On newer macOS versions, prefer `--level debug` over older examples using separate `--info --debug` flags. For a specific launchd service/process:

```bash
/usr/bin/log stream --style compact --level debug --process <process-name>
/usr/bin/log stream --style compact --level debug --predicate 'process == "<process-name>" OR eventMessage CONTAINS "<launchd.label>"'
```
