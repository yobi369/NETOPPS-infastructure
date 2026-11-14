"""Command-line entry point for python -m netopps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from netopps.health import check_connectivity
from netopps.planner import allocate_subnets
from netopps.topology import NetworkTopology, TopologyError
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

    health_parser = subparsers.add_parser(
        "check-connectivity",
        help="check TCP reachability only for explicitly listed management endpoints",
    )
    health_parser.add_argument("file", type=Path, help="path to a valid inventory JSON file")
    health_parser.add_argument("--allow-network", action="store_true", help="explicitly permit TCP connection attempts")
    health_parser.add_argument("--limit", type=int, default=20, help="maximum devices to check (1-100; default 20)")
    health_parser.add_argument("--timeout", type=float, default=1.0, help="per-connection timeout in seconds (0.1-3.0)")

    topology_parser = subparsers.add_parser(
        "topology-report", help="analyze an operator-supplied topology without network access"
    )
    topology_parser.add_argument("file", type=Path, help="path to a topology JSON file")
    topology_parser.add_argument("--disable-node", action="append", default=[], help="simulate a failed node (repeatable)")
    topology_parser.add_argument("--disable-link", action="append", default=[], help="simulate a failed link (repeatable)")
    topology_parser.add_argument("--path-from", help="optional source node for lowest-latency path analysis")
    topology_parser.add_argument("--path-to", help="optional target node for lowest-latency path analysis")
    topology_parser.add_argument("--traffic-file", type=Path, help="optional versioned JSON traffic-demand scenario")

    diff_parser = subparsers.add_parser(
        "topology-diff", help="compare two operator-supplied topology scenarios"
    )
    diff_parser.add_argument("baseline", type=Path, help="baseline topology JSON file")
    diff_parser.add_argument("candidate", type=Path, help="candidate topology JSON file")

    risk_parser = subparsers.add_parser(
        "topology-risk", help="calculate explainable structural fragility for a topology"
    )
    risk_parser.add_argument("file", type=Path, help="topology JSON file")
    args = parser.parse_args()

    if args.command == "check-connectivity" and not args.allow_network:
        print("error: check-connectivity requires explicit --allow-network consent", file=sys.stderr)
        return 2

    if args.command == "topology-report":
        document, read_status = _read_inventory(args.file)
        if read_status:
            return read_status
        try:
            topology = NetworkTopology.from_dict(document)
            report = topology.report()
            if args.disable_node or args.disable_link:
                report["failure_simulation"] = topology.simulate_failure(
                    disabled_nodes=set(args.disable_node), disabled_links=set(args.disable_link)
                )
            if bool(args.path_from) != bool(args.path_to):
                raise TopologyError("--path-from and --path-to must be supplied together")
            if args.path_from and args.path_to:
                report["path_analysis"] = topology.shortest_path(args.path_from, args.path_to)
            if args.traffic_file:
                traffic_document, traffic_status = _read_inventory(args.traffic_file)
                if traffic_status:
                    return traffic_status
                if (not isinstance(traffic_document, dict)
                        or isinstance(traffic_document.get("schema_version"), bool)
                        or traffic_document.get("schema_version") != 1
                        or not isinstance(traffic_document.get("demands"), list)):
                    raise TopologyError("traffic file must contain schema_version 1 and a demands array")
                report["traffic_simulation"] = topology.simulate_traffic(traffic_document["demands"])
            print(json.dumps(report, indent=2))
            return 0
        except (TopologyError, ValueError, TypeError) as exc:
            print(json.dumps({"mode": "simulation-only", "valid": False, "error": str(exc)}, indent=2))
            return 2

    if args.command == "topology-diff":
        baseline_document, baseline_status = _read_inventory(args.baseline)
        if baseline_status:
            return baseline_status
        candidate_document, candidate_status = _read_inventory(args.candidate)
        if candidate_status:
            return candidate_status
        try:
            baseline = NetworkTopology.from_dict(baseline_document)
            candidate = NetworkTopology.from_dict(candidate_document)
            print(json.dumps(baseline.compare(candidate), indent=2))
            return 0
        except (TopologyError, ValueError, TypeError) as exc:
            print(json.dumps({"mode": "simulation-only", "valid": False, "error": str(exc)}, indent=2))
            return 2

    if args.command == "topology-risk":
        document, read_status = _read_inventory(args.file)
        if read_status:
            return read_status
        try:
            topology = NetworkTopology.from_dict(document)
            print(json.dumps(topology.risk_report(), indent=2))
            return 0
        except (TopologyError, ValueError, TypeError) as exc:
            print(json.dumps({"mode": "simulation-only", "valid": False, "error": str(exc)}, indent=2))
            return 2

    inventory, read_status = _read_inventory(args.file)
    if read_status:
        return read_status

    findings = validate_inventory(inventory)
    if findings:
        print(json.dumps({"output_schema_version": 1, "valid": False, "finding_count": len(findings), "findings": findings}, indent=2))
        return 1

    if args.command == "validate":
        print(json.dumps({"output_schema_version": 1, "valid": True, "finding_count": 0, "findings": []}, indent=2))
        return 0

    if args.command == "check-connectivity":
        try:
            report = check_connectivity(inventory, limit=args.limit, timeout=args.timeout)
        except (ValueError, TypeError) as exc:
            print(json.dumps({"output_schema_version": 1, "valid": False, "error": str(exc)}, indent=2))
            return 2
        report["output_schema_version"] = 1
        report["valid"] = report["all_reachable"] and not report["scope_truncated"]
        print(json.dumps(report, indent=2))
        return 0 if report["valid"] else 1

    try:
        allocated = allocate_subnets(inventory, args.pool, args.prefix, args.count)
    except (ValueError, TypeError) as exc:
        print(json.dumps({"output_schema_version": 1, "valid": False, "error": str(exc), "allocated": []}, indent=2))
        return 2

    complete = len(allocated) == args.count
    print(json.dumps({
        "output_schema_version": 1,
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
