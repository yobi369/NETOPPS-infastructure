""""Local-first institutional pilot manifest and evidence packaging tools."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys, zipfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

MAX_MANIFEST_BYTES = 1024 * 1024
PILOT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")
REQUIRED = {"schema_version", "pilot_id", "institution", "title", "status", "authorization", "artifacts", "evidence", "assessments"}
STATUSES = {"draft", "authorized", "in_progress", "closed"}
ROLES = {"baseline_topology", "baseline_dependencies", "candidate_topology", "candidate_dependencies", "assessment_report", "supporting_evidence"}
EVIDENCE_STATES = {"unreviewed", "accepted", "rejected", "superseded", "unknown"}

class PilotError(ValueError):
    pass

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def safe_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise PilotError("artifact path must be a non-empty POSIX relative path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise PilotError(f"unsafe artifact path: {relative!r}")
    target = (root / Path(*pure.parts)).resolve()
    if not target.is_relative_to(root.resolve()):
        raise PilotError(f"artifact escapes pilot directory: {relative!r}")
    if not target.is_file():
        raise PilotError(f"artifact does not exist or is not a regular file: {relative!r}")
    return target

def load_manifest(root: Path) -> dict[str, Any]:
    try:
        raw = (root / "pilot-manifest.json").read_bytes()
    except OSError as exc:
        raise PilotError(f"cannot read pilot-manifest.json: {exc}") from exc
    if len(raw) > MAX_MANIFEST_BYTES:
        raise PilotError("pilot manifest exceeds 1 MiB")
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotError(f"pilot manifest is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise PilotError("pilot manifest root must be an object")
    missing = sorted(REQUIRED - doc.keys())
    if missing:
        raise PilotError("pilot manifest missing required fields: " + ", ".join(missing))
    if isinstance(doc["schema_version"], bool) or doc["schema_version"] != 1:
        raise PilotError("schema_version must be integer 1")
    if not isinstance(doc["pilot_id"], str) or not PILOT_ID.fullmatch(doc["pilot_id"]):
        raise PilotError("pilot_id must be 3-64 safe characters")
    for field in ("institution", "title"):
        if not isinstance(doc[field], str) or not doc[field].strip() or len(doc[field]) > 200:
            raise PilotError(f"{field} must be a non-empty string of at most 200 characters")
    if doc["status"] not in STATUSES:
        raise PilotError("unsupported pilot status")
    auth = doc["authorization"]
    if not isinstance(auth, dict):
        raise PilotError("authorization must be an object")
    for field in ("reference", "environment", "data_classification"):
        if not isinstance(auth.get(field), str) or not auth[field].strip():
            raise PilotError(f"authorization.{field} is required")
    for field in ("artifacts", "evidence", "assessments"):
        if not isinstance(doc[field], list):
            raise PilotError(f"{field} must be an array")
    return doc

def validate_workspace(root: Path) -> list[str]:
    doc = load_manifest(root)
    errors: list[str] = []
    artifacts: dict[str, dict[str, Any]] = {}
    for i, item in enumerate(doc["artifacts"]):
        label = f"artifacts[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object"); continue
        ident, role, rel, expected = (item.get(k) for k in ("id", "role", "path", "sha256"))
        if not isinstance(ident, str) or not ident or ident in artifacts:
            errors.append(f"{label}.id must be unique and non-empty"); continue
        if role not in ROLES:
            errors.append(f"{label}.role is unsupported")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(f"{label}.sha256 must be a lowercase SHA-256 digest"); continue
        try:
            actual = sha256_file(safe_file(root, rel))
            if actual != expected:
                errors.append(f"{label} hash mismatch for {rel}")
        except (PilotError, OSError) as exc:
            errors.append(f"{label}: {exc}")
        artifacts[ident] = item
    evidence_ids: set[str] = set()
    for i, item in enumerate(doc["evidence"]):
        label = f"evidence[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object"); continue
        ident = item.get("id")
        if not isinstance(ident, str) or not ident or ident in evidence_ids:
            errors.append(f"{label}.id must be unique and non-empty"); continue
        evidence_ids.add(ident)
        if item.get("validation_status") not in EVIDENCE_STATES:
            errors.append(f"{label}.validation_status is unsupported")
        for field in ("claim", "source_reference", "owner", "permitted_use"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{label}.{field} is required")
        if item.get("artifact_id") is not None and item["artifact_id"] not in artifacts:
            errors.append(f"{label}.artifact_id does not reference a declared artifact")
        if item.get("collected_on"):
            try: date.fromisoformat(item["collected_on"])
            except (TypeError, ValueError): errors.append(f"{label}.collected_on must use YYYY-MM-DD")
    assessment_ids: set[str] = set()
    for i, item in enumerate(doc["assessments"]):
        label = f"assessments[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object"); continue
        ident = item.get("id")
        if not isinstance(ident, str) or not ident or ident in assessment_ids:
            errors.append(f"{label}.id must be unique and non-empty"); continue
        assessment_ids.add(ident)
        if item.get("kind") not in {"baseline", "candidate", "comparison"}:
            errors.append(f"{label}.kind is unsupported")
        report = artifacts.get(item.get("report_artifact_id"))
        if not report or report.get("role") != "assessment_report":
            errors.append(f"{label}.report_artifact_id must reference an assessment_report artifact")
        refs = item.get("evidence_ids", [])
        if not isinstance(refs, list) or any(ref not in evidence_ids for ref in refs):
            errors.append(f"{label}.evidence_ids must reference declared evidence records")
    for role in ("baseline_topology", "baseline_dependencies"):
        if not any(item.get("role") == role for item in artifacts.values()):
            errors.append(f"at least one {role} artifact is required")
    return errors

def init_workspace(root: Path, pilot_id: str, institution: str, title: str) -> None:
    if not PILOT_ID.fullmatch(pilot_id):
        raise PilotError("pilot_id must be 3-64 safe characters")
    if not institution.strip() or not title.strip():
        raise PilotError("institution and title are required")
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "pilot-manifest.json"
    if manifest.exists():
        raise PilotError("pilot-manifest.json already exists; refusing to overwrite")
    for folder in ("inputs/baseline", "inputs/candidate", "reports", "evidence"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    doc = {"schema_version": 1, "pilot_id": pilot_id, "institution": institution.strip(), "title": title.strip(),
           "status": "draft", "authorization": {"reference": "PENDING — written authorization required",
           "environment": "PENDING — institution-approved environment",
           "data_classification": "PENDING — institution-approved classification"},
           "artifacts": [], "evidence": [], "assessments": []}
    manifest.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    with (root / "evidence-register.csv").open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerow(["id", "claim", "source_reference", "owner", "collected_on", "validation_status", "permitted_use", "artifact_id", "reviewer", "reviewed_on", "limitations"])
    (root / "README.txt").write_text("Local NETOPPS pilot workspace. Keep within institution-approved storage. Never place credentials, personal data or unredacted production topology in public repositories.\n", encoding="utf-8")

def package_workspace(root: Path, output: Path) -> None:
    errors = validate_workspace(root)
    if errors:
        raise PilotError("workspace validation failed:\n- " + "\n- ".join(errors))
    output = output.resolve()
    if output.is_relative_to(root.resolve()):
        raise PilotError("package output must be outside the pilot workspace")
    doc = load_manifest(root)
    files = {"pilot-manifest.json": root / "pilot-manifest.json", "evidence-register.csv": root / "evidence-register.csv"}
    for item in doc["artifacts"]:
        files[item["path"]] = safe_file(root, item["path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(files.items()):
            archive.write(path, name)

def main() -> int:
    parser = argparse.ArgumentParser(prog="netopps-pilot", description="Manage a local, evidence-linked institutional pilot workspace.")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init"); init.add_argument("--directory", type=Path, required=True); init.add_argument("--pilot-id", required=True); init.add_argument("--institution", required=True); init.add_argument("--title", required=True)
    validate = commands.add_parser("validate"); validate.add_argument("--directory", type=Path, default=Path("."))
    package = commands.add_parser("package"); package.add_argument("--directory", type=Path, default=Path(".")); package.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            init_workspace(args.directory, args.pilot_id, args.institution, args.title); print(f"Created local pilot workspace: {args.directory}"); return 0
        if args.command == "validate":
            errors = validate_workspace(args.directory); print(json.dumps({"valid": not errors, "errors": errors}, indent=2)); return 0 if not errors else 1
        package_workspace(args.directory, args.output); print(f"Created validated pilot package: {args.output}"); return 0
    except (OSError, PilotError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2

if __name__ == "__main__":
    raise SystemExit(main())
