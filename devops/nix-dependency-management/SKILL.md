---
name: nix-dependency-management
description: Resolve, compare, and add Nix/NixOS/Home Manager package dependencies, including optional tool dependencies and third-party flakes.
---

# Nix dependency management

Use this skill when the user asks whether a dependency is available on NixOS/Nix, how to install optional dependencies declaratively, whether to use an alternative package, or whether to add an external flake.

## Workflow

1. Identify the dependency shape.
   - Is it a CLI binary, Python module, library, language-server, plugin dependency, or system service?
   - Determine whether the caller needs the command on `PATH`, a Python import, a shared library, or a build input.

2. Check the user's config before recommending edits.
   - Locate `flake.nix`, Home Manager modules, and relevant `home.packages` / `environment.systemPackages` declarations.
   - In this user's dotfiles, Nix config is typically under `~/dotfiles`, with Home Manager modules under `nix/`.

3. Verify package availability with Nix, not memory.
   - Prefer direct eval when the attribute is plausible:
     - `nix eval --raw nixpkgs#<attr>.name`
     - `nix eval --raw nixpkgs#python3Packages.<module>.name`
     - `nix eval --raw nixpkgs#python313Packages.<module>.name`
   - Use `nix search nixpkgs <query> --json` for broader discovery.
   - For current upstream facts or popularity, use web/GitHub search as supporting evidence only.

4. Prefer nixpkgs packages before external flakes.
   - If a suitable package exists in nixpkgs, recommend that first.
   - If only an external flake exists, explain the trade-off: extra input/lock churn and trust surface versus exact tool support.
   - For optional dependencies, recommend the packaged alternative first unless the feature demonstrably requires the un-packaged tool.

5. Give concrete Home Manager/NixOS snippets.
   - For user-level tools: `home.packages = [ pkgs.<pkg> ];`
   - For host/system tools: `environment.systemPackages = with pkgs; [ <pkg> ];`
   - For flake inputs already passed via `extraSpecialArgs = { inherit inputs; };`, use `inputs.<name>.packages.${pkgs.stdenv.hostPlatform.system}.default` from Home Manager modules.
- When a third-party flake drops its overlay output, remove `nixpkgs.overlays = [ inputs.<name>.overlays.default ];` and replace `pkgs.<namespace>.<pkg>` references with a local package-set binding such as:
  ```nix
  let
    upstreamPkgs = inputs.<name>.packages.${pkgs.stdenv.hostPlatform.system};
  in
  upstreamPkgs.<pkg>
  ```
  Verify package attrs exist with `nix flake show <flake> --json` or `nix eval` before editing call sites.
- When one package breaks on current nixpkgs but the rest of the system should stay current, pin only that package through a dedicated old-nixpkgs input and a tiny overlay. Preserve `config = prev.config;` when importing the pinned nixpkgs so unfree/package config carries over. See `references/pin-single-package-from-old-nixpkgs.md`.

6. For "what tools/plugins should I add?" audits, inspect the actual toolchain before recommending.
   - Read the user's Nix/Home Manager package declarations, imported modules, symlinked config directories, and relevant app configs such as Neovim `vim.pack.add`, tmux, zsh, git, and `.tool-versions`/mise files.
   - Identify tools the config already expects but Nix does not provide declaratively (for example shell hooks in `.zshrc`, Git LFS filters in git config, Neovim test/debug runners, LSP server commands, formatter/linter binaries). Prioritize these as "missing support for existing workflow" above generic trendy tools.
   - For Neovim plugin recommendations, compare against the existing plugin set and choose complementary class-level additions (formatting orchestration, diagnostics UI, project-wide replace, motion, AI/MCP integration) rather than duplicating capabilities already covered by Snacks, mini.nvim, oil, etc.
   - Verify every proposed nixpkgs attribute against the user's flake systems, not just `nixpkgs#...`, when cross-platform config is present. Example:
     ```bash
     nix eval --raw --no-write-lock-file .#nixosConfigurations.<host>.pkgs.<attr>.name
     nix eval --raw --no-write-lock-file .#darwinConfigurations.<host>.pkgs.<attr>.name
     ```
   - When recommending shell integrations, prefer Home Manager modules where they exist (`programs.direnv`, `programs.zoxide`, `programs.eza`, `programs.bat`) instead of only adding packages to `home.packages`.

