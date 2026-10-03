# Agent configuration

This flake exports a Home Manager module that links the repository to
`~/.agents`. It has no external flake inputs.

## Home Manager integration

Add the repository as a flake input:

```nix
inputs.agents.url = "github:rhermens/.agents";
```

Then import its module in your Home Manager configuration:

```nix
{ inputs, ... }:
{
  imports = [ inputs.agents.homeManagerModules.default ];
}
```

This works for standalone Home Manager or Home Manager imported through NixOS.

The module links the entire flake source to `~/.agents`, so the skills are
available at `~/.agents/skills`. Move or back up any existing `~/.agents`
directory before activating this module; Home Manager needs to replace that
path with its managed symlink.
