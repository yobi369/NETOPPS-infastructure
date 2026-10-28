from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from netopps.health import check_connectivity


class ConnectivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = {
            "schema_version": 1,
            "devices": [
                {"id": "router-01", "hostname": "router-01.example.test", "management_ip": "192.0.2.10", "role": "router"},
                {"id": "switch-01", "hostname": "switch-01.example.test", "management_ip": "192.0.2.11", "management_port": 830, "role": "switch"},
            ],
            "networks": [],
        }

    @patch("netopps.health.socket.create_connection")
    def test_successful_check_is_read_only(self, create_connection: Mock) -> None:
        connection = Mock()
        create_connection.return_value = connection
        report = check_connectivity(self.inventory, limit=1, timeout=0.5)
        self.assertTrue(report["all_reachable"])
        self.assertFalse(report["configuration_changed"])
        self.assertEqual(1, report["checked_count"])
        self.assertEqual("reachable", report["results"][0]["status"])
        create_connection.assert_called_once_with(("192.0.2.10", 22), timeout=0.5)
        connection.close.assert_called_once()

    @patch("netopps.health.socket.create_connection", side_effect=TimeoutError)
    def test_timeout_is_reported_without_exception_leak(self, create_connection: Mock) -> None:
        report = check_connectivity(self.inventory, limit=1, timeout=0.5)
        self.assertFalse(report["all_reachable"])
        self.assertEqual("timeout", report["results"][0]["reason"])

    @patch("netopps.health.socket.create_connection", side_effect=ConnectionRefusedError)
    def test_refused_connection_is_reported(self, create_connection: Mock) -> None:
        report = check_connectivity(self.inventory, limit=1)
        self.assertEqual("connection_refused", report["results"][0]["reason"])

    @patch("netopps.health.socket.create_connection")
    def test_scope_limit_is_reported_and_bounded(self, create_connection: Mock) -> None:
        create_connection.return_value = Mock()
        report = check_connectivity(self.inventory, limit=1)
        self.assertEqual(1, report["checked_count"])
        self.assertEqual(2, report["total_devices"])
        self.assertTrue(report["scope_truncated"])
        create_connection.assert_called_once()

    def test_empty_inventory_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "no devices to check"):
            check_connectivity({"devices": []})

    def test_invalid_limit_and_timeout_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "limit must"):
            check_connectivity(self.inventory, limit=101)
        with self.assertRaisesRegex(ValueError, "timeout must"):
            check_connectivity(self.inventory, timeout=4)
        with self.assertRaisesRegex(TypeError, "finite number"):
            check_connectivity(self.inventory, timeout=float("nan"))

    def test_inventory_is_not_mutated(self) -> None:
        original = {"networks": [], "devices": list(self.inventory["devices"])}
        with patch("netopps.health.socket.create_connection", return_value=Mock()):
            check_connectivity(self.inventory)
        self.assertEqual(original["devices"], self.inventory["devices"])


if __name__ == "__main__":
    unittest.main()