7. Verify when making edits.
   - After editing, run the relevant `nix flake check`, `home-manager switch --flake ...`, or `nixos-rebuild dry-build/switch --flake ...` command only when scope is clear and side effects are acceptable.
   - If canonical verification is not obvious or external tooling requests it, create a focused temporary `hermes-verify-*` script with OS temp-directory APIs (`tempfile.mkstemp`/`mktemp`) rather than hand-writing into system temp paths. Run it against the changed Nix behavior, remove it when possible, and report it explicitly as ad-hoc verification rather than full suite green. For cross-platform guards, a concise probe can import the edited module twice with Linux and Darwin `system` values and assert the guarded attr is absent/present as intended.
   - For local flake eval/build probes, prefer `--no-write-lock-file` unless the requested task is to update the lockfile; this prevents verification from adding incidental `flake.lock` churn.
   - For Home Manager symlink-collision fixes, verify both declaration and behavior: the file entry has the intended `source`/`force` settings, the live target is a symlink to the canonical dotfiles path, the referenced file parses, and any relevant app writer preserves the symlink.

## Pitfalls

- In NixOS/nix-darwin modules, avoid wrapping the whole returned module in `lib.optionalAttrs pkgs.stdenv.isDarwin ...` (or otherwise forcing `pkgs` while the module is being imported). Under the module system this can recurse through `_module.args.pkgs`. Prefer returning a normal attrset and putting `lib.mkIf pkgs.stdenv.isDarwin` on the specific option value, e.g. `homebrew = lib.mkIf pkgs.stdenv.isDarwin { ...; };`.
- For Powerlevel10k instant prompt under Home Manager, setting `POWERLEVEL9K_INSTANT_PROMPT=verbose` in the p10k config is not enough; the instant-prompt cache source block must appear at the very top of the generated `.zshrc`. Use `programs.zsh.initContent = lib.mkBefore '' ... '';` rather than deprecated `initExtraFirst`, and escape Zsh parameter expansion in Nix strings as `''${...}` (for example `''${XDG_CACHE_HOME:-$HOME/.cache}` and `''${(%):-%n}`). Keep the block before plugin sourcing/completion because Home Manager sources `programs.zsh.plugins` later in `initContent`.
- For Home Manager-managed dotfile symlinks that an app may replace with a real file (for example config writers that use atomic replace), use the attrset form with `force = true;` so activation restores the symlink instead of failing with a clobbering/collision error:
  ```nix
  home.file.".app/config.yaml" = {
    source = config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/dotfiles/app/config.yaml";
    force = true;
  };
  ```
  Only apply this when the source file is the desired canonical copy; preserve or compare any existing real file before replacing it.
- Do not conclude a package is unavailable from web search alone; check `nix search` and plausible attr paths.
- Do not add third-party flakes for optional niceties before checking packaged alternatives.
- Do not hard-code architecture-specific flake package paths when `${pkgs.stdenv.hostPlatform.system}` is available.
- Distinguish Python package availability from CLI availability; a Python module in `home.packages` may not provide the command the user expects.
- For macOS `.app` bundles created with Nix/Home Manager, a PNG in `Contents/Resources` is not enough for Finder/Dock icons. Generate an `.icns`, place it in `Contents/Resources`, and add `CFBundleIconFile` to `Info.plist`.
- For GApps-wrapped packages, do not manually call `wrapGAppsHook` as if it accepted a target binary or output name; it is a fixup hook that expects the stdenv `output` variable. To wrap one explicit binary in an override, replace the call with `wrapGApp <program>`. See `references/mongodb-compass-wrapgapp.md`.
- If a tool invocation is blocked by user confirmation or policy, stop and report the partial verification rather than retrying through another route.

## References

- `references/latex-unicode-converters.md`: notes on LaTeX-to-Unicode converter options for NixOS/Home Manager.
- `references/pin-single-package-from-old-nixpkgs.md`: overlay pattern for pinning one broken package to an older nixpkgs revision while keeping the rest of the system current.
- `references/macos-app-bundle-icons.md`: recipe for wiring macOS `.app` icons from Nix/Home Manager using `libicns` and `CFBundleIconFile`.
- `references/mongodb-compass-wrapgapp.md`: fix for `mongodb-compass` manual GApps wrapping failures; use `wrapGApp` rather than calling `wrapGAppsHook` directly, plus focused verification notes.
