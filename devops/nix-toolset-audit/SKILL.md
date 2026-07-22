---
name: nix-toolset-audit
description: Use when auditing the user's Nix/Home Manager/dotfiles setup to recommend useful new developer tools, Neovim plugins, LSP/formatter/debugger packages, shell utilities, or AI/MCP utilities without immediately editing the config.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [nix, home-manager, dotfiles, neovim, developer-tools, cli-tools, recommendations]
    related_skills: [nix-dependency-management]
---

# Nix Toolset Audit

## Overview

Use this workflow to inspect a user's Nix/NixOS/nix-darwin/Home Manager dotfiles and recommend tool changes with an anti-bloat bias. The default output should be a minimal audit: identify config references that are broken/stale, recommend removing unused hooks before installing dependencies, and suggest additions only when they resolve clear current friction or an existing config expectation. The goal is not a generic "cool tools" dump.

This is especially useful for users with declarative dotfiles who ask for new Neovim plugins, CLI utilities, language tooling, AI-agent/MCP utilities, shell workflow improvements, or Nix-specific development tools — but the recommendation bar should stay high.

## When to Use

- User asks for "new good tools", "plugins for my setup", "what should I add to my Nix config", or similar.
- User wants recommendations based on their own dotfiles/toolset rather than general popularity.
- The repo contains `flake.nix`, `nix/*.nix`, Home Manager modules, Neovim config, shell/tmux/git config, or AI-agent config.

Do not use this as an implementation workflow unless the user explicitly asks to apply the changes. By default, audit and recommend only.

## Workflow

1. **Load Nix dependency guidance.**
   - Load the local `nix-dependency-management` skill when available; if ambiguous, prefer the dotfiles-local version when operating in `~/dotfiles`.
   - Completion criterion: package availability and flake-edit advice follows the user's Nix conventions.

2. **Discover the config surface.**
   - Find Nix files:
     ```text
     search_files(pattern="*.nix", target="files", path=".", limit=200)
     ```
   - Search for package and program declarations:
     ```text
     search_files(pattern="home\\.packages|environment\\.systemPackages|programs\\.|services\\.|inputs\\.", file_glob="*.nix", path=".", context=2, limit=150)
     ```
   - Read the important modules, usually `flake.nix`, `nix/home.nix`, `nix/development.nix`, `nix/ai.nix`, and host modules.
   - Completion criterion: you know the host systems, imported modules, current package sets, enabled programs/services, and any third-party flake inputs.

3. **Inventory editor and terminal config.**
   - List and read Neovim files:
     ```text
     search_files(pattern="*", target="files", path="nvim", limit=200)
     read_file(path="nvim/.config/nvim/lua/config/pack.lua")
     ```
   - Search plugin config for LSP, DAP, testing, picker, formatter, lint, notes, AI, and git integrations.
   - Read shell/tmux/git config if present: `.zshrc`, `.zsh_plugins.txt`, `tmux.conf`, git config, `.tool-versions`.
   - Completion criterion: every recommendation can be tied to a present workflow, a missing declared dependency, or a clear gap.

4. **Infer gaps from actual references.**
   Prioritize tools that the config already assumes or would immediately improve an existing workflow:
   - Shell config references `direnv` hook but Nix does not enable `programs.direnv` → recommend `programs.direnv` + `nix-direnv`.
   - Git config has Git LFS filters but no `git-lfs` package → recommend `pkgs.git-lfs`.
   - Neotest Go adapter uses `gotestsum` → recommend `pkgs.gotestsum`.
   - DAP configs exist → recommend `delve` for Go, JS debug adapters as needed, and language-specific debuggers.
   - LSP settings reference `vtsls`, `gopls`, `rust-analyzer`, or Nix LSPs → recommend declarative packages for those commands.
   - Neovim has `nvim-lint` or format-on-save but no dedicated formatter orchestration → recommend `conform.nvim` and formatter packages.
   - Picker-heavy setup with `snacks.nvim` → recommend tools that enhance search/replace and navigation (`grug-far.nvim`, `trouble.nvim`, `flash.nvim`/`mini.jump2d`).
   - Nix dotfiles repo lacks Nix lint/format/build helpers → recommend `nil`/`nixd`, `alejandra`, `deadnix`, `statix`, `nh`, `nix-output-monitor`, `nvd`.
   - Modern terminal basics missing → recommend `zoxide`, `eza`, `bat`, `jq`, `yq-go`, `just`, `watchexec`, `hyperfine`, `ast-grep`, `ripgrep-all`.
   - Completion criterion: gaps are evidence-backed, not trend-backed.

