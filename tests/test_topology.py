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
        self.assertEqual({"capacity_mbps"}, set(result["links"]["changed"][0]["changes"]))
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


    def test_site_failure_scenario_removes_all_nodes_at_site(self) -> None:
        topology = NetworkTopology.from_dict({
            "schema_version": 1,
            "nodes": [
                {"id": "core", "site": "hq"},
                {"id": "edge", "site": "branch"},
                {"id": "server", "site": "hq"},
                {"id": "isolated", "site": "warehouse"},
            ],
            "links": [
                {"id": "core-edge", "source": "core", "target": "edge",
                 "latency_ms": 1, "capacity_mbps": 100},
                {"id": "edge-server", "source": "edge", "target": "server",
                 "latency_ms": 1, "capacity_mbps": 100},
            ],
        })
        before = topology.report()
        result = topology.analyze_scenarios([
            {"id": "branch-outage", "name": "Branch site unavailable",
             "failure_type": "site", "target": "branch"},
            {"id": "edge-outage", "failure_type": "node", "target": "edge"},
            {"id": "uplink-outage", "failure_type": "link", "target": "core-edge"},
        ])
        self.assertEqual(["branch-outage", "edge-outage", "uplink-outage"],
                         [item["id"] for item in result["scenarios"]])
        site_result = result["scenarios"][0]
        self.assertEqual(["edge"], site_result["failed_nodes"])
        self.assertEqual(3, site_result["impact"]["component_count_after"])
        self.assertEqual(1, site_result["impact"]["newly_disconnected_node_pairs"])
        self.assertEqual(3, site_result["remaining_topology"]["node_count"])
        self.assertEqual(before, topology.report())
        self.assertFalse(result["topology_mutated"])

    def test_scenario_pack_rejects_unknown_site_and_duplicate_ids(self) -> None:
        with self.assertRaisesRegex(TopologyError, "unknown or empty site"):
            self.topology.analyze_scenarios([
                {"id": "bad-site", "failure_type": "site", "target": "missing"}
            ])
        scenario = {"id": "same", "failure_type": "node", "target": "core"}
        with self.assertRaisesRegex(TopologyError, "duplicate scenario id"):
            self.topology.analyze_scenarios([scenario, scenario])

    def test_scenario_traffic_impact_identifies_failed_endpoints_and_lost_routes(self) -> None:
        topology = NetworkTopology.from_dict({
            "schema_version": 1,
            "nodes": [{"id": "a", "site": "hq"}, {"id": "b", "site": "branch"},
                      {"id": "c", "site": "hq"}, {"id": "d", "site": "hq"}],
            "links": [
                {"id": "ab", "source": "a", "target": "b", "latency_ms": 1, "capacity_mbps": 100},
                {"id": "bc", "source": "b", "target": "c", "latency_ms": 1, "capacity_mbps": 100},
                {"id": "cd", "source": "c", "target": "d", "latency_ms": 1, "capacity_mbps": 100},
                {"id": "ad", "source": "a", "target": "d", "latency_ms": 8, "capacity_mbps": 100},
            ],
        })
        demands = [
            {"id": "branch-service", "source": "a", "target": "b", "demand_mbps": 20},
            {"id": "hq-service", "source": "a", "target": "d", "demand_mbps": 30},
            {"id": "cross-site", "source": "b", "target": "d", "demand_mbps": 40},
        ]
        before = topology.report()
        result = topology.analyze_scenarios(
            [{"id": "branch-loss", "failure_type": "site", "target": "branch"}],
            traffic_demands=demands,
        )
        impact = result["scenarios"][0]["traffic_impact"]
        self.assertEqual(2, impact["newly_affected_demand_count"])
        self.assertEqual(60.0, impact["newly_affected_mbps"])
        self.assertEqual(2, impact["endpoint_unavailable_count"])
        self.assertEqual(["branch-service", "cross-site"],
                         [item["id"] for item in impact["affected_demands"]])
        self.assertEqual(30.0, impact["remaining_routed_mbps"])
        self.assertFalse(impact["topology_mutated"])
        self.assertEqual(before, topology.report())

    def test_scenario_traffic_reports_route_loss_when_endpoints_survive(self) -> None:
        topology = NetworkTopology.from_dict({
            "schema_version": 1,
            "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}],
            "links": [
                {"id": "ab", "source": "a", "target": "b", "latency_ms": 1, "capacity_mbps": 10},
                {"id": "bc", "source": "b", "target": "c", "latency_ms": 1, "capacity_mbps": 10},
                {"id": "cd", "source": "c", "target": "d", "latency_ms": 1, "capacity_mbps": 10},
            ],
        })
        result = topology.analyze_scenarios(
            [{"id": "middle-link", "failure_type": "link", "target": "bc"}],
            traffic_demands=[
                {"id": "a-to-d", "source": "a", "target": "d", "demand_mbps": 7}
            ],
        )
        impact = result["scenarios"][0]["traffic_impact"]
        self.assertEqual(1, impact["unroutable_after_failure_count"])
        self.assertEqual(1, impact["newly_affected_demand_count"])
        self.assertEqual("no_surviving_route", impact["affected_demands"][0]["reason"])
        self.assertEqual(7.0, impact["newly_affected_mbps"])

    def test_scenario_traffic_rejects_invalid_demand_pack(self) -> None:
        with self.assertRaisesRegex(TopologyError, "positive number"):
            self.topology.analyze_scenarios(
                [{"id": "node-loss", "failure_type": "node", "target": "core"}],
                traffic_demands=[
                    {"id": "bad", "source": "core", "target": "edge-a", "demand_mbps": 0}
                ],
            )

    def test_scenario_pack_rejects_non_string_failure_type(self) -> None:
        with self.assertRaisesRegex(TopologyError, "failure_type must be"):
            self.topology.analyze_scenarios([
                {"id": "bad-type", "failure_type": [], "target": "core"}
            ])

    def test_same_node_path_is_zero_cost(self) -> None:
        self.assertEqual({"nodes": ["core"], "links": [], "latency_ms": 0.0},
                         self.topology.shortest_path("core", "core"))

    def test_scenario_traffic_weights_critical_services_and_groups_demands(self) -> None:
        topology = NetworkTopology.from_dict({
            "schema_version": 1,
            "nodes": [{"id": item} for item in ["a", "b", "c"]],
            "links": [
                {"id": "ab", "source": "a", "target": "b", "latency_ms": 1, "capacity_mbps": 100},
                {"id": "bc", "source": "b", "target": "c", "latency_ms": 1, "capacity_mbps": 100},
            ],
        })
        demands = [
            {"id": "bank-api", "source": "a", "target": "c", "demand_mbps": 20,
             "service_id": "banking", "service_name": "Core Banking",
             "criticality": "mission_critical", "dependency_weight": 2.0},
            {"id": "bank-events", "source": "a", "target": "c", "demand_mbps": 10,
             "service_id": "banking", "service_name": "Core Banking",
             "criticality": "mission_critical", "dependency_weight": 2.0},
            {"id": "guest-wifi", "source": "a", "target": "c", "demand_mbps": 80,
             "service_id": "guest", "service_name": "Guest Wi-Fi",
             "criticality": "low", "dependency_weight": 0.5},
        ]
        result = topology.analyze_scenarios(
            [{"id": "core-loss", "failure_type": "node", "target": "b"}],
            traffic_demands=demands,
        )
        impact = result["scenarios"][0]["traffic_impact"]
        self.assertEqual(110.0, impact["newly_affected_mbps"])
        self.assertEqual(280.0, impact["total_weighted_impact_mbps"])
        self.assertEqual(2, impact["affected_service_count"])
        self.assertEqual("banking", impact["affected_services"][0]["service_id"])
        self.assertEqual(2, impact["affected_services"][0]["affected_demand_count"])
        self.assertEqual(240.0, impact["affected_services"][0]["weighted_impact_mbps"])

    def test_traffic_criticality_and_dependency_weight_are_validated(self) -> None:
        cases = [
            ("criticality", "extreme", "criticality must be"),
            ("dependency_weight", 0, "dependency_weight must be"),
            ("dependency_weight", True, "dependency_weight must be"),
            ("service_id", "", "service_id must be"),
        ]
        for field, value, message in cases:
            demand = {"id": "bad", "source": "core", "target": "edge-a", "demand_mbps": 5}
            demand[field] = value
            with (
                self.subTest(field=field, value=value),
                self.assertRaisesRegex(TopologyError, message),
            ):
                self.topology.simulate_traffic([demand])

    def test_legacy_traffic_demands_keep_backward_compatible_defaults(self) -> None:
        result = self.topology.simulate_traffic([
            {"id": "legacy", "source": "core", "target": "edge-a", "demand_mbps": 5}
        ])
        demand = result["demands"][0]
        self.assertEqual("legacy", demand["service_id"])
        self.assertEqual("standard", demand["criticality"])
        self.assertEqual(1.0, demand["dependency_weight"])
        self.assertEqual(7.5, demand["weighted_impact_mbps"])

if __name__ == "__main__":
    unittest.main()
