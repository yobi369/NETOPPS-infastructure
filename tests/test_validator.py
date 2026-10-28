from __future__ import annotations

import json
import unittest
from pathlib import Path

from netopps.validator import validate_inventory


class InventoryValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = {
            "schema_version": 1,
            "devices": [{
                "id": "router-01",
                "hostname": "router-01.example.test",
                "management_ip": "192.0.2.10",
                "management_port": 22,
                "role": "router",
            }],
            "networks": [{"id": "users", "cidr": "198.51.100.0/24"}],
        }

    def test_example_inventory_passes(self) -> None:
        example = json.loads(Path("examples/inventory.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_inventory(example))

    def test_unknown_top_level_property_is_rejected(self) -> None:
        data = {**self.valid, "unexpected": True}
        self.assertIn("inventory.unknown_property", {f["code"] for f in validate_inventory(data)})

    def test_invalid_site_is_rejected(self) -> None:
        device = {**self.valid["devices"][0], "site": ""}
        data = {**self.valid, "devices": [device]}
        self.assertIn("device.site", {f["code"] for f in validate_inventory(data)})

    def test_non_object_is_rejected(self) -> None:
        self.assertEqual("inventory.type", validate_inventory([])[0]["code"])

    def test_wrong_schema_version_is_rejected(self) -> None:
        for version in ("1", True, 1.0, None):
            with self.subTest(version=version):
                data = {**self.valid, "schema_version": version}
                self.assertIn("inventory.schema_version", {f["code"] for f in validate_inventory(data)})

    def test_duplicate_device_ids_are_rejected(self) -> None:
        data = {**self.valid, "devices": self.valid["devices"] * 2}
        self.assertIn("device.duplicate_id", {f["code"] for f in validate_inventory(data)})

    def test_invalid_dns_hostname_is_rejected(self) -> None:
        for hostname in ("bad..host", "-bad.example.test", "bad_label.example.test", "a" * 64 + ".example.test"):
            with self.subTest(hostname=hostname):
                device = {**self.valid["devices"][0], "hostname": hostname}
                data = {**self.valid, "devices": [device]}
                self.assertIn("device.hostname", {f["code"] for f in validate_inventory(data)})

    def test_duplicate_hostnames_are_rejected_case_insensitively(self) -> None:
        second = {**self.valid["devices"][0], "id": "router-02", "hostname": "ROUTER-01.EXAMPLE.TEST."}
        data = {**self.valid, "devices": [self.valid["devices"][0], second]}
        self.assertIn("device.duplicate_hostname", {f["code"] for f in validate_inventory(data)})

    def test_duplicate_management_ips_are_rejected(self) -> None:
        second = {**self.valid["devices"][0], "id": "router-02"}
        data = {**self.valid, "devices": [self.valid["devices"][0], second]}
        self.assertIn("device.duplicate_management_ip", {f["code"] for f in validate_inventory(data)})

    def test_invalid_ip_and_port_are_rejected(self) -> None:
        device = {**self.valid["devices"][0], "management_ip": "999.1.1.1", "management_port": True}
        data = {**self.valid, "devices": [device]}
        codes = {f["code"] for f in validate_inventory(data)}
        self.assertIn("device.management_ip", codes)
        self.assertIn("device.management_port", codes)

    def test_invalid_role_type_is_rejected(self) -> None:
        device = {**self.valid["devices"][0], "role": ["router"]}
        data = {**self.valid, "devices": [device]}
        self.assertIn("device.role", {f["code"] for f in validate_inventory(data)})

    def test_invalid_cidr_boundary_is_rejected(self) -> None:
        data = {**self.valid, "networks": [{"id": "bad", "cidr": "198.51.100.1/24"}]}
        self.assertIn("network.cidr", {f["code"] for f in validate_inventory(data)})

    def test_duplicate_network_ids_are_rejected(self) -> None:
        data = {**self.valid, "networks": [
            {"id": "users", "cidr": "198.51.100.0/24"},
            {"id": "users", "cidr": "203.0.113.0/24"},
        ]}
        self.assertIn("network.duplicate_id", {f["code"] for f in validate_inventory(data)})

    def test_excessive_overlap_findings_are_bounded(self) -> None:
        data = {**self.valid, "networks": [
            {"id": f"net-{index}", "cidr": "10.0.0.0/24"} for index in range(200)
        ]}
        findings = validate_inventory(data)
        codes = [finding["code"] for finding in findings]
        self.assertIn("network.overlap_limit", codes)
        self.assertEqual(10_000, codes.count("network.overlap"))

    def test_excessive_network_count_is_rejected(self) -> None:
        data = {**self.valid, "networks": [
            {"id": f"net-{index}", "cidr": f"10.{index // 256}.{index % 256}.0/24"}
            for index in range(10_001)
        ]}
        self.assertIn("networks.limit", {finding["code"] for finding in validate_inventory(data)})

    def test_overlapping_networks_are_reported(self) -> None:
        data = {**self.valid, "networks": [
            {"id": "parent", "cidr": "10.0.0.0/16"},
            {"id": "child", "cidr": "10.0.1.0/24"},
        ]}
        self.assertIn("network.overlap", {f["code"] for f in validate_inventory(data)})

    def test_disjoint_ipv4_and_ipv6_networks_pass(self) -> None:
        data = {**self.valid, "networks": [
            {"id": "v4", "cidr": "192.0.2.0/24"},
            {"id": "v6", "cidr": "2001:db8::/32"},
        ]}
        self.assertEqual([], validate_inventory(data))

    def test_findings_are_deterministically_sorted(self) -> None:
        data = {**self.valid, "schema_version": 2, "networks": [
            {"id": "a", "cidr": "10.0.0.0/24"},
            {"id": "b", "cidr": "10.0.0.0/25"},
        ]}
        first = validate_inventory(data)
        self.assertEqual(first, validate_inventory(data))
        self.assertEqual(first, sorted(first, key=lambda item: (item["path"], item["code"], item["message"])))


if __name__ == "__main__":
    unittest.main()
