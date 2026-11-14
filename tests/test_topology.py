from __future__ import annotations
import unittest
from netopps.topology import NetworkTopology, TopologyError

def sample_topology() -> dict[str, object]:
    return {
        "schema_version": 1,
        "nodes": [{"id": "core", "role": "router"}, {"id": "edge-a", "role": "switch"},
                  {"id": "edge-b", "role": "switch"}, {"id": "server", "role": "server"},
                  {"id": "isolated", "role": "other"}],
        "links": [
            {"id": "core-a", "source": "core", "target": "edge-a", "latency_ms": 1, "capacity_mbps": 1000},
            {"id": "core-b", "source": "core", "target": "edge-b", "latency_ms": 2, "capacity_mbps": 1000},
            {"id": "a-server", "source": "edge-a", "target": "server", "latency_ms": 3, "capacity_mbps": 100},
            {"id": "b-server", "source": "edge-b", "target": "server", "latency_ms": 8, "capacity_mbps": 100},
        ],
    }

class NetworkTopologyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = NetworkTopology.from_dict(sample_topology())

    def test_report_is_deterministic(self) -> None:
        report = self.topology.report()
        self.assertEqual(5, report["node_count"])
        self.assertEqual(4, report["active_link_count"])
        self.assertEqual(2, report["component_count"])
        self.assertEqual([["core", "edge-a", "edge-b", "server"], ["isolated"]], report["components"])
        self.assertEqual(["isolated"], report["isolated_nodes"])
        self.assertEqual(report, self.topology.report())

    def test_shortest_path_uses_lowest_total_latency(self) -> None:
        result = self.topology.shortest_path("core", "server")
        self.assertEqual(["core", "edge-a", "server"], result["nodes"])
        self.assertEqual(["core-a", "a-server"], result["links"])
        self.assertEqual(4.0, result["latency_ms"])

    def test_unreachable_path_returns_none(self) -> None:
        self.assertIsNone(self.topology.shortest_path("core", "isolated"))

    def test_failure_simulation_reports_partition_without_mutation(self) -> None:
        before = self.topology.report()
        result = self.topology.simulate_failure(disabled_links={"core-a", "core-b"})
        self.assertEqual(4, result["component_count_after"])
        self.assertEqual(5, result["newly_disconnected_node_pairs"])
        self.assertFalse(result["topology_mutated"])
        self.assertEqual(before, self.topology.report())

    def test_node_failure_removes_node_and_incident_links(self) -> None:
        result = self.topology.simulate_failure(disabled_nodes={"core"})
        self.assertEqual(4, result["remaining_node_count"])
        self.assertEqual(3, result["component_count_after"])

    def test_rejects_duplicate_nodes(self) -> None:
        document = sample_topology()
        document["nodes"] = [{"id": "same"}, {"id": "same"}]
        with self.assertRaisesRegex(TopologyError, "duplicate node"):
            NetworkTopology.from_dict(document)

    def test_rejects_unknown_link_endpoint(self) -> None:
        document = sample_topology()
        document["links"] = [{"id": "bad", "source": "core", "target": "missing",
                              "latency_ms": 1, "capacity_mbps": 10}]
        with self.assertRaisesRegex(TopologyError, "unknown node"):
            NetworkTopology.from_dict(document)

    def test_rejects_invalid_link_metrics(self) -> None:
        document = sample_topology()
        document["links"] = [{"id": "bad", "source": "core", "target": "edge-a",
                              "latency_ms": -1, "capacity_mbps": 10}]
        with self.assertRaisesRegex(TopologyError, "latency_ms"):
            NetworkTopology.from_dict(document)

    def test_rejects_unknown_failure_targets(self) -> None:
        with self.assertRaisesRegex(TopologyError, "unknown disabled links"):
            self.topology.simulate_failure(disabled_links={"not-a-link"})

    def test_same_node_path_is_zero_cost(self) -> None:
        self.assertEqual({"nodes": ["core"], "links": [], "latency_ms": 0.0},
                         self.topology.shortest_path("core", "core"))

if __name__ == "__main__":
    unittest.main()
