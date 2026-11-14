from __future__ import annotations
import hashlib, json, tempfile, unittest, zipfile
from pathlib import Path
from netopps.pilot import PilotError, init_workspace, package_workspace, validate_workspace

class PilotWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "pilot"
        init_workspace(self.root, "pilot-test-01", "Example Institution", "Resilience evaluation")
        self.artifacts = []
        self.add_artifact("topology", "baseline_topology", "inputs/baseline/topology.json", '{"schema_version":1}')
        self.add_artifact("services", "baseline_dependencies", "inputs/baseline/services.json", '{"schema_version":1}')
        self.add_artifact("report", "assessment_report", "reports/baseline.json", '{"assessment":"synthetic"}')
        self.doc = json.loads((self.root / "pilot-manifest.json").read_text())
        self.doc["artifacts"] = self.artifacts
        self.doc["authorization"] = {"reference":"AUTH-001","environment":"approved offline workstation","data_classification":"sanitized synthetic"}
        self.write()
    def tearDown(self): self.temp.cleanup()
    def add_artifact(self, ident, role, rel, content):
        path = self.root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
        self.artifacts.append({"id":ident,"role":role,"path":rel,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    def write(self): (self.root / "pilot-manifest.json").write_text(json.dumps(self.doc))
    def test_valid_workspace(self): self.assertEqual(validate_workspace(self.root), [])
    def test_hash_mismatch_detected(self):
        (self.root / "inputs/baseline/topology.json").write_text("changed")
        self.assertTrue(any("hash mismatch" in e for e in validate_workspace(self.root)))
    def test_path_traversal_rejected(self):
        self.doc["artifacts"][0]["path"] = "../outside.json"; self.write()
        self.assertTrue(any("unsafe artifact path" in e for e in validate_workspace(self.root)))
    def test_duplicate_artifact_id_rejected(self):
        self.doc["artifacts"].append(dict(self.doc["artifacts"][0])); self.write()
        self.assertTrue(any("unique" in e for e in validate_workspace(self.root)))
    def test_assessment_must_reference_report(self):
        self.doc["assessments"] = [{"id":"a1","kind":"baseline","report_artifact_id":"services","evidence_ids":[]}]
        self.write(); self.assertTrue(any("assessment_report" in e for e in validate_workspace(self.root)))
    def test_unknown_evidence_reference_rejected(self):
        self.doc["assessments"] = [{"id":"a1","kind":"baseline","report_artifact_id":"report","evidence_ids":["missing"]}]
        self.write(); self.assertTrue(any("evidence_ids" in e for e in validate_workspace(self.root)))
    def test_package_contains_only_declared_files(self):
        output = Path(self.temp.name) / "package.zip"; package_workspace(self.root, output)
        with zipfile.ZipFile(output) as archive: names = set(archive.namelist())
        self.assertEqual(names, {"pilot-manifest.json","evidence-register.csv","inputs/baseline/topology.json","inputs/baseline/services.json","reports/baseline.json"})
    def test_package_refuses_output_inside_workspace(self):
        with self.assertRaises(PilotError): package_workspace(self.root, self.root / "package.zip")
    def test_init_refuses_overwrite(self):
        with self.assertRaises(PilotError): init_workspace(self.root, "pilot-test-02", "Other", "Other")
if __name__ == "__main__": unittest.main()
