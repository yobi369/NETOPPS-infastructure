# Changelog

All notable changes to NETOPPS are documented here. This project currently uses an early `0.x` version; interfaces may change before a stable release.

## Unreleased

### Added
- Local JSON inventory validation with deterministic findings and explicit exit codes.
- Duplicate device/network identifiers, duplicate hostnames and management IP checks.
- IPv4/IPv6 CIDR validation and bounded overlap reporting.
- Read-only IPv4/IPv6 subnet allocation planning.
- Explicitly opted-in TCP reachability checks limited to inventory-listed management endpoints.
- Input-size, UTF-8, duplicate JSON-key, and excessive-nesting safeguards.
- Versioned inventory JSON Schema, schema validation tests, and a versioned CLI output contract.
- Python package metadata and `netopps` console entry point.
- CI across Python 3.11, 3.12, and 3.13 with linting, static security analysis, coverage, schema checks, and wheel installation verification.
- Security, contributor, operations, architecture, roadmap, and production-readiness documentation.

### Limitations
- No live device adapters, active discovery, monitoring service, authentication service, persistent storage, or configuration write operations.
- No production deployment or external network lab validation has been completed.
- No license has been selected.


## Unreleased — Network digital twin foundation

- Added a deterministic, simulation-only topology model with strict node/link validation.
- Added connected-component, isolated-node, degree, and declared-capacity summaries.
- Added lowest-latency path analysis and hypothetical node/link failure simulation.
- Added the topology-report CLI command and a synthetic topology fixture.
- Added regression tests and documented the distinction between modeled inputs and live telemetry.
- No live network discovery, telemetry collection, or configuration changes were introduced.


## Unreleased — Traffic-demand simulation

- Added deterministic single-path traffic assignment using lowest-latency routes.
- Added per-link carried-load, utilization, and capacity-overload estimates.
- Added versioned traffic scenario input, CLI integration, tests, and model-limit documentation.
- Kept all traffic analysis local and simulation-only; no packets are generated and no live telemetry is read.
