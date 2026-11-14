"""Ed25519 approvals and evidence governance for local NETOPPS pilot workspaces."""
from __future__ import annotations
import argparse, base64, getpass, hashlib, json, os, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from netopps.pilot import PilotError, load_manifest, safe_file, sha256_file, validate_workspace

ALG = "Ed25519"
REGISTRY_VERSION = 1
ZIP_TIME = (1980, 1, 1, 0, 0, 0)

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def fingerprint(key: Ed25519PublicKey) -> str:
    raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()

def load_private(path: Path, password: str) -> Ed25519PrivateKey:
    try: key = serialization.load_pem_private_key(path.read_bytes(), password=password.encode())
    except (OSError, ValueError, TypeError) as exc: raise PilotError(f"cannot load encrypted private key: {exc}") from exc
    if not isinstance(key, Ed25519PrivateKey): raise PilotError("private key must be Ed25519")
    return key

def load_public(path: Path) -> Ed25519PublicKey:
    try: key = serialization.load_pem_public_key(path.read_bytes())
    except (OSError, ValueError) as exc: raise PilotError(f"cannot load public key: {exc}") from exc
    if not isinstance(key, Ed25519PublicKey): raise PilotError("public key must be Ed25519")
    return key

def keygen(private_path: Path, public_path: Path, password: str) -> str:
    if len(password) < 12: raise PilotError("private-key passphrase must contain at least 12 characters")
    if private_path.exists() or public_path.exists(): raise PilotError("refusing to overwrite existing key files")
    private_path.parent.mkdir(parents=True, exist_ok=True); public_path.parent.mkdir(parents=True, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(password.encode())))
    os.chmod(private_path, 0o600)
    public_path.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    os.chmod(public_path, 0o644)
    return fingerprint(key.public_key())

def load_registry(path: Path) -> dict[str, Any]:
    try: doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc: raise PilotError(f"cannot read reviewer registry: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema_version") != REGISTRY_VERSION or not isinstance(doc.get("reviewers"), dict):
        raise PilotError("trust registry must contain schema_version 1 and a reviewers object")
    return doc

