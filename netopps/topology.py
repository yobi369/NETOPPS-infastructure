"""Deterministic, simulation-only network digital twin primitives.

This module models operator-supplied topology data. It never discovers devices,
opens sockets, persists state, or changes a live network.
"""
from __future__ import annotations

import heapq
import math
from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Node:
    """A logical network node in the digital twin."""
    id: str
    role: str = "unknown"
    site: str = ""

@dataclass(frozen=True, slots=True)
class Link:
    """An undirected logical link with simulation attributes."""
    id: str
    source: str
    target: str
    latency_ms: float
    capacity_mbps: float
    enabled: bool = True

class TopologyError(ValueError):
    """Raised when a topology document is malformed or ambiguous."""

class NetworkTopology:
    """Immutable topology model with deterministic graph analysis."""
    def __init__(self, nodes: tuple[Node, ...], links: tuple[Link, ...]) -> None:
        self._nodes = {node.id: node for node in nodes}
        self._links = {link.id: link for link in links}
        self._ordered_node_ids = tuple(sorted(self._nodes))
        self._ordered_links = tuple(sorted(self._links.values(), key=lambda item: item.id))

    @classmethod
    def from_dict(cls, document: Any) -> NetworkTopology:
        """Build a topology from a JSON-compatible mapping."""
        if not isinstance(document, dict):
            raise TopologyError("topology must be an object")
        unknown = set(document) - {"schema_version", "nodes", "links"}
        if unknown:
            raise TopologyError(f"unknown topology properties: {', '.join(sorted(unknown))}")
        version = document.get("schema_version")
        if isinstance(version, bool) or version != 1:
            raise TopologyError("schema_version must be the integer 1")
        raw_nodes, raw_links = document.get("nodes"), document.get("links")
        if not isinstance(raw_nodes, list) or not isinstance(raw_links, list):
            raise TopologyError("nodes and links must both be arrays")

        nodes: list[Node] = []
        node_ids: set[str] = set()
        for index, item in enumerate(raw_nodes):
            if not isinstance(item, dict):
                raise TopologyError(f"nodes[{index}] must be an object")
            identifier = item.get("id")
            role, site = item.get("role", "unknown"), item.get("site", "")
            if not isinstance(identifier, str) or not identifier.strip():
                raise TopologyError(f"nodes[{index}].id must be a non-empty string")
            if identifier in node_ids:
                raise TopologyError(f"duplicate node id: {identifier}")
            if not isinstance(role, str) or not isinstance(site, str):
                raise TopologyError(f"nodes[{index}] role and site must be strings")
            node_ids.add(identifier)
            nodes.append(Node(identifier, role, site))

        links: list[Link] = []
        link_ids: set[str] = set()
        for index, item in enumerate(raw_links):
            if not isinstance(item, dict):
                raise TopologyError(f"links[{index}] must be an object")
            identifier, source, target = item.get("id"), item.get("source"), item.get("target")
            if not isinstance(identifier, str) or not identifier.strip():
                raise TopologyError(f"links[{index}].id must be a non-empty string")
            if identifier in link_ids:
                raise TopologyError(f"duplicate link id: {identifier}")
            if not isinstance(source, str) or source not in node_ids:
                raise TopologyError(f"links[{index}].source references an unknown node")
            if not isinstance(target, str) or target not in node_ids:
                raise TopologyError(f"links[{index}].target references an unknown node")
            if source == target:
                raise TopologyError(f"links[{index}] cannot connect a node to itself")
            latency, capacity = item.get("latency_ms"), item.get("capacity_mbps")
            enabled = item.get("enabled", True)
            if (isinstance(latency, bool) or not isinstance(latency, (int, float))
                    or not math.isfinite(latency) or latency < 0):
                raise TopologyError(f"links[{index}].latency_ms must be a finite non-negative number")
            if (isinstance(capacity, bool) or not isinstance(capacity, (int, float))
                    or not math.isfinite(capacity) or capacity <= 0):
                raise TopologyError(f"links[{index}].capacity_mbps must be a finite positive number")
            if not isinstance(enabled, bool):
                raise TopologyError(f"links[{index}].enabled must be a boolean")
            link_ids.add(identifier)
            links.append(Link(identifier, source, target, float(latency), float(capacity), enabled))
        return cls(tuple(nodes), tuple(links))

    @property
    def node_ids(self) -> tuple[str, ...]:
        """Return node identifiers in stable order."""
        return self._ordered_node_ids

    @property
    def link_ids(self) -> tuple[str, ...]:
        """Return link identifiers in stable order."""
        return tuple(link.id for link in self._ordered_links)

    def _adjacency(self, disabled_nodes: frozenset[str] = frozenset(),
                   disabled_links: frozenset[str] = frozenset()) -> dict[str, list[tuple[str, Link]]]:
        unknown_nodes = disabled_nodes - self._nodes.keys()
        unknown_links = disabled_links - self._links.keys()
        if unknown_nodes:
            raise TopologyError(f"unknown disabled nodes: {', '.join(sorted(unknown_nodes))}")
        if unknown_links:
            raise TopologyError(f"unknown disabled links: {', '.join(sorted(unknown_links))}")
        graph = {node_id: [] for node_id in self._ordered_node_ids if node_id not in disabled_nodes}
        for link in self._ordered_links:
            if not link.enabled or link.id in disabled_links:
                continue
            if link.source in disabled_nodes or link.target in disabled_nodes:
                continue
            graph[link.source].append((link.target, link))
            graph[link.target].append((link.source, link))
        for neighbors in graph.values():
            neighbors.sort(key=lambda item: (item[0], item[1].id))
        return graph

    @staticmethod
    def _components(graph: dict[str, list[tuple[str, Link]]]) -> list[list[str]]:
        unseen = set(graph)
        components: list[list[str]] = []
        while unseen:
            start = min(unseen)
            queue = deque([start])
            unseen.remove(start)
            component: list[str] = []
            while queue:
                current = queue.popleft()
                component.append(current)
                for neighbor, _link in graph[current]:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        queue.append(neighbor)
            components.append(sorted(component))
        return sorted(components, key=lambda component: component[0])

    def report(self) -> dict[str, Any]:
        """Return stable summary metrics for the modeled topology."""
        graph = self._adjacency()
        components = self._components(graph)
        active_links = [link for link in self._ordered_links if link.enabled]
        degree = {node_id: len(graph[node_id]) for node_id in self._ordered_node_ids}
        return {
            "mode": "simulation-only", "node_count": len(self._nodes),
            "link_count": len(self._links), "active_link_count": len(active_links),
            "component_count": len(components), "components": components,
            "isolated_nodes": [node_id for node_id, count in degree.items() if count == 0],
            "average_degree": round(sum(degree.values()) / len(degree), 3) if degree else 0.0,
            "total_declared_capacity_mbps": round(sum(link.capacity_mbps for link in active_links), 3),
        }

    def shortest_path(self, source: str, target: str) -> dict[str, Any] | None:
        """Find the lowest-latency path; return None when no route exists."""
        if source not in self._nodes or target not in self._nodes:
            raise TopologyError("source and target must be known node identifiers")
        if source == target:
            return {"nodes": [source], "links": [], "latency_ms": 0.0}
        graph = self._adjacency()
        distances = {source: 0.0}
        previous: dict[str, tuple[str, str]] = {}
        queue: list[tuple[float, str]] = [(0.0, source)]
        visited: set[str] = set()
        while queue:
            distance, current = heapq.heappop(queue)
            if current in visited:
                continue
            visited.add(current)
            if current == target:
                break
            for neighbor, link in graph[current]:
                candidate = distance + link.latency_ms
                if candidate < distances.get(neighbor, math.inf):
                    distances[neighbor] = candidate
                    previous[neighbor] = (current, link.id)
                    heapq.heappush(queue, (candidate, neighbor))
        if target not in distances:
            return None
        path_nodes, path_links = [target], []
        current = target
        while current != source:
            parent, link_id = previous[current]
            path_nodes.append(parent)
            path_links.append(link_id)
            current = parent
        return {"nodes": list(reversed(path_nodes)), "links": list(reversed(path_links)),
                "latency_ms": round(distances[target], 6)}



    def compare(self, candidate: NetworkTopology) -> dict[str, Any]:
        """Return a deterministic, identity-based diff against another topology."""
        if not isinstance(candidate, NetworkTopology):
            raise TopologyError("candidate must be a NetworkTopology")

        baseline_nodes = self._nodes
        candidate_nodes = candidate._nodes
        added_nodes = sorted(candidate_nodes.keys() - baseline_nodes.keys())
        removed_nodes = sorted(baseline_nodes.keys() - candidate_nodes.keys())
        changed_nodes = []
        for identifier in sorted(baseline_nodes.keys() & candidate_nodes.keys()):
            before, after = baseline_nodes[identifier], candidate_nodes[identifier]
            changes = {}
            for field in ("role", "site"):
                old_value, new_value = getattr(before, field), getattr(after, field)
                if old_value != new_value:
                    changes[field] = {"before": old_value, "after": new_value}
            if changes:
                changed_nodes.append({"id": identifier, "changes": changes})

        def link_state(link: Link) -> dict[str, Any]:
            return {
                "endpoints": sorted((link.source, link.target)),
                "latency_ms": link.latency_ms,
                "capacity_mbps": link.capacity_mbps,
                "enabled": link.enabled,
            }

        baseline_links = self._links
        candidate_links = candidate._links
        added_links = [
            {"id": identifier, **link_state(candidate_links[identifier])}
            for identifier in sorted(candidate_links.keys() - baseline_links.keys())
        ]
        removed_links = [
            {"id": identifier, **link_state(baseline_links[identifier])}
            for identifier in sorted(baseline_links.keys() - candidate_links.keys())
        ]
        changed_links = []
        for identifier in sorted(baseline_links.keys() & candidate_links.keys()):
            before, after = link_state(baseline_links[identifier]), link_state(candidate_links[identifier])
            changes = {
                field: {"before": before[field], "after": after[field]}
                for field in before if before[field] != after[field]
            }
            if changes:
                changed_links.append({"id": identifier, "changes": changes})

        summary = {
            "nodes_added": len(added_nodes), "nodes_removed": len(removed_nodes),
            "nodes_changed": len(changed_nodes), "links_added": len(added_links),
            "links_removed": len(removed_links), "links_changed": len(changed_links),
        }
        return {
            "mode": "simulation-only", "comparison": "baseline-to-candidate",
            "summary": summary,
            "nodes": {
                "added": added_nodes, "removed": removed_nodes, "changed": changed_nodes,
            },
            "links": {
                "added": added_links, "removed": removed_links, "changed": changed_links,
            },
            "topology_mutated": False,
        }

    def _critical_elements(self) -> tuple[list[str], list[str]]:
        """Find articulation nodes and bridge links with iterative Tarjan traversal."""
        graph = self._adjacency()
        discovery: dict[str, int] = {}
        low: dict[str, int] = {}
        parent: dict[str, str | None] = {}
        parent_edge: dict[str, str | None] = {}
        child_count: dict[str, int] = {}
        articulation: set[str] = set()
        bridges: set[str] = set()
        clock = 0

        for root in self._ordered_node_ids:
            if root in discovery:
                continue
            parent[root] = None
            parent_edge[root] = None
            child_count[root] = 0
            discovery[root] = low[root] = clock
            clock += 1
            stack: list[tuple[str, int]] = [(root, 0)]

            while stack:
                current, offset = stack[-1]
                neighbors = graph[current]
                if offset < len(neighbors):
                    neighbor, link = neighbors[offset]
                    stack[-1] = (current, offset + 1)
                    if link.id == parent_edge[current]:
                        continue
                    if neighbor not in discovery:
                        parent[neighbor] = current
                        parent_edge[neighbor] = link.id
                        child_count[neighbor] = 0
                        child_count[current] += 1
                        discovery[neighbor] = low[neighbor] = clock
                        clock += 1
                        stack.append((neighbor, 0))
                    else:
                        low[current] = min(low[current], discovery[neighbor])
                    continue

                stack.pop()
                ancestor = parent[current]
                if ancestor is None:
                    if child_count[current] > 1:
                        articulation.add(current)
                    continue

                low[ancestor] = min(low[ancestor], low[current])
                if parent[ancestor] is not None and low[current] >= discovery[ancestor]:
                    articulation.add(ancestor)
                if low[current] > discovery[ancestor]:
                    bridge_id = parent_edge[current]
                    if bridge_id is not None:
                        bridges.add(bridge_id)

        return sorted(articulation), sorted(bridges)

    def risk_report(self) -> dict[str, Any]:
        """Calculate a transparent rule-based topology fragility score (0-100)."""
        topology = self.report()
        articulation_nodes, bridge_links = self._critical_elements()
        isolated_nodes = topology["isolated_nodes"]
        component_count = topology["component_count"]

        fragmentation_points = min(25.0, max(0, component_count - 1) * 12.5)
        articulation_points = min(30.0, len(articulation_nodes) * 10.0)
        bridge_points = min(25.0, len(bridge_links) * 5.0)
        isolation_points = min(20.0, len(isolated_nodes) * 5.0)
        factors = [
            {
                "factor": "network_fragmentation", "points": fragmentation_points,
                "evidence": {"component_count": component_count, "components": topology["components"]},
                "rationale": "Multiple disconnected components reduce end-to-end reachability.",
            },
            {
                "factor": "articulation_nodes", "points": articulation_points,
                "evidence": {"node_ids": articulation_nodes},
                "rationale": "Removing an articulation node would split at least one connected component.",
            },
            {
                "factor": "bridge_links", "points": bridge_points,
                "evidence": {"link_ids": bridge_links},
                "rationale": "Removing a bridge link would split at least one connected component.",
            },
            {
                "factor": "isolated_nodes", "points": isolation_points,
                "evidence": {"node_ids": isolated_nodes},
                "rationale": "Isolated nodes have no active modeled path to other nodes.",
            },
        ]
        score = round(min(100.0, sum(item["points"] for item in factors)), 1)
        severity = (
            "low" if score < 25 else "guarded" if score < 50
            else "elevated" if score < 75 else "critical"
        )
        return {
            "mode": "simulation-only", "risk_model": "NETOPPS-structural-fragility-v1",
            "score": score, "severity": severity, "scale": "0-100 rule-based points; not a probability",
            "factors": factors,
            "critical_nodes": articulation_nodes, "critical_links": bridge_links,
            "topology_mutated": False,
        }

    def simulate_traffic(self, demands: Any) -> dict[str, Any]:
        """Route modeled traffic demands and estimate declared-link capacity pressure."""
        if not isinstance(demands, list):
            raise TopologyError("traffic demands must be an array")
        seen_ids: set[str] = set()
        loads = {link.id: 0.0 for link in self._ordered_links}
        demand_results: list[dict[str, Any]] = []
        total_requested = 0.0
        total_routed = 0.0

        for index, demand in enumerate(demands):
            if not isinstance(demand, dict):
                raise TopologyError(f"demands[{index}] must be an object")
            unknown = set(demand) - {"id", "source", "target", "demand_mbps"}
            if unknown:
                raise TopologyError(f"demands[{index}] has unknown properties")
            identifier = demand.get("id")
            source, target = demand.get("source"), demand.get("target")
            rate = demand.get("demand_mbps")
            if not isinstance(identifier, str) or not identifier.strip():
                raise TopologyError(f"demands[{index}].id must be a non-empty string")
            if identifier in seen_ids:
                raise TopologyError(f"duplicate traffic demand id: {identifier}")
            if not isinstance(source, str) or source not in self._nodes:
                raise TopologyError(f"demands[{index}].source references an unknown node")
            if not isinstance(target, str) or target not in self._nodes:
                raise TopologyError(f"demands[{index}].target references an unknown node")
            if (isinstance(rate, bool) or not isinstance(rate, (int, float))
                    or not math.isfinite(rate) or rate <= 0):
                raise TopologyError(f"demands[{index}].demand_mbps must be a finite positive number")
            seen_ids.add(identifier)
            total_requested += float(rate)
            route = self.shortest_path(source, target)
            if route is None:
                demand_results.append({
                    "id": identifier, "status": "unroutable",
                    "source": source, "target": target, "demand_mbps": float(rate),
                })
                continue
            total_routed += float(rate)
            for link_id in route["links"]:
                loads[link_id] += float(rate)
            demand_results.append({
                "id": identifier, "status": "routed", "source": source,
                "target": target, "demand_mbps": float(rate), "path": route,
            })

        link_results = []
        for link in self._ordered_links:
            carried = loads[link.id]
            utilization = carried / link.capacity_mbps * 100 if link.enabled else 0.0
            overloaded = max(0.0, carried - link.capacity_mbps) if link.enabled else 0.0
            link_results.append({
                "id": link.id, "enabled": link.enabled,
                "carried_mbps": round(carried, 6),
                "capacity_mbps": link.capacity_mbps,
                "utilization_pct": round(utilization, 3),
                "overloaded_mbps": round(overloaded, 6),
                "status": "disabled" if not link.enabled else (
                    "congested" if overloaded > 0 else "within_capacity"
                ),
            })

        return {
            "mode": "simulation-only",
            "routing_policy": "lowest-latency single path per demand",
            "demand_count": len(demand_results),
            "total_requested_mbps": round(total_requested, 6),
            "total_routed_mbps": round(total_routed, 6),
            "unroutable_demand_count": sum(item["status"] == "unroutable" for item in demand_results),
            "congested_link_count": sum(item["status"] == "congested" for item in link_results),
            "demands": sorted(demand_results, key=lambda item: item["id"]),
            "links": link_results,
            "topology_mutated": False,
        }


    def _scenario_traffic_impact(
        self, remaining_topology: NetworkTopology, demands: list[dict[str, Any]],
        failed_nodes: set[str],
    ) -> dict[str, Any]:
        """Measure modeled demand impact after a failure without live traffic."""
        baseline = self.simulate_traffic(demands)
        surviving_demands = [
            demand for demand in demands
            if demand["source"] not in failed_nodes and demand["target"] not in failed_nodes
        ]
        after = remaining_topology.simulate_traffic(surviving_demands)
        after_by_id = {item["id"]: item for item in after["demands"]}
        baseline_by_id = {item["id"]: item for item in baseline["demands"]}
        affected: list[dict[str, Any]] = []
        endpoint_unavailable_count = 0
        unroutable_after_count = 0

        for demand in sorted(demands, key=lambda item: item["id"]):
            identifier = demand["id"]
            before_status = baseline_by_id[identifier]["status"]
            if demand["source"] in failed_nodes or demand["target"] in failed_nodes:
                after_status = "endpoint_unavailable"
                reason = "source_or_target_node_failed"
                endpoint_unavailable_count += 1
            else:
                after_status = after_by_id[identifier]["status"]
                reason = "no_surviving_route" if after_status == "unroutable" else ""
            if after_status != "routed":
                unroutable_after_count += 1
            if before_status == "routed" and after_status != "routed":
                affected.append({
                    "id": identifier, "status_after_failure": after_status,
                    "reason": reason, "demand_mbps": float(demand["demand_mbps"]),
                })

        return {
            "mode": "simulation-only",
            "demand_count": len(demands),
            "endpoint_unavailable_count": endpoint_unavailable_count,
            "unroutable_after_failure_count": unroutable_after_count,
            "newly_affected_demand_count": len(affected),
            "newly_affected_mbps": round(sum(item["demand_mbps"] for item in affected), 6),
            "remaining_routed_mbps": after["total_routed_mbps"],
            "remaining_congested_link_count": after["congested_link_count"],
            "affected_demands": affected,
            "topology_mutated": False,
        }

    def analyze_scenarios(
        self, scenarios: Any, traffic_demands: Any | None = None,
    ) -> dict[str, Any]:
        """Run deterministic node, link, and site failures, optionally with traffic impact."""
        if not isinstance(scenarios, list):
            raise TopologyError("scenarios must be an array")
        seen_ids: set[str] = set()
        baseline = self.report()
        if traffic_demands is not None:
            # Validate the complete demand contract against the baseline before simulation.
            self.simulate_traffic(traffic_demands)
        results: list[dict[str, Any]] = []

        for index, scenario in enumerate(scenarios):
            if not isinstance(scenario, dict):
                raise TopologyError(f"scenarios[{index}] must be an object")
            unknown = set(scenario) - {"id", "name", "failure_type", "target"}
            if unknown:
                raise TopologyError(f"scenarios[{index}] has unknown properties")
            identifier, name = scenario.get("id"), scenario.get("name", "")
            failure_type, target = scenario.get("failure_type"), scenario.get("target")
            if not isinstance(identifier, str) or not identifier.strip():
                raise TopologyError(f"scenarios[{index}].id must be a non-empty string")
            if identifier in seen_ids:
                raise TopologyError(f"duplicate scenario id: {identifier}")
            if not isinstance(name, str):
                raise TopologyError(f"scenarios[{index}].name must be a string")
            if not isinstance(failure_type, str) or failure_type not in {"node", "link", "site"}:
                raise TopologyError(f"scenarios[{index}].failure_type must be node, link, or site")
            if not isinstance(target, str) or not target.strip():
                raise TopologyError(f"scenarios[{index}].target must be a non-empty string")
            seen_ids.add(identifier)

            if failure_type == "node":
                if target not in self._nodes:
                    raise TopologyError(f"scenario {identifier} references unknown node: {target}")
                failed_nodes = {target}
                failed_links: set[str] = set()
            elif failure_type == "link":
                if target not in self._links:
                    raise TopologyError(f"scenario {identifier} references unknown link: {target}")
                failed_nodes = set()
                failed_links = {target}
            else:
                failed_nodes = {
                    node.id for node in self._nodes.values() if node.site == target
                }
                if not failed_nodes:
                    raise TopologyError(f"scenario {identifier} references unknown or empty site: {target}")
                failed_links = set()

            impact = self.simulate_failure(
                disabled_nodes=failed_nodes, disabled_links=failed_links
            )
            remaining_nodes = tuple(
                node for node in self._nodes.values() if node.id not in failed_nodes
            )
            remaining_links = tuple(
                Link(
                    link.id, link.source, link.target, link.latency_ms,
                    link.capacity_mbps,
                    link.enabled and link.id not in failed_links,
                )
                for link in self._ordered_links
                if link.source not in failed_nodes and link.target not in failed_nodes
            )
            remaining_topology = NetworkTopology(remaining_nodes, remaining_links)
            remaining_report = remaining_topology.report()
            scenario_result = {
                "id": identifier, "name": name, "failure_type": failure_type,
                "target": target, "failed_nodes": sorted(failed_nodes),
                "failed_links": sorted(failed_links),
                "impact": impact,
                "remaining_topology": {
                    "node_count": remaining_report["node_count"],
                    "active_link_count": remaining_report["active_link_count"],
                    "component_count": remaining_report["component_count"],
                    "components": remaining_report["components"],
                    "isolated_nodes": remaining_report["isolated_nodes"],
                },
            }
            if traffic_demands is not None:
                scenario_result["traffic_impact"] = self._scenario_traffic_impact(
                    remaining_topology, traffic_demands, failed_nodes
                )
            results.append(scenario_result)

        return {
            "mode": "simulation-only", "scenario_pack_version": 1,
            "baseline": {
                "node_count": baseline["node_count"],
                "active_link_count": baseline["active_link_count"],
                "component_count": baseline["component_count"],
                "components": baseline["components"],
            },
            "scenario_count": len(results),
            "scenarios": sorted(results, key=lambda item: item["id"]),
            "topology_mutated": False,
        }

    def simulate_failure(self, *, disabled_nodes: set[str] | None = None,
                         disabled_links: set[str] | None = None) -> dict[str, Any]:
        """Compare baseline and failure-state connectivity without mutating the twin."""
        node_failures = frozenset(disabled_nodes or set())
        link_failures = frozenset(disabled_links or set())
        baseline = self._components(self._adjacency())
        after = self._components(self._adjacency(node_failures, link_failures))
        baseline_component = {node: index for index, group in enumerate(baseline) for node in group}
        after_component = {node: index for index, group in enumerate(after) for node in group}
        disrupted_pairs = 0
        survivors = sorted(after_component)
        for index, left in enumerate(survivors):
            for right in survivors[index + 1:]:
                if (baseline_component[left] == baseline_component[right]
                        and after_component[left] != after_component[right]):
                    disrupted_pairs += 1
        return {
            "mode": "simulation-only", "failed_nodes": sorted(node_failures),
            "failed_links": sorted(link_failures), "remaining_node_count": len(after_component),
            "component_count_before": len(baseline), "component_count_after": len(after),
            "components_after": after, "newly_disconnected_node_pairs": disrupted_pairs,
            "topology_mutated": False,
        }
