# Resilience Optimization and Recovery Planning

## Purpose

The resilience planner turns NETOPPS' operator-declared topology and service dependency model into a ranked, explainable planning assessment. It is local, deterministic, read-only, and simulation-only.

## Run

```bash
netopps resilience-report examples/multi-site-topology.json examples/service-dependencies.json
netopps resilience-report examples/multi-site-topology.json examples/service-dependencies.json --candidate-dependencies proposed-service-dependencies.json
```

The command emits JSON with. To compare a concrete proposal, pass `--candidate-dependencies` with a second valid version-1 service dependency document. The report then compares baseline and candidate service-state counts, weighted affected-service priority, and modeled capacity-gap counts; negative impact/gap deltas indicate modeled improvement.

The command emits JSON with:

- **Executive assessment:** baseline service state counts, highest-risk failure domain, leading conditional recommendation, capacity-gap counts, and first recovery priority.
- **Weakest dependencies:** one-at-a-time node, link, and site failure scenarios, ranked by affected service priority weight and unavailable-service count.
- **Redundancy recommendations:** proposed design work to add an explicitly modeled alternative. The avoided impact is conditional on independence, support coverage, successful failover, and sufficient capacity.
- **Capacity assessment:** capacity shortfalls observed in modeled failure states, computed from declared redundancy member capacities and the service's declared required capacity. Missing inputs remain unknown.
- **Recovery priorities:** deterministic ordering by service criticality and dependency weight, with service state as a tie-breaker.

## Interpretation

A failure domain is tested individually; the planner does not infer failure probabilities. `weighted_impact` is the sum of declared service priority weights for services that become degraded or unavailable in that scenario. It is not a financial loss, outage duration, or probability.

A redundancy recommendation is not a generated network design or an assertion that an alternate provider exists. Operators must identify a genuinely independent alternative, validate its technical compatibility, declare its capacity, and add it to a candidate dependency document. The existing topology and dependency document are never changed by the report.

Capacity gaps are meaningful only when both `required_capacity_mbps` and every relevant redundancy member's `capacity_mbps` are supplied. Unknown capacity is not treated as zero and is not estimated from link bandwidth.

Recovery priorities express a suggested order for restoration planning from declared criticality and dependency weight. They do not encode RTO/RPO, staffing, spare-part availability, restoration duration, legal obligations, or business continuity plans.

## Safety and model limits

- No network I/O, discovery, telemetry ingestion, configuration change, or live failover is performed.
- The current assessment evaluates individual declared infrastructure failures, not correlated or simultaneous failures.
- Declared site labels do not prove geographic or power-domain independence.
- Declared provider alternatives do not prove separate ownership, conduits, upstream carriers, DNS, identity, or control planes.
- No SLA compliance, outage probability, restoration time, or operational readiness is asserted.

For stronger evidence, validate proposed designs in an authorized lab and incorporate verified physical diversity, measured throughput, failover tests, and institution-approved recovery objectives.
