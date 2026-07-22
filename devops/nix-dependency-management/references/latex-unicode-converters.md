# LaTeX-to-Unicode converters on NixOS

Session context: user asked about optional Neovim/plugin dependencies for converting `latex` strings to Unicode: `libtexprintf`/`utftex` and `pylatexenc`/`latex2text`, then asked for alternatives.

## Verified package facts from the session

- `pylatexenc` is in nixpkgs as a Python package, verified via:
  - `nix eval --raw nixpkgs#python313Packages.pylatexenc.name`
  - observed result: `python3.13-pylatexenc-2.10`
- `libtexprintf` was not found in nixpkgs via `nix search nixpkgs libtexprintf --json`.
- A third-party flake exists: `github:SirSpunny/libtexprintf-flake`, exposing `packages.<system>.default` as `libtexprintf-1.31` at the time checked.
- `unicodeit` is in nixpkgs, verified via:
  - `nix eval --raw nixpkgs#unicodeit.name`
  - observed result: `unicodeit-0.7.5`
- `pandoc` is in nixpkgs but is usually heavier than needed for small LaTeX-string-to-Unicode conversion.

## Recommendation pattern

For optional plugin dependencies, prefer nixpkgs alternatives first:

```nix
home.packages = [
  pkgs.python3Packages.pylatexenc
  pkgs.unicodeit
];
```

Use `pylatexenc` first when the plugin supports `latex2text`; it is packaged and parser-oriented.
Use `unicodeit` as the lightweight alternative for math-symbol-style LaTeX tag conversion.
Only add `libtexprintf`/`utftex` if the plugin specifically needs it or if output quality is better enough to justify an external flake.

## External flake shape for libtexprintf

If needed:

```nix
# flake.nix inputs
libtexprintf.url = "github:SirSpunny/libtexprintf-flake";
```

If the repo already passes `inputs` into Home Manager via `extraSpecialArgs`, modules can refer to:

```nix
inputs.libtexprintf.packages.${pkgs.stdenv.hostPlatform.system}.default
```

Avoid hard-coding `x86_64-linux` unless the config is intentionally single-host.
