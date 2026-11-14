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
