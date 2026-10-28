from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


class InventorySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((ROOT / "schemas" / "inventory.schema.json").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def test_example_inventory_matches_schema(self) -> None:
        example = json.loads((ROOT / "examples" / "inventory.json").read_text(encoding="utf-8"))
        self.assertEqual([], list(self.validator.iter_errors(example)))

    def test_missing_required_root_property_is_rejected(self) -> None:
        self.assertTrue(list(self.validator.iter_errors({"schema_version": 1, "devices": []})))

    def test_invalid_hostname_is_rejected(self) -> None:
        data = {
            "schema_version": 1,
            "devices": [{
                "id": "router-01",
                "hostname": "bad..hostname",
                "management_ip": "192.0.2.10",
                "role": "router",
            }],
            "networks": [],
        }
        errors = list(self.validator.iter_errors(data))
        self.assertTrue(any(error.json_path.endswith("hostname") for error in errors))

    def test_invalid_management_ip_is_rejected(self) -> None:
        data = {
            "schema_version": 1,
            "devices": [{
                "id": "router-01",
                "hostname": "router-01.example.test",
                "management_ip": "999.1.1.1",
                "role": "router",
            }],
            "networks": [],
        }
        errors = list(self.validator.iter_errors(data))
        self.assertTrue(any(error.json_path.endswith("management_ip") for error in errors))

    def test_invalid_role_is_rejected(self) -> None:
        data = {
            "schema_version": 1,
            "devices": [{
                "id": "router-01",
                "hostname": "router-01.example.test",
                "management_ip": "192.0.2.10",
                "role": "unknown-role",
            }],
            "networks": [],
        }
        self.assertTrue(list(self.validator.iter_errors(data)))


if __name__ == "__main__":
    unittest.main()
