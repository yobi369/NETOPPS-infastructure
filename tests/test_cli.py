from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from netopps.__main__ import _check_json_nesting, main


class CliTests(unittest.TestCase):
    def run_cli(self, payload: bytes, *, exists: bool = True, extra_args: list[str] | None = None) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            if exists:
                path.write_bytes(payload)
            stdout, stderr = io.StringIO(), io.StringIO()
            with (
                patch.object(sys, "argv", ["netopps", *(extra_args or ["validate"]), str(path)]),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                code = main()
            return code, stdout.getvalue(), stderr.getvalue()

    def test_resilience_report_cli_emits_assessment_json(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            topology_path = Path(directory) / "topology.json"
            dependencies_path = Path(directory) / "dependencies.json"
            topology_path.write_text(
                (root / "examples/multi-site-topology.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            dependencies_path.write_text(
                (root / "examples/service-dependencies.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", [
                    "netopps", "resilience-report", str(topology_path), str(dependencies_path)
                ]),
                contextlib.redirect_stdout(stdout),
            ):
                code = main()
        report = json.loads(stdout.getvalue())
        self.assertEqual(0, code)
        self.assertEqual("institutional-resilience-and-recovery-plan", report["report_type"])
        self.assertFalse(report["candidate_comparison"]["candidate_supplied"])

    def test_valid_inventory_returns_zero_and_json(self) -> None:
        payload = json.dumps({
            "schema_version": 1,
            "devices": [],
            "networks": [],
        }).encode()
        code, stdout, stderr = self.run_cli(payload)
        self.assertEqual(0, code)
        result = json.loads(stdout)
        self.assertTrue(result["valid"])
        self.assertEqual(1, result["output_schema_version"])
        self.assertEqual("", stderr)

    def test_invalid_inventory_returns_one(self) -> None:
        code, stdout, _ = self.run_cli(b'{"schema_version": 1, "devices": "bad", "networks": []}')
        self.assertEqual(1, code)
        result = json.loads(stdout)
        self.assertFalse(result["valid"])
        self.assertEqual(1, result["output_schema_version"])

    def test_malformed_json_returns_two(self) -> None:
        code, _, stderr = self.run_cli(b'{"schema_version":')
        self.assertEqual(2, code)
        self.assertIn("invalid JSON", stderr)

    def test_duplicate_json_keys_return_two(self) -> None:
        code, _, stderr = self.run_cli(b'{"schema_version": 1, "schema_version": 1}')
        self.assertEqual(2, code)
        self.assertIn("duplicate JSON object key", stderr)

    def test_json_nesting_scanner_ignores_delimiters_inside_strings(self) -> None:
        _check_json_nesting('{"note":"' + "[" * 150 + '" }')

    def test_excessively_nested_json_returns_two(self) -> None:
        payload = b"[" * 1500 + b"0" + b"]" * 1500
        code, _, stderr = self.run_cli(payload)
        self.assertEqual(2, code)
        self.assertIn("nesting exceeds", stderr)

    def test_non_utf8_input_returns_two(self) -> None:
        code, _, stderr = self.run_cli(b'\xff\xfe')
        self.assertEqual(2, code)
        self.assertIn("UTF-8", stderr)

    def test_oversized_input_returns_two(self) -> None:
        code, _, stderr = self.run_cli(b" " * (5 * 1024 * 1024 + 1))
        self.assertEqual(2, code)
        self.assertIn("safety limit", stderr)

    def test_missing_file_returns_two(self) -> None:
        code, _, stderr = self.run_cli(b"", exists=False)
        self.assertEqual(2, code)
        self.assertIn("cannot read", stderr)

    def test_connectivity_requires_explicit_network_consent(self) -> None:
        payload = json.dumps({"schema_version": 1, "devices": [], "networks": []}).encode()
        code, _, stderr = self.run_cli(payload, extra_args=["check-connectivity"])
        self.assertEqual(2, code)
        self.assertIn("requires explicit --allow-network", stderr)

    def test_connectivity_cli_uses_mocked_socket_and_versions_output(self) -> None:
        payload = json.dumps({
            "schema_version": 1,
            "devices": [{
                "id": "router-01",
                "hostname": "router-01.example.test",
                "management_ip": "192.0.2.10",
                "role": "router",
            }],
            "networks": [],
        }).encode()
        with patch("netopps.health.socket.create_connection", return_value=Mock()) as connect:
            code, stdout, _ = self.run_cli(
                payload,
                extra_args=["check-connectivity", "--allow-network", "--limit", "1", "--timeout", "0.5"],
            )
        result = json.loads(stdout)
        self.assertEqual(0, code)
        self.assertEqual(1, result["output_schema_version"])
        self.assertEqual("read-only-tcp-check", result["mode"])
        self.assertFalse(result["configuration_changed"])
        connect.assert_called_once_with(("192.0.2.10", 22), timeout=0.5)

    def test_connectivity_cli_marks_truncated_scope_incomplete(self) -> None:
        payload = json.dumps({
            "schema_version": 1,
            "devices": [
                {"id": "router-01", "hostname": "router-01.example.test", "management_ip": "192.0.2.10", "role": "router"},
                {"id": "router-02", "hostname": "router-02.example.test", "management_ip": "192.0.2.11", "role": "router"},
            ],
            "networks": [],
        }).encode()
        with patch("netopps.health.socket.create_connection", return_value=Mock()):
            code, stdout, _ = self.run_cli(
                payload,
                extra_args=["check-connectivity", "--allow-network", "--limit", "1"],
            )
        result = json.loads(stdout)
        self.assertEqual(1, code)
        self.assertFalse(result["valid"])
        self.assertTrue(result["scope_truncated"])


    def test_topology_report_cli_analyzes_path_and_failure_without_network_io(self) -> None:
        payload = json.dumps({
            "schema_version": 1,
            "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
            "links": [
                {"id": "ab", "source": "a", "target": "b", "latency_ms": 1, "capacity_mbps": 100},
                {"id": "bc", "source": "b", "target": "c", "latency_ms": 2, "capacity_mbps": 100},
            ],
        }).encode()
        with patch("socket.socket") as socket_factory:
            code, stdout, stderr = self.run_cli(
                payload,
                extra_args=["topology-report", "--path-from", "a", "--path-to", "c", "--disable-link", "ab"],
            )
        result = json.loads(stdout)
        self.assertEqual(0, code)
        self.assertEqual("simulation-only", result["mode"])
        self.assertEqual(["a", "b", "c"], result["path_analysis"]["nodes"])
        self.assertEqual(2, result["failure_simulation"]["component_count_after"])
        self.assertFalse(result["failure_simulation"]["topology_mutated"])
        socket_factory.assert_not_called()
        self.assertEqual("", stderr)


    def test_topology_cli_accepts_separate_traffic_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            topology_path = Path(directory) / "topology.json"
            traffic_path = Path(directory) / "traffic.json"
            topology_path.write_text(json.dumps({
                "schema_version": 1,
                "nodes": [{"id": "a"}, {"id": "b"}],
                "links": [{"id": "ab", "source": "a", "target": "b",
                           "latency_ms": 1, "capacity_mbps": 10}],
            }), encoding="utf-8")
            traffic_path.write_text(json.dumps({
                "schema_version": 1,
                "demands": [{"id": "flow-1", "source": "a", "target": "b", "demand_mbps": 15}],
            }), encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", ["netopps", "topology-report", str(topology_path),
                                           "--traffic-file", str(traffic_path)]),
                contextlib.redirect_stdout(stdout),
                patch("socket.socket") as socket_factory,
            ):
                code = main()
        result = json.loads(stdout.getvalue())
        self.assertEqual(0, code)
        self.assertEqual(1, result["traffic_simulation"]["congested_link_count"])
        self.assertEqual(5.0, result["traffic_simulation"]["links"][0]["overloaded_mbps"])
        socket_factory.assert_not_called()


    def test_topology_risk_cli_returns_explainable_score_without_network_io(self) -> None:
        payload = json.dumps({
            "schema_version": 1,
            "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
            "links": [
                {"id": "ab", "source": "a", "target": "b", "latency_ms": 1, "capacity_mbps": 10},
                {"id": "bc", "source": "b", "target": "c", "latency_ms": 1, "capacity_mbps": 10},
            ],
        }).encode()
        with patch("socket.socket") as socket_factory:
            code, stdout, stderr = self.run_cli(payload, extra_args=["topology-risk"])
        result = json.loads(stdout)
        self.assertEqual(0, code)
        self.assertEqual(20.0, result["score"])
        self.assertEqual(["b"], result["critical_nodes"])
        self.assertEqual(["ab", "bc"], result["critical_links"])
        self.assertEqual("simulation-only", result["mode"])
        self.assertFalse(result["topology_mutated"])
        socket_factory.assert_not_called()
        self.assertEqual("", stderr)

    def test_topology_diff_cli_compares_two_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            candidate = Path(directory) / "candidate.json"
            baseline.write_text(json.dumps({
                "schema_version": 1,
                "nodes": [{"id": "a"}, {"id": "b"}],
                "links": [{"id": "ab", "source": "a", "target": "b",
                           "latency_ms": 1, "capacity_mbps": 10}],
            }), encoding="utf-8")
            candidate.write_text(json.dumps({
                "schema_version": 1,
                "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
                "links": [{"id": "ab", "source": "a", "target": "b",
                           "latency_ms": 1, "capacity_mbps": 10}],
            }), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with (
                patch.object(sys, "argv", ["netopps", "topology-diff", str(baseline), str(candidate)]),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
                patch("socket.socket") as socket_factory,
            ):
                code = main()
        result = json.loads(stdout.getvalue())
        self.assertEqual(0, code)
        self.assertEqual(["c"], result["nodes"]["added"])
        self.assertEqual(1, result["summary"]["nodes_added"])
        self.assertFalse(result["topology_mutated"])
        socket_factory.assert_not_called()
        self.assertEqual("", stderr.getvalue())


    def test_topology_scenarios_cli_runs_site_failure_pack_locally(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            topology_path = Path(directory) / "topology.json"
            scenarios_path = Path(directory) / "scenarios.json"
            topology_path.write_text(json.dumps({
                "schema_version": 1,
                "nodes": [
                    {"id": "core", "site": "hq"},
                    {"id": "edge", "site": "branch"},
                    {"id": "server", "site": "hq"},
                ],
                "links": [
                    {"id": "core-edge", "source": "core", "target": "edge",
                     "latency_ms": 1, "capacity_mbps": 100},
                    {"id": "edge-server", "source": "edge", "target": "server",
                     "latency_ms": 1, "capacity_mbps": 100},
                ],
            }), encoding="utf-8")
            scenarios_path.write_text(json.dumps({
                "schema_version": 1,
                "scenarios": [
                    {"id": "branch-outage", "failure_type": "site", "target": "branch"}
                ],
            }), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with (
                patch.object(sys, "argv", ["netopps", "topology-scenarios",
                                           str(topology_path), str(scenarios_path)]),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
                patch("socket.socket") as socket_factory,
            ):
                code = main()
        result = json.loads(stdout.getvalue())
        self.assertEqual(0, code)
        self.assertEqual(1, result["scenario_count"])
        self.assertEqual(["edge"], result["scenarios"][0]["failed_nodes"])
        self.assertEqual(1, result["scenarios"][0]["impact"]["newly_disconnected_node_pairs"])
        self.assertFalse(result["topology_mutated"])
        socket_factory.assert_not_called()
        self.assertEqual("", stderr.getvalue())

    def test_topology_scenarios_cli_accepts_traffic_file_without_network_io(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            topology_path = Path(directory) / "topology.json"
            scenarios_path = Path(directory) / "scenarios.json"
            traffic_path = Path(directory) / "traffic.json"
            topology_path.write_text(json.dumps({
                "schema_version": 1,
                "nodes": [{"id": "a", "site": "hq"}, {"id": "b", "site": "branch"},
                          {"id": "c", "site": "hq"}],
                "links": [
                    {"id": "ab", "source": "a", "target": "b", "latency_ms": 1, "capacity_mbps": 100},
                    {"id": "bc", "source": "b", "target": "c", "latency_ms": 1, "capacity_mbps": 100},
                    {"id": "ac", "source": "a", "target": "c", "latency_ms": 5, "capacity_mbps": 100},
                ],
            }), encoding="utf-8")
            scenarios_path.write_text(json.dumps({
                "schema_version": 1,
                "scenarios": [{"id": "branch-outage", "failure_type": "site", "target": "branch"}],
            }), encoding="utf-8")
            traffic_path.write_text(json.dumps({
                "schema_version": 1,
                "demands": [{"id": "branch-flow", "source": "a", "target": "b", "demand_mbps": 12}],
            }), encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", ["netopps", "topology-scenarios",
                    str(topology_path), str(scenarios_path), "--traffic-file", str(traffic_path)]),
                contextlib.redirect_stdout(stdout),
                patch("socket.socket") as socket_factory,
            ):
                code = main()
        result = json.loads(stdout.getvalue())
        impact = result["scenarios"][0]["traffic_impact"]
        self.assertEqual(0, code)
        self.assertEqual(1, impact["newly_affected_demand_count"])
        self.assertEqual(12.0, impact["newly_affected_mbps"])
        socket_factory.assert_not_called()

    def test_plan_subnets_is_read_only_and_deterministic(self) -> None:
        payload = json.dumps({
            "schema_version": 1,
            "devices": [],
            "networks": [{"id": "used", "cidr": "10.0.0.0/24"}],
        }).encode()
        code, stdout, stderr = self.run_cli(
            payload,
            extra_args=["plan-subnets", "--pool", "10.0.0.0/16", "--prefix", "24", "--count", "2"],
        )
        result = json.loads(stdout)
        self.assertEqual(0, code)
        self.assertEqual(["10.0.1.0/24", "10.0.2.0/24"], result["allocated"])
        self.assertFalse(result["applied"])
        self.assertEqual(1, result["output_schema_version"])
        self.assertEqual("", stderr)

    def test_plan_subnets_reports_incomplete_plan(self) -> None:
        payload = json.dumps({
            "schema_version": 1,
            "devices": [],
            "networks": [{"id": "reserved", "cidr": "10.0.0.0/24"}],
        }).encode()
        code, stdout, _ = self.run_cli(
            payload,
            extra_args=["plan-subnets", "--pool", "10.0.0.0/24", "--prefix", "24", "--count", "1"],
        )
        result = json.loads(stdout)
        self.assertEqual(1, code)
        self.assertFalse(result["complete"])
        self.assertEqual([], result["allocated"])

    def test_plan_subnets_rejects_invalid_pool(self) -> None:
        payload = json.dumps({"schema_version": 1, "devices": [], "networks": []}).encode()
        code, stdout, _ = self.run_cli(
            payload,
            extra_args=["plan-subnets", "--pool", "not-a-cidr", "--prefix", "24", "--count", "1"],
        )
        self.assertEqual(2, code)
        result = json.loads(stdout)
        self.assertFalse(result["valid"])
        self.assertEqual(1, result["output_schema_version"])


    def test_topology_scenarios_cli_accepts_dependency_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            topology_path = Path(directory) / "topology.json"
            scenarios_path = Path(directory) / "scenarios.json"
            dependency_path = Path(directory) / "dependencies.json"
            topology_path.write_text(json.dumps({
                "schema_version": 1,
                "nodes": [{"id": "core", "site": "hq"}, {"id": "edge", "site": "branch"}],
                "links": [{"id": "core-edge", "source": "core", "target": "edge",
                           "latency_ms": 1, "capacity_mbps": 100}],
            }), encoding="utf-8")
            scenarios_path.write_text(json.dumps({
                "schema_version": 1,
                "scenarios": [{"id": "core-loss", "failure_type": "node", "target": "core"}],
            }), encoding="utf-8")
            dependency_path.write_text(json.dumps({
                "schema_version": 1,
                "services": [{"id": "auth", "name": "Authentication"},
                             {"id": "payments", "name": "Payments"}],
                "dependencies": [
                    {"service_id": "auth", "depends_on_type": "node", "depends_on_id": "core"},
                    {"service_id": "payments", "depends_on_type": "service", "depends_on_id": "auth"},
                ],
            }), encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", ["netopps", "topology-scenarios",
                    str(topology_path), str(scenarios_path), "--dependency-file", str(dependency_path)]),
                contextlib.redirect_stdout(stdout),
                patch("socket.socket") as socket_factory,
            ):
                code = main()
        result = json.loads(stdout.getvalue())
        impact = result["scenarios"][0]["service_dependency_impact"]
        self.assertEqual(0, code)
        self.assertEqual(2, impact["unavailable_count"])
        socket_factory.assert_not_called()

if __name__ == "__main__":
    unittest.main()
