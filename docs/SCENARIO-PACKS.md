# Multi-Site Failure Scenario Packs

## Purpose

Scenario packs make topology resilience checks repeatable. A single versioned JSON file can describe whole-site, individual-node, and individual-link failures against an operator-supplied topology.

## Run the example

    netopps topology-scenarios examples/multi-site-topology.json examples/failure-scenarios.json

With traffic-impact analysis:

    netopps topology-scenarios examples/multi-site-topology.json examples/failure-scenarios.json --traffic-file examples/traffic-demands.json

The report includes:
- Baseline node count, active-link count, connected components, and component membership.
- Optional traffic impact per scenario when a traffic-demand file is supplied, including failed endpoints, demands that lose all surviving routes, newly affected Mbps, and remaining modeled routed Mbps.
- Each scenario's target and the nodes/links removed from the simulated state.
- Before/after component counts and newly disconnected surviving node pairs.
- Remaining topology node/link counts, components, and isolated nodes.

Scenarios are returned in stable ID order. The topology object is not mutated.

## Scenario contract

The pack is a JSON object with `schema_version: 1` and a `scenarios` array. Each scenario has:
- `id`: unique, non-empty stable identifier.
- `name`: optional human-readable label.
- `failure_type`: `site`, `node`, or `link`.
- `target`: exact site label, node ID, or link ID from the topology.

A site failure disables every node whose `site` label exactly matches the target and all incident links. A node failure disables that node and its incident links. A link failure disables only the selected link. Unknown targets fail closed.

## Interpretation and limitations

This is a deterministic graph scenario tool, not a fault-injection system. It does not power off equipment, disable interfaces, generate traffic, test protocol convergence, or verify physical diversity. Site membership is only as accurate as the supplied labels. The result quantifies modeled connectivity loss among surviving nodes, not business impact or service availability. Optional traffic impact adds demand-level reachability estimates, but it still does not represent application health, business criticality, measured throughput, SLA compliance, or live service availability. A demand is newly affected only when it was routable in the baseline and becomes unavailable or unroutable after the modeled failure.

Use sanitized, synthetic topology data in source control. Never treat a scenario result as permission to run a live change.
