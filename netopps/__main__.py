"""Command-line entry point for python -m netopps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from netopps.planner import allocate_subnets
from netopps.validator import validate_inventory

_MAX_INPUT_BYTES = 5 * 1024 * 1024
_MAX_JSON_DEPTH = 100


class DuplicateJSONKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


class JSONNestingLimitError(ValueError):
    """Raised when JSON nesting exceeds the supported safety limit."""


def _check_json_nesting(text: str) -> None:
    """Bound structural nesting without counting braces inside JSON strings."""
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == chr(92):
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > _MAX_JSON_DEPTH:
                raise JSONNestingLimitError(
                    f"JSON nesting exceeds the {_MAX_JSON_DEPTH}-level safety limit"
                )
        elif character in "]}":
            depth -= 1


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKeyError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _read_inventory(path: Path) -> tuple[Any | None, int]:
    try:
        with path.open("rb") as handle:
            raw = handle.read(_MAX_INPUT_BYTES + 1)
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return None, 2

    if len(raw) > _MAX_INPUT_BYTES:
        print(f"error: input exceeds the {_MAX_INPUT_BYTES}-byte safety limit", file=sys.stderr)
        return None, 2

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"error: input must be UTF-8 text (byte offset {exc.start})", file=sys.stderr)
        return None, 2

    try:
        _check_json_nesting(text)
        return json.loads(text, object_pairs_hook=_unique_object), 0
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return None, 2
    except (DuplicateJSONKeyError, JSONNestingLimitError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return None, 2
    except RecursionError:
        print("error: JSON nesting exceeds parser safety limits", file=sys.stderr)
        return None, 2


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="netopps",
        description="Validate local network inventory and create read-only subnet plans.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate inventory and network ranges")
    validate_parser.add_argument("file", type=Path, help="path to inventory JSON file")

    plan_parser = subparsers.add_parser("plan-subnets", help="plan free subnets without changing infrastructure")
    plan_parser.add_argument("file", type=Path, help="path to a valid inventory JSON file")
    plan_parser.add_argument("--pool", required=True, help="parent CIDR pool, for example 10.20.0.0/16")
    plan_parser.add_argument("--prefix", required=True, type=int, help="desired subnet prefix, for example 24")
    plan_parser.add_argument("--count", required=True, type=int, help="number of subnets to plan (1-256)")
    args = parser.parse_args()

    inventory, read_status = _read_inventory(args.file)
    if read_status:
        return read_status

    findings = validate_inventory(inventory)
    if findings:
        print(json.dumps({"valid": False, "finding_count": len(findings), "findings": findings}, indent=2))
        return 1

    if args.command == "validate":
        print(json.dumps({"valid": True, "finding_count": 0, "findings": []}, indent=2))
        return 0

    try:
        allocated = allocate_subnets(inventory, args.pool, args.prefix, args.count)
    except (ValueError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc), "allocated": []}, indent=2))
        return 2

    complete = len(allocated) == args.count
    print(json.dumps({
        "valid": complete,
        "mode": "plan-only",
        "pool": args.pool,
        "prefix": args.prefix,
        "requested": args.count,
        "allocated_count": len(allocated),
        "allocated": allocated,
        "complete": complete,
        "applied": False,
    }, indent=2))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
