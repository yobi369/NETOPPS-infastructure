# Engineering Decision Records

## ADR-001: Start with a local, read-only validator

**Status:** Accepted

**Context:** Network automation can cause outages when inventory assumptions are wrong. The repository needs a useful, testable base before connecting to live systems.

**Decision:** Begin with a standard-library Python CLI that parses local JSON and checks inventory structure, management endpoints, and overlapping CIDRs. It does not perform network I/O.

**Consequences:** Easy to run on a laptop and in CI with no external services or credentials. It cannot report device reachability or live configuration state.

## ADR-002: Treat documentation as an operational contract

**Status:** Accepted

**Decision:** Every feature must document current behavior, safety boundaries, failure modes, and what has not been verified. Future roadmap items must not be described as implemented.

**Consequences:** The README and readiness claims stay aligned with executable behavior and test evidence.


## ADR-003: Use a simulation-first digital twin

**Status:** Accepted

The first adaptive-intelligence research milestone is a deterministic graph model built from operator-supplied topology data. It must not discover devices, open sockets, collect telemetry, or mutate live infrastructure. This enables reproducible failure and path-analysis experiments without operational risk.

## ADR-004: Keep simulated metrics distinct from observed telemetry

**Status:** Accepted

Declared capacity and latency are scenario inputs, not measurements. Reports and documentation must label the model as simulation-only and must not imply that the digital twin reflects current network state unless a future evidence-backed ingestion adapter is implemented.


## ADR-005: Model traffic as explicit demand scenarios

**Status:** Accepted

Traffic demand is supplied as a separate, versioned scenario and assigned deterministically to one lowest-latency path. The model aggregates rates on shared links and compares them with declared capacities. It must clearly disclose its single-path assumptions and must not present estimates as measured utilization or generate live traffic.


## ADR-006: Keep structural risk scoring explainable and deterministic

**Status:** Accepted

NETOPPS uses a transparent rule-based score derived only from the supplied topology graph. The score reports separate evidence for fragmentation, articulation nodes, bridge links, and isolated nodes. It is a prioritization heuristic, not an outage probability or a substitute for operational risk assessment. Factor weights and severity bands are versioned and documented.


## ADR-007: Represent repeatable failures as versioned scenario packs

**Status:** Accepted

Failure scenarios are declared in a separate versioned JSON pack and reference exact site labels, node IDs, or link IDs from the supplied topology. Site failure removes all nodes assigned to that site and their incident links in the simulation. Each result reports baseline and remaining connectivity without mutating the source model. This is not live fault injection or a claim of physical site independence.

## ADR-008: Attach modeled traffic impact to failure scenarios

**Status:** Accepted

Failure scenario packs may consume the existing versioned traffic-demand contract. For each simulated failure, demands whose endpoints fail are marked endpoint-unavailable; surviving endpoint pairs are re-routed over the residual topology. Only baseline-routable demands that become unavailable or unroutable count as newly affected. Reports include affected demand IDs and rates plus remaining modeled routed demand. This is a local estimate, not application monitoring, observed throughput, SLA evidence, or live traffic generation.

## ADR-009: Weight modeled failure impact by declared service criticality

**Status:** Accepted

**Context:** Raw Mbps alone cannot distinguish ordinary traffic from traffic
supporting an institution’s critical service. Prioritization must not invent
business facts that are absent from the supplied model.

**Decision:** Extend the existing version-1 traffic-demand contract with optional
service identity, criticality, and dependency-weight metadata. Defaults preserve
compatibility. Compute weighted impact using demand Mbps, a documented
criticality multiplier, and a bounded operator-supplied dependency weight.
Aggregate affected demands by service ID and rank service summaries deterministically.

**Consequences:** Failure reports distinguish services using declared metadata
while retaining raw Mbps and demand-level evidence. Weights are model inputs only;
they do not establish actual business criticality, dependencies, SLA compliance,
service health, or outage probability.


## ADR-010: Model explicit service-to-infrastructure dependencies

**Status:** Accepted

**Context:** Traffic demand and service criticality alone cannot represent the
cascade from a failed infrastructure component through a supporting platform
into dependent institutional services.

**Decision:** Accept a separate version-1 service dependency document. Services
may depend on other services, topology nodes, links, or sites. Dependencies are
required by default; optional dependencies degrade rather than make a service
unavailable. Validate references, reject duplicate edges and service cycles,
and evaluate the graph deterministically in dependency-first order for each
failure scenario.

