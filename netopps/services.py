"""Explicit, simulation-only service dependency graph analysis."""
from __future__ import annotations

import math
from typing import Any

from netopps.topology import NetworkTopology, TopologyError

_CRITICALITY = {"low": 1.0, "standard": 1.5, "high": 2.5, "mission_critical": 4.0}


def analyze_service_dependencies(topology: NetworkTopology, document: Any,
                                 failed_nodes: set[str] | None = None,
                                 failed_links: set[str] | None = None,
                                 failed_sites: set[str] | None = None) -> dict[str, Any]:
    """Evaluate declared dependencies against one simulated failure state."""
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
        if not isinstance(item, dict) or set(item) - {"id", "name", "criticality", "dependency_weight"}:
            raise TopologyError(f"services[{index}] has invalid properties")
        identifier, name = item.get("id"), item.get("name")
        criticality, weight = item.get("criticality", "standard"), item.get("dependency_weight", 1.0)
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
        services[identifier] = {"id": identifier, "name": name, "criticality": criticality, "dependency_weight": float(weight)}
    sites = {node.site for node in topology._nodes.values() if node.site}
    adjacency: dict[str, list[dict[str, Any]]] = {identifier: [] for identifier in services}
    service_edges: dict[str, set[str]] = {identifier: set() for identifier in services}
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(raw_dependencies):
        if not isinstance(item, dict) or set(item) - {"service_id", "depends_on_type", "depends_on_id", "required"}:
            raise TopologyError(f"dependencies[{index}] has invalid properties")
        owner, kind, target = item.get("service_id"), item.get("depends_on_type"), item.get("depends_on_id")
        required = item.get("required", True)
        if not isinstance(owner, str) or owner not in services:
            raise TopologyError(f"dependencies[{index}].service_id references an unknown service")
        if not isinstance(kind, str) or kind not in {"service", "node", "link", "site"}:
            raise TopologyError(f"dependencies[{index}].depends_on_type must be service, node, link, or site")
        if not isinstance(target, str) or not target.strip():
            raise TopologyError(f"dependencies[{index}].depends_on_id must be a non-empty string")
        if not isinstance(required, bool):
            raise TopologyError(f"dependencies[{index}].required must be a boolean")
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
        adjacency[owner].append({"type": kind, "id": target, "required": required})
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
        for dependency in sorted(adjacency[owner], key=lambda value: (value["type"], value["id"])):
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
            if target_status != "available":
                failed.append({"depends_on_type": kind, "depends_on_id": target, "required": required, "status": target_status, "reason": reason})
                if required and target_status == "unavailable":
                    unavailable = True
                else:
                    degraded = True
        state = "unavailable" if unavailable else "degraded" if degraded else "available"
        metadata = services[owner]
        statuses[owner] = {**metadata, "status": state, "failed_dependencies": failed,
                           "priority_weight": round(_CRITICALITY[metadata["criticality"]] * metadata["dependency_weight"], 6)}
    ordered = sorted(statuses.values(), key=lambda item: (
        0 if item["status"] == "unavailable" else 1 if item["status"] == "degraded" else 2,
        -item["priority_weight"], item["id"],
    ))
    return {
        "mode": "simulation-only", "dependency_model": "NETOPPS-service-dependency-v1",
        "service_count": len(services),
        "unavailable_count": sum(item["status"] == "unavailable" for item in ordered),
        "degraded_count": sum(item["status"] == "degraded" for item in ordered),
        "available_count": sum(item["status"] == "available" for item in ordered),
        "affected_services": [item for item in ordered if item["status"] != "available"],
        "services": ordered, "topology_mutated": False,
    }