# Pin one package to an older nixpkgs revision

Use when a single package breaks on current nixpkgs but the rest of the system should stay on the current flake input.

## Pattern

Add a dedicated nixpkgs input pinned to a known-good revision:

```nix
inputs = {
  nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  nixpkgs-foo.url = "github:nixos/nixpkgs/<known-good-rev>";
};
```

Then override only that package via an overlay:

```nix
outputs = { self, nixpkgs, nixpkgs-foo, ... }@inputs:
  let
    fooOverlay = final: prev: {
      foo = (import nixpkgs-foo {
        system = prev.stdenv.hostPlatform.system;
        config = prev.config;
      }).foo;
    };
  in {
    nixosConfigurations.host = nixpkgs.lib.nixosSystem {
      modules = [
        {
          nixpkgs.overlays = [ fooOverlay ];
        }
      ];
    };
  };
```

Use `config = prev.config;` so unfree/allowlist configuration and other nixpkgs config from the main package set carry over.

## Verification

Prefer targeted verification before a full switch:

```bash
nix eval --raw '.#nixosConfigurations.<host>.pkgs.foo.version'
nix eval --raw '.#nixosConfigurations.<host>.pkgs.foo.drvPath'
nix build --no-link --print-out-paths '.#nixosConfigurations.<host>.pkgs.foo'
nix build --no-link --print-out-paths '.#nixosConfigurations."<host>".config.system.build.nixos-rebuild'
```

When external process checks require ad-hoc evidence, put those commands in a temporary `/tmp/hermes-verify-*` script, run it, remove it, and explicitly report it as ad-hoc verification.

## MongoDB Compass example

`mongodb-compass` can fail in nixpkgs when its binary Electron package interacts badly with `wrapGAppsHook` from a newer nixpkgs. The many `patchelf: cannot find section '.interp'` lines can be harmless because the package may tolerate them with `|| true`; identify the real fatal line before patching.

A practical workaround is to pin only `mongodb-compass` to a previous known-good nixpkgs revision using the overlay pattern above, leaving the rest of the system on current nixpkgs. Note this pins the nixpkgs package definition/hook context; it may or may not change the upstream application version.