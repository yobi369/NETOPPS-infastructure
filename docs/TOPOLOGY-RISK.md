# Topology Diff and Structural Risk

## Topology comparison

Run:

    netopps topology-diff examples/topology.json examples/topology-candidate.json

The command compares stable node and link IDs and reports additions, removals, and attribute changes. Node `role` and `site` values are compared. Link endpoint pairs are canonicalized because links are undirected; a source/target reversal alone is not a change. Link latency, declared capacity, and enabled state are compared. Changing an object's ID is represented as a removal plus an addition.

The comparison is deterministic and does not modify either input.

## Structural risk analysis

Run:

    netopps topology-risk examples/topology.json

The model uses iterative graph traversal to identify:
- **Articulation nodes:** removing the node would split a previously connected component.
- **Bridge links:** removing the link would split a previously connected component.
- **Disconnected components:** groups with no active modeled path between them.
- **Isolated nodes:** nodes with no active modeled links.

## Score model: NETOPPS-structural-fragility-v1

The 0–100 score is the sum of four capped factor contributions:

| Factor | Points | Cap |
|---|---:|---:|
| Each component beyond the first | 12.5 | 25 |
| Each articulation node | 10 | 30 |
| Each bridge link | 5 | 25 |
| Each isolated node | 5 | 20 |

The final score is capped at 100. Severity bands are:
- 0–24.9: low
- 25–49.9: guarded
- 50–74.9: elevated
- 75–100: critical

Every factor includes its points, evidence IDs or component membership, and a rationale in the JSON result. The score is deterministic for a given topology and model version.

## Interpretation limits

This is a structural-fragility prioritization heuristic, not an outage probability, service-level estimate, cyber-risk rating, or measured operational risk. It does not model device reliability, shared power, geographic hazards, routing protocols, failover timers, redundancy quality, traffic criticality, or observed telemetry. A bridge link is structurally important in this graph, but may have a tested backup outside the supplied model. Conversely, an apparently redundant graph may share a common physical failure domain not represented in the input.

Use the score to identify questions for an engineer, not to automatically approve or reject a network design. Keep topology inputs synthetic or sanitized; do not commit production network details.