**Consequences:** Scenario reports can distinguish available, degraded, and
unavailable services and show cascading dependency evidence. A link dependency
is unavailable when the link is explicitly failed, disabled in the baseline,
or incident to a failed node. The graph is operator-declared and simulation-only;
no dependency discovery, service health checks, SLA claims, or live network
operations are implied.


## ADR-011: Explain recursive institutional dependency impact

**Status:** Accepted

**Context:** A service graph can show cascading states, but operators and
institutional stakeholders also need a traceable root-cause path and a stable
way to prioritize the organizations affected by a modeled infrastructure
failure.

**Decision:** Extend the existing version-1 service records with optional,
paired institution ID/name metadata. For every affected service, expose a
deterministic causal path from a failed infrastructure object through any
supporting services to the affected service. Report additional distinct causal
path counts, direct versus transitive scope, and institution summaries ranked
by the sum of unique affected service priority weights. Preserve the existing
available/degraded/unavailable state rules and existing CLI integration.

**Consequences:** Institution-level summaries are only as reliable as supplied
ownership, criticality, dependency and topology declarations. The primary path
is a deterministic explanation, not a live route or health observation.
Services without institution metadata remain reportable but unassigned.


## ADR-012: Model service redundancy and failover capacity

**Status:** Accepted

**Context:** A dependency graph that treats every edge independently cannot
represent alternative providers or distinguish a surviving failover path from
a service whose only dependency has failed. Institutional resilience analysis
must make redundancy assumptions explicit and auditable.

**Decision:** Allow dependencies to declare a `redundancy_group` whose members
are alternatives (OR semantics), while ungrouped dependencies retain their
existing independent required/optional behavior. All members in a group must
agree on required/optional status. Optional per-member declared capacity and an
optional service-level required capacity threshold support transparent
remaining-capacity estimates. A surviving alternative after a member failure
preserves service operation but marks it degraded because redundancy has been
consumed.

**Consequences:** Reports expose active failover, surviving member counts and
remaining declared capacity. Capacity adequacy is unknown when capacity inputs
are incomplete. This is a deterministic model only: it does not validate
physical diversity, provider independence, live failover, measured throughput,
recovery time, or SLA compliance.


## ADR-013: Rank resilience options and recovery priorities from explicit models

**Status:** Accepted

**Context:** Failure simulations identify impact, but institutional decision-makers also need a ranked view of weak dependency failure domains, conditional redundancy actions, declared capacity gaps, and recovery order.

**Decision:** Add a deterministic read-only assessment that evaluates each declared infrastructure dependency as an individual failure scenario, ranks the resulting service impact, and proposes explicit redundancy design work only as a conditional planning action. Evaluate declared redundancy-group capacity during those scenarios and report numeric shortfalls only when both required and available capacity are supplied. Rank recovery priorities using declared criticality and dependency weights. Expose a machine-readable executive summary through a dedicated CLI command.

**Consequences:** Results are reproducible planning evidence based on operator-supplied inputs. A proposed alternative is not treated as an implemented candidate or a guaranteed benefit. Physical diversity, correlated failures, failover behavior, live capacity, recovery-time objectives, and service-level agreements require independent evidence and validation.


## ADR-014: Model correlated failure domains, diversity evidence, and recovery objectives

**Status:** Accepted

**Context:** Single-asset failure simulations can overstate resilience when nominally separate alternatives share power, carrier, site, route, or other common-cause dependencies. Recovery planning also needs institution-defined RTO/RPO targets, while evidence supporting physical-diversity claims must remain traceable.

**Decision:** Allow infrastructure dependency edges to declare shared failure_domains labels and optional diversity_evidence metadata. Evaluate each shared label as a correlated failure affecting all tagged nodes, links, and sites. Compare members of each redundancy group for shared failure-domain labels. Allow services to declare positive rto_minutes and non-negative rpo_minutes; expose these objectives and use them as deterministic recovery-priority tie-breakers after criticality and dependency weight.

**Consequences:** Reports distinguish detected shared-domain overlap, missing independent evidence, and operator-recorded independent evidence. NETOPPS does not retrieve or authenticate evidence references, validate physical routes, or certify provider/site independence. Correlated scenarios are only as complete as the supplied labels. RTO/RPO values are planning targets, not observed restoration performance or SLA compliance.
