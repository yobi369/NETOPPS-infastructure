"""Deterministic resilience optimization and recovery planning (simulation-only)."""
from __future__ import annotations

from typing import Any

from netopps.services import analyze_service_dependencies
from netopps.topology import NetworkTopology, TopologyError


def analyze_resilience(topology: NetworkTopology, dependencies: Any) -> dict[str, Any]:
    """Rank weak institutional dependencies and model planning opportunities.

    Recommendations are hypotheses: the planner cannot invent an alternate asset,
    prove physical diversity, or assert that a proposed provider has capacity.
    """
    if not isinstance(dependencies, dict):
        raise TopologyError("dependency document must be an object")
    baseline = analyze_service_dependencies(topology, dependencies)
    services = {item["id"]: item for item in baseline["services"]}
    raw_edges = dependencies.get("dependencies", [])
    scenarios: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in raw_edges:
        kind, target = edge.get("depends_on_type"), edge.get("depends_on_id")
        if kind not in {"node", "link", "site"}:
            continue
        key = (kind, target)
        if key in scenarios:
            continue
        failed = analyze_service_dependencies(
            topology, dependencies,
            failed_nodes={target} if kind == "node" else None,
            failed_links={target} if kind == "link" else None,
            failed_sites={target} if kind == "site" else None,
        )
        affected = failed["affected_services"]
        scenarios[key] = {
            "dependency": {"type": kind, "id": target},
            "affected_services": [item["id"] for item in affected],
            "unavailable_services": [item["id"] for item in affected if item["status"] == "unavailable"],
            "degraded_services": [item["id"] for item in affected if item["status"] == "degraded"],
            "weighted_impact": round(sum(item["priority_weight"] for item in affected), 6),
            "institution_ids": sorted({item["institution_id"] for item in affected if item["institution_id"]}),
        }

    weaknesses = sorted(scenarios.values(), key=lambda item: (
        -item["weighted_impact"], -len(item["unavailable_services"]),
        item["dependency"]["type"], item["dependency"]["id"],
    ))
    recommendations: list[dict[str, Any]] = []
    for item in weaknesses:
        if not item["affected_services"]:
            continue
        impacted = [services[identifier] for identifier in item["affected_services"]]
        priority = max((service["priority_weight"] for service in impacted), default=0.0)
        recommendations.append({
            "priority": "critical" if any(s["criticality"] == "mission_critical" for s in impacted) else "high",
            "protect_dependency": item["dependency"],
            "affected_services": item["affected_services"],
            "affected_institutions": item["institution_ids"],
            "modeled_weighted_impact": item["weighted_impact"],
            "recommended_action": (
                "Design and validate an independent alternative, then model it in an explicit "
                "redundancy_group with declared capacity and required_capacity_mbps."
            ),
            "potential_avoided_weighted_impact_if_validated": item["weighted_impact"],
            "assumptions": [
                "The alternative is genuinely independent of the protected failure domain.",
                "The alternative supports every listed affected service.",
                "Failover works and capacity is sufficient.",
            ],
            "priority_weight_of_most_critical_affected_service": priority,
        })

    capacity_gaps: list[dict[str, Any]] = []
    for service in baseline["services"]:
        for group in service["redundancy"]:
            required = group["required_capacity_mbps"]
            available = group["remaining_capacity_mbps"]
            if required is not None and available is not None and available < required:
                capacity_gaps.append({
                    "service_id": service["id"], "service_name": service["name"],
                    "redundancy_group": group["group"],
                    "required_capacity_mbps": required,
                    "declared_available_capacity_mbps": available,
                    "capacity_gap_mbps": round(required - available, 6),
                })
            elif required is not None and available is None:
                capacity_gaps.append({
                    "service_id": service["id"], "service_name": service["name"],
                    "redundancy_group": group["group"],
                    "required_capacity_mbps": required,
                    "declared_available_capacity_mbps": None,
                    "capacity_gap_mbps": None,
                    "status": "unknown_incomplete_capacity_inputs",
                })

    recovery = sorted(baseline["services"], key=lambda item: (
        -item["priority_weight"],
        0 if item["criticality"] == "mission_critical" else 1,
        0 if item["status"] == "unavailable" else 1 if item["status"] == "degraded" else 2,
        item["id"],
    ))
    recovery_priorities = [{
        "rank": index,
        "service_id": item["id"],
        "service_name": item["name"],
        "institution_id": item["institution_id"],
        "institution_name": item["institution_name"],
        "criticality": item["criticality"],
        "priority_weight": item["priority_weight"],
        "baseline_status": item["status"],
        "recovery_reason": (
            "Highest declared criticality/dependency weight"
            if item["criticality"] == "mission_critical"
            else "Ranked by declared criticality and dependency weight"
        ),
    } for index, item in enumerate(recovery, 1)]

    baseline_affected = baseline["unavailable_count"] + baseline["degraded_count"]
    executive = {
        "headline": (
            f"{len(weaknesses)} infrastructure dependency failure domains assessed; "
            f"{baseline_affected} services are degraded or unavailable in the baseline."
        ),
        "baseline": {
            "service_count": baseline["service_count"],
            "available": baseline["available_count"],
            "degraded": baseline["degraded_count"],
            "unavailable": baseline["unavailable_count"],
        },
        "highest_risk_dependency": weaknesses[0]["dependency"] if weaknesses else None,
        "top_recommendation": recommendations[0] if recommendations else None,
        "capacity_gap_count": sum(gap.get("capacity_gap_mbps") is not None for gap in capacity_gaps),
        "unknown_capacity_count": sum(gap.get("capacity_gap_mbps") is None for gap in capacity_gaps),
        "first_recovery_priority": recovery_priorities[0] if recovery_priorities else None,
    }
    return {
        "mode": "simulation-only",
        "report_type": "institutional-resilience-and-recovery-plan",
        "model_version": 1,
        "executive_assessment": executive,
        "baseline_service_resilience": baseline,
        "weakest_dependencies": weaknesses,
        "redundancy_recommendations": recommendations,
        "capacity_assessment": capacity_gaps,
        "recovery_priorities": recovery_priorities,
        "scenario_comparison": {
            "baseline_affected_service_count": baseline_affected,
            "single_dependency_failure_scenarios": len(weaknesses),
            "proposed_change_results": "not_asserted_without_a_concrete_candidate_dependency_and_capacity",
            "comparison_method": (
                "Each declared infrastructure dependency is failed individually. "
                "Recommendation impact is the modeled service priority weight exposed "
                "to that failure, not a guaranteed benefit."
            ),
        },
        "limitations": [
            "Inputs are operator-declared and are not live telemetry.",
            "Single-failure scenarios do not model correlated or simultaneous failures.",
            "Redundancy benefit is conditional on physical independence, successful failover, and sufficient capacity.",
            "No recovery-time objective, restoration duration, or SLA is inferred.",
            "Unknown capacity remains unknown; the planner does not invent values.",
        ],
        "topology_mutated": False,
        "dependency_document_mutated": False,
    }
