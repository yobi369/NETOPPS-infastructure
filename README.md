# NETOPPS Infrastructure

**A safety-first, observable, automation-ready network infrastructure toolkit.**

NETOPPS is being shaped into a practical NetOps engineering workspace: inventory validation, network-plan checks, operational runbooks, reproducible tests, and eventually carefully gated automation. The first principle is simple: **inspect and validate before changing live infrastructure**.

> Status: foundation phase. This repository is not yet a live network controller. The validator described below is the initial reference implementation; device integrations and live monitoring remain future work.

## Why this project

Network changes fail in expensive ways when inventory is inconsistent, addressing plans overlap, assumptions are undocumented, or automation has no safe rollback. NETOPPS aims to make those risks visible early, using small composable tools, machine-readable inputs, evidence-backed reports, and explicit operator approval.

## Design principles

- **Read-only by default:** no device configuration changes or network scans in the foundation tooling.
- **Fail closed:** malformed or ambiguous inventory is an error, not a guessed value.
- **Explainable checks:** every finding identifies the affected object and reason.
- **Portable and low-cost:** Python standard library for core validation; no paid services required.
- **Evidence over claims:** CI results and actual test coverage determine readiness statements.
- **Human-controlled change:** future write-capable actions require dry-run plans, explicit approval, timeouts, and rollback strategy.
- **Small composable tools:** useful CLI primitives before a sprawling dashboard.

## Current capabilities

- Validate JSON infrastructure inventory structure.
- Generate deterministic, read-only subnet allocation plans from a specified IPv4 or IPv6 pool.
- Check IPv4/IPv6 CIDR syntax and detect overlapping networks.
- Detect duplicate device identifiers, DNS hostname syntax and duplicates, duplicate management IP addresses, invalid roles, and invalid management ports.
- Reject ambiguous duplicate JSON keys, malformed UTF-8, excessively nested JSON, and input files larger than 5 MiB. Inventory sizes and overlap findings are also bounded.
- Produce deterministic machine-readable findings with documented exit codes.
- Exercise CLI and validator behavior with automated tests.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m netopps validate examples/inventory.json
netopps plan-subnets examples/inventory.json --pool 10.20.0.0/16 --prefix 24 --count 4
python -m unittest discover -s tests -v
```

Exit codes: `0` means checks passed, `1` means inventory validation findings exist, and `2` means the input could not be safely read or parsed.

To validate your own inventory, copy `examples/inventory.json` and update it with non-sensitive lab data. Do not commit credentials, private keys, SNMP communities, or real production topology details.

## Inventory contract

The versioned interchange schema is in [schemas/inventory.schema.json](schemas/inventory.schema.json). The schema defines the data shape; the Python validator additionally checks semantic conditions such as overlapping networks and duplicate management addresses.

## Repository map

- `netopps/` — core validation, subnet planning package, and CLI.
- `tests/` — validator and CLI regression tests.
- `examples/` — safe, synthetic inventory.
- `schemas/` — versioned inventory schema.
- `docs/ARCHITECTURE.md` — boundaries and extension points.
- `docs/SECURITY.md` — threat model and safe-use rules.
- `docs/OPERATIONS.md` — repeatable local workflow and incident discipline.
- `docs/ROADMAP.md` — staged delivery with verifiable acceptance criteria.
- `docs/PRODUCTION-READINESS.md` — release gates and current gaps.
- `docs/RELEASE.md` — controlled release and rollback process.
- `docs/SCHEMA-COMPATIBILITY.md` — schema versioning and migration rules.
- `CHANGELOG.md` — implemented changes and limitations.
- `docs/DECISIONS.md` — engineering decision records.

## Safety boundaries

The current implementation parses local JSON only. It does not connect to routers, switches, firewalls, cloud accounts, or external hosts. Do not use this repository to test networks you do not own or have explicit permission to assess. Any future discovery or configuration feature must be opt-in, scoped, rate-limited, auditable, and documented before implementation.

## Development and CI

```bash
python -m compileall -q netopps tests
python -m json.tool schemas/inventory.schema.json > /dev/null
python -m unittest discover -s tests -v
python -m netopps validate examples/inventory.json
```

GitHub Actions runs these checks on Python 3.11, 3.12, and 3.13. A successful run verifies this local validator scope only; it does not verify live devices or production deployment.

## Contribution quality bar

Every feature should include tests, a clear failure mode, updated documentation, and an explicit statement of whether it is simulated, local-only, or verified against real infrastructure. Avoid committing secrets or claiming operational readiness without evidence.

## License

No license has been selected yet. Until a license is added, do not assume the repository grants permission to redistribute or reuse its contents.
