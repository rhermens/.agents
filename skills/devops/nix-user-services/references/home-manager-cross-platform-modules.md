# Cross-platform Home Manager service modules

Use this reference when a flake exports a Home Manager service module that must work from direct Home Manager imports and from NixOS/nix-darwin module lists.

## Flake output shape

Do not put reusable `homeManagerModules.default` inside `flake-utils.lib.eachDefaultSystem`; that produces `homeManagerModules.<system>.default` and consumers using `homeManagerModules.default` get `attribute 'default' missing`.

Preferred shape:

```nix
outputs = { self, nixpkgs, flake-utils, crane }:
  let
    homeManagerModule = { config, lib, pkgs, ... }:
      let
        package = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      in {
        options = { /* Home Manager options */ };
        config = { /* Home Manager config */ };
      };
  in
  flake-utils.lib.eachDefaultSystem (system: {
    packages.default = /* package for system */;
  }) // {
    homeManagerModules.default = homeManagerModule;
    homeManagerModules.<name> = homeManagerModule;

    nixosModules.default = { ... }: {
      home-manager.sharedModules = [ homeManagerModule ];
    };

    darwinModules.default = { ... }: {
      home-manager.sharedModules = [ homeManagerModule ];
    };
  };
```

Use the wrapper modules from top-level NixOS/nix-darwin module lists. Use `homeManagerModules.default` only inside a Home Manager import list.

## Platform service gating

Inside real Home Manager modules, prefer lazy module conditionals:

```nix
config = lib.mkIf enabled (lib.mkMerge [
  { home.packages = [ package ]; }

  (lib.mkIf pkgs.stdenv.isLinux {
    systemd.user.services.<name> = { /* ... */ };
  })

  (lib.mkIf pkgs.stdenv.isDarwin {
    launchd.agents.<name> = { /* ... */ };
  })
]);
```

Do not use `lib.optionalAttrs pkgs.stdenv.isLinux { ... }` in module `config` when `pkgs` is supplied by the module system. `optionalAttrs` is strict in its condition and can force `_module.args.pkgs` during module collection, causing infinite recursion in NixOS/Home Manager integration.

For launchd, use argument lists rather than shell strings:

```nix
ProgramArguments = [
  "${package}/bin/example"
  "--path"
  (toString service.path)
  "--interval"
  (toString service.interval)
];
```

For systemd `ExecStart`, shell-escape string-like user values:

```nix
ExecStart = "${package}/bin/example --path ${lib.escapeShellArg (toString service.path)} --interval ${toString service.interval}";
```

## Option types

If the CLI expands `~` itself, allow string paths in addition to Nix path literals:

```nix
path = lib.mkOption {
  type = lib.types.either lib.types.path lib.types.str;
  default = lib.mkHomeDirPath "example";
};
```

For positive integer CLI flags such as sync intervals:

```nix
interval = lib.mkOption {
  type = lib.types.ints.positive;
  default = 60;
  description = "Sync interval in seconds";
};
```

## Verification pattern

Create an ad-hoc `/tmp/hermes-verify-*` script that evaluates both Linux and Darwin package sets with representative enabled/disabled services. In the dummy eval module, declare both possible platform namespaces so `mkIf false` trees can be type-checked without unrelated missing-option noise:

```nix
options = {
  home.packages = lib.mkOption { type = lib.types.listOf lib.types.anything; default = [ ]; };
  systemd.user.services = lib.mkOption { type = lib.types.attrsOf lib.types.anything; default = { }; };
  launchd.agents = lib.mkOption { type = lib.types.attrsOf lib.types.anything; default = { }; };
};
```

Assert:

- top-level `homeManagerModules.default`, `nixosModules.default`, and `darwinModules.default` exist
- Linux generates only expected `systemd.user.services`
- Darwin generates only expected `launchd.agents`
- disabled services are omitted
- CLI args such as `--path`, `--log-level`, and `--interval` are present with expected defaults/custom values

For full integration, test a consumer flake with `--override-input <input> /path/to/local/repo` before asking the user to update their lock file.
