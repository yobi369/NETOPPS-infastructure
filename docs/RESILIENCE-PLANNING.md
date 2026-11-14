# Resilience Optimization and Recovery Planning

## Purpose

The resilience planner turns NETOPPS' operator-declared topology and service dependency model into a ranked, explainable planning assessment. It is local, deterministic, read-only, and simulation-only.

## Run

```bash
netopps resilience-report examples/multi-site-topology.json examples/service-dependencies.json
netopps resilience-report examples/multi-site-topology.json examples/service-dependencies.json --candidate-dependencies examples/service-dependencies-candidate.json
# Export a self-contained executive HTML briefing
netopps resilience-report examples/multi-site-topology.json examples/service-dependencies.json --format html --output resilience-briefing.html
```

The default JSON output is machine-readable. Use --format html to render a self-contained, offline executive briefing; add --output FILE to write it to a file instead of stdout. The HTML report includes summary metrics, dependency risks, correlated failures, diversity evidence status, recovery priorities, capacity gaps, candidate comparisons, and model limitations. It uses no external scripts, stylesheets, fonts, images, or network calls and escapes all model-supplied text.

The JSON report contains the following sections. To compare a concrete proposal, pass `--candidate-dependencies` with a second valid version-1 service dependency document. The report then compares baseline and candidate service-state counts, weighted affected-service priority, and modeled capacity-gap counts; negative impact/gap deltas indicate modeled improvement.

The command emits JSON with:

- **Executive assessment:** baseline service state counts, highest-risk failure domain, leading conditional recommendation, capacity-gap counts, and first recovery priority.
- **Weakest dependencies:** one-at-a-time node, link, and site failure scenarios, ranked by affected service priority weight and unavailable-service count.
- **Redundancy recommendations:** proposed design work to add an explicitly modeled alternative. The avoided impact is conditional on independence, support coverage, successful failover, and sufficient capacity.
- **Capacity assessment:** capacity shortfalls observed in modeled failure states, computed from declared redundancy member capacities and the service's declared required capacity. Missing inputs remain unknown.
- **Correlated failure scenarios:** each declared `failure_domains` label is failed as a shared cause across all tagged nodes, links, and sites.
- **Physical diversity assessment:** redundancy members are compared for shared failure-domain labels and linked to operator-supplied evidence records.
- **Recovery priorities:** deterministic ordering by service criticality and dependency weight, then tighter declared RTO/RPO objectives; missing objectives remain unset.

## Interpretation

A failure domain is tested individually; the planner does not infer failure probabilities. `weighted_impact` is the sum of declared service priority weights for services that become degraded or unavailable in that scenario. It is not a financial loss, outage duration, or probability.

A redundancy recommendation is not a generated network design or an assertion that an alternate provider exists. Operators must identify a genuinely independent alternative, validate its technical compatibility, declare its capacity, and add it to a candidate dependency document. The existing topology and dependency document are never changed by the report.

Capacity gaps are meaningful only when both `required_capacity_mbps` and every relevant redundancy member's `capacity_mbps` are supplied. Unknown capacity is not treated as zero and is not estimated from link bandwidth.

Services may optionally declare `rto_minutes` (positive) and `rpo_minutes` (non-negative). These are institution-defined recovery targets, not measured recovery performance. They are surfaced in recovery priorities and used as tie-breakers after declared service priority. NETOPPS never invents missing objectives.

Infrastructure dependency edges may declare `failure_domains`, a list of shared-cause labels such as `power:shared-grid` or `carrier:carrier-a`. Every asset tagged with the same label is failed together in a correlated scenario. These labels are operator declarations; incomplete labels hide real common causes. A redundancy group is flagged when members share any declared failure domain.

A `diversity_evidence` record can include `evidence_ref`, `evidence_type`, `verification_status`, and (for `independently_verified`) `verified_at` and `verified_by`. The report distinguishes shared-domain overlap, missing independent evidence, and operator-recorded independent evidence. Evidence references and verification labels are not fetched, checked, or authenticated by NETOPPS. A status of `operator_recorded_independent_evidence` is not a NETOPPS certification of physical separation.

Recovery priorities express a suggested order for restoration planning from declared criticality, dependency weight, RTO, and RPO. They do not encode staffing, spare-part availability, restoration duration, legal obligations, or business continuity plans.

## Safety and model limits

- No network I/O, discovery, telemetry ingestion, configuration change, or live failover is performed.
- Correlated scenarios fail all assets carrying the same declared failure-domain label; other simultaneous or unknown common-cause failures remain outside the model.
- Declared site labels and diversity evidence do not prove geographic, power, conduit, provider-ownership, or control-plane independence.
- Declared provider alternatives do not prove separate ownership, conduits, upstream carriers, DNS, identity, or control planes.
- No SLA compliance, outage probability, restoration time, or operational readiness is asserted.

For stronger evidence, validate proposed designs in an authorized lab and incorporate verified physical diversity, measured throughput, failover tests, and institution-approved recovery objectives.
