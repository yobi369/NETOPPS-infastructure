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
- Deterministic traffic-demand routing over one lowest-latency path per demand.
- Per-link modeled load, utilization, and capacity-overload estimates.

Traffic demand assumptions and limitations are documented in [Traffic Simulation](TRAFFIC-SIMULATION.md).

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

1. Add topology-diff and risk scoring with explainable evidence.
2. Add reproducible scenario packs for link, node, and site failures.
3. Compare candidate network plans against baseline metrics.
4. Only after simulator contracts mature, design a read-only adapter interface and authorized lab acceptance protocol.
