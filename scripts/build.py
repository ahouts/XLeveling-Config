#!/usr/bin/env python3
"""Build strict JSON config files from root-level JSONC sources."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def strip_comments(text: str) -> str:
    output: list[str] = []
    i = 0
    in_string = False
    escape = False

    while i < len(text):
        char = text[i]
        next_char = text[i + 1] if i + 1 < len(text) else ""

        if in_string:
            output.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            i += 1
            continue

        if char == "/" and next_char == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue

        if char == "/" and next_char == "*":
            i += 2
            closed = False
            while i < len(text):
                if text[i] == "*" and i + 1 < len(text) and text[i + 1] == "/":
                    i += 2
                    closed = True
                    break
                if text[i] in "\r\n":
                    output.append(text[i])
                i += 1
            if not closed:
                raise ValueError("unterminated block comment")
            continue

        output.append(char)
        i += 1

    return "".join(output)


def remove_trailing_commas(text: str) -> str:
    output: list[str] = []
    i = 0
    in_string = False
    escape = False

    while i < len(text):
        char = text[i]

        if in_string:
            output.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            i += 1
            continue

        if char == ",":
            j = i + 1
            while j < len(text) and text[j] in " \t\r\n":
                j += 1
            if j < len(text) and text[j] in "}]":
                i += 1
                continue

        output.append(char)
        i += 1

    return "".join(output)


def convert_jsonc(text: str) -> str:
    return remove_trailing_commas(strip_comments(text))


def context_for_error(text: str, line: int, column: int) -> str:
    lines = text.splitlines()
    if not 1 <= line <= len(lines):
        return ""
    source_line = lines[line - 1]
    pointer = " " * (max(column, 1) - 1) + "^"
    return f"\n{source_line}\n{pointer}"


def build_file(source: Path) -> Path:
    try:
        converted = convert_jsonc(source.read_text(encoding="utf-8"))
        json.loads(converted)
    except json.JSONDecodeError as error:
        context = context_for_error(converted, error.lineno, error.colno)
        raise RuntimeError(f"{source.name}:{error.lineno}:{error.colno}: {error.msg}{context}") from error
    except ValueError as error:
        raise RuntimeError(f"{source.name}: {error}") from error

    target = DIST / f"{source.stem}.json"
    target.write_text(converted, encoding="utf-8")
    return target


def main() -> int:
    sources = sorted(ROOT.glob("*.jsonc"))
    if not sources:
        print("No root-level .jsonc files found.", file=sys.stderr)
        return 1

    DIST.mkdir(exist_ok=True)
    for old_output in DIST.glob("*.json"):
        old_output.unlink()

    try:
        outputs = [build_file(source) for source in sources]
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    for output in outputs:
        print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