5. **Verify candidate package availability with Nix.**
   - For a single attr:
     ```bash
     nix eval --raw --no-write-lock-file nixpkgs#<attr>.name
     ```
   - For this user's multi-system flake, verify against each configured system when possible:
     ```bash
     nix eval --raw --no-write-lock-file .#nixosConfigurations.<host>.pkgs.<attr>.name
     nix eval --raw --no-write-lock-file .#darwinConfigurations.<host>.pkgs.<attr>.name
     ```
   - Batch candidates in a shell loop and record misses explicitly.
   - Completion criterion: every Nix package recommendation is known to evaluate for the relevant system(s), or the limitation is stated.

6. **Check Neovim plugin health/popularity only as supporting evidence.**
   - Use GitHub API or web search for plugin metadata such as stars, archived status, and recent `pushed_at`.
   - Do not over-index on stars; fit to the existing config matters more.
   - Good candidates for a modern Lua/`vim.pack` setup often include:
     - `stevearc/conform.nvim` — formatter orchestration.
     - `MagicDuck/grug-far.nvim` — project find/replace.
     - `folke/trouble.nvim` — diagnostics/references/quickfix UI.
     - `folke/flash.nvim` — fast navigation, unless `mini.jump2d` is preferred to avoid another plugin.
     - `rachartier/tiny-inline-diagnostic.nvim` — readable inline diagnostics.
     - `olimorris/codecompanion.nvim`, `ravitemer/mcphub.nvim`, or `coder/claudecode.nvim` — only when the user already has AI-agent/MCP workflows.
   - Completion criterion: plugin recommendations mention whether they overlap with existing plugins like Snacks or Mini.

7. **Return a prioritized recommendation, not a wall of packages.**
   Structure the answer as:
   - What was observed in the current config.
   - Minimal cleanup options first: remove stale hooks/config references when the user may not need the tool.
   - Only then list additions, ordered by clear value/risk, with a short justification tied to observed friction.
   - Concrete Nix/Home Manager placement hints for any additions.
   - Neovim plugin lines for `vim.pack.add` only when the plugin fills a real gap and does not overlap existing Mini/Snacks functionality.
   - A small "first patch" bundle the user can approve, ideally no more than 3-5 changes.
   - Completion criterion: the user can choose between "remove stale config" and "install the referenced tool" without further clarification.

## Candidate Buckets

### Nix/Home Manager essentials

```nix
programs.direnv = {
  enable = true;
  enableZshIntegration = true;
  nix-direnv.enable = true;
};
```

```nix
home.packages = [
  pkgs.git-lfs
  pkgs.nil
  pkgs.nixd
  pkgs.alejandra
  pkgs.deadnix
  pkgs.statix
  pkgs.nix-output-monitor
  pkgs.nh
  pkgs.nvd
];
```

### Language, LSP, formatter, debugger support

```nix
home.packages = [
  pkgs.vtsls
  pkgs.vue-language-server
  pkgs.gopls
  pkgs.rust-analyzer
  pkgs.lua-language-server
  pkgs.stylua
  pkgs.shfmt
  pkgs.shellcheck
  pkgs.marksman
  pkgs.taplo
  pkgs.yaml-language-server
  pkgs.biome
  pkgs.ruff
  pkgs.basedpyright
  pkgs.prettierd
  pkgs.eslint_d
  pkgs.gotestsum
  pkgs.delve
  pkgs.gofumpt
  pkgs.gotools
];
```

### Modern CLI utilities

```nix
home.packages = [
  pkgs.zoxide
  pkgs.eza
  pkgs.bat
  pkgs.jq
  pkgs.yq-go
  pkgs.just
  pkgs.watchexec
  pkgs.hyperfine
  pkgs.tokei
  pkgs.bottom
  pkgs.dust
  pkgs.duf
  pkgs.ast-grep
  pkgs.ripgrep-all
  pkgs.sd
  pkgs.xh
  pkgs.posting
  pkgs.lazydocker
];
```

Prefer Home Manager modules for shell-integrated tools when available:

```nix
programs.zoxide = {
  enable = true;
  enableZshIntegration = true;
};

programs.eza = {
  enable = true;
  enableZshIntegration = true;
};

programs.bat.enable = true;
```

### Neovim plugin candidates for `vim.pack.add`

