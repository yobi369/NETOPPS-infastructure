"""Command-line entry point for python -m netopps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from netopps.validator import validate_inventory

_MAX_INPUT_BYTES = 5 * 1024 * 1024


class DuplicateJSONKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKeyError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="netopps",
        description="Validate a local JSON network inventory without contacting devices.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate inventory and network ranges")
    validate_parser.add_argument("file", type=Path, help="path to inventory JSON file")
    args = parser.parse_args()

    try:
        raw = args.file.read_bytes()
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2

    if len(raw) > _MAX_INPUT_BYTES:
        print(f"error: input exceeds the {_MAX_INPUT_BYTES}-byte safety limit", file=sys.stderr)
        return 2

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"error: input must be UTF-8 text (byte offset {exc.start})", file=sys.stderr)
        return 2

    try:
        inventory = json.loads(text, object_pairs_hook=_unique_object)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    except DuplicateJSONKeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    findings = validate_inventory(inventory)
    print(json.dumps({"valid": not findings, "finding_count": len(findings), "findings": findings}, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
