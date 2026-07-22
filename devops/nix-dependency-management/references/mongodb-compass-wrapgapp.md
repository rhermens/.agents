# MongoDB Compass: manual GApps wrapping override

Context: nixpkgs `mongodb-compass` 1.49.10 had a build command ending in:

```bash
wrapGAppsHook $out/bin/mongodb-compass
```

Manually calling `wrapGAppsHook` can fail with:

```text
wrapGAppsHookHasRunForOutput: bad array subscript
```

Reason: `wrapGAppsHook` is the fixup hook function. It expects the stdenv fixup environment to provide the shell variable `output`; passing `out` as an argument does not set it. For one explicit binary, call `wrapGApp` instead.

Overlay pattern:

```nix
nixpkgs.overlays = [
  (final: prev: {
    mongodb-compass = prev.mongodb-compass.overrideAttrs (old: {
      buildCommand = builtins.replaceStrings
        [ "wrapGAppsHook $out/bin/mongodb-compass" ]
        [ "wrapGApp $out/bin/mongodb-compass" ]
        old.buildCommand;
    });
  })
];
```

Focused ad-hoc verification pattern:

```bash
tmp_script=$(mktemp /tmp/hermes-verify-mongodb-compass.XXXXXX.sh)
# write script with python3/pathlib or another safe method
# include --no-write-lock-file on nix eval/build to avoid incidental flake.lock edits
nix eval --no-write-lock-file --impure --raw '.#nixosConfigurations.omen.pkgs.mongodb-compass.buildCommand'
nix build --no-write-lock-file --no-link --print-out-paths '.#nixosConfigurations.omen.pkgs.mongodb-compass'
$out_path/bin/mongodb-compass --version
rm -f "$tmp_script"
```

Expected version probe for the confirmed case:

```text
MongoDB Compass 1.49.10
```

Pitfall: when verifying local flakes with unlocked/new inputs, `nix eval` or `nix build` may update `flake.lock` unless `--no-write-lock-file` is used. If this happens accidentally, revert unrelated lockfile churn and re-run focused verification with `--no-write-lock-file`.