```lua
'https://github.com/stevearc/conform.nvim',
'https://github.com/MagicDuck/grug-far.nvim',
'https://github.com/folke/trouble.nvim',
'https://github.com/folke/flash.nvim',
'https://github.com/rachartier/tiny-inline-diagnostic.nvim',
```

AI/MCP/editor-agent candidates, if they fit the user's workflow:

```lua
'https://github.com/olimorris/codecompanion.nvim',
'https://github.com/ravitemer/mcphub.nvim',
'https://github.com/coder/claudecode.nvim',
```

## Common Pitfalls

1. **Ambiguous “Linux/Nix version” questions.** When the user asks where a Linux version is defined in Nix files, distinguish the separate concepts before answering: `nixpkgs.hostPlatform` / `system` declares architecture-platform (for example `x86_64-linux`), `system.stateVersion` / `home.stateVersion` are compatibility baselines and not kernel or release pins, the flake input URL and `flake.lock` pin the nixpkgs revision/release channel, and the actual kernel version is usually derived from `config.boot.kernelPackages.kernel.version` unless `boot.kernelPackages` is overridden. Search for `boot.kernelPackages`, `linuxPackages`, `kernel`, and state version options, then verify with `nix eval --raw --no-write-lock-file .#nixosConfigurations.<host>.config.boot.kernelPackages.kernel.version` when a host output exists.

2. **Shell prompt/shell alternatives should be config-fit comparisons, not generic recommendations.** When comparing Powerlevel10k, Starship, Fish, Pure, or Oh My Posh in the user's dotfiles, inspect the actual shell modules and dotfiles first. Tie the recommendation to observed config: plugin manager use, generated prompt config size, prompt features in use, shell integrations (`fzf`, `direnv`, `mise`), vi-mode needs, and cross-shell portability. Prefer “trial alongside existing shell” for Fish or major shell changes; avoid immediately changing the login shell until interactive config is proven.

3. **Recommending packages without checking the user's flake systems.** Always verify with `nix eval`, ideally through each flake output's `pkgs` so overlays/platforms are respected.

2. **Missing tools already referenced by config.** Search for command strings in shell, git, Neovim, DAP, and test configs; these are often the highest-value additions.

3. **Confusing Neovim plugin dependencies with CLI dependencies.** A plugin may install itself through `vim.pack`, while formatters, language servers, debug adapters, and test runners often still need commands on `PATH`.

4. **Adding both overlapping Neovim plugins and Mini/Snacks equivalents.** If the user already uses `mini.nvim` or `snacks.nvim`, call out overlap and recommend the least redundant option.

5. **Using `home.packages` for tools with Home Manager modules.** For shell-integrated tools like `direnv`, `zoxide`, `eza`, and `bat`, prefer Home Manager modules when they provide integration and config.

6. **Presenting a giant undifferentiated package list.** Always include a highest-value subset and a low-risk first patch.

7. **Treating web popularity as proof.** GitHub stars and recent pushes are supporting evidence only; fit to the user's config is primary.

8. **PipeWire/WirePlumber HDMI “mute” can be output-profile state, not the channel-swap rule.** When auditing NixOS audio config with `services.pipewire.wireplumber.extraConfig` and broad `monitor.alsa.rules`, verify live PipeWire state before blaming `audio.position`. For normal stereo L/R swap, `[ "FR" "FL" ]` is valid. If sound is apparently muted while `wpctl get-volume @DEFAULT_AUDIO_SINK@` says unmuted, compare the live sink/profile from `wpctl status`/`wpctl inspect @DEFAULT_AUDIO_SINK@` with persisted defaults in `~/.local/state/wireplumber/default-nodes` and `default-profile`; GPU HDMI/DP outputs can flip between `hdmi-stereo`, `hdmi-stereo-extra1`, and `hdmi-stereo-extra2`. See `references/pipewire-wireplumber-hdmi-output-state.md` for the command pattern and remediation options.

## Verification Checklist

- [ ] Relevant Nix dependency skill loaded.
- [ ] `flake.nix` and imported Nix modules read.
- [ ] Home Manager packages/programs and host system packages inventoried.
- [ ] Neovim `pack.lua`/lock/config files read.
- [ ] Shell, tmux, git, and tool-version files checked when present.
- [ ] Missing-but-referenced commands identified.
- [ ] Candidate package attrs evaluated against the relevant flake systems.
- [ ] Neovim plugins checked for activity/archive status when recommending new external plugins.
- [ ] Recommendations are prioritized and tied to observed evidence.
- [ ] First-patch bundle is small enough for the user to approve directly.
