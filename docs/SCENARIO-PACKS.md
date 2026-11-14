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

## Service criticality and dependency weighting

Traffic-demand records may optionally include `service_id`, `service_name`,
`criticality`, and `dependency_weight`. Existing records remain valid:
omitted values default to the demand ID, that ID as the service name,
`standard` criticality, and a dependency weight of `1.0`.

| Criticality | Multiplier |
| --- | ---: |
| low | 1.0 |
| standard | 1.5 |
| high | 2.5 |
| mission_critical | 4.0 |

`dependency_weight` is an operator-supplied relative importance factor from
`0.1` through `10.0`. Weighted impact is:

`demand_mbps × criticality_multiplier × dependency_weight`

Demands sharing a `service_id` are grouped in scenario results. Reports retain
raw affected Mbps and rank affected services by weighted impact, then declared
criticality, then stable service ID. These are explicit modeling inputs; NETOPPS
does not infer service dependencies or business criticality.

Example traffic-demand record:

```json
{
  "id": "core-banking-api",
  "source": "core-router",
  "target": "banking-app",
  "demand_mbps": 30,
  "service_id": "core-banking",
  "service_name": "Core Banking",
  "criticality": "mission_critical",
  "dependency_weight": 2.0
}
```

This prioritization is not a business-impact assessment, measured dependency
graph, SLA calculation, outage probability, or evidence of actual service health.
Operators must supply and validate the criticality and dependency metadata.

## Explicit service dependency graph

An optional dependency file adds a directed, versioned service graph to failure
analysis. Run it independently of traffic-demand analysis:

    netopps topology-scenarios examples/multi-site-topology.json examples/failure-scenarios.json --dependency-file examples/service-dependencies.json

The file uses schema_version 1, a services array, and a dependencies array.
A service declares id, name, and optional criticality and dependency weight
metadata. Each dependency declares service_id, depends_on_type (service, node,
link, or site), depends_on_id, and optional required (default true). All
references must resolve exactly against the service graph or supplied topology.
Duplicate edges and service dependency cycles are rejected.

A failed required infrastructure dependency makes its service unavailable. A
failed optional dependency degrades it. A link dependency is also considered
failed when either endpoint node is removed by a node or site scenario, even if
the link was not named directly in the failure. A required supporting service
that is unavailable propagates unavailability to dependent services; a
degraded supporting service propagates degradation. Reports include baseline
states and per-scenario available, degraded, and unavailable counts, affected
services, and the specific failed dependency evidence.

Criticality and dependency weights are retained as prioritization metadata;
they do not change dependency-state rules. This remains a deterministic
simulation, not application monitoring, live dependency discovery, SLA
verification, or proof that a service is operational.

## Institutional dependency-impact reports

The service dependency document may add `institution_id` and
`institution_name` to each service. Supply both or neither; services sharing
an institution ID must use the same institution name. This is operator-declared
ownership metadata, not an inferred organizational relationship.

For every affected service, the report includes:
- `impact_scope`: `direct` when its own infrastructure dependency failed,
  or `transitive` when impact arrived through a supporting service.
- `failure_path`: one deterministic, shortest trace from the failed node,
  link, or site to the affected service.
- `additional_failure_path_count`: the number of other distinct causal paths
  found for that service. Direct dependency evidence remains in
  `failed_dependencies`.
- `status`: `unavailable` when a required dependency is unavailable,
  `degraded` when only optional dependencies or degraded supporting services
  are affected, otherwise `available`.

The report also returns `affected_institutions`, ranked by the sum of each
unique affected service's declared priority weight
(`criticality multiplier × dependency_weight). Services are counted once per
institution even when multiple dependency paths reach them. Institution
summaries include unavailable/degraded counts and affected service IDs. Services
without institution metadata remain in the service report but are not assigned
to an institution. A missing dependency or an unverified application-health
signal is not silently treated as degraded; this model reports only states
supported by the declared graph and simulated failure.

Run with the existing scenario command:

    netopps topology-scenarios examples/multi-site-topology.json examples/failure-scenarios.json --dependency-file examples/service-dependencies.json

This remains a local, deterministic simulation. The primary path is an
explanation of modeled dependency causality, not proof of a live incident path,
application health, recovery time, SLA breach, or business loss.


## Institutional resilience and redundancy groups

Service dependency records may declare optional `redundancy_group` and
`capacity_mbps` fields. Dependencies for the same service and redundancy-group
name represent alternative providers or infrastructure dependencies (OR
semantics): one surviving member can keep the dependency group operational.
All members in a group must agree on the `required` flag. Ungrouped
dependencies retain the existing independent AND semantics.

When one or more alternatives fail but another remains operational, NETOPPS
reports the service as `degraded` because failover has consumed redundancy.
The report's `redundancy` entry shows member counts, whether failover is
active, and remaining declared capacity. Capacity is summed only when every
member in that group declares a valid `capacity_mbps`; otherwise remaining
capacity is `null` and capacity adequacy is unknown.

A service may optionally declare `required_capacity_mbps`. For each
redundancy group, NETOPPS compares the surviving declared capacity with that
threshold. A shortfall with some capacity remaining is degraded; zero
surviving capacity makes a required group unavailable. If capacity inputs or
the threshold are absent, NETOPPS does not infer capacity adequacy. This is a
declared-capacity model, not measured throughput, tested failover, physical
provider diversity, or an SLA guarantee.

Example:

```json
{
  "service_id": "identity-platform",
  "depends_on_type": "node",
  "depends_on_id": "backup-server",
  "redundancy_group": "identity-ha",
  "capacity_mbps": 250
}
```

Use the example dependency file to see two identity-platform alternatives and
a declared 300 Mbps service capacity requirement. Simulating loss of either
provider leaves 250 Mbps and correctly reports degraded service with active
failover; losing both makes the required dependency unavailable.
