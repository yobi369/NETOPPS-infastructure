"""Command-line entry point for python -m netopps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from netopps.validator import validate_inventory


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
        inventory = json.loads(args.file.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2

    findings = validate_inventory(inventory)
    print(json.dumps({"valid": not findings, "finding_count": len(findings), "findings": findings}, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
