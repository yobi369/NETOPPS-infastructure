from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from netopps.__main__ import main


class CliTests(unittest.TestCase):
    def run_cli(self, payload: bytes, *, exists: bool = True) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            if exists:
                path.write_bytes(payload)
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, "argv", ["netopps", "validate", str(path)]):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code = main()
            return code, stdout.getvalue(), stderr.getvalue()

    def test_valid_inventory_returns_zero_and_json(self) -> None:
        payload = json.dumps({
            "schema_version": 1,
            "devices": [],
            "networks": [],
        }).encode()
        code, stdout, stderr = self.run_cli(payload)
        self.assertEqual(0, code)
        self.assertTrue(json.loads(stdout)["valid"])
        self.assertEqual("", stderr)

    def test_invalid_inventory_returns_one(self) -> None:
        code, stdout, _ = self.run_cli(b'{"schema_version": 1, "devices": "bad", "networks": []}')
        self.assertEqual(1, code)
        self.assertFalse(json.loads(stdout)["valid"])

    def test_malformed_json_returns_two(self) -> None:
        code, _, stderr = self.run_cli(b'{"schema_version":')
        self.assertEqual(2, code)
        self.assertIn("invalid JSON", stderr)

    def test_duplicate_json_keys_return_two(self) -> None:
        code, _, stderr = self.run_cli(b'{"schema_version": 1, "schema_version": 1}')
        self.assertEqual(2, code)
        self.assertIn("duplicate JSON object key", stderr)

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


if __name__ == "__main__":
    unittest.main()
