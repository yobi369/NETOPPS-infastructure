from __future__ import annotations

import contextlib
import io
import random
import tempfile
import unittest
from pathlib import Path

from netopps.__main__ import _read_inventory
from netopps.validator import validate_inventory


class ParserRobustnessTests(unittest.TestCase):
    def test_deterministic_malformed_input_smoke_fuzz(self) -> None:
        rng = random.Random(20261028)
        alphabet = bytes(range(256))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fuzz-input.json"
            for case in range(250):
                payload = bytes(rng.choice(alphabet) for _ in range(rng.randint(0, 256)))
                path.write_bytes(payload)
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    inventory, status = _read_inventory(path)
                self.assertIn(status, (0, 2), msg=f"case {case}")
                if status == 0:
                    findings = validate_inventory(inventory)
                    self.assertIsInstance(findings, list, msg=f"case {case}")
                else:
                    self.assertIsNone(inventory, msg=f"case {case}")


if __name__ == "__main__":
    unittest.main()
