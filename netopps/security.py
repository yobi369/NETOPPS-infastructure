"""Institutional trust administration and independent pilot verification."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from netopps.governance import (
    ALG, canonical, fingerprint, load_private, load_public, load_registry,
    signed, trusted, verify_signed,
)
from netopps.pilot import PilotError, load_manifest, sha256_file


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _admin(registry: Path, key_path: Path, password: str):
    key = load_private(key_path, password)
    fp = fingerprint(key.public_key())
    record, _ = trusted(registry, fp)
    if record.get("role") not in {"Trust Administrator", "Security Administrator"}:
        raise PilotError("trust changes require an active Trust Administrator or Security Administrator")
    return key, fp, record


def rotate_reviewer(registry: Path, old_fingerprint: str, new_public_key: Path,
                    reviewer_id: str, name: str, organization: str, role: str,
                    admin_key: Path, password: str, receipt: Path) -> str:
    key, admin_fp, actor = _admin(registry, admin_key, password)
    doc = load_registry(registry)
    old = doc["reviewers"].get(old_fingerprint)
    if not isinstance(old, dict) or old.get("status") != "active":
        raise PilotError("old reviewer key is not active")
    new_key = load_public(new_public_key)
    new_fp = fingerprint(new_key)
    if new_fp in doc["reviewers"] or any(r.get("reviewer_id") == reviewer_id for r in doc["reviewers"].values()):
        raise PilotError("new key fingerprint or reviewer ID is already registered")
    if not new_public_key.resolve().is_relative_to(registry.resolve().parent):
        raise PilotError("new public key must be beneath the trust registry directory")
    old["status"] = "revoked"
    old["revoked_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    old["revocation_reason"] = "rotated"
    doc["reviewers"][new_fp] = {
        "reviewer_id": reviewer_id, "display_name": name, "organization": organization,
        "role": role, "public_key": new_public_key.resolve().relative_to(registry.resolve().parent).as_posix(),
        "algorithm": ALG, "fingerprint_sha256": new_fp, "status": "active",
        "activated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    _write_json(registry, doc)
    payload = {"schema_version": 1, "event": "reviewer.key_rotated", "old_fingerprint": old_fingerprint,
               "new_fingerprint": new_fp, "reviewer_id": reviewer_id, "actor": actor["reviewer_id"],
               "actor_fingerprint": admin_fp, "occurred_at": datetime.now(UTC).isoformat(timespec="seconds")}
    _write_json(receipt, signed(payload, key, admin_fp))
    return new_fp


def revoke_reviewer(registry: Path, target_fingerprint: str, reason: str,
                    admin_key: Path, password: str, receipt: Path) -> None:
    key, admin_fp, actor = _admin(registry, admin_key, password)
    if not reason.strip() or len(reason) > 500:
        raise PilotError("revocation reason must be 1-500 characters")
    doc = load_registry(registry)
    target = doc["reviewers"].get(target_fingerprint)
    if not isinstance(target, dict) or target.get("status") != "active":
        raise PilotError("target reviewer key is not active")
    target["status"] = "revoked"
    target["revoked_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    target["revocation_reason"] = reason
    _write_json(registry, doc)
    payload = {"schema_version": 1, "event": "reviewer.key_revoked", "fingerprint": target_fingerprint,
               "reviewer_id": target["reviewer_id"], "reason": reason, "actor": actor["reviewer_id"],
               "actor_fingerprint": admin_fp, "occurred_at": datetime.now(UTC).isoformat(timespec="seconds")}
    _write_json(receipt, signed(payload, key, admin_fp))


def verify_trust_change(receipt: Path, registry: Path) -> dict[str, Any]:
    doc = json.loads(receipt.read_text(encoding="utf-8"))
    actor = verify_signed(doc, registry)
    if doc["payload"].get("actor") != actor.get("reviewer_id"):
        raise PilotError("trust-change actor does not match signer")
    return {"valid": True, "event": doc["payload"].get("event"), "actor": actor["reviewer_id"]}


def create_checkpoint(root: Path, registry: Path, private_key: Path, password: str, output: Path) -> str:
    from netopps.governance import audit_verify
    state = audit_verify(root, registry)
    key = load_private(private_key, password)
    fp = fingerprint(key.public_key())
    reviewer, _ = trusted(registry, fp)
    payload = {"schema_version": 1, "pilot_id": load_manifest(root)["pilot_id"],
               "entry_count": state["entries"], "head_hash": state["head_hash"],
               "checkpointed_at": datetime.now(UTC).isoformat(timespec="seconds"),
               "reviewer_id": reviewer["reviewer_id"]}
    _write_json(output, signed(payload, key, fp))
    return state["head_hash"]


def verify_checkpoint(root: Path, registry: Path, checkpoint: Path) -> dict[str, Any]:
    from netopps.governance import audit_verify
    doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    reviewer = verify_signed(doc, registry)
    payload = doc["payload"]
    state = audit_verify(root, registry)
    if payload.get("reviewer_id") != reviewer.get("reviewer_id"):
        raise PilotError("checkpoint reviewer does not match signer")
    if payload.get("pilot_id") != load_manifest(root)["pilot_id"]:
        raise PilotError("checkpoint belongs to a different pilot")
    if payload.get("entry_count") != state["entries"] or payload.get("head_hash") != state["head_hash"]:
        raise PilotError("audit log does not match independently retained checkpoint")
    return {"valid": True, "entry_count": state["entries"], "head_hash": state["head_hash"]}


def verify_approval_policy(root: Path, registry: Path, policy_path: Path,
                           approval_paths: list[Path]) -> dict[str, Any]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    required = policy.get("required_approvals")
    allowed_roles = policy.get("allowed_roles")
    if not isinstance(required, int) or isinstance(required, bool) or required < 1:
        raise PilotError("policy required_approvals must be a positive integer")
    if not isinstance(allowed_roles, list) or not allowed_roles or any(not isinstance(r, str) for r in allowed_roles):
        raise PilotError("policy allowed_roles must be a non-empty list")
    from netopps.governance import verify_approval
    accepted = []
    reviewers = set()
    for path in approval_paths:
        result = verify_approval(path, registry, root)
        if result["decision"] != "approved":
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        record, _ = trusted(registry, doc["signature"]["key_fingerprint_sha256"])
        if record["role"] not in allowed_roles:
            raise PilotError(f"reviewer role {record['role']!r} is not allowed by policy")
        if record["reviewer_id"] in reviewers:
            raise PilotError("approval threshold requires distinct reviewers")
        reviewers.add(record["reviewer_id"])
        accepted.append(result["approval_id"])
    if len(accepted) < required:
        raise PilotError(f"approval threshold not met: {len(accepted)} of {required}")
    return {"valid": True, "required_approvals": required, "verified_approvals": len(accepted),
            "reviewers": sorted(reviewers), "approval_ids": accepted}


def verify_package(package_path: Path) -> dict[str, Any]:
    """Verify package structure, manifest hashes and signatures without extracting files."""
    try:
        with zipfile.ZipFile(package_path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise PilotError("package contains duplicate paths")
            if any(name.startswith("/") or ".." in Path(name).parts or "\\" in name for name in names):
                raise PilotError("package contains unsafe paths")
            files = {name: archive.read(name) for name in names}
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise PilotError(f"cannot read evidence package: {exc}") from exc
    if "pilot-manifest.json" not in files or "trust/reviewers.json" not in files:
        raise PilotError("package must include pilot manifest and reviewer trust registry")
    manifest = json.loads(files["pilot-manifest.json"])
    registry = json.loads(files["trust/reviewers.json"])
    if manifest.get("schema_version") != 1 or registry.get("schema_version") != 1:
        raise PilotError("unsupported package or trust-registry schema")
    checked = 0
    for artifact in manifest.get("artifacts", []):
        name = artifact.get("path")
        if name not in files:
            raise PilotError(f"package is missing declared artifact: {name}")
        if hashlib.sha256(files[name]).hexdigest() != artifact.get("sha256"):
            raise PilotError(f"artifact hash mismatch: {name}")
        checked += 1
    public_keys = {}
    for fp, record in registry.get("reviewers", {}).items():
        name = "trust/" + record.get("public_key", "")
        if name not in files:
            raise PilotError(f"package is missing reviewer public key: {name}")
        key = serialization.load_pem_public_key(files[name])
        if not isinstance(key, Ed25519PublicKey) or fingerprint(key) != fp or record.get("fingerprint_sha256") != fp:
            raise PilotError(f"reviewer public key fingerprint mismatch: {fp}")
        public_keys[fp] = (key, record)
    # Validate baseline/candidate provenance records against the packaged manifest and artifacts.
    provenance_records = 0
    manifest_digest = hashlib.sha256(files["pilot-manifest.json"]).hexdigest()
    for name, raw in files.items():
        if not name.startswith("provenance/") or not name.endswith(".json"):
            continue
        record = json.loads(raw)
        if record.get("manifest_sha256") != manifest_digest:
            raise PilotError(f"provenance manifest digest mismatch: {name}")
        for item in record.get("inputs", []):
            artifact = next((a for a in manifest.get("artifacts", []) if a.get("id") == item.get("artifact_id")), None)
            if not artifact or artifact.get("path") not in files or hashlib.sha256(files[artifact["path"]]).hexdigest() != item.get("sha256"):
                raise PilotError(f"provenance input digest mismatch: {name}")
        report = record.get("assessment_report", {})
        report_artifact = next((a for a in manifest.get("artifacts", []) if a.get("id") == report.get("artifact_id")), None)
        if not report_artifact or report_artifact.get("path") not in files or hashlib.sha256(files[report_artifact["path"]]).hexdigest() != report.get("sha256"):
            raise PilotError(f"provenance report digest mismatch: {name}")
        provenance_records += 1
    # Verify the signed append-only activity chain from the package contents.
    audit_entries = 0
    previous_hash = "0" * 64
    audit_bytes = files.get("audit/activity.jsonl", b"")
    for line_no, line in enumerate(audit_bytes.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        entry = json.loads(line)
        payload = dict(entry["payload"])
        entry_hash = payload.pop("entry_hash")
        if entry_hash != hashlib.sha256(canonical(payload)).hexdigest() or payload.get("previous_hash") != previous_hash or payload.get("sequence") != audit_entries + 1:
            raise PilotError(f"packaged audit chain integrity failure at line {line_no}")
        signer = entry["signature"]["key_fingerprint_sha256"]
        key_record = public_keys.get(signer)
        if not key_record or key_record[1].get("status") not in {"active", "revoked"}:
            raise PilotError(f"packaged audit signer is unknown: {signer}")
        import base64
        key_record[0].verify(base64.b64decode(entry["signature"]["value_base64"], validate=True), canonical(entry["payload"]))
        if entry["payload"].get("actor", {}).get("reviewer_id") != key_record[1].get("reviewer_id"):
            raise PilotError(f"packaged audit actor mismatch at line {line_no}")
        previous_hash = entry_hash
        audit_entries += 1
    approvals = 0
    for name, raw in files.items():
        if not name.startswith("approvals/") or not name.endswith(".json"):
            continue
        doc = json.loads(raw); payload = doc["payload"]; sig = doc["signature"]
        key_record = public_keys.get(sig.get("key_fingerprint_sha256"))
        if not key_record or key_record[1].get("status") not in {"active", "revoked"}:
            raise PilotError(f"approval signer is not active in packaged trust registry: {name}")
        key_record[0].verify(__import__("base64").b64decode(sig["value_base64"], validate=True), canonical(payload))
        if payload.get("manifest_sha256") != hashlib.sha256(files["pilot-manifest.json"]).hexdigest():
            raise PilotError(f"approval manifest digest mismatch: {name}")
        report = next((a for a in manifest.get("artifacts", []) if a.get("id") == payload.get("report_artifact_id")), None)
        if not report or hashlib.sha256(files[report["path"]]).hexdigest() != payload.get("report_sha256"):
            raise PilotError(f"approval report digest mismatch: {name}")
        approvals += 1
    return {"valid": True, "pilot_id": manifest.get("pilot_id"), "artifacts_verified": checked,
            "reviewer_keys_verified": len(public_keys), "approvals_verified": approvals,\n            "provenance_records_verified": provenance_records, "audit_entries_verified": audit_entries,
            "package_sha256": sha256_file(package_path)}


def main() -> int:
    parser = argparse.ArgumentParser(prog="netopps-security", description="Institutional trust administration and evidence verification.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("verify-package"); p.add_argument("--package", type=Path, required=True)
    p = sub.add_parser("rotate-reviewer")
    p.add_argument("--registry", type=Path, required=True); p.add_argument("--old-fingerprint", required=True)
    p.add_argument("--new-public-key", type=Path, required=True); p.add_argument("--reviewer-id", required=True)
    p.add_argument("--display-name", required=True); p.add_argument("--organization", required=True)
    p.add_argument("--role", required=True); p.add_argument("--admin-private-key", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("revoke-reviewer")
    p.add_argument("--registry", type=Path, required=True); p.add_argument("--fingerprint", required=True)
    p.add_argument("--reason", required=True); p.add_argument("--admin-private-key", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-trust-change"); p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p = sub.add_parser("verify-checkpoint"); p.add_argument("--directory", type=Path, required=True); p.add_argument("--registry", type=Path, required=True); p.add_argument("--checkpoint", type=Path, required=True)
    p = sub.add_parser("checkpoint"); p.add_argument("--directory", type=Path, required=True); p.add_argument("--registry", type=Path, required=True); p.add_argument("--private-key", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("verify-policy"); p.add_argument("--directory", type=Path, required=True); p.add_argument("--registry", type=Path, required=True); p.add_argument("--policy", type=Path, required=True); p.add_argument("--approvals", type=Path, nargs="+", required=True)
    args = parser.parse_args()
    try:
        if args.command == "verify-package": result = verify_package(args.package)
        elif args.command == "verify-trust-change": result = verify_trust_change(args.receipt, args.registry)
        elif args.command == "rotate-reviewer":
            password = __import__("getpass").getpass("Trust administrator passphrase: ")
            fp = rotate_reviewer(args.registry, args.old_fingerprint, args.new_public_key, args.reviewer_id,
                                 args.display_name, args.organization, args.role, args.admin_private_key,
                                 password, args.receipt)
            result = {"new_fingerprint_sha256": fp, "receipt": str(args.receipt)}
        elif args.command == "revoke-reviewer":
            password = __import__("getpass").getpass("Trust administrator passphrase: ")
            revoke_reviewer(args.registry, args.fingerprint, args.reason, args.admin_private_key, password, args.receipt)
            result = {"revoked_fingerprint_sha256": args.fingerprint, "receipt": str(args.receipt)}
        elif args.command == "verify-checkpoint": result = verify_checkpoint(args.directory, args.registry, args.checkpoint)
        elif args.command == "verify-policy": result = verify_approval_policy(args.directory, args.registry, args.policy, args.approvals)
        else:
            password = __import__("getpass").getpass("Private-key passphrase: ")
            result = {"head_hash": create_checkpoint(args.directory, args.registry, args.private_key, password, args.output), "output": str(args.output)}
        print(json.dumps(result, indent=2)); return 0
    except (OSError, ValueError, KeyError, InvalidSignature) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
