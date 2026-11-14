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
- [x] CLI input-size limit, UTF-8 validation, duplicate JSON-key rejection, and nesting-depth limit.
- [x] Deterministic malformed-input smoke fuzz test.
- [x] Installable Python package with a console entry point.
- [ ] Observe successful GitHub Actions runs on the latest branch head after the most recent changes.

## Phase 2 — Inventory quality

- [x] Publish a versioned JSON Schema contract for inventory structure.
- [x] Detect duplicate management IP addresses and case-insensitive duplicate hostnames.
- [x] Add schema-driven compatibility tests and document version migration rules.
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

- [x] Add opt-in TCP connectivity checks for inventory-listed endpoints with timeouts and bounded concurrency.
- [x] Test connectivity behavior using mocked sockets and no external network access.
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


## Phase 6 — Simulation-first network intelligence

- [x] Introduce a deterministic topology model with strict input validation.
- [x] Report connected components, isolated nodes, degree, and declared link capacity.
- [x] Compute lowest-latency paths over modeled links.
- [x] Simulate node/link failures and quantify newly disconnected surviving node pairs.
- [x] Add deterministic traffic-demand and congestion scenarios.
- [x] Add topology diffs and explainable risk scoring.
- [x] Add site-level failure scenario packs and baseline comparisons.
- [x] Quantify optional traffic-demand reachability impact for each failure scenario.
- [x] Prioritize affected services using declared criticality and dependency weights.
- [x] Evaluate explicit service dependencies on services, nodes, links, and sites, including required/optional behavior and cascading impact.
- [x] Trace direct and recursive failure paths, classify direct/transitive impact, and rank affected institutions using unique service criticality/dependency weights.
- [x] Rank weakest institutional dependency failure domains and conditional redundancy recommendations.
- [x] Assess declared failover capacity under modeled single-dependency failures and rank recovery priorities.
- [x] Produce machine-readable executive resilience assessments through the CLI.
- [x] Compare baseline and proposed dependency models with before/after service impact and capacity-gap deltas.
- [x] Simulate correlated failures across operator-declared shared power, carrier, site, route, and other failure-domain labels.
- [x] Record diversity evidence metadata and flag shared failure domains across redundancy-group members without claiming independent authentication.
- [x] Capture service-defined RTO/RPO targets and use them in recovery-priority tie-breaking.
- [x] Export a self-contained, offline executive HTML briefing from the resilience assessment.

Acceptance: simulations are deterministic, non-mutating, have no network I/O, and distinguish declared scenario inputs from observed telemetry.


## Phase 7 — Commercial and contributor rights readiness

- [x] Document the distinction between the AGPL community path and a separately signed commercial licence.
- [x] Add a contributor licence agreement template that preserves contributor ownership while granting explicit project relicensing rights.
- [x] Require CLA acceptance before merging external contributions into the dual-licensed codebase.
- [x] Add a commercial agreement template with scope, deployment, fee, support, data, IP, warranty, liability, and signature schedules.
- [x] Add a commercial readiness checklist and clearly disclose current product boundaries.
- [ ] Obtain qualified legal review of the CLA, commercial agreement, AGPL notices, historical MIT grants, and ownership chain.
- [ ] Verify the rights holder's legal identity and rights for all existing code, documentation, examples, and assets.
- [ ] Complete third-party licence inventory and publish release-specific SBOM / notices.
- [ ] Define actual commercial pricing, support scope, deployment limits, and any SLA before making customer offers.

Acceptance: no external contribution is treated as commercially relicensable without a signed rights grant; no customer receives commercial rights, warranty, SLA, or support commitment until a complete agreement is signed by authorized parties.


## Phase 8 — Institutional go-to-market enablement

- [x] Prepare a sector-aware institutional product overview for government, universities, telecom operators, and enterprise infrastructure teams.
- [x] Document community and separately negotiated commercial licensing paths without inventing prices or implying unimplemented features.
- [x] Add a customer-specific proposal template with scope, deliverables, acceptance, fees, licensing, support, data, assumptions, and exclusions.
- [x] Add a discovery and bounded-pilot guide with qualification questions and stop/re-scope conditions.
- [ ] Validate positioning and procurement requirements with prospective institutional stakeholders.
- [ ] Confirm rights-holder identity, ownership chain, legal review, and third-party notices before issuing commercial offers.
- [ ] Establish approved pricing, delivery capacity, support process, and customer reference/acceptance workflow.

Acceptance: customer-facing material accurately reflects the current local CLI and simulation-only capabilities; no unsupported hosting, integration, SLA, certification, or live-control claim is made.


## Phase 9 — Institutional Pilot Edition

- [x] Define a controlled six-stage pilot lifecycle from onboarding to executive comparison.
- [x] Add a pilot charter template covering authorization, governance, scope, evidence, method, acceptance and stop conditions.
- [x] Add an evidence register template for provenance, freshness, ownership, validation state and permitted use.
- [x] Add an institutional acceptance checklist covering authorization, inputs, baseline, candidate, executive assessment and closeout.
- [x] Document the local CLI execution path using the existing resilience engine and report viewer.
- [x] Add a local pilot manifest generator with authorization metadata, artifact hash validation, evidence references and repeatable ZIP packaging.
- [ ] Validate the workflow with an authorized institutional partner and reviewer.
- [ ] Validate the workflow with an authorized institutional partner and reviewer.

Acceptance: pilot records identify approved scope and input versions; evidence and assumptions remain distinguishable; baseline input hashes detect drift; candidate comparisons use the same scope; sensitive data remains within the institution-approved environment; no unsupported hosted, live-monitoring or automated-control capability is implied.
