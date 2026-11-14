# Network Digital Twin — Foundation

## Purpose

The digital twin is a deterministic, simulation-only representation of an operator-supplied network graph. It gives NETOPPS a safe place to reason about topology, path latency, connectivity partitions, and hypothetical failures before any live integration is considered.

This is a simulation-only graph-analysis foundation, not a live monitoring system, network scanner, traffic generator, or autonomous controller.

## Input contract

A topology document is a JSON object with:

- schema_version: integer 1.
- nodes: unique node identifiers with optional role and site labels.
- links: unique link identifiers, source and target node IDs, non-negative latency in milliseconds, positive declared capacity in Mbps, and optional enabled state.

See examples/topology.json.

The model rejects duplicate IDs, unknown endpoints, self-links, invalid metrics, and malformed fields. It sorts identifiers and adjacency lists so reports are reproducible.

## Current capabilities

- Stable topology summary: node/link counts, connected components, isolated nodes, average degree, and declared active-link capacity.
- Lowest-total-latency path between two modeled nodes.
- Hypothetical node and link failure simulation.
- Before/after component comparison and count of newly disconnected surviving node pairs.
- Explicit non-mutation indicator in simulation results.
- Identity-based baseline/candidate topology diffs for nodes and links.
- Explainable structural-fragility scoring with articulation-node, bridge-link, fragmentation, and isolation evidence.
- Versioned node, link, and site failure scenario packs with before/after connectivity impact.
- Deterministic traffic-demand routing over one lowest-latency path per demand.
- Per-link modeled load, utilization, and capacity-overload estimates.

Traffic demand assumptions and limitations are documented in [Traffic Simulation](TRAFFIC-SIMULATION.md).

## Comparison and structural risk

Use `netopps topology-diff baseline.json candidate.json` to report added, removed, and changed nodes and links. Node role/site attributes and link endpoints/latency/capacity/enabled state are compared. Link endpoints are treated as undirected; reversing source and target alone is not a change. IDs are the stable identity keys.

Use `netopps topology-risk examples/topology.json` to calculate a transparent 0–100 structural-fragility score. The score is a rule-based prioritization heuristic, not a probability of outage or a measured operational risk. The weights and evidence are documented in [Topology Risk](TOPOLOGY-RISK.md).

## Example

    import json
    from pathlib import Path
    from netopps.topology import NetworkTopology

    document = json.loads(Path("examples/topology.json").read_text(encoding="utf-8"))
    twin = NetworkTopology.from_dict(document)
    print(twin.report())
    print(twin.shortest_path("core-router", "app-server"))
    print(twin.simulate_failure(disabled_links={"core-to-a"}))

## Safety and limitations

- Pure local computation; no sockets, discovery, device credentials, telemetry collection, or configuration writes.
- All topology data is supplied by the operator and may be incomplete or inaccurate.
- Link capacity is declared metadata, not measured throughput; latency is a simulation input, not a live measurement.
- Failure simulation removes modeled nodes/links only. It does not test physical failover or convergence behavior.
- No claim of autonomous intelligence, self-healing, or production network validation is made.

## Next research steps

1. Compare candidate network plans against baseline metrics and traffic scenarios.
2. Add scenario-specific traffic reachability and service dependency analysis.
3. Only after simulator contracts mature, design a read-only adapter interface and authorized lab acceptance protocol.
