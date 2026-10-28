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
- Check IPv4/IPv6 CIDR syntax and detect overlapping networks.
- Detect duplicate device identifiers and invalid management ports.
- Produce deterministic machine-readable findings with non-zero exit status on invalid input.
- Run automated unit tests and CI checks on supported Python versions.

These are the scope of the foundation implementation, not claims of live device monitoring or production deployment.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m netopps validate examples/inventory.json
python -m unittest discover -s tests -v
```

To validate your own inventory, copy `examples/inventory.json` and update it with non-sensitive lab data. Do not commit credentials, private keys, SNMP communities, or real production topology details.

## Inventory format

```json
{
  "schema_version": 1,
  "devices": [
    {
      "id": "lab-router-01",
      "hostname": "router-01.example.test",
      "management_ip": "192.0.2.10",
      "management_port": 22,
      "role": "router",
      "site": "lab"
    }
  ],
  "networks": [
    {"id": "lab-users", "cidr": "192.0.2.0/27", "site": "lab"}
  ]
}
```

The example uses documentation-only address space. Network overlap checks compare network ranges regardless of address family; different IPv4/IPv6 families do not overlap.

## Repository map

- `netopps/` — core validation package and CLI.
- `tests/` — deterministic tests for valid and invalid input.
- `examples/` — safe, synthetic inventory.
- `docs/ARCHITECTURE.md` — boundaries and extension points.
- `docs/SECURITY.md` — threat model and safe-use rules.
- `docs/OPERATIONS.md` — repeatable local workflow and incident discipline.
- `docs/ROADMAP.md` — staged delivery with verifiable acceptance criteria.
- `docs/DECISIONS.md` — engineering decision record.

## Safety boundaries

The current implementation parses local JSON only. It does not connect to routers, switches, firewalls, cloud accounts, or external hosts. Do not use this repository to test networks you do not own or have explicit permission to assess. Any future discovery or configuration feature must be opt-in, scoped, rate-limited, auditable, and documented before implementation.

## Development

```bash
python -m unittest discover -s tests -v
python -m netopps validate examples/inventory.json
```

See [Architecture](docs/ARCHITECTURE.md), [Security](docs/SECURITY.md), [Operations](docs/OPERATIONS.md), and [Roadmap](docs/ROADMAP.md).

## Contribution quality bar

Every feature should include tests, a clear failure mode, updated documentation, and an explicit statement of whether it is simulated, local-only, or verified against real infrastructure. Avoid committing secrets or claiming operational readiness without evidence.

## License

No license has been selected yet. Until a license is added, do not assume the repository grants permission to redistribute or reuse its contents.
