from __future__ import annotations

import json
import unittest

from netopps.resilience import analyze_resilience
from netopps.topology import NetworkTopology

ROOT = __file__.rsplit("/", 2)[0]


def load_fixture(name: str) -> dict:
    with open(f"{ROOT}/examples/{name}", encoding="utf-8") as handle:
        return json.load(handle)


class ResilienceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology_doc = load_fixture("multi-site-topology.json")
        self.dependency_doc = load_fixture("service-dependencies.json")
        self.topology = NetworkTopology.from_dict(self.topology_doc)

    def test_report_ranks_dependencies_and_recovery_deterministically(self) -> None:
        first = analyze_resilience(self.topology, self.dependency_doc)
        second = analyze_resilience(self.topology, self.dependency_doc)
        self.assertEqual(first, second)
        self.assertEqual("simulation-only", first["mode"])
        self.assertTrue(first["weakest_dependencies"])
        self.assertEqual(list(range(1, len(first["recovery_priorities"]) + 1)),
                         [item["rank"] for item in first["recovery_priorities"]])

    def test_capacity_shortfall_is_reported_from_declared_inputs(self) -> None:
        report = analyze_resilience(self.topology, self.dependency_doc)
        self.assertTrue(any(item.get("capacity_gap_mbps") == 50
                            for item in report["capacity_assessment"]))

    def test_missing_capacity_is_not_invented(self) -> None:
        document = json.loads(json.dumps(self.dependency_doc))
        for edge in document["dependencies"]:
            if edge.get("redundancy_group") == "identity-ha":
                edge.pop("capacity_mbps", None)
        report = analyze_resilience(self.topology, document)
        self.assertTrue(any(item.get("status") == "unknown_incomplete_capacity_inputs"
                            for item in report["capacity_assessment"]))

    def test_inputs_are_not_mutated(self) -> None:
        topology_before = json.loads(json.dumps(self.topology_doc))
        dependencies_before = json.loads(json.dumps(self.dependency_doc))
        analyze_resilience(self.topology, self.dependency_doc)
        self.assertEqual(topology_before, self.topology_doc)
        self.assertEqual(dependencies_before, self.dependency_doc)

    def test_recommendations_are_conditional_not_claimed_as_verified(self) -> None:
        report = analyze_resilience(self.topology, self.dependency_doc)
        for item in report["redundancy_recommendations"]:
            self.assertEqual(3, len(item["assumptions"]))
        self.assertIn("not_asserted_without_a_concrete_candidate_dependency_and_capacity",
                      report["scenario_comparison"]["proposed_change_results"])


if __name__ == "__main__":
    unittest.main()
