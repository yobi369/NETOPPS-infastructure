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


## Unreleased — Topology comparison and structural risk

- Added deterministic baseline-to-candidate node and link diffs.
- Added iterative articulation-node and bridge-link analysis, including parallel-link handling.
- Added explainable 0–100 structural-fragility scoring with factor-level evidence and documented weights.
- Added `topology-diff` and `topology-risk` CLI commands with local-only regression tests.
- Scores are heuristics, not outage probabilities; no live telemetry or network operations are involved.


## Unreleased — Multi-site failure scenario packs

- Added versioned scenario packs for whole-site, node, and link failures.
- Added deterministic before/after component and surviving-node connectivity impact reports.
- Added multi-site synthetic topology and failure scenario examples, CLI command, tests, and documentation.
- Site failures remove all nodes carrying the exact target site label in the simulated state only.
- Added optional traffic-demand impact analysis per failure scenario, including failed endpoints, route loss, newly affected Mbps, and residual routed demand.
- Added CLI integration and regression coverage proving the feature performs no network I/O and does not mutate the baseline topology.
- Added backward-compatible service identity, criticality classes, and bounded dependency weights to traffic-demand simulation.
- Failure scenario reports now include weighted impact per affected demand and deterministic affected-service summaries.
- Documented the formula, defaults, examples, and limits; no business metadata is inferred and no live telemetry is accessed.

- Added a versioned, explicit service dependency graph for service-to-service and service-to-infrastructure relationships.
- Failure scenarios now report available, degraded, and unavailable services, including cascading required dependencies and optional dependency degradation.
- Added CLI integration, strict reference/cycle validation, synthetic dependency examples, and documented simulation-only boundaries.
- Corrected service dependency evaluation so links incident to failed nodes/sites are unavailable to dependent services; added regression tests for node, site, and pre-disabled link cases.


## Unreleased — Institutional dependency-impact intelligence

- Added paired institution identity metadata to service dependency records.
- Added deterministic infrastructure-to-service failure paths and direct/transitive impact classification.
- Added distinct additional-path counts while retaining per-dependency causal evidence.
- Added institution-level aggregation and ranking using unique affected service priority weights.
- Preserved required/optional dependency state semantics and the existing scenario CLI contract.
- Added regression coverage for recursive propagation, multiple causal paths, institutional ranking, identity validation, non-mutation, and optional-dependency degradation.


## Unreleased — Institutional resilience and redundancy intelligence

- Added explicit OR-semantics redundancy groups for alternative service dependencies while preserving existing ungrouped dependency behavior.
- Added failover activation and remaining declared capacity reporting.
- Added optional service capacity requirements and explicit capacity-adequacy/unknown reporting.
- Added validation for mixed required/optional members in a redundancy group.
- Added regression tests for successful failover, capacity shortfall, total redundancy exhaustion, optional groups, and invalid group contracts.
- Extended the synthetic institutional example and documented the simulation-only limits of declared redundancy and capacity.


## Unreleased — Resilience optimization and recovery planning

- Added a deterministic resilience assessment for operator-declared institutional service dependencies.
- Ranked single infrastructure dependency failure domains by modeled service impact and generated conditional redundancy recommendations.
- Assessed declared failover capacity under each modeled single-dependency failure and reported numeric gaps or unknown inputs.
- Added deterministic recovery priorities based on declared criticality and dependency weights, plus an executive assessment summary.
- Added the `resilience-report` CLI, regression tests, and documented model assumptions and limitations.
- Recommendations are planning hypotheses; no physical independence, successful failover, restoration time, or live state is claimed.
