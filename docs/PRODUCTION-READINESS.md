# Production Readiness Gates

This document is a release checklist, not a claim that the project has passed it. Mark a gate complete only when its evidence is linked or recorded.

## Current release posture

**Status: early foundation / not production-ready.** The current tool validates local JSON inventory only. It has no device adapters, live monitoring, service/API, authentication, persistence, deployment target, or independent security assessment.

## Gate A — Core correctness

- [x] Unit tests cover core inventory checks.
- [x] CLI returns documented exit codes for valid, invalid, and unreadable input.
- [x] CLI rejects malformed JSON, duplicate JSON keys, non-UTF-8 input, excessive nesting, and inputs over 5 MiB.
- [x] Inventory item counts and overlap report volume have explicit limits.
- [x] DNS hostname labels are validated against the versioned schema contract.
- [x] Subnet planner is deterministic, dry-run only, and bounded to one million candidates.
- [ ] Latest GitHub Actions run passes on every supported Python version for the current branch head.
- [x] Test coverage is measured and an 80% minimum threshold is enforced in CI.
- [ ] Fuzz/property tests exercise parser and CIDR boundary behavior.

## Gate B — Security and supply chain

- [x] Pin GitHub Actions to immutable commit SHAs and document reviewed updates.
- [x] Run Bandit static analysis in CI.
- [ ] Add secret scanning and triage all findings.
- [ ] Add threat-model review for each network integration.
- [x] Define supported Python versions (Python 3.11+) and weekly dependency update proposals.
- [ ] Complete independent review before privileged live integrations.

## Gate C — Operational safety

- [x] Publish a versioned inventory JSON Schema and validate it in automated tests.
- [x] Test invalid address formats using the JSON Schema format checker.
- [x] Define a schema compatibility and migration policy; migration tooling remains future work.
- [x] Establish versioned machine-readable output and backward-compatibility contract tests.
- [ ] Add structured logs without secrets or sensitive topology leakage.
- [ ] Define safe handling of customer inventory, retention, access, and deletion.
- [ ] Create operator runbooks and incident/rollback procedures for each integration.

## Gate D — Real infrastructure integrations

This gate applies only if device access is added.

- [ ] Explicit target allowlists and least-privilege credentials.
- [ ] Read-only adapter mode by default.
- [ ] Connection and command timeouts, bounded concurrency, and rate limits.
- [ ] Simulator and contract tests, including partial failures and device timeouts.
- [ ] Lab validation against representative supported devices and firmware.
- [ ] Change plan, separate approval/apply step, post-change verification, and rollback before any write capability.

## Gate E — Deployment and support

This gate applies only if a service is added.

- [ ] Supported deployment topology and configuration documented.
- [ ] Authentication, authorization, secret management, and audit events tested.
- [ ] Health checks, metrics, alerting, backup/restore, and recovery objectives defined.
- [ ] CI/CD uses least privilege and protected release approvals.
- [ ] Load, failure-injection, recovery, and upgrade tests pass.
- [ ] A named maintainer and vulnerability-reporting process are documented.

## Release decision

A release can be called production-ready only for a clearly stated scope and environment after all applicable gates are evidenced. Passing the local validator CI does not establish that live network operations or a future hosted service are production-ready.
