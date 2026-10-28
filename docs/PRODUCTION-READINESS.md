# Production Readiness Gates

This document is a release checklist, not a claim that the project has passed it. Mark a gate complete only when its evidence is linked or recorded.

## Current release posture

**Status: production candidate for the documented local CLI scope; live-network acceptance remains pending.** Inventory validation and subnet planning are local-only. The optional TCP check is read-only and opt-in, but must pass the authorized lab acceptance procedure before its results are used for operational decisions. The project is not a live network controller and has no device configuration adapters, continuous monitoring, service/API, authentication, persistence, deployment target, or independent security assessment.

## Gate A — Core correctness

- [x] Unit tests cover core inventory checks.
- [x] CLI returns documented exit codes for valid, invalid, and unreadable input.
- [x] CLI rejects malformed JSON, duplicate JSON keys, non-UTF-8 input, excessive nesting, and inputs over 5 MiB.
- [x] Inventory item counts and overlap report volume have explicit limits.
- [x] DNS hostname labels are validated against the versioned schema contract.
- [x] Subnet planner is deterministic, dry-run only, and bounded to one million candidates.
- [x] [CI run #247](https://github.com/yobi369/NETOPPS-infastructure/actions/runs/40635063318) passed on the merged PR head across Python 3.11, 3.12, and 3.13.
- [x] Test coverage is measured and an 80% minimum threshold is enforced in CI.
- [x] Deterministic randomized/property-style tests exercise subnet overlap and allocation boundaries.
- [x] Deterministic malformed-input smoke fuzzing exercises 250 byte sequences; deeper property-based parser fuzzing remains future hardening.

## Gate B — Security and supply chain

- [x] Pin GitHub Actions to immutable commit SHAs and document reviewed updates.
- [x] Run Bandit static analysis in CI.
- [x] Audit installed Python dependencies for known vulnerabilities in CI.
- [x] Run repository-wide detect-secrets scanning in CI; generated metadata is excluded and findings fail the build.
- [x] Document the threat model and scope for the current TCP connectivity integration; future integrations require separate review.
- [x] Define supported Python versions (Python 3.11+) and weekly dependency update proposals.
- [ ] Independent review remains required before any future privileged or write-capable integration.

## Gate C — Operational safety

- [x] Publish a versioned inventory JSON Schema and validate it in automated tests.
- [x] Test invalid address formats using the JSON Schema format checker.
- [x] Define a schema compatibility and migration policy; migration tooling remains future work.
- [x] Establish versioned machine-readable output and backward-compatibility contract tests.
- [x] Current CLI emits versioned machine-readable JSON and bounded reason codes; a separate log subsystem is not applicable to this one-shot CLI.
- [x] Document local-only processing and operator responsibility for inventory/report access, retention, and deletion.
- [x] Document operations and safe-use runbooks for current validation, planning, and connectivity commands.

## Gate D — Real infrastructure integrations

This gate covers the optional TCP reachability command; device-specific protocol/configuration adapters would require additional controls.

- [x] Explicit target scope is limited to inventory-listed endpoints.
- [x] Connectivity mode is read-only and requires explicit operator opt-in.
- [x] Connection timeouts and bounded concurrency are enforced.
- [x] Per-run target count, concurrency, and timeout limits are enforced; repeated-run pacing is the operator/orchestrator's responsibility for this one-shot CLI.
- [ ] Complete the [authorized network lab acceptance checklist](LAB-ACCEPTANCE.md) before relying on connectivity results operationally.
- [x] Mocked socket tests cover success, timeout, refusal, and partial scope; loopback integration test verifies a real local TCP handshake.
- [ ] Real-network lab validation remains outstanding; no device-specific protocols or firmware adapters are implemented.
- [n/a] No write-capable configuration feature exists. Approval, post-change verification, and rollback gates are mandatory before one is introduced.

## Gate E — Deployment and support

Not applicable to the current local CLI; complete these gates before introducing a hosted service or API.

- [n/a] No hosted service or API is implemented; these requirements become mandatory if one is introduced.
- [n/a] Authentication, authorization, secret management, and service audit events are not applicable to the current local CLI.
- [n/a] Service health checks, metrics, alerting, backup/restore, and recovery objectives are not applicable to the current local CLI.
- [n/a] Hosted CI/CD release approvals are not applicable; the current CI uses read-only permissions.
- [n/a] Service load, failure-injection, recovery, and upgrade tests are not applicable until a service exists.
- [x] Repository-level vulnerability reporting policy is documented in `SECURITY.md`.

## Release decision

A release can be called production-ready only for a clearly stated scope and environment after all applicable gates are evidenced. The current local CLI is a production candidate for inventory validation and subnet planning. The opt-in TCP check still requires the authorized lab acceptance checklist before operational reliance. No license has been selected; do not distribute the package for third-party reuse until the owner makes that decision. Passing CI does not establish that a live network controller or future hosted service is production-ready.
