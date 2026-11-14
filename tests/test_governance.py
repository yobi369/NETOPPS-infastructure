from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from netopps.governance import (
    PilotError,
    approve,
    audit_append,
    audit_verify,
    keygen,
    package,
    provenance,
    register_reviewer,
    verify_approval,
)
from netopps.pilot import init_workspace

class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.base=Path(self.temp.name); self.root=self.base/"pilot"
        init_workspace(self.root,"pilot-governance-01","Example Institution","Synthetic resilience review")
        trust=self.root/"trust"; self.private=trust/"reviewer.private.pem"; self.public=trust/"reviewer.public.pem"; self.registry=trust/"reviewers.json"
        self.fp=keygen(self.private,self.public,"test-passphrase-2026")
        register_reviewer(self.registry,self.public,"reviewer-001","Test Reviewer","Example Institution","Resilience Reviewer")
        self.artifacts=[]
        self.add("base-topology","baseline_topology","inputs/baseline/topology.json",'{"nodes":[],"links":[]}')
        self.add("base-dependencies","baseline_dependencies","inputs/baseline/services.json",'{"services":[]}')
        self.add("candidate-topology","candidate_topology","inputs/candidate/topology.json",'{"nodes":[{"id":"x"}],"links":[]}')
        self.add("candidate-dependencies","candidate_dependencies","inputs/candidate/services.json",'{"services":[{"id":"x"}]}')
        self.add("comparison-report","assessment_report","reports/comparison.json",'{"summary":"synthetic"}')
        path=self.root/"pilot-manifest.json"; doc=json.loads(path.read_text())
        doc["authorization"]={"reference":"AUTH-SYNTHETIC","environment":"offline test workspace","data_classification":"synthetic"}
        doc["artifacts"]=self.artifacts; doc["assessments"]=[{"id":"comparison-01","kind":"comparison","report_artifact_id":"comparison-report","evidence_ids":[]}]
        path.write_text(json.dumps(doc,indent=2)+"\n")
    def tearDown(self): self.temp.cleanup()
    def add(self,ident,role,rel,content):
        path=self.root/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content)
        self.artifacts.append({"id":ident,"role":role,"path":rel,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    def test_encrypted_keypair(self):
        self.assertEqual(64,len(self.fp)); self.assertIn(b"ENCRYPTED",self.private.read_bytes()); self.assertEqual(0o600,self.private.stat().st_mode&0o777)
    def test_signed_approval_verifies_and_binds_manifest(self):
        path=self.root/"approvals"/"review.json"; approve(self.root,self.registry,self.private,"test-passphrase-2026","comparison-01","approved",path)
        self.assertTrue(verify_approval(path,self.registry,self.root)["valid"])
        manifest=self.root/"pilot-manifest.json"; manifest.write_text(manifest.read_text()+" ")
        with self.assertRaisesRegex(PilotError,"manifest"): verify_approval(path,self.registry,self.root)
    def test_unregistered_key_cannot_approve(self):
        other=self.base/"other.key"; pub=self.base/"other.pub"; keygen(other,pub,"another-passphrase-2026")
        with self.assertRaisesRegex(PilotError,"not active"): approve(self.root,self.registry,other,"another-passphrase-2026","comparison-01","approved",self.root/"approval.json")
    def test_audit_chain_signature_and_tamper_detection(self):
        audit_append(self.root,self.registry,self.private,"test-passphrase-2026","pilot.created",{"source":"test"})
        audit_append(self.root,self.registry,self.private,"test-passphrase-2026","assessment.reviewed",{"assessment":"comparison-01"})
        self.assertEqual(2,audit_verify(self.root,self.registry)["entries"])
        path=self.root/"audit"/"activity.jsonl"; rows=path.read_text().splitlines(); doc=json.loads(rows[0]); doc["payload"]["details"]["source"]="tampered"; rows[0]=json.dumps(doc); path.write_text("\n".join(rows)+"\n")
        with self.assertRaises(PilotError): audit_verify(self.root,self.registry)
    def test_provenance_tracks_both_model_versions_and_report(self):
        path=self.root/"provenance"/"comparison.json"; provenance(self.root,"comparison-01",path); doc=json.loads(path.read_text())
        self.assertEqual({"baseline_topology","baseline_dependencies","candidate_topology","candidate_dependencies"},{a["role"] for a in doc["inputs"]})
        self.assertEqual("comparison-report",doc["assessment_report"]["artifact_id"])
    def test_package_is_reproducible_and_excludes_private_key(self):
        first=self.base/"one.zip"; second=self.base/"two.zip"
        self.assertEqual(package(self.root,first),package(self.root,second))
        with zipfile.ZipFile(first) as archive:
            self.assertEqual((1980,1,1,0,0,0),archive.infolist()[0].date_time)
            self.assertIn("trust/reviewers.json",archive.namelist())
            self.assertIn("trust/reviewer.public.pem",archive.namelist())
            self.assertNotIn("trust/reviewer.private.pem",archive.namelist())
    def test_key_files_are_not_overwritten(self):
        with self.assertRaisesRegex(PilotError,"overwrite"): keygen(self.private,self.public,"test-passphrase-2026")

if __name__=="__main__": unittest.main()
