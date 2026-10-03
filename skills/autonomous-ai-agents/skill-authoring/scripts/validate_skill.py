#!/usr/bin/env python3
"""Validate a portable Agent Skill using only the Python standard library."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_LINK_RE = re.compile(r"\]\(((?:scripts|references|assets)/[^) #]+)")
ABSOLUTE_PATH_RE = re.compile(r"(?<![\w.-])(?:/home/[^/\s]+|/Users/[^/\s]+)/(?:[^\s`'\"<>]+)")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value


def frontmatter_value(lines: list[str], key: str) -> str | None:
    prefix = f"{key}:"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        raw = line[len(prefix) :].strip()
        if raw not in {"|", ">", "|-", ">-", "|+", ">+"}:
            return unquote(raw)
        block: list[str] = []
        for following in lines[index + 1 :]:
            if following.startswith((" ", "\t")) or not following.strip():
                block.append(following.strip())
            else:
                break
        separator = " " if raw.startswith(">") else "\n"
        return separator.join(block).strip()
    return None


def validate(skill_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    skill_dir = skill_path if skill_path.is_dir() else skill_path.parent
    skill_file = skill_dir / "SKILL.md" if skill_path.is_dir() else skill_path

    if not skill_file.is_file():
        return [f"Missing SKILL.md: {skill_file}"], warnings

    try:
        content = skill_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["SKILL.md must be valid UTF-8"], warnings

    if content.startswith("\ufeff"):
        errors.append("SKILL.md must not start with a UTF-8 BOM")
    if not content.startswith("---\n"):
        errors.append("SKILL.md must start with '---' at byte zero")
        return errors, warnings

    closing = content.find("\n---\n", 4)
    if closing < 0:
        errors.append("YAML frontmatter must end with a line containing only '---'")
        return errors, warnings

    frontmatter = content[4:closing].splitlines()
    body = content[closing + 5 :]
    name = frontmatter_value(frontmatter, "name")
    description = frontmatter_value(frontmatter, "description")
    compatibility = frontmatter_value(frontmatter, "compatibility")

    if not name:
        errors.append("Frontmatter requires a non-empty name")
    else:
        if len(name) > 64:
            errors.append("name exceeds 64 characters")
        if not NAME_RE.fullmatch(name):
            errors.append("name must contain lowercase letters, digits, and single hyphens only")
        if skill_dir.name != name:
            errors.append(f"Directory '{skill_dir.name}' must match name '{name}'")

    if not description:
        errors.append("Frontmatter requires a non-empty description")
    elif len(description) > 1024:
        errors.append("description exceeds 1024 characters")

    if compatibility and len(compatibility) > 500:
        errors.append("compatibility exceeds 500 characters")

    if not body.strip():
        errors.append("SKILL.md requires a non-empty Markdown body")

    for relative in sorted(set(LOCAL_LINK_RE.findall(body))):
        if not (skill_dir / relative).exists():
            errors.append(f"Referenced file does not exist: {relative}")

    for match in sorted(set(ABSOLUTE_PATH_RE.findall(content))):
        warnings.append(f"Machine-specific absolute path: {match}")

    if len(content) > 100_000:
        warnings.append("SKILL.md exceeds 100,000 characters; split detail into references/")
    elif len(content) > 20_000:
        warnings.append("SKILL.md exceeds 20,000 characters; consider progressive disclosure")

    if not re.search(r"^##?\s+.*(?:workflow|instructions|usage|procedure)", body, re.I | re.M):
        warnings.append("No workflow, instructions, usage, or procedure heading found")
    if not re.search(r"(?:validate|verification|checklist|test)", body, re.I):
        warnings.append("No explicit validation or verification guidance found")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path, help="Skill directory or SKILL.md path")
    args = parser.parse_args()

    errors, warnings = validate(args.skill.expanduser().resolve())
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"PASS: 0 errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
