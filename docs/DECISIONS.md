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
