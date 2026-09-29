#!/usr/bin/env python3
"""Check the AFP skill package metadata and local Markdown references."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def quoted_field(text: str, field: str) -> str | None:
    match = re.search(rf'^\s+{re.escape(field)}:\s*"([^"]*)"\s*$', text, re.MULTILINE)
    return match.group(1) if match else None


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        return ["Missing SKILL.md."]

    skill = skill_path.read_text(encoding="utf-8")
    if not skill.startswith("---\n") or "\n---\n" not in skill[4:]:
        errors.append("SKILL.md needs YAML frontmatter delimited by ---.")
    else:
        frontmatter = skill.split("---", 2)[1]
        name = re.search(r"^name:\s*([\w-]+)\s*$", frontmatter, re.MULTILINE)
        description = re.search(r"^description:\s*.+$", frontmatter, re.MULTILINE)
        if not name or name.group(1) != root.name:
            errors.append(f"Skill name must match package directory ({root.name}).")
        if not description:
            errors.append("SKILL.md frontmatter needs a description.")

    agent_path = root / "agents/openai.yaml"
    if not agent_path.is_file():
        errors.append("Missing agents/openai.yaml.")
    else:
        agent = agent_path.read_text(encoding="utf-8")
        for field in ("display_name", "short_description", "default_prompt"):
            if quoted_field(agent, field) is None:
                errors.append(f"agents/openai.yaml needs a quoted interface.{field}.")
        short = quoted_field(agent, "short_description")
        if short is not None and not 25 <= len(short) <= 64:
            errors.append("short_description must be 25–64 characters.")
        prompt = quoted_field(agent, "default_prompt") or ""
        if "$afp-style" not in prompt:
            errors.append("default_prompt must invoke $afp-style.")

    documents = [skill_path, *sorted(root.glob("README.md")), *sorted((root / "examples").rglob("*.md")), *sorted((root / "references").rglob("*.md"))]
    checked_links = 0
    for document in documents:
        if not document.is_file():
            continue
        in_fence = False
        for line_number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), start=1):
            if re.match(r"^\s*(```|~~~)", line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for raw_target in LINK.findall(line):
                target = raw_target.strip().strip("<>").split("#", 1)[0]
                if not target or target.startswith(("http:", "https:", "mailto:")):
                    continue
                checked_links += 1
                path = (document.parent / unquote(target)).resolve()
                if not path.exists():
                    errors.append(f"{document.relative_to(root)}:{line_number}: missing link target {target!r}.")

    if not errors:
        print(f"Package valid: metadata and {checked_links} local Markdown links checked.")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Package validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
