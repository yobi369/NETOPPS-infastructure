from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from netopps.governance import keygen, register_reviewer, approve, package, verify_approval
from netopps.pilot import init_workspace
from netopps.security import create_checkpoint, verify_checkpoint, verify_approval_policy, verify_package, revoke_reviewer, rotate_reviewer, verify_trust_change


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "pilot"
        init_workspace(self.root, "security-pilot-01", "Example Institution", "Synthetic security test")
        self.trust = self.root / "trust"
        self.trust.mkdir(exist_ok=True)
        self.admin_private = self.base / "admin.private.pem"
        self.admin_public = self.trust / "admin.public.pem"
        keygen(self.admin_private, self.admin_public, "admin-passphrase-2026")
        register_reviewer(self.trust / "reviewers.json", self.admin_public, "admin-01", "Trust Admin", "Example Institution", "Trust Administrator")
        self.reviewer_private = self.base / "reviewer.private.pem"
        self.reviewer_public = self.trust / "reviewer.public.pem"
        keygen(self.reviewer_private, self.reviewer_public, "reviewer-passphrase-2026")
        register_reviewer(self.trust / "reviewers.json", self.reviewer_public, "reviewer-01", "Reviewer One", "Example Institution", "Resilience Reviewer")
        self.registry = self.trust / "reviewers.json"
        self.artifacts = []
        self._artifact("base-topology", "baseline_topology", "inputs/base/topology.json", "{}")
        self._artifact("base-deps", "baseline_dependencies", "inputs/base/deps.json", "{}")
        self._artifact("report", "assessment_report", "reports/report.json", '{"ok":true}')
        manifest = json.loads((self.root / "pilot-manifest.json").read_text())
        manifest["authorization"] = {"reference": "AUTH-TEST", "environment": "offline", "data_classification": "synthetic"}
        manifest["artifacts"] = self.artifacts
        manifest["assessments"] = [{"id": "assessment-01", "kind": "baseline", "report_artifact_id": "report", "evidence_ids": []}]
        (self.root / "pilot-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    def tearDown(self):
        self.temp.cleanup()

    def _artifact(self, ident, role, relative, content):
        import hashlib
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self.artifacts.append({"id": ident, "role": role, "path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

    def test_signed_checkpoint_detects_truncation(self):
        self.root.joinpath("audit").mkdir()
        self.root.joinpath("audit/activity.jsonl").write_text("")
        checkpoint = self.base / "head.json"
        create_checkpoint(self.root, self.registry, self.admin_private, "admin-passphrase-2026", checkpoint)
        self.assertTrue(verify_checkpoint(self.root, self.registry, checkpoint)["valid"])
        self.root.joinpath("audit/activity.jsonl").write_text('{"removed":true}\n')
        with self.assertRaises(ValueError):
            verify_checkpoint(self.root, self.registry, checkpoint)

    def test_rotation_revokes_old_key_and_signed_receipt_verifies(self):
        new_private = self.base / "new.private.pem"
        new_public = self.trust / "new.public.pem"
        keygen(new_private, new_public, "new-reviewer-passphrase")
        old_fp = json.loads(self.registry.read_text())["reviewers"]
        old_fp = next(fp for fp, rec in old_fp.items() if rec["reviewer_id"] == "reviewer-01")
        approval = self.root / "approvals/pre-rotation.json"
        approve(self.root, self.registry, self.reviewer_private, "reviewer-passphrase-2026", "assessment-01", "approved", approval)
        receipt = self.base / "rotation.json"
        rotate_reviewer(self.registry, old_fp, new_public, "reviewer-02", "Reviewer Two", "Example Institution", "Resilience Reviewer", self.admin_private, "admin-passphrase-2026", receipt)
        self.assertEqual("revoked", json.loads(self.registry.read_text())["reviewers"][old_fp]["status"])
        self.assertTrue(verify_trust_change(receipt, self.registry)["valid"])
        self.assertTrue(verify_approval(approval, self.registry, self.root)["valid"])

    def test_revocation_requires_trust_admin(self):
        fp = next(fp for fp, rec in json.loads(self.registry.read_text())["reviewers"].items() if rec["reviewer_id"] == "reviewer-01")
        with self.assertRaisesRegex(ValueError, "Trust Administrator"):
            revoke_reviewer(self.registry, fp, "departure", self.reviewer_private, "reviewer-passphrase-2026", self.base / "revoke.json")

    def test_distinct_role_qualified_approval_policy(self):
        approval = self.root / "approvals/one.json"
        approve(self.root, self.registry, self.reviewer_private, "reviewer-passphrase-2026", "assessment-01", "approved", approval)
        policy = self.base / "policy.json"
        policy.write_text(json.dumps({"required_approvals": 1, "allowed_roles": ["Resilience Reviewer"]}))
        result = verify_approval_policy(self.root, self.registry, policy, [approval])
        self.assertTrue(result["valid"])
        with self.assertRaisesRegex(ValueError, "threshold"):
            verify_approval_policy(self.root, self.registry, policy, [])

    def test_external_package_verifier(self):
        archive = self.base / "evidence.zip"
        package(self.root, archive)
        result = verify_package(archive)
        self.assertTrue(result["valid"])
        self.assertEqual(3, result["artifacts_verified"])


if __name__ == "__main__":
    unittest.main()
