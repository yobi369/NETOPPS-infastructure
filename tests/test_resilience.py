from __future__ import annotations

import json
import unittest

from netopps.report import render_resilience_html
from netopps.resilience import analyze_resilience
from netopps.topology import NetworkTopology, TopologyError

ROOT = __file__.rsplit("/", 2)[0]


def load_fixture(name: str) -> dict:
    with open(f"{ROOT}/examples/{name}", encoding="utf-8") as handle:
        return json.load(handle)


class ResilienceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology_doc = load_fixture("multi-site-topology.json")
        self.dependency_doc = load_fixture("service-dependencies.json")
        self.topology = NetworkTopology.from_dict(self.topology_doc)

    def test_html_briefing_is_self_contained_and_escapes_untrusted_values(self) -> None:
        report = analyze_resilience(self.topology, self.dependency_doc)
        report["executive_assessment"]["headline"] = "<script>alert('x')</script>"
        output = render_resilience_html(report)
        self.assertIn("Institutional Resilience Briefing", output)
        self.assertIn("&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;", output)
        self.assertNotIn("<script>alert", output)
        self.assertIn("Content-Security-Policy", output)
        self.assertIn("Correlated failure scenarios", output)
        self.assertNotIn("https://", output)


    def test_html_briefing_handles_empty_finding_sections(self) -> None:
        report = analyze_resilience(self.topology, self.dependency_doc)
        report["weakest_dependencies"] = []
        report["correlated_failure_scenarios"] = []
        report["physical_diversity_assessment"] = []
        report["redundancy_recommendations"] = []
        report["capacity_assessment"] = []
        report["recovery_priorities"] = []
        output = render_resilience_html(report)
        self.assertGreaterEqual(output.count("No findings."), 5)

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


    def test_candidate_dependency_model_compares_before_and_after_capacity(self) -> None:
        candidate = load_fixture("service-dependencies-candidate.json")
        report = analyze_resilience(self.topology, self.dependency_doc, candidate)
        comparison = report["candidate_comparison"]
        self.assertTrue(comparison["candidate_supplied"])
        self.assertLess(
            comparison["candidate"]["modeled_capacity_gap_count"],
            comparison["baseline"]["modeled_capacity_gap_count"],
        )
        self.assertLess(comparison["change"]["modeled_capacity_gaps"], 0)


    def test_correlated_failure_domains_combine_multiple_assets(self) -> None:
        document = json.loads(json.dumps(self.dependency_doc))
        for edge in document["dependencies"]:
            if edge.get("depends_on_type") == "node" and edge.get("depends_on_id") in {"backup-server", "hq-core"}:
                edge["failure_domains"] = ["shared-power-domain"]
        report = analyze_resilience(self.topology, document)
        scenario = next(
            item for item in report["correlated_failure_scenarios"]
            if item["failure_domain"] == "shared-power-domain"
        )
        self.assertEqual(["backup-server", "hq-core"], scenario["failed_assets"]["nodes"])
        self.assertIn("identity-platform", scenario["unavailable_services"])

    def test_diversity_report_detects_shared_domains_and_unverified_evidence(self) -> None:
        document = json.loads(json.dumps(self.dependency_doc))
        for edge in document["dependencies"]:
            if edge.get("redundancy_group") == "identity-ha":
                edge["failure_domains"] = ["shared-carrier"]
                edge["diversity_evidence"] = {
                    "evidence_ref": "example-only:carrier-record",
                    "evidence_type": "carrier_attestation",
                    "verification_status": "documented",
                }
        report = analyze_resilience(self.topology, document)
        group = next(item for item in report["physical_diversity_assessment"]
                     if item["service_id"] == "identity-platform")
        self.assertEqual(["shared-carrier"], group["shared_failure_domains"])
        self.assertEqual("shared_failure_domain_detected", group["diversity_status"])


    def test_diversity_evidence_record_is_reported_but_not_authenticated(self) -> None:
        document = json.loads(json.dumps(self.dependency_doc))
        for edge in document["dependencies"]:
            if edge.get("redundancy_group") == "identity-ha":
                edge["failure_domains"] = [f"independent:{edge['depends_on_id']}"]
                edge["diversity_evidence"] = {
                    "evidence_ref": f"example-only:{edge['depends_on_id']}",
                    "evidence_type": "site_survey",
                    "verification_status": "independently_verified",
                    "verified_at": "2026-11-14",
                    "verified_by": "Synthetic test fixture",
                }
        report = analyze_resilience(self.topology, document)
        group = next(item for item in report["physical_diversity_assessment"]
                     if item["service_id"] == "identity-platform")
        self.assertEqual("operator_recorded_independent_evidence", group["diversity_status"])
        self.assertIn("does not independently authenticate", group["interpretation"])

    def test_recovery_objectives_are_reported_without_inventing_targets(self) -> None:
        document = json.loads(json.dumps(self.dependency_doc))
        document["services"][0]["rto_minutes"] = 45
        document["services"][0]["rpo_minutes"] = 10
        report = analyze_resilience(self.topology, document)
        identity = next(item for item in report["recovery_priorities"]
                        if item["service_id"] == "identity-platform")
        self.assertEqual({"rto_minutes": 45.0, "rpo_minutes": 10.0, "status": "defined"},
                         identity["recovery_objectives"])
        guest = next(item for item in report["recovery_priorities"]
                     if item["service_id"] == "guest-wifi")
        self.assertEqual("not_defined", guest["recovery_objectives"]["status"])

    def test_invalid_recovery_objective_is_rejected(self) -> None:
        document = json.loads(json.dumps(self.dependency_doc))
        document["services"][0]["rto_minutes"] = 0
        with self.assertRaises(TopologyError):
            analyze_resilience(self.topology, document)

    def test_recommendations_are_conditional_not_claimed_as_verified(self) -> None:
        report = analyze_resilience(self.topology, self.dependency_doc)
        for item in report["redundancy_recommendations"]:
            self.assertEqual(3, len(item["assumptions"]))
        self.assertIn("not_asserted_without_a_concrete_candidate_dependency_and_capacity",
                      report["scenario_comparison"]["proposed_change_results"])


if __name__ == "__main__":
    unittest.main()