def register_reviewer(registry_path: Path, public_path: Path, reviewer_id: str, name: str, organization: str, role: str) -> str:
    for label, value in (("reviewer_id", reviewer_id), ("display_name", name), ("organization", organization), ("role", role)):
        if not isinstance(value, str) or not value.strip() or len(value) > 200: raise PilotError(f"{label} must be non-empty and at most 200 characters")
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    public_path = public_path.resolve()
    if not public_path.is_relative_to(registry_path.resolve().parent): raise PilotError("public key must be stored beneath the trust registry directory")
    key = load_public(public_path); fp = fingerprint(key)
    registry = load_registry(registry_path) if registry_path.exists() else {"schema_version": 1, "reviewers": {}}
    if any(r.get("reviewer_id") == reviewer_id for r in registry["reviewers"].values()): raise PilotError("reviewer_id already registered")
    if fp in registry["reviewers"]: raise PilotError("public key already registered")
    registry["reviewers"][fp] = {"reviewer_id":reviewer_id,"display_name":name.strip(),"organization":organization.strip(),"role":role.strip(),"public_key":os.path.relpath(public_path,registry_path.resolve().parent),"algorithm":ALG,"fingerprint_sha256":fp,"status":"active"}
    registry_path.write_text(json.dumps(registry,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return fp

def trusted(registry_path: Path, fp: str) -> tuple[dict[str, Any], Ed25519PublicKey]:
    registry=load_registry(registry_path); record=registry["reviewers"].get(fp)
    if not isinstance(record,dict) or record.get("status")!="active": raise PilotError("signing key is not active in trust registry")
    if record.get("algorithm")!=ALG or record.get("fingerprint_sha256")!=fp: raise PilotError("trust record fingerprint or algorithm mismatch")
    base=registry_path.resolve().parent; key_path=(base/record.get("public_key","")).resolve()
    if not key_path.is_relative_to(base): raise PilotError("registered public key escapes trust directory")
    key=load_public(key_path)
    if fingerprint(key)!=fp: raise PilotError("registered public key fingerprint mismatch")
    return record,key

def signed(payload: dict[str,Any], key: Ed25519PrivateKey, fp: str) -> dict[str,Any]:
    return {"payload":payload,"signature":{"algorithm":ALG,"key_fingerprint_sha256":fp,"value_base64":base64.b64encode(key.sign(canonical(payload))).decode("ascii")}}

def verify_signed(doc: dict[str,Any], registry: Path) -> dict[str,Any]:
    try:
        payload=doc["payload"]; sig=doc["signature"]; fp=sig["key_fingerprint_sha256"]
        if sig["algorithm"]!=ALG or not isinstance(payload,dict): raise PilotError("unsupported signature envelope")
        record,key=trusted(registry,fp); key.verify(base64.b64decode(sig["value_base64"],validate=True),canonical(payload))
    except (KeyError,TypeError,ValueError,InvalidSignature) as exc: raise PilotError(f"signature verification failed: {exc}") from exc
    return record

def approve(root: Path, registry: Path, private_path: Path, password: str, assessment_id: str, decision: str, output: Path) -> None:
    errors=validate_workspace(root)
    if errors: raise PilotError("workspace validation failed: "+"; ".join(errors))
    if decision not in {"approved","rejected","needs_revision"}: raise PilotError("invalid approval decision")
    manifest=load_manifest(root); assessment=next((a for a in manifest["assessments"] if a.get("id")==assessment_id),None)
    if assessment is None: raise PilotError("assessment not found")
    report=next(a for a in manifest["artifacts"] if a["id"]==assessment["report_artifact_id"])
    key=load_private(private_path,password); fp=fingerprint(key.public_key()); reviewer,_=trusted(registry,fp)
    payload={"schema_version":1,"approval_id":hashlib.sha256(os.urandom(32)).hexdigest()[:24],"pilot_id":manifest["pilot_id"],"assessment_id":assessment_id,"assessment_kind":assessment["kind"],"decision":decision,"manifest_sha256":hashlib.sha256((root/"pilot-manifest.json").read_bytes()).hexdigest(),"report_artifact_id":report["id"],"report_sha256":sha256_file(safe_file(root,report["path"])),"reviewer":{k:reviewer[k] for k in ("reviewer_id","display_name","organization","role")},"signed_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(signed(payload,key,fp),indent=2,sort_keys=True)+"\n",encoding="utf-8")

def verify_approval(path: Path, registry: Path, root: Path|None=None) -> dict[str,Any]:
    try: doc=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,UnicodeDecodeError,json.JSONDecodeError) as exc: raise PilotError(f"cannot read approval: {exc}") from exc
    reviewer=verify_signed(doc,registry); payload=doc["payload"]
    if payload.get("reviewer",{}).get("reviewer_id")!=reviewer.get("reviewer_id"): raise PilotError("signed reviewer identity differs from trust registry")
    if root is not None:
        if hashlib.sha256((root/"pilot-manifest.json").read_bytes()).hexdigest()!=payload.get("manifest_sha256"): raise PilotError("approval does not match current pilot manifest")
        manifest=load_manifest(root); artifact=next((a for a in manifest["artifacts"] if a.get("id")==payload.get("report_artifact_id")),None)
        if artifact is None or sha256_file(safe_file(root,artifact["path"]))!=payload.get("report_sha256"): raise PilotError("approval does not match current assessment report")
    return {"valid":True,"reviewer_id":reviewer["reviewer_id"],"decision":payload.get("decision"),"approval_id":payload.get("approval_id"),"signed_at":payload.get("signed_at")}

def audit_verify(root: Path, registry: Path) -> dict[str,Any]:
    path=root/"audit"/"activity.jsonl"
    if not path.exists(): return {"valid":True,"entries":0,"head_hash":"0"*64}
    prev="0"*64; count=0
    try:
        for line_no,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
            if not line.strip(): continue
            doc=json.loads(line); payload=dict(doc["payload"]); entry_hash=payload.pop("entry_hash")
            if entry_hash!=hashlib.sha256(canonical(payload)).hexdigest() or payload.get("previous_hash")!=prev or payload.get("sequence")!=count+1: raise PilotError(f"audit chain integrity failure at line {line_no}")
            doc["payload"]={**payload,"entry_hash":entry_hash}; reviewer=verify_signed(doc,registry)
            if doc["payload"].get("actor",{}).get("reviewer_id")!=reviewer.get("reviewer_id"): raise PilotError(f"audit actor mismatch at line {line_no}")
            prev=entry_hash; count+=1
    except (OSError,UnicodeDecodeError,json.JSONDecodeError,KeyError,TypeError) as exc: raise PilotError(f"cannot verify audit log: {exc}") from exc
    return {"valid":True,"entries":count,"head_hash":prev}

def audit_append(root: Path, registry: Path, private_path: Path, password: str, event_type: str, details: dict[str,Any]) -> str:
    if not event_type.strip() or len(event_type)>100: raise PilotError("event type must be non-empty and at most 100 characters")
    key=load_private(private_path,password); fp=fingerprint(key.public_key()); reviewer,_=trusted(registry,fp)
    path=root/"audit"/"activity.jsonl"; path.parent.mkdir(parents=True,exist_ok=True)
    current=audit_verify(root,registry); seq=current["entries"]+1
    payload={"sequence":seq,"previous_hash":current["head_hash"],"event_type":event_type,"details":details,"actor":{k:reviewer[k] for k in ("reviewer_id","display_name","organization","role")},"occurred_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
    entry_hash=hashlib.sha256(canonical(payload)).hexdigest()
    with path.open("a",encoding="utf-8") as handle: handle.write(json.dumps(signed({**payload,"entry_hash":entry_hash},key,fp),sort_keys=True)+"\n")
    return entry_hash

def provenance(root: Path, assessment_id: str, output: Path) -> None:
    errors=validate_workspace(root)
    if errors: raise PilotError("workspace validation failed: "+"; ".join(errors))
    manifest=load_manifest(root); assessment=next((a for a in manifest["assessments"] if a.get("id")==assessment_id),None)
    if not assessment: raise PilotError("assessment not found")
    report=next(a for a in manifest["artifacts"] if a["id"]==assessment["report_artifact_id"])
    roles={"baseline_topology","baseline_dependencies","candidate_topology","candidate_dependencies"}
    inputs=[{"artifact_id":a["id"],"role":a["role"],"path":a["path"],"sha256":sha256_file(safe_file(root,a["path"]))} for a in manifest["artifacts"] if a["role"] in roles]
    present={a["role"] for a in inputs}
    if not {"baseline_topology","baseline_dependencies"}.issubset(present): raise PilotError("provenance requires baseline topology and dependencies")
    if assessment["kind"]=="comparison" and not {"candidate_topology","candidate_dependencies"}.issubset(present): raise PilotError("comparison provenance requires candidate topology and dependencies")
    doc={"schema_version":1,"pilot_id":manifest["pilot_id"],"assessment_id":assessment_id,"manifest_sha256":hashlib.sha256((root/"pilot-manifest.json").read_bytes()).hexdigest(),"inputs":sorted(inputs,key=lambda a:(a["role"],a["artifact_id"])),"assessment_report":{"artifact_id":report["id"],"path":report["path"],"sha256":sha256_file(safe_file(root,report["path"]))},"evidence_ids":sorted(assessment.get("evidence_ids",[]))}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def package(root: Path, output: Path) -> str:
    errors=validate_workspace(root)
    if errors: raise PilotError("workspace validation failed: "+"; ".join(errors))
    output=output.resolve()
    if output.is_relative_to(root.resolve()): raise PilotError("package output must be outside pilot workspace")
    manifest=load_manifest(root); files={"pilot-manifest.json":root/"pilot-manifest.json"}
    register=root/"evidence-register.csv"
    if register.exists(): files["evidence-register.csv"]=register
    for item in manifest["artifacts"]: files[item["path"]]=safe_file(root,item["path"])
    for folder in ("approvals","provenance","audit"):
        directory=root/folder
        if directory.exists():
            for path in sorted(directory.rglob("*")):
                if path.is_file():
                    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()): raise PilotError(f"unsafe package path: {path}")
                    files[path.relative_to(root).as_posix()]=path
    # Include only the explicit public trust registry and public keys; never sweep trust directories.
    registry=root/"trust"/"reviewers.json"
    if registry.exists():
        files["trust/reviewers.json"]=registry
        trust=load_registry(registry)
        for record in trust["reviewers"].values():
            key_path=(registry.parent/record["public_key"]).resolve()
            if not key_path.is_relative_to(registry.parent.resolve()): raise PilotError("public key escapes trust directory")
            files[key_path.relative_to(root).as_posix()]=key_path
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,path in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=ZIP_TIME); info.compress_type=zipfile.ZIP_DEFLATED; info.create_system=3; info.external_attr=0o100644<<16
            archive.writestr(info,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return hashlib.sha256(output.read_bytes()).hexdigest()

def main() -> int:
    parser=argparse.ArgumentParser(prog="netopps-governance",description="Local Ed25519 governance for NETOPPS pilot cases.")
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("keygen"); p.add_argument("--private-key",type=Path,required=True); p.add_argument("--public-key",type=Path,required=True)
    p=sub.add_parser("register-reviewer"); p.add_argument("--registry",type=Path,required=True); p.add_argument("--public-key",type=Path,required=True); p.add_argument("--reviewer-id",required=True); p.add_argument("--display-name",required=True); p.add_argument("--organization",required=True); p.add_argument("--role",required=True)
    p=sub.add_parser("approve"); p.add_argument("--directory",type=Path,required=True); p.add_argument("--registry",type=Path,required=True); p.add_argument("--private-key",type=Path,required=True); p.add_argument("--assessment-id",required=True); p.add_argument("--decision",choices=("approved","rejected","needs_revision"),required=True); p.add_argument("--output",type=Path,required=True)
    p=sub.add_parser("verify-approval"); p.add_argument("--approval",type=Path,required=True); p.add_argument("--registry",type=Path,required=True); p.add_argument("--directory",type=Path)
    p=sub.add_parser("audit-append"); p.add_argument("--directory",type=Path,required=True); p.add_argument("--registry",type=Path,required=True); p.add_argument("--private-key",type=Path,required=True); p.add_argument("--event-type",required=True); p.add_argument("--details",default="{}")
    p=sub.add_parser("audit-verify"); p.add_argument("--directory",type=Path,required=True); p.add_argument("--registry",type=Path,required=True)
    p=sub.add_parser("provenance"); p.add_argument("--directory",type=Path,required=True); p.add_argument("--assessment-id",required=True); p.add_argument("--output",type=Path,required=True)
    p=sub.add_parser("package"); p.add_argument("--directory",type=Path,required=True); p.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command=="keygen":
            password=getpass.getpass("New private-key passphrase (minimum 12 characters): "); print(json.dumps({"fingerprint_sha256":keygen(args.private_key,args.public_key,password)},indent=2))
        elif args.command=="register-reviewer": print(json.dumps({"key_fingerprint_sha256":register_reviewer(args.registry,args.public_key,args.reviewer_id,args.display_name,args.organization,args.role)},indent=2))
        elif args.command=="approve":
            password=getpass.getpass("Private-key passphrase: "); approve(args.directory,args.registry,args.private_key,password,args.assessment_id,args.decision,args.output); print(f"Signed approval written: {args.output}")
        elif args.command=="verify-approval": print(json.dumps(verify_approval(args.approval,args.registry,args.directory),indent=2))
        elif args.command=="audit-append":
            password=getpass.getpass("Private-key passphrase: "); details=json.loads(args.details)
            if not isinstance(details,dict): raise PilotError("--details must be a JSON object")
            print(json.dumps({"entry_hash":audit_append(args.directory,args.registry,args.private_key,password,args.event_type,details)},indent=2))
        elif args.command=="audit-verify": print(json.dumps(audit_verify(args.directory,args.registry),indent=2))
        elif args.command=="provenance": provenance(args.directory,args.assessment_id,args.output); print(f"Provenance written: {args.output}")
        else: print(json.dumps({"package_sha256":package(args.directory,args.output),"output":str(args.output)},indent=2))
        return 0
    except (OSError,PilotError,ValueError) as exc:
        print(f"error: {exc}",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
