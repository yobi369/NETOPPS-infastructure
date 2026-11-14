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
        self.assertEqual(3, result["component_count_after"])
        self.assertEqual(3, result["newly_disconnected_node_pairs"])
        self.assertFalse(result["topology_mutated"])
        self.assertEqual(before, self.topology.report())

    def test_node_failure_removes_node_and_incident_links(self) -> None:
        result = self.topology.simulate_failure(disabled_nodes={"core"})
        self.assertEqual(4, result["remaining_node_count"])
        self.assertEqual(2, result["component_count_after"])

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


    def test_traffic_simulation_estimates_congestion_without_mutation(self) -> None:
        before = self.topology.report()
        result = self.topology.simulate_traffic([
            {"id": "heavy", "source": "core", "target": "server", "demand_mbps": 150},
            {"id": "unreachable", "source": "isolated", "target": "core", "demand_mbps": 10},
        ])
        self.assertEqual(160.0, result["total_requested_mbps"])
        self.assertEqual(150.0, result["total_routed_mbps"])
        self.assertEqual(1, result["unroutable_demand_count"])
        self.assertEqual(1, result["congested_link_count"])
        congested = next(link for link in result["links"] if link["id"] == "a-server")
        self.assertEqual("congested", congested["status"])
        self.assertEqual(50.0, congested["overloaded_mbps"])
        self.assertFalse(result["topology_mutated"])
        self.assertEqual(before, self.topology.report())

    def test_traffic_simulation_rejects_invalid_demands(self) -> None:
        with self.assertRaisesRegex(TopologyError, "positive number"):
            self.topology.simulate_traffic([
                {"id": "bad", "source": "core", "target": "server", "demand_mbps": 0}
            ])

    def test_traffic_simulation_rejects_duplicate_demand_ids(self) -> None:
        demand = {"id": "same", "source": "core", "target": "server", "demand_mbps": 1}
        with self.assertRaisesRegex(TopologyError, "duplicate traffic demand"):
            self.topology.simulate_traffic([demand, demand])


    def test_topology_diff_reports_added_removed_and_changed_objects(self) -> None:
        baseline_document = sample_topology()
        candidate_document = {
            "schema_version": 1,
            "nodes": [
                {"id": "core", "role": "firewall"},
                {"id": "edge-a", "role": "switch"},
                {"id": "edge-b", "role": "switch"},
                {"id": "server", "role": "server"},
                {"id": "new-node", "role": "router"},
            ],
            "links": [
                {"id": "core-a", "source": "edge-a", "target": "core",
                 "latency_ms": 1, "capacity_mbps": 2000},
                {"id": "core-b", "source": "core", "target": "edge-b",
                 "latency_ms": 2, "capacity_mbps": 1000},
                {"id": "a-server", "source": "edge-a", "target": "server",
                 "latency_ms": 3, "capacity_mbps": 100},
                {"id": "new-link", "source": "edge-a", "target": "edge-b",
                 "latency_ms": 1, "capacity_mbps": 500},
            ],
        }
        baseline = NetworkTopology.from_dict(baseline_document)
        candidate = NetworkTopology.from_dict(candidate_document)
        result = baseline.compare(candidate)
        self.assertEqual(["new-node"], result["nodes"]["added"])
        self.assertEqual(["isolated"], result["nodes"]["removed"])
        self.assertEqual("firewall", result["nodes"]["changed"][0]["changes"]["role"]["after"])
        self.assertEqual(["new-link"], [item["id"] for item in result["links"]["added"]])
        self.assertEqual(["b-server"], [item["id"] for item in result["links"]["removed"]])
        self.assertEqual(["core-a"], [item["id"] for item in result["links"]["changed"]])
        self.assertEqual(["edge-a", "core"], result["links"]["changed"][0]["changes"]["endpoints"]["before"])
        self.assertFalse(result["topology_mutated"])

    def test_risk_report_explains_articulation_nodes_and_bridge_links(self) -> None:
        topology = NetworkTopology.from_dict({
            "schema_version": 1,
            "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
            "links": [
                {"id": "ab", "source": "a", "target": "b", "latency_ms": 1, "capacity_mbps": 10},
                {"id": "bc", "source": "b", "target": "c", "latency_ms": 1, "capacity_mbps": 10},
            ],
        })
        result = topology.risk_report()
        self.assertEqual(20.0, result["score"])
        self.assertEqual("low", result["severity"])
        self.assertEqual(["b"], result["critical_nodes"])
        self.assertEqual(["ab", "bc"], result["critical_links"])
        self.assertEqual(10.0, result["factors"][1]["points"])
        self.assertEqual(10.0, result["factors"][2]["points"])
        self.assertFalse(result["topology_mutated"])

    def test_parallel_links_are_not_both_classified_as_bridges(self) -> None:
        topology = NetworkTopology.from_dict({
            "schema_version": 1,
            "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
            "links": [
                {"id": "ab-1", "source": "a", "target": "b", "latency_ms": 1, "capacity_mbps": 10},
                {"id": "ab-2", "source": "a", "target": "b", "latency_ms": 2, "capacity_mbps": 10},
                {"id": "bc", "source": "b", "target": "c", "latency_ms": 1, "capacity_mbps": 10},
            ],
        })
        result = topology.risk_report()
        self.assertEqual(["bc"], result["critical_links"])
        self.assertEqual(["b"], result["critical_nodes"])

    def test_empty_topology_has_zero_structural_risk(self) -> None:
        topology = NetworkTopology.from_dict({"schema_version": 1, "nodes": [], "links": []})
        result = topology.risk_report()
        self.assertEqual(0.0, result["score"])
        self.assertEqual("low", result["severity"])

    def test_same_node_path_is_zero_cost(self) -> None:
        self.assertEqual({"nodes": ["core"], "links": [], "latency_ms": 0.0},
                         self.topology.shortest_path("core", "core"))

if __name__ == "__main__":
    unittest.main()
