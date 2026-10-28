# Architecture

## Current implementation

The foundation is a Python CLI. Inventory validation and subnet planning are local-only; the optional connectivity command can open bounded TCP connections to explicitly listed management endpoints only when the operator supplies `--allow-network`.

1. `python -m netopps validate <file>` reads a local JSON document.
2. JSON decoding errors are reported to stderr and return exit code 2.
3. Structural and semantic checks produce stable findings with `code`, `path`, and `message`.
4. Valid input exits 0; invalid inventory exits 1.
5. The validator and subnet planner never open sockets or change device state.
6. The subnet planner emits deterministic candidate CIDRs and explicitly labels plans as not applied.
7. The connectivity checker opens TCP sockets only to inventory-listed management endpoints, sends no application payload, and closes each connection.
8. Allocation checks merge occupied address ranges before searching, bounding the work by inventory sorting plus the configured candidate limit.
9. Connectivity concurrency is capped at eight workers and per-connection timeout at three seconds.
8. Connectivity checks target only inventory-listed management IPs, require an explicit CLI opt-in, use bounded concurrency/timeouts, and send no application data.

## Boundaries

- Input: operator-supplied JSON files.
- Core: Python standard library, including `ipaddress`.
- Output: human-readable JSON to stdout.
- Persistence: none.
- Authentication: not applicable; no service/API exists.
- Device adapters, metrics collection, web UI, and automated remediation: not implemented.

## Extension strategy

Prefer pure functions and explicit interfaces. Keep parsing separate from policy checks; keep policy checks separate from integrations. An integration should have a simulator and contract tests before a live adapter. All write-capable operations must generate a reviewable plan first and require a separate explicit apply step.

## Future target architecture

- Inventory adapters with schema-versioned normalization.
- Plan engine that computes intended changes without applying them.
- Policy checks for CIDR overlaps, naming, ownership, and approved maintenance windows.
- Read-only device adapters with timeouts, bounded concurrency, and redacted logs.
- Evidence store for check results and change events.
- Approval gate and rollback strategy for any configuration write.
- Optional dashboard only after stable API and authorization boundaries exist.

These are design directions, not current features.
