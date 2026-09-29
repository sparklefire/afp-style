#!/usr/bin/env python3
"""Insert generated AFP-style illustrations into a copy of a Markdown article."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote


def _paragraph_bounds(lines: list[str], index: int) -> tuple[int, int]:
    line = lines[index].lstrip()
    fence = None
    for prior in lines[: index + 1]:
        marker = re.match(r"^\s*(`{3,}|~{3,})", prior)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
    if fence is not None:
        raise ValueError("Anchors inside fenced code blocks are unsupported; use a heading or paragraph.")
    if line.startswith("#"):
        return index, index + 1
    if line.startswith(("- ", "* ", "+ ", ">", "|", "```", "~~~")) or re.match(r"\d+[.)] ", line):
        raise ValueError("Anchors in lists, tables, quotes, and code blocks are unsupported; use a heading or paragraph.")

    start = index
    while start > 0 and lines[start - 1].strip() and not lines[start - 1].lstrip().startswith("#"):
        start -= 1
    end = index + 1
    while end < len(lines) and lines[end].strip() and not lines[end].lstrip().startswith("#"):
        end += 1
    return start, end


def _clean(value: object, field: str) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    if not text:
        raise ValueError(f"Each manifest item needs a non-empty {field}.")
    return text


def insert_illustrations(article: str, manifest: list[dict]) -> str:
    """Return a new article with images inserted at unique heading/paragraph anchors."""
    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a JSON array.")
    lines = article.splitlines(keepends=True)
    insertions: dict[int, list[str]] = defaultdict(list)

    for number, item in enumerate(manifest, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Manifest item {number} must be an object.")
        anchor = _clean(item.get("anchor"), "anchor")
        image_path = _clean(item.get("image_path"), "image_path").replace("\\", "/")
        position = str(item.get("position", "after")).lower()
        if position not in {"before", "after"}:
            raise ValueError(f"Manifest item {number}: position must be 'before' or 'after'.")

        matches = [i for i, line in enumerate(lines) if anchor in line]
        if len(matches) != 1:
            reason = "not found" if not matches else "ambiguous"
            raise ValueError(f"Anchor {anchor!r} is {reason}; use text that occurs on exactly one line.")
        start, end = _paragraph_bounds(lines, matches[0])
        insertion_at = start if position == "before" else end

        alt = _clean(item.get("alt") or item.get("caption") or f"AFP 风格配图 {number}", "alt")
        caption = str(item.get("caption") or "").replace("\r", " ").replace("\n", " ").strip()
        disclosure = str(item.get("disclosure") or "AI 生成示意图").replace("\r", " ").replace("\n", " ").strip()
        image_url = quote(image_path, safe="/:._~-")
        block = f"![{alt}]({image_url})\n"
        label = " · ".join(part for part in (disclosure, caption) if part)
        if label:
            block += f"*{label}*\n"
        insertions[insertion_at].append((position, block))

    output: list[str] = []
    for index in range(len(lines) + 1):
        if index in insertions:
            for position, block in insertions[index]:
                output.append(("\n" if position == "after" and output and output[-1].strip() else "") + block)
                if position == "before":
                    output.append("\n")
        if index < len(lines):
            output.append(lines[index])
    return "".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", required=True, type=Path, help="Source Markdown article")
    parser.add_argument("--manifest", required=True, type=Path, help="JSON array describing images and anchors")
    parser.add_argument("--output", type=Path, help="Output Markdown path (default: <stem>_afp_illustrated.md)")
    parser.add_argument("--force", action="store_true", help="Replace an existing output file")
    args = parser.parse_args()

    try:
        article_path = args.article.resolve(strict=True)
        manifest_path = args.manifest.resolve(strict=True)
        output_path = args.output.resolve() if args.output else article_path.with_name(f"{article_path.stem}_afp_illustrated{article_path.suffix}")
        if output_path == article_path:
            raise ValueError("Output path must not overwrite the source article.")
        if output_path.exists() and not args.force:
            raise ValueError(f"Output already exists: {output_path} (pass --force to replace it).")
        article = article_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        result = insert_illustrations(article, manifest)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote illustrated article: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
