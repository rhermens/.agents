---
name: agent-skills-portability
description: "Organize and share Agent Skills across Hermes, Claude Code, Pi, Codex, and dotfiles-managed setups."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, dotfiles, claude-code, pi, portability, agent-skills]
    related_skills: [hermes-agent-skill-authoring, hermes-agent, claude-code, codex]
---

# Agent Skills Portability

## Overview

Use this skill when the user wants to keep one reusable skill library that works across multiple agent harnesses such as Hermes, Claude Code, Pi, Codex, and other Agent Skills-compatible tools.

The default strategy is: **one categorized dotfiles source of truth, then per-agent compatibility views**. Do not duplicate skill bodies per tool unless there is no symlink/configuration path available.

## When to Use

- User asks where to store skills in `~/dotfiles` or another synced repo.
- User asks whether categorized skill folders are compatible across agents.
- User wants the same `SKILL.md` skills available in Hermes, Claude Code, Pi, Codex, or similar tools.
- User is migrating skills from `~/.hermes/skills`, `~/.claude/skills`, `.claude/skills`, `~/.codex/skills`, or `.agents/skills` into a shared library.

Don't use for:

- Writing a single new skill's instructions; use `hermes-agent-skill-authoring` if the task is about SKILL.md content quality.
- Debugging a specific agent CLI install or auth problem.

## Recommended Source Layout

Keep the git-tracked source under dotfiles and categorize for humans:

```text
~/dotfiles/agent-skills/
  software-development/
    test-driven-development/
      SKILL.md
      references/
      templates/
      scripts/
      assets/
  research/
    arxiv/
      SKILL.md
  productivity/
    obsidian/
      SKILL.md
```

Rules:

1. Each actual skill is a directory containing `SKILL.md`.
2. The folder basename should match the frontmatter `name`.
3. Supporting files stay inside the same skill directory under `references/`, `templates/`, `scripts/`, or `assets/`.
4. Category names are organizational only; do not rely on them as part of the invocation name.

Good frontmatter baseline:

```yaml
---
name: test-driven-development
description: Use TDD red-green-refactor for coding tasks.
---
```

## Hermes Setup

Hermes recursively discovers `SKILL.md` files under the main skills dir and configured external skill directories. Prefer adding the dotfiles root to config:

```yaml
skills:
  external_dirs:
    - ~/dotfiles/agent-skills
```

This keeps Hermes' local skill directory for agent-created or installed skills while treating dotfiles skills as externally owned.

Fallback when config is not available: create symlinks from `~/.hermes/skills/<skill-name>` to each source skill directory. Prefer config over symlinks because it preserves category organization without maintaining many links.

## Pi Setup

Pi documents recursive discovery of directories containing `SKILL.md` in skill locations. Add the dotfiles skill root to Pi's settings:

```json
{
  "skills": ["~/dotfiles/agent-skills"]
}
```

Pi can also read skills from Claude Code or Codex skill directories by listing those directories, but prefer pointing Pi at the shared source root instead of chaining one agent's runtime directory through another.

## Claude Code Setup

Claude Code supports skills under `~/.claude/skills/<skill-name>/SKILL.md` for personal skills and `.claude/skills/` for project skills. Project discovery includes parent and nested `.claude/skills/` locations, but arbitrary categorized personal-skill roots can be version- and setup-sensitive.

Safest compatibility view: keep dotfiles categorized, then expose a flat symlink tree for Claude Code:

```bash
mkdir -p ~/.claude/skills
ln -s ~/dotfiles/agent-skills/software-development/test-driven-development ~/.claude/skills/test-driven-development
ln -s ~/dotfiles/agent-skills/research/arxiv ~/.claude/skills/arxiv
```

This preserves `/skill-name` command names and avoids depending on whether Claude Code recursively scans nonstandard personal category directories.

## Portability Checklist

- [ ] One canonical copy of each skill lives in dotfiles or another source repo.
- [ ] The skill is self-contained: `SKILL.md` plus local support directories.
- [ ] `name:` matches the folder basename and is stable across tools.
- [ ] Agent-specific metadata is optional; the main markdown remains useful if ignored.
- [ ] Hermes points at the shared root via `skills.external_dirs` or symlinks.
- [ ] Pi points at the shared root through its `skills` settings array.
- [ ] Claude Code has either direct supported discovery or a flat `~/.claude/skills/<name>` symlink view.
- [ ] No duplicated per-agent copies that can drift.

## Common Pitfalls

1. **Making category depth part of the contract.** Some harnesses recursively discover `SKILL.md`; others expect flat `~/.tool/skills/<name>/SKILL.md` views. Categories are for source organization, not invocation semantics.

2. **Duplicating skills into every agent directory.** Copies drift. Use external-dir settings or symlinks.

3. **Omitting `name:` because one harness derives it from the folder.** Different tools may prefer frontmatter or parent directory. Include `name:` and keep it aligned.

4. **Encoding Hermes-only behavior as mandatory.** `metadata.hermes` is useful for Hermes, but cross-agent skills should still function when another harness ignores that metadata.

5. **Flattening the source tree to satisfy one agent.** Keep the source ergonomic and categorized; build a flat compatibility view for agents that need it.

## Verification

After changing layout, verify each target agent can list or invoke one known skill:

- Hermes: start a fresh session or run the relevant skill listing command, then load/invoke the skill.
- Pi: start Pi after settings changes and invoke `/skill-name` or ask for a task matching the description.
- Claude Code: start a new Claude Code session and invoke `/skill-name` from the flat symlink view.

If one agent fails to discover the categorized source directly, do not conclude the skill format is incompatible. Add or repair that agent's compatibility view first.
