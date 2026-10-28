# Roadmap and Acceptance Criteria

This roadmap records intent. A milestone is complete only when its acceptance criteria are implemented and evidenced in CI or a reproducible manual test.

## Phase 1 — Reliable foundation

- [x] Local JSON inventory validator.
- [x] Device identifier, hostname, IP, role, and port checks.
- [x] CIDR parsing and overlap detection.
- [x] Deterministic JSON findings and exit codes.
- [x] Synthetic example inventory and unit tests.
- [x] CI workflow for Python 3.11–3.13.
- [x] Security, architecture, operations, and production-readiness documentation.
- [x] CLI input-size limit, UTF-8 validation, and duplicate JSON-key rejection.
- [x] Installable Python package with a console entry point.
- [ ] Observe successful GitHub Actions runs on the latest branch head after the most recent changes.

## Phase 2 — Inventory quality

- [x] Publish a versioned JSON Schema contract for inventory structure.
- [x] Detect duplicate management IP addresses.
- [ ] Add schema-driven compatibility tests and version migration rules.
- [ ] Add safe CSV import/export with round-trip tests.
- [ ] Add site consistency checks.
- [ ] Add report summaries that distinguish errors from warnings.

Acceptance: fixtures cover valid/invalid cases; import/export preserves data; schema compatibility is documented.

## Phase 3 — Network planning

- [x] Add deterministic read-only subnet allocation planning.
- Add subnet utilization summaries and before/after inventory diffs.
- Add property-based or fuzz-style tests for address boundaries.

Acceptance: no plan is applied to a device; edge cases and IPv4/IPv6 are tested.

## Phase 4 — Read-only observability

- Add opt-in, explicitly scoped checks with timeouts and bounded concurrency.
- Support simulation mode with deterministic fake devices.
- Redact sensitive data and provide structured event output.

Acceptance: simulator tests run in CI; live checks are opt-in; no unbounded discovery.

## Phase 5 — Controlled automation

- Add change plans, approval gates, maintenance-window metadata, and rollback documentation.
- Add adapters only after simulator and contract tests.
- Keep credentials external to source control.

Acceptance: no write operation runs without an explicit approved apply action; failure and rollback paths are tested.

## Non-goals until separately justified

- Unscoped internet scanning.
- Silent configuration changes.
- Storing production secrets in Git.
- Claims of production readiness without environment-specific validation.
