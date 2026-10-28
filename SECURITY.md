# Security Policy

## Scope

NETOPPS currently validates local JSON inventory and creates read-only subnet allocation plans. It does not connect to network devices or change infrastructure.

## Reporting a vulnerability

Please do not publish exploitable details, credentials, or sensitive topology information in a public issue. If GitHub private vulnerability reporting is enabled for this repository, use it. Otherwise, contact the repository maintainer through a private channel before disclosing details publicly.

Include the affected commit or version, impact, reproduction steps using synthetic data, and any suggested mitigation. Do not include real secrets or customer data.

## Response expectations

This project has no formal SLA or staffed security response team. The maintainer will assess reports as availability permits. Do not assume a report is acknowledged until you receive a response.

## Security boundaries

The production-readiness requirements and design constraints are documented in [docs/SECURITY.md](docs/SECURITY.md) and [docs/PRODUCTION-READINESS.md](docs/PRODUCTION-READINESS.md).
