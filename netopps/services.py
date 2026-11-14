"""Explainable, simulation-only institutional service dependency analysis."""
from __future__ import annotations

import math
from typing import Any

from netopps.topology import NetworkTopology, TopologyError

_CRITICALITY = {"low": 1.0, "standard": 1.5, "high": 2.5, "mission_critical": 4.0}


def analyze_service_dependencies(topology: NetworkTopology, document: Any,
                                 failed_nodes: set[str] | None = None,
                                 failed_links: set[str] | None = None,
                                 failed_sites: set[str] | None = None) -> dict[str, Any]:
    """Evaluate dependencies and trace each affected service to a failed root."""
    if not isinstance(document, dict):
        raise TopologyError("service dependency file must be an object")
    if set(document) != {"schema_version", "services", "dependencies"}:
        raise TopologyError("service dependency file must contain schema_version, services, and dependencies")
    if isinstance(document.get("schema_version"), bool) or document.get("schema_version") != 1:
        raise TopologyError("service dependency schema_version must be the integer 1")
    raw_services, raw_dependencies = document.get("services"), document.get("dependencies")
    if not isinstance(raw_services, list) or not isinstance(raw_dependencies, list):
        raise TopologyError("service dependency services and dependencies must be arrays")

    services: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(raw_services):
        allowed = {"id", "name", "criticality", "dependency_weight", "institution_id", "institution_name", "required_capacity_mbps", "rto_minutes", "rpo_minutes"}
        if not isinstance(item, dict) or set(item) - allowed:
            raise TopologyError(f"services[{index}] has invalid properties")
        identifier, name = item.get("id"), item.get("name")
        criticality, weight = item.get("criticality", "standard"), item.get("dependency_weight", 1.0)
        institution_id, institution_name = item.get("institution_id"), item.get("institution_name")
        required_capacity = item.get("required_capacity_mbps")
        rto_minutes, rpo_minutes = item.get("rto_minutes"), item.get("rpo_minutes")
        if not isinstance(identifier, str) or not identifier.strip():
            raise TopologyError(f"services[{index}].id must be a non-empty string")
        if identifier in services:
            raise TopologyError(f"duplicate service id: {identifier}")
        if not isinstance(name, str) or not name.strip():
            raise TopologyError(f"services[{index}].name must be a non-empty string")
        if not isinstance(criticality, str) or criticality not in _CRITICALITY:
            raise TopologyError(f"services[{index}].criticality must be low, standard, high, or mission_critical")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight) or not 0.1 <= weight <= 10.0:
            raise TopologyError(f"services[{index}].dependency_weight must be a finite number from 0.1 to 10.0")
        if required_capacity is not None and (isinstance(required_capacity, bool) or not isinstance(required_capacity, (int, float)) or not math.isfinite(required_capacity) or required_capacity <= 0):
            raise TopologyError(f"services[{index}].required_capacity_mbps must be a finite positive number")
        if rto_minutes is not None and (isinstance(rto_minutes, bool) or not isinstance(rto_minutes, (int, float)) or not math.isfinite(rto_minutes) or rto_minutes <= 0):
            raise TopologyError(f"services[{index}].rto_minutes must be a finite positive number")
        if rpo_minutes is not None and (isinstance(rpo_minutes, bool) or not isinstance(rpo_minutes, (int, float)) or not math.isfinite(rpo_minutes) or rpo_minutes < 0):
            raise TopologyError(f"services[{index}].rpo_minutes must be a finite non-negative number")
        if (institution_id is None) != (institution_name is None):
            raise TopologyError(f"services[{index}] must provide institution_id and institution_name together")
        if institution_id is not None and (
            not isinstance(institution_id, str) or not institution_id.strip()
            or not isinstance(institution_name, str) or not institution_name.strip()
        ):
            raise TopologyError(f"services[{index}] institution identity fields must be non-empty strings")
        services[identifier] = {
            "id": identifier, "name": name, "criticality": criticality,
            "dependency_weight": float(weight),
            "institution_id": institution_id, "institution_name": institution_name,
            "required_capacity_mbps": float(required_capacity) if required_capacity is not None else None,
            "rto_minutes": float(rto_minutes) if rto_minutes is not None else None,
            "rpo_minutes": float(rpo_minutes) if rpo_minutes is not None else None,
        }

    sites = {node.site for node in topology._nodes.values() if node.site}
    adjacency: dict[str, list[dict[str, Any]]] = {identifier: [] for identifier in services}
    service_edges: dict[str, set[str]] = {identifier: set() for identifier in services}
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(raw_dependencies):
        if not isinstance(item, dict) or set(item) - {"service_id", "depends_on_type", "depends_on_id", "required", "redundancy_group", "capacity_mbps", "failure_domains", "diversity_evidence"}:
            raise TopologyError(f"dependencies[{index}] has invalid properties")
        owner, kind, target = item.get("service_id"), item.get("depends_on_type"), item.get("depends_on_id")
        required = item.get("required", True)
        redundancy_group, capacity = item.get("redundancy_group"), item.get("capacity_mbps")
        failure_domains = item.get("failure_domains", [])
        diversity_evidence = item.get("diversity_evidence")
        if not isinstance(owner, str) or owner not in services:
            raise TopologyError(f"dependencies[{index}].service_id references an unknown service")
        if not isinstance(kind, str) or kind not in {"service", "node", "link", "site"}:
            raise TopologyError(f"dependencies[{index}].depends_on_type must be service, node, link, or site")
        if not isinstance(target, str) or not target.strip():
            raise TopologyError(f"dependencies[{index}].depends_on_id must be a non-empty string")
        if not isinstance(required, bool):
            raise TopologyError(f"dependencies[{index}].required must be a boolean")
        if redundancy_group is not None and (not isinstance(redundancy_group, str) or not redundancy_group.strip()):
            raise TopologyError(f"dependencies[{index}].redundancy_group must be a non-empty string")
        if capacity is not None and (isinstance(capacity, bool) or not isinstance(capacity, (int, float)) or not math.isfinite(capacity) or capacity <= 0):
            raise TopologyError(f"dependencies[{index}].capacity_mbps must be a finite positive number")
        if not isinstance(failure_domains, list) or any(not isinstance(value, str) or not value.strip() for value in failure_domains) or len(failure_domains) != len(set(failure_domains)):
            raise TopologyError(f"dependencies[{index}].failure_domains must be an array of unique non-empty strings")
        if failure_domains and kind == "service":
            raise TopologyError(f"dependencies[{index}].failure_domains can only annotate infrastructure dependencies")
        if diversity_evidence is not None:
            evidence_fields = {"evidence_ref", "evidence_type", "verification_status", "verified_at", "verified_by"}
            if not isinstance(diversity_evidence, dict) or set(diversity_evidence) - evidence_fields:
                raise TopologyError(f"dependencies[{index}].diversity_evidence has invalid properties")
            if diversity_evidence.get("verification_status") not in {"unverified", "documented", "independently_verified"}:
                raise TopologyError(f"dependencies[{index}].diversity_evidence.verification_status is invalid")
            if diversity_evidence.get("evidence_type") not in {"site_survey", "carrier_attestation", "route_trace", "power_audit", "failover_test", "other"}:
                raise TopologyError(f"dependencies[{index}].diversity_evidence.evidence_type is invalid")
            if not isinstance(diversity_evidence.get("evidence_ref"), str) or not diversity_evidence["evidence_ref"].strip():
                raise TopologyError(f"dependencies[{index}].diversity_evidence.evidence_ref must be non-empty")
            if diversity_evidence["verification_status"] == "independently_verified" and any(
                not isinstance(diversity_evidence.get(field), str) or not diversity_evidence[field].strip()
                for field in ("verified_at", "verified_by")
            ):
                raise TopologyError(f"dependencies[{index}] independently verified diversity evidence requires verified_at and verified_by")
        if kind == "service" and target not in services:
            raise TopologyError(f"dependencies[{index}] references an unknown service")
        if kind == "node" and target not in topology._nodes:
            raise TopologyError(f"dependencies[{index}] references an unknown node")
        if kind == "link" and target not in topology._links:
            raise TopologyError(f"dependencies[{index}] references an unknown link")
        if kind == "site" and target not in sites:
            raise TopologyError(f"dependencies[{index}] references an unknown site")
        key = (owner, kind, target)
        if key in seen:
            raise TopologyError(f"duplicate dependency: {owner} -> {kind}:{target}")
        seen.add(key)
        adjacency[owner].append({"type": kind, "id": target, "required": required,
                                 "redundancy_group": redundancy_group,
                                 "capacity_mbps": float(capacity) if capacity is not None else None,
                                 "failure_domains": sorted(failure_domains),
                                 "diversity_evidence": diversity_evidence})
        if kind == "service":
            service_edges[owner].add(target)

    remaining = {key: len(value) for key, value in service_edges.items()}
    dependents: dict[str, list[str]] = {key: [] for key in services}
    for owner, targets in service_edges.items():
        for target in targets:
            dependents[target].append(owner)
    ready = sorted(key for key, count in remaining.items() if count == 0)
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for dependent in sorted(dependents[current]):
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                ready.append(dependent)
                ready.sort()
    if len(order) != len(services):
        raise TopologyError("service dependency graph contains a cycle")

    nodes_down, sites_down = failed_nodes or set(), failed_sites or set()
    explicitly_down_links = (failed_links or set()) | {
        key for key, link in topology._links.items() if not link.enabled
    }
    endpoint_failed_links = {
        key for key, link in topology._links.items()
        if link.source in nodes_down or link.target in nodes_down
    }
    links_down = explicitly_down_links | endpoint_failed_links
    statuses: dict[str, dict[str, Any]] = {}

    for owner in order:
        failed: list[dict[str, Any]] = []
        unavailable = False
        degraded = False
        candidate_paths: set[tuple[tuple[str, str], ...]] = set()
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for offset, dependency in enumerate(adjacency[owner]):
            group_id = dependency["redundancy_group"]
            key = ("redundancy", group_id) if group_id is not None else ("single", str(offset))
            groups.setdefault(key, []).append(dependency)

        redundancy_results: list[dict[str, Any]] = []
        for group_key, members in sorted(groups.items()):
            evaluated: list[dict[str, Any]] = []
            for dependency in sorted(members, key=lambda value: (value["type"], value["id"])):
                kind, target, required = dependency["type"], dependency["id"], dependency["required"]
                target_status, reason = "available", ""
                if kind == "node" and target in nodes_down:
                    target_status, reason = "unavailable", "node_failed"
                elif kind == "link" and target in links_down:
                    target_status, reason = "unavailable", (
                        "link_endpoint_failed" if target in endpoint_failed_links else "link_failed"
                    )
                elif kind == "site" and target in sites_down:
                    target_status, reason = "unavailable", "site_failed"
                elif kind == "service":
                    target_status = statuses[target]["status"]
                    if target_status != "available":
                        reason = "supporting_service_" + target_status
                evaluated.append({**dependency, "status": target_status, "reason": reason})
            failed_members = [item for item in evaluated if item["status"] != "available"]
            operational = [item for item in evaluated if item["status"] != "unavailable"]
            is_group = group_key[0] == "redundancy"
            group_required = members[0]["required"]
            if is_group and any(item["required"] != group_required for item in members):
                raise TopologyError(f"redundancy group {group_key[1]!r} on service {owner!r} mixes required and optional members")
            for item in failed_members:
                failed.append({
                    "depends_on_type": item["type"], "depends_on_id": item["id"],
                    "required": item["required"], "status": item["status"],
                    "reason": item["reason"],
                    **({"redundancy_group": group_key[1]} if is_group else {}),
                })
                if item["type"] == "service":
                    inherited = statuses[item["id"]].get("_failure_paths", [])
                    for path in inherited:
                        candidate_paths.add((*path, ("service", owner)))
                else:
                    candidate_paths.add(((item["type"], item["id"]), ("service", owner)))

            active_capacity = (
                round(sum(item["capacity_mbps"] for item in operational), 6)
                if operational and all(item["capacity_mbps"] is not None for item in evaluated)
                else None
            )
            capacity_requirement = services[owner]["required_capacity_mbps"] if is_group else None
            capacity_shortfall = (
                capacity_requirement is not None and active_capacity is not None
                and active_capacity < capacity_requirement
            )
            if not operational:
                if group_required:
                    unavailable = True
                else:
                    degraded = True
            elif failed_members:
                # A surviving alternative preserves service, but redundancy has been consumed.
                degraded = True
            if capacity_shortfall:
                if active_capacity == 0:
                    unavailable = unavailable or group_required
                    degraded = degraded or not group_required
                else:
                    degraded = True
            redundancy_results.append({
                "group": group_key[1] if is_group else None,
                "required": group_required,
                "member_count": len(evaluated),
                "operational_member_count": len(operational),
                "failed_member_count": len(failed_members),
                "failover_active": bool(is_group and failed_members and operational),
                "remaining_capacity_mbps": active_capacity,
                "required_capacity_mbps": capacity_requirement,
                "capacity_adequate": (
                    active_capacity >= capacity_requirement
                    if active_capacity is not None and capacity_requirement is not None else None
                ),
            })

        state = "unavailable" if unavailable else "degraded" if degraded else "available"
        metadata = services[owner]
        priority = round(_CRITICALITY[metadata["criticality"]] * metadata["dependency_weight"], 6)
        paths = sorted(candidate_paths, key=lambda path: (len(path), path))
        public_paths = [
            [{"type": kind, "id": identifier} for kind, identifier in path]
            for path in paths
        ]
        statuses[owner] = {
            **metadata, "status": state, "failed_dependencies": failed,
            "redundancy": redundancy_results,
            "priority_weight": priority,
            "_failure_paths": paths,
            "failure_path": public_paths[0] if public_paths else [],
            "additional_failure_path_count": max(0, len(public_paths) - 1),
            "impact_scope": "direct" if paths and len(paths[0]) == 2 else "transitive" if paths else None,
        }

    ordered = sorted(statuses.values(), key=lambda item: (
        0 if item["status"] == "unavailable" else 1 if item["status"] == "degraded" else 2,
        -item["priority_weight"], item["id"],
    ))
    public_services = [{key: value for key, value in item.items() if key != "_failure_paths"}
                       for item in ordered]
    institution_groups: dict[str, dict[str, Any]] = {}
    for item in public_services:
        institution_id = item["institution_id"]
        if institution_id is None or item["status"] == "available":
            continue
        group = institution_groups.setdefault(institution_id, {
            "institution_id": institution_id, "institution_name": item["institution_name"],
            "affected_service_count": 0, "unavailable_count": 0, "degraded_count": 0,
            "weighted_impact": 0.0, "services": [],
        })
        if group["institution_name"] != item["institution_name"]:
            raise TopologyError(f"institution_id {institution_id!r} has conflicting names")
        group["affected_service_count"] += 1
        group["unavailable_count"] += item["status"] == "unavailable"
        group["degraded_count"] += item["status"] == "degraded"
        group["weighted_impact"] += item["priority_weight"]
        group["services"].append(item["id"])
    institutions = sorted(institution_groups.values(), key=lambda item: (
        -item["weighted_impact"], -item["unavailable_count"], item["institution_id"],
    ))
    for item in institutions:
        item["weighted_impact"] = round(item["weighted_impact"], 6)
        item["services"].sort()

    return {
        "mode": "simulation-only", "dependency_model": "NETOPPS-service-dependency-v1",
        "service_count": len(services),
        "unavailable_count": sum(item["status"] == "unavailable" for item in public_services),
        "degraded_count": sum(item["status"] == "degraded" for item in public_services),
        "available_count": sum(item["status"] == "available" for item in public_services),
        "affected_services": [item for item in public_services if item["status"] != "available"],
        "services": public_services, "affected_institutions": institutions,
        "topology_mutated": False,
    }
