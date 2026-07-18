#!/usr/bin/env python3
"""Capture and independently verify Rover Bean first-article evidence bundles."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from typing import Any, BinaryIO, Iterator
from urllib.parse import urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = Path("commissioning/plan-v2.json")
DEFAULT_BUNDLE = ROOT / "output" / "commissioning" / "first-article-v2"
EVIDENCE_NAME = "evidence.json"
MANIFEST_NAME = "bundle-manifest.json"
SIGNATURE_NAME = MANIFEST_NAME + ".sig"
EVIDENCE_SCHEMA = 2
MANIFEST_SCHEMA = 1
GENESIS_HASH = "0" * 64
NAMESPACE = "rover-bean-commissioning"
MAX_ATTACHMENT_BYTES = 512 * 1024 * 1024
MAX_AUTOMATED_OUTPUT_BYTES = 16 * 1024 * 1024
OBJECT_RE = re.compile(r"^[0-9a-f]{64}$")
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")
ROBOT_SERIAL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SIGNER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,127}$")
INTEGER_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)$")
NUMBER_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$")
MEASUREMENT_TYPES = ("string", "boolean", "integer", "number")

SOURCE_BLOBS = {
    "guide_sha256": "output/pdf/codex_robot_body_v2_assembly_guide.pdf",
    "body_3mf_sha256": "cad/bambu/codex_robot_body_v2_p1s.3mf",
    "coupon_3mf_sha256": "cad/bambu/codex_robot_body_v2_coupons_p1s.3mf",
    "fixture_sha256": "commissioning/fixture-v1.json",
}
SOURCE_TREES = {
    "firmware_tree_sha256": "firmware/pico2-safety",
    "robotd_tree_sha256": "software/robotd",
    "appliance_tree_sha256": "software/appliance",
}


class EvidenceError(ValueError):
    """A fail-closed evidence validation error."""


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    """Return the schema's reproducible canonical JSON representation."""
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return text.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise EvidenceError(f"value is not canonical JSON: {exc}") from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def validate_operator(value: str) -> None:
    if not value or len(value) > 128 or any(ord(character) < 32 or character in "|\x7f" for character in value):
        raise EvidenceError("operator must be 1-128 printable characters without table delimiters")


def validate_signer(value: str) -> None:
    if not SIGNER_RE.fullmatch(value):
        raise EvidenceError("signer principal contains unsupported characters")


def validate_origin_url(value: str) -> None:
    if not value or any(ord(character) < 32 for character in value):
        raise EvidenceError("source origin URL is missing or unsafe")
    parsed = urlsplit(value)
    if parsed.scheme in ("http", "https") and (parsed.username or parsed.password):
        raise EvidenceError("source origin URL must not contain embedded credentials")


def fsync_dir(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".tmp-{path.name}-{uuid4().hex}"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
        fsync_dir(path.parent)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


@contextmanager
def bundle_lock(bundle: Path, exclusive: bool = True) -> Iterator[None]:
    bundle.parent.mkdir(parents=True, exist_ok=True)
    lock_path = bundle.parent / f".{bundle.name}.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def git(repo: Path, arguments: list[str], *, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout


def resolve_commit(repo: Path, reference: str) -> str:
    commit = git(repo, ["rev-parse", "--verify", f"{reference}^{{commit}}"])
    value = commit.decode("ascii").strip()
    if not COMMIT_RE.fullmatch(value):
        raise EvidenceError(f"Git returned an invalid commit ID for {reference!r}")
    return value


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    return git(repo, ["show", f"{commit}:{path}"])


def git_tree_digest(repo: Path, commit: str, tree_path: str) -> str:
    raw = git(repo, ["ls-tree", "-r", "-z", commit, "--", tree_path])
    entries: list[tuple[bytes, bytes]] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        try:
            metadata, path = item.split(b"\t", 1)
            _mode, kind, object_id = metadata.split(b" ", 2)
        except ValueError as exc:
            raise EvidenceError(f"malformed git tree entry under {tree_path}") from exc
        if kind != b"blob":
            continue
        blob = git(repo, ["cat-file", "blob", object_id.decode("ascii")])
        entries.append((path, hashlib.sha256(blob).hexdigest().encode("ascii")))
    if not entries:
        raise EvidenceError(f"source tree is empty at {commit}:{tree_path}")
    serialized = b"".join(path + b"\0" + digest + b"\n" for path, digest in sorted(entries))
    return sha256_bytes(serialized)


def source_provenance(repo: Path, commit: str) -> dict[str, str]:
    provenance = {
        field: sha256_bytes(git_blob(repo, commit, path))
        for field, path in SOURCE_BLOBS.items()
    }
    provenance.update({
        field: git_tree_digest(repo, commit, path)
        for field, path in SOURCE_TREES.items()
    })
    return provenance


def validate_plan_schema(plan: dict[str, Any]) -> None:
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise EvidenceError("commissioning plan must contain steps")
    type_groups = plan.get("measurement_types")
    if not isinstance(type_groups, dict) or set(type_groups) != set(MEASUREMENT_TYPES):
        raise EvidenceError("commissioning plan must declare string/boolean/integer/number measurement types")
    declared_types: dict[str, str] = {}
    for type_name in MEASUREMENT_TYPES:
        fields = type_groups[type_name]
        if not isinstance(fields, list) or len(fields) != len(set(fields)):
            raise EvidenceError(f"commissioning plan {type_name} measurement list is malformed")
        for field in fields:
            if not isinstance(field, str) or not field or field in declared_types:
                raise EvidenceError(f"commissioning measurement type is duplicated or malformed: {field!r}")
            declared_types[field] = type_name
    step_ids: set[str] = set()
    used_measurements: set[str] = set()
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("id"), str):
            raise EvidenceError("commissioning plan contains a malformed step")
        step_id = step["id"]
        if step_id in step_ids:
            raise EvidenceError(f"commissioning plan repeats step {step_id}")
        step_ids.add(step_id)
        required = step.get("required_measurements", [])
        if not isinstance(required, list) or len(required) != len(set(required)):
            raise EvidenceError(f"{step_id}: required measurements are malformed or duplicated")
        used_measurements.update(required)
        for field in required:
            if field not in declared_types:
                raise EvidenceError(f"{step_id}: measurement {field} has no declared type")
        artifacts = step.get("required_artifacts", [])
        roles: set[str] = set()
        bound_measurements: set[str] = set()
        for artifact in artifacts:
            if not isinstance(artifact, dict) or not isinstance(artifact.get("role"), str):
                raise EvidenceError(f"{step_id}: malformed required artifact")
            role = artifact["role"]
            if role in roles:
                raise EvidenceError(f"{step_id}: duplicate artifact role {role}")
            roles.add(role)
            measurement = artifact.get("measurement")
            value_kind = artifact.get("value")
            if measurement is None:
                if value_kind is not None:
                    raise EvidenceError(f"{step_id}: artifact {role} has a value kind without a measurement")
                continue
            if measurement not in required or value_kind not in ("uri", "sha256"):
                raise EvidenceError(f"{step_id}: artifact {role} has an invalid measurement binding")
            bound_measurements.add(measurement)
        automatic = set(SOURCE_BLOBS) | set(SOURCE_TREES)
        for field in required:
            if (field.endswith("_uri") or field.endswith("_sha256")) and field not in bound_measurements | automatic:
                raise EvidenceError(f"{step_id}: evidence field {field} is not bound to bytes")
        automated_role = step.get("automated_artifact_role")
        if step.get("command") and automated_role not in roles:
            raise EvidenceError(f"{step_id}: safe command lacks a declared automated artifact role")
        for rule in step.get("acceptance", []):
            if (rule.get("field") not in required or rule.get("op") not in ("eq", "lte", "gte")
                    or "value" not in rule):
                raise EvidenceError(f"{step_id}: malformed acceptance predicate")
            if not measurement_matches_type(rule["value"], declared_types[rule["field"]]):
                raise EvidenceError(f"{step_id}: acceptance value has the wrong measurement type")
    unused_types = set(declared_types) - used_measurements
    if unused_types:
        raise EvidenceError(f"commissioning plan declares unused measurement types: {', '.join(sorted(unused_types))}")


def plan_at(repo: Path, commit: str | None = None) -> tuple[dict[str, Any], str]:
    raw = git_blob(repo, commit, PLAN_PATH.as_posix()) if commit else (repo / PLAN_PATH).read_bytes()
    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid commissioning plan JSON: {exc}") from exc
    if plan.get("schema_version") != 2:
        raise EvidenceError("commissioning plan must use schema_version 2")
    validate_plan_schema(plan)
    return plan, sha256_bytes(raw)


def validate_scalar(value: Any, field: str) -> None:
    if isinstance(value, (dict, list)) or value is None:
        raise EvidenceError(f"measurement {field} must be a non-null JSON scalar")
    if isinstance(value, float) and not math.isfinite(value):
        raise EvidenceError(f"measurement {field} must be finite")
    canonical_json(value)


def plan_measurement_types(plan: dict[str, Any]) -> dict[str, str]:
    return {
        field: type_name
        for type_name, fields in plan["measurement_types"].items()
        for field in fields
    }


def measurement_matches_type(value: Any, type_name: str) -> bool:
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "boolean":
        return type(value) is bool
    if type_name == "integer":
        return type(value) is int
    if type_name == "number":
        return type(value) in (int, float) and (not isinstance(value, float) or math.isfinite(value))
    return False


def coerce_measurements(values: dict[str, Any], types: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field, raw in values.items():
        type_name = types[field]
        if not isinstance(raw, str):
            if not measurement_matches_type(raw, type_name):
                raise EvidenceError(f"measurement {field} must be {type_name}")
            parsed = raw
        elif type_name == "string":
            parsed = raw
        elif type_name == "boolean":
            if raw not in ("true", "false"):
                raise EvidenceError(f"measurement {field} must be exactly true or false")
            parsed = raw == "true"
        elif type_name == "integer":
            if not INTEGER_RE.fullmatch(raw):
                raise EvidenceError(f"measurement {field} must be a canonical integer")
            parsed = int(raw)
        elif type_name == "number":
            if not NUMBER_RE.fullmatch(raw):
                raise EvidenceError(f"measurement {field} must be a canonical finite number")
            parsed = float(raw) if any(character in raw for character in ".eE") else int(raw)
        else:
            raise EvidenceError(f"measurement {field} has unknown type {type_name!r}")
        validate_scalar(parsed, field)
        result[field] = parsed
    return result


def parse_measurements(values: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise EvidenceError(f"measurement must be key=value: {value!r}")
        key, raw = value.split("=", 1)
        if not key or key in result:
            raise EvidenceError(f"duplicate or empty measurement name: {key!r}")
        result[key] = raw
    return result


def parse_assignments(values: list[str], description: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise EvidenceError(f"{description} must be role=path: {value!r}")
        role, path = value.split("=", 1)
        if not role or not path or role in result:
            raise EvidenceError(f"duplicate or empty {description} role: {role!r}")
        result[role] = path
    return result


def evidence_path(bundle: Path) -> Path:
    return bundle / EVIDENCE_NAME


def objects_path(bundle: Path) -> Path:
    return bundle / "objects" / "sha256"


def load_evidence(bundle: Path) -> dict[str, Any]:
    path = evidence_path(bundle)
    if not path.exists():
        raise EvidenceError(f"no evidence bundle at {bundle}; run init first")
    if path.is_symlink() or not path.is_file():
        raise EvidenceError("evidence.json must be a regular file, not a symlink")
    raw = path.read_bytes()
    try:
        evidence = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid evidence JSON: {exc}") from exc
    if not isinstance(evidence, dict):
        raise EvidenceError("evidence root must be an object")
    schema = evidence.get("schema_version")
    if schema == 1:
        raise EvidenceError("legacy evidence schema v1 is unsupported; start a v2 bundle and re-record observations")
    if schema != EVIDENCE_SCHEMA:
        raise EvidenceError(f"unsupported or missing evidence schema_version: {schema!r}")
    if raw != canonical_json(evidence):
        raise EvidenceError("evidence.json is not canonical JSON")
    required_strings = (
        "bundle_id", "robot_serial", "source_commit", "source_ref", "source_ref_commit",
        "plan_revision", "plan_sha256", "created_at", "created_by",
    )
    for field in required_strings:
        if not isinstance(evidence.get(field), str) or not evidence[field]:
            raise EvidenceError(f"evidence identity field {field} is missing or invalid")
    if not COMMIT_RE.fullmatch(evidence["source_commit"]):
        raise EvidenceError("evidence source_commit is invalid")
    if not COMMIT_RE.fullmatch(evidence["source_ref_commit"]):
        raise EvidenceError("evidence source_ref_commit is invalid")
    if not ROBOT_SERIAL_RE.fullmatch(evidence["robot_serial"]):
        raise EvidenceError("evidence robot_serial is invalid")
    if not OBJECT_RE.fullmatch(evidence["plan_sha256"]):
        raise EvidenceError("evidence plan_sha256 is invalid")
    if not RFC3339_RE.fullmatch(evidence["created_at"]):
        raise EvidenceError("evidence created_at is not UTC RFC3339 seconds")
    if not isinstance(evidence.get("source_provenance"), dict):
        raise EvidenceError("evidence source_provenance is missing or invalid")
    validate_operator(evidence["created_by"])
    validate_origin_url(evidence.get("origin_url", ""))
    if not isinstance(evidence.get("events"), list):
        raise EvidenceError("evidence events must be an array")
    return evidence


def save_evidence(bundle: Path, evidence: dict[str, Any]) -> None:
    atomic_write(evidence_path(bundle), canonical_json(evidence))


def ensure_bundle_layout(bundle: Path) -> None:
    if bundle.exists() and (bundle.is_symlink() or not bundle.is_dir()):
        raise EvidenceError("bundle path must be a real directory")
    bundle.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(bundle, 0o700)
    directory = objects_path(bundle)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)


def event_digest(event: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in event.items() if key != "event_sha256"}
    return sha256_bytes(canonical_json(unsigned))


def verify_event_chain(evidence: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    previous = GENESIS_HASH
    for index, event in enumerate(evidence.get("events", []), start=1):
        if not isinstance(event, dict):
            failures.append(f"event {index}: not an object")
            continue
        if event.get("sequence") != index:
            failures.append(f"event {index}: sequence is {event.get('sequence')!r}")
        if event.get("result") not in ("pass", "fail", "blocked"):
            failures.append(f"event {index}: invalid result {event.get('result')!r}")
        if not isinstance(event.get("step_id"), str) or not event["step_id"]:
            failures.append(f"event {index}: step_id is missing")
        if not isinstance(event.get("operator"), str) or not event["operator"]:
            failures.append(f"event {index}: operator is missing")
        else:
            try:
                validate_operator(event["operator"])
            except EvidenceError as exc:
                failures.append(f"event {index}: {exc}")
        if not isinstance(event.get("note"), str):
            failures.append(f"event {index}: note is not text")
        if not isinstance(event.get("measurements"), dict):
            failures.append(f"event {index}: measurements are not an object")
        if not isinstance(event.get("attachments"), list):
            failures.append(f"event {index}: attachments are not an array")
        if not isinstance(event.get("attestations"), list):
            failures.append(f"event {index}: attestations are not an array")
        if event.get("previous_event_sha256") != previous:
            failures.append(f"event {index}: previous hash does not match")
        actual = event_digest(event)
        if event.get("event_sha256") != actual:
            failures.append(f"event {index}: event hash does not match")
        timestamp = event.get("recorded_at")
        if not isinstance(timestamp, str) or not RFC3339_RE.fullmatch(timestamp):
            failures.append(f"event {index}: recorded_at is not UTC RFC3339 seconds")
        previous = event.get("event_sha256", "")
    return failures


def latest_events(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for event in evidence.get("events", []):
        if isinstance(event, dict) and isinstance(event.get("step_id"), str):
            result[event["step_id"]] = event
    return result


def artifact_specs(step: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["role"]: item for item in step.get("required_artifacts", [])}


def validate_acceptance(step: dict[str, Any], measurements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for rule in step.get("acceptance", []):
        field = rule["field"]
        if field not in measurements or measurements[field] in (None, ""):
            continue
        actual = measurements[field]
        expected = rule["value"]
        operation = rule["op"]
        try:
            if operation == "eq":
                accepted = actual == expected
            elif operation == "lte":
                accepted = actual <= expected
            elif operation == "gte":
                accepted = actual >= expected
            else:
                accepted = False
        except TypeError:
            accepted = False
        if not accepted:
            failures.append(f"{step['id']}: {field}={actual!r} fails {operation} {expected!r}")
    return failures


def verify_steps(plan: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    steps = {step["id"]: step for step in plan["steps"]}
    measurement_types = plan_measurement_types(plan)
    current = latest_events(evidence)
    for event in evidence.get("events", []):
        if event.get("step_id") not in steps:
            failures.append(f"event {event.get('sequence')}: unknown step {event.get('step_id')!r}")
    role_digests: dict[str, tuple[str, str]] = {}
    for step in plan["steps"]:
        record = current.get(step["id"])
        if not record:
            failures.append(f"{step['id']}: no record")
            continue
        if record.get("result") != "pass":
            failures.append(f"{step['id']}: result is {record.get('result')!r}")
        measurements = record.get("measurements", {})
        if not isinstance(measurements, dict):
            failures.append(f"{step['id']}: measurements are not an object")
            measurements = {}
        for field in step.get("required_measurements", []):
            if field not in measurements or measurements[field] in (None, ""):
                failures.append(f"{step['id']}: missing measurement {field}")
            else:
                try:
                    validate_scalar(measurements[field], field)
                    if not measurement_matches_type(measurements[field], measurement_types[field]):
                        failures.append(
                            f"{step['id']}: measurement {field} must be {measurement_types[field]}")
                except EvidenceError as exc:
                    failures.append(f"{step['id']}: {exc}")
        failures.extend(validate_acceptance(step, measurements))
        attachments = record.get("attachments", [])
        by_role: dict[str, dict[str, Any]] = {}
        for item in attachments:
            if not isinstance(item, dict):
                failures.append(f"{step['id']}: attachment is not an object")
                continue
            role = item.get("role")
            if role in by_role:
                failures.append(f"{step['id']}: duplicate artifact role {role}")
            if role not in artifact_specs(step):
                failures.append(f"{step['id']}: undeclared artifact role {role!r}")
            digest = item.get("sha256")
            if not isinstance(digest, str) or not OBJECT_RE.fullmatch(digest):
                failures.append(f"{step['id']}: artifact {role} has invalid digest")
            if item.get("uri") != f"evidence:sha256:{digest}":
                failures.append(f"{step['id']}: artifact {role} has invalid URI")
            if not isinstance(item.get("size"), int) or item["size"] < 0:
                failures.append(f"{step['id']}: artifact {role} has invalid size")
            name = item.get("name")
            if (not isinstance(name, str) or not name or Path(name).name != name
                    or any(ord(character) < 32 for character in name)):
                failures.append(f"{step['id']}: artifact {role} has invalid source name")
            if isinstance(role, str):
                by_role[role] = item
        for role, spec in artifact_specs(step).items():
            attachment = by_role.get(role)
            if not attachment:
                failures.append(f"{step['id']}: missing required artifact {role}")
                continue
            digest = attachment.get("sha256")
            measurement = spec.get("measurement")
            if spec.get("value") == "uri" and measurements.get(measurement) != f"evidence:sha256:{digest}":
                failures.append(f"{step['id']}: {measurement} does not resolve to artifact {role}")
            if spec.get("value") == "sha256" and measurements.get(measurement) != digest:
                failures.append(f"{step['id']}: {measurement} does not match artifact {role}")
            if digest in role_digests and not spec.get("allow_reuse", False):
                prior_step, prior_role = role_digests[digest]
                if (prior_step, prior_role) != (step["id"], role):
                    failures.append(
                        f"{step['id']}: artifact {role} reuses {prior_step}/{prior_role} without permission")
            else:
                role_digests[digest] = (step["id"], role)
        required_attestations = set(step.get("attestations", []))
        actual_attestations = set(record.get("attestations", []))
        for attestation in sorted(required_attestations - actual_attestations):
            failures.append(f"{step['id']}: missing attestation {attestation}")
    first = current.get("C001", {})
    if first.get("measurements", {}).get("robot_serial") != evidence.get("robot_serial"):
        failures.append("C001: robot_serial does not match bundle identity")
    return failures


# Compatibility name retained for callers of the original commissioning module.
verify = verify_steps


def attachment_references(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    references: dict[str, dict[str, Any]] = {}
    for event in evidence.get("events", []):
        for attachment in event.get("attachments", []):
            digest = attachment.get("sha256")
            if isinstance(digest, str):
                existing = references.get(digest)
                identity = {
                    "sha256": digest,
                    "size": attachment.get("size"),
                    "uri": attachment.get("uri"),
                }
                if existing and existing != identity:
                    raise EvidenceError(f"conflicting metadata for object {digest}")
                references[digest] = identity
    return references


def scan_bundle_files(bundle: Path) -> set[str]:
    files: set[str] = set()
    root = bundle.resolve(strict=True)
    for current, directories, filenames in os.walk(bundle, followlinks=False):
        current_path = Path(current)
        for name in [*directories, *filenames]:
            candidate = current_path / name
            info = candidate.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise EvidenceError(f"symlink is forbidden in evidence bundle: {candidate.relative_to(bundle)}")
        for filename in filenames:
            candidate = current_path / filename
            info = candidate.stat()
            if not stat.S_ISREG(info.st_mode):
                raise EvidenceError(f"non-regular file in evidence bundle: {candidate.relative_to(bundle)}")
            resolved = candidate.resolve(strict=True)
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise EvidenceError(f"bundle path escapes root: {candidate}") from exc
            files.add(candidate.relative_to(bundle).as_posix())
    return files


def verify_objects(bundle: Path, evidence: dict[str, Any], *, sealed: bool) -> list[str]:
    failures: list[str] = []
    try:
        references = attachment_references(evidence)
        files = scan_bundle_files(bundle)
    except EvidenceError as exc:
        return [str(exc)]
    expected = {EVIDENCE_NAME}
    for digest, reference in references.items():
        if not OBJECT_RE.fullmatch(digest):
            failures.append(f"malformed object digest {digest!r}")
            continue
        expected.add(f"objects/sha256/{digest}")
        path = objects_path(bundle) / digest
        if not path.exists():
            failures.append(f"missing object {digest}")
            continue
        info = path.stat()
        if info.st_nlink != 1:
            failures.append(f"object {digest} has {info.st_nlink} hard links")
        actual, size = sha256_file(path)
        if actual != digest:
            failures.append(f"object {digest} content hash is {actual}")
        if reference.get("size") != size:
            failures.append(f"object {digest} size is {size}, expected {reference.get('size')!r}")
        if reference.get("uri") != f"evidence:sha256:{digest}":
            failures.append(f"object {digest} has invalid evidence URI")
    if sealed:
        expected.update({MANIFEST_NAME, SIGNATURE_NAME})
    extras = sorted(files - expected)
    missing = sorted(expected - files)
    failures.extend(f"unlisted bundle file {path}" for path in extras)
    failures.extend(f"missing bundle file {path}" for path in missing)
    return failures


def verify_provenance(
    evidence: dict[str, Any], source_repo: Path
) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    commit = evidence.get("source_commit")
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        return None, ["bundle source_commit is invalid"]
    try:
        plan, plan_hash = plan_at(source_repo, commit)
        if plan_hash != evidence.get("plan_sha256"):
            failures.append("commissioning plan hash does not match source commit")
        if plan.get("revision") != evidence.get("plan_revision"):
            failures.append("commissioning plan revision does not match source commit")
        computed = source_provenance(source_repo, commit)
        if computed != evidence.get("source_provenance"):
            failures.append("source artifact/tree provenance does not match source commit")
        ref = evidence.get("source_ref")
        resolved_ref = resolve_commit(source_repo, ref)
        if resolved_ref != evidence.get("source_ref_commit"):
            failures.append("source ref no longer resolves to the recorded commit")
        ancestor = subprocess.run(
            ["git", "-C", str(source_repo), "merge-base", "--is-ancestor", commit, resolved_ref],
            check=False,
        )
        if ancestor.returncode != 0:
            failures.append("source commit is not reachable from recorded source ref")
    except EvidenceError as exc:
        failures.append(str(exc))
        plan = None
    return plan, failures


def validate_unsealed(bundle: Path, source_repo: Path) -> tuple[dict[str, Any], dict[str, Any] | None, list[str]]:
    evidence = load_evidence(bundle)
    failures = verify_event_chain(evidence)
    plan, provenance_failures = verify_provenance(evidence, source_repo)
    failures.extend(provenance_failures)
    if plan is not None:
        failures.extend(verify_steps(plan, evidence))
    failures.extend(verify_objects(bundle, evidence, sealed=False))
    return evidence, plan, failures


def install_object_from_stream(bundle: Path, source: BinaryIO, maximum: int) -> dict[str, Any]:
    directory = objects_path(bundle)
    temporary = directory / f".tmp-import-{uuid4().hex}"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    digest = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as target:
            while chunk := source.read(1024 * 1024):
                size += len(chunk)
                if size > maximum:
                    raise EvidenceError(f"attachment exceeds {maximum} bytes")
                digest.update(chunk)
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        hexdigest = digest.hexdigest()
        destination = directory / hexdigest
        if destination.exists():
            destination_info = destination.lstat()
            if stat.S_ISLNK(destination_info.st_mode) or not stat.S_ISREG(destination_info.st_mode):
                raise EvidenceError(f"existing object path is unsafe: {hexdigest}")
            if destination_info.st_nlink != 1:
                raise EvidenceError(f"existing object {hexdigest} has hard links")
            existing, existing_size = sha256_file(destination)
            if existing != hexdigest or existing_size != size:
                raise EvidenceError(f"existing object {hexdigest} is corrupt")
            temporary.unlink()
        else:
            os.replace(temporary, destination)
            os.chmod(destination, 0o400)
            fsync_dir(directory)
        return {"sha256": hexdigest, "size": size, "uri": f"evidence:sha256:{hexdigest}"}
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def import_attachment(bundle: Path, path: Path) -> dict[str, Any]:
    if not hasattr(os, "O_NOFOLLOW"):
        raise EvidenceError("this platform lacks O_NOFOLLOW; evidence import is unsupported")
    try:
        path_info = path.lstat()
        if stat.S_ISLNK(path_info.st_mode):
            raise EvidenceError(f"attachment may not be a symlink: {path}")
        if not stat.S_ISREG(path_info.st_mode):
            raise EvidenceError(f"attachment is not a regular file: {path}")
    except FileNotFoundError as exc:
        raise EvidenceError(f"attachment does not exist: {path}") from exc
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise EvidenceError(f"cannot safely open attachment {path}: {exc}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise EvidenceError(f"attachment is not a regular file: {path}")
        if info.st_size > MAX_ATTACHMENT_BYTES:
            raise EvidenceError(f"attachment exceeds {MAX_ATTACHMENT_BYTES} bytes")
        source = os.fdopen(descriptor, "rb", closefd=True)
        descriptor = -1
        with source:
            installed = install_object_from_stream(bundle, source, MAX_ATTACHMENT_BYTES)
            after = os.fstat(source.fileno())
            if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
            ):
                raise EvidenceError(f"attachment changed while it was being imported: {path}")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    installed["name"] = path.name
    return installed


def import_bytes(bundle: Path, data: bytes, name: str) -> dict[str, Any]:
    if len(data) > MAX_AUTOMATED_OUTPUT_BYTES:
        raise EvidenceError("automated output exceeded the capture limit")
    from io import BytesIO
    installed = install_object_from_stream(bundle, BytesIO(data), MAX_AUTOMATED_OUTPUT_BYTES)
    installed["name"] = name
    return installed


def ensure_not_sealed(bundle: Path) -> None:
    if (bundle / MANIFEST_NAME).exists() or (bundle / SIGNATURE_NAME).exists():
        raise EvidenceError("bundle has seal material; start a superseding bundle for corrections")


def initialize_bundle(
    bundle: Path,
    source_repo: Path,
    robot_serial: str,
    operator: str,
    source_ref: str,
    supersedes_bundle: Path | None = None,
    supersedes_allowed_signers: Path | None = None,
    supersedes_signer: str | None = None,
) -> dict[str, Any]:
    with bundle_lock(bundle):
        if not ROBOT_SERIAL_RE.fullmatch(robot_serial):
            raise EvidenceError("robot serial must use 1-64 letters, digits, dots, underscores, or hyphens")
        validate_operator(operator)
        if bundle.is_symlink() or (bundle.exists() and not bundle.is_dir()):
            raise EvidenceError("bundle path must be a new real directory")
        if bundle.exists() and any(bundle.iterdir()):
            raise EvidenceError(f"bundle directory is not empty: {bundle}")
        if not source_ref.startswith("refs/tags/"):
            raise EvidenceError("source-ref must be an immutable release tag under refs/tags/")
        if git(source_repo, ["status", "--porcelain", "--untracked-files=no"]).strip():
            raise EvidenceError("source repository has tracked changes; commit them before init")
        commit = resolve_commit(source_repo, "HEAD")
        resolved_ref = resolve_commit(source_repo, source_ref)
        ancestor = subprocess.run(
            ["git", "-C", str(source_repo), "merge-base", "--is-ancestor", commit, resolved_ref],
            check=False,
        )
        if ancestor.returncode != 0:
            raise EvidenceError("HEAD is not reachable from the requested source ref")
        origin_url = git(source_repo, ["remote", "get-url", "origin"]).decode("utf-8").strip()
        validate_origin_url(origin_url)
        plan, plan_hash = plan_at(source_repo, commit)
        supersedes = None
        if supersedes_bundle is not None:
            if supersedes_allowed_signers is None or not supersedes_signer:
                raise EvidenceError(
                    "superseding a bundle requires its out-of-band allowed signers and signer principal")
            prior = load_evidence(supersedes_bundle)
            manifest_path = supersedes_bundle / MANIFEST_NAME
            signature_path = supersedes_bundle / SIGNATURE_NAME
            if not manifest_path.is_file() or not signature_path.is_file():
                raise EvidenceError("superseded bundle must contain a complete seal")
            prior_manifest = json.loads(manifest_path.read_bytes())
            if prior_manifest.get("bundle_id") != prior.get("bundle_id"):
                raise EvidenceError("superseded bundle manifest identity mismatch")
            completeness, integrity, trust = verify_sealed_bundle(
                supersedes_bundle,
                source_repo,
                supersedes_allowed_signers,
                supersedes_signer,
                prior["robot_serial"],
            )
            if completeness or integrity or trust:
                raise EvidenceError(
                    "superseded bundle does not independently verify:\n- "
                    + "\n- ".join(completeness + integrity + trust))
            supersedes = {
                "bundle_id": prior["bundle_id"],
                "manifest_sha256": sha256_file(manifest_path)[0],
            }
        ensure_bundle_layout(bundle)
        evidence: dict[str, Any] = {
            "schema_version": EVIDENCE_SCHEMA,
            "bundle_id": str(uuid4()),
            "robot_serial": robot_serial,
            "source_commit": commit,
            "source_ref": source_ref,
            "source_ref_commit": resolved_ref,
            "origin_url": origin_url,
            "plan_revision": plan["revision"],
            "plan_sha256": plan_hash,
            "source_provenance": source_provenance(source_repo, commit),
            "created_at": now(),
            "created_by": operator,
            "supersedes": supersedes,
            "events": [],
        }
        save_evidence(bundle, evidence)
        return evidence


def append_event(
    bundle: Path,
    source_repo: Path,
    step_id: str,
    result: str,
    operator: str,
    note: str,
    measurements: dict[str, Any],
    attachment_paths: dict[str, str],
    attestations: list[str],
    automated_attachment: tuple[str, bytes, str] | None = None,
) -> dict[str, Any]:
    with bundle_lock(bundle):
        validate_operator(operator)
        ensure_not_sealed(bundle)
        evidence = load_evidence(bundle)
        plan, failures = verify_provenance(evidence, source_repo)
        if failures or plan is None:
            raise EvidenceError("; ".join(failures))
        steps = {step["id"]: step for step in plan["steps"]}
        step = steps.get(step_id)
        if step is None:
            raise EvidenceError(f"unknown step {step_id}")
        allowed_measurements = set(step.get("required_measurements", []))
        automatic_fields = set(evidence["source_provenance"]) | {"robot_serial"}
        unknown = set(measurements) - allowed_measurements
        if unknown:
            raise EvidenceError(f"unknown measurements for {step_id}: {', '.join(sorted(unknown))}")
        if set(measurements) & automatic_fields:
            raise EvidenceError("source-controlled C001 measurements are auto-derived")
        if step_id == "C001":
            measurements = {
                **measurements,
                "robot_serial": evidence["robot_serial"],
                **evidence["source_provenance"],
            }
        specs = artifact_specs(step)
        unknown_roles = set(attachment_paths) - set(specs)
        if unknown_roles:
            raise EvidenceError(f"unknown artifact roles for {step_id}: {', '.join(sorted(unknown_roles))}")
        attachments: list[dict[str, Any]] = []
        for role, path in attachment_paths.items():
            attachment = import_attachment(bundle, Path(path))
            attachment["role"] = role
            attachments.append(attachment)
        if automated_attachment is not None:
            role, data, name = automated_attachment
            if role not in specs:
                raise EvidenceError(f"automated artifact role {role} is not declared for {step_id}")
            attachment = import_bytes(bundle, data, name)
            attachment["role"] = role
            attachments.append(attachment)
        for attachment in attachments:
            spec = specs[attachment["role"]]
            measurement = spec.get("measurement")
            if spec.get("value") == "uri":
                measurements[measurement] = attachment["uri"]
            elif spec.get("value") == "sha256":
                measurements[measurement] = attachment["sha256"]
        measurements = coerce_measurements(measurements, plan_measurement_types(plan))
        undeclared_attestations = set(attestations) - set(step.get("attestations", []))
        if undeclared_attestations:
            raise EvidenceError(
                f"undeclared attestations for {step_id}: {', '.join(sorted(undeclared_attestations))}")
        sequence = len(evidence["events"]) + 1
        previous = evidence["events"][-1]["event_sha256"] if evidence["events"] else GENESIS_HASH
        event: dict[str, Any] = {
            "sequence": sequence,
            "step_id": step_id,
            "result": result,
            "operator": operator,
            "recorded_at": now(),
            "note": note,
            "measurements": measurements,
            "attachments": sorted(attachments, key=lambda item: item["role"]),
            "attestations": sorted(attestations),
            "previous_event_sha256": previous,
        }
        event["event_sha256"] = event_digest(event)
        evidence["events"].append(event)
        save_evidence(bundle, evidence)
        return event


def cleanup_orphans(bundle: Path) -> list[str]:
    removed: list[str] = []
    with bundle_lock(bundle):
        manifest_candidate = bundle / MANIFEST_NAME
        signature_candidate = bundle / SIGNATURE_NAME
        if manifest_candidate.exists() and signature_candidate.exists():
            completed = subprocess.run(
                ["ssh-keygen", "-Y", "check-novalidate", "-n", NAMESPACE,
                 "-s", str(signature_candidate)],
                input=manifest_candidate.read_bytes(), stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False)
            if completed.returncode == 0:
                raise EvidenceError("valid seal material cannot be cleaned; start a superseding bundle")
        evidence = load_evidence(bundle)
        referenced = set(attachment_references(evidence))
        for candidate in objects_path(bundle).iterdir():
            if candidate.name.startswith(".tmp-"):
                candidate.unlink()
                removed.append(candidate.name)
            elif OBJECT_RE.fullmatch(candidate.name) and candidate.name not in referenced:
                digest, _size = sha256_file(candidate)
                if digest != candidate.name:
                    raise EvidenceError(f"refusing to remove corrupt orphan object {candidate.name}")
                candidate.unlink()
                removed.append(candidate.name)
        for name in (MANIFEST_NAME, SIGNATURE_NAME):
            candidate = bundle / name
            if candidate.exists():
                candidate.unlink()
                removed.append(name)
        for candidate in bundle.iterdir():
            if candidate.is_file() and (
                candidate.name.startswith(f".tmp-{EVIDENCE_NAME}-")
                or candidate.name.startswith(f".tmp-{MANIFEST_NAME}-")
            ):
                candidate.unlink()
                removed.append(candidate.name)
        fsync_dir(objects_path(bundle))
        fsync_dir(bundle)
    return removed


def openssh_version() -> tuple[int, int]:
    executable = shutil.which("ssh-keygen")
    ssh = shutil.which("ssh")
    if not executable or not ssh:
        raise EvidenceError("OpenSSH ssh and ssh-keygen are required for bundle signatures")
    completed = subprocess.run([ssh, "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    version_text = (completed.stdout + completed.stderr).decode("ascii", errors="replace")
    match = re.search(r"OpenSSH_(\d+)\.(\d+)", version_text)
    if not match:
        raise EvidenceError(f"could not identify OpenSSH version: {version_text.strip()}")
    version = (int(match.group(1)), int(match.group(2)))
    if version < (8, 8):
        raise EvidenceError("OpenSSH 8.8 or newer is required for signed evidence verification")
    return version


def manifest_for(bundle: Path, evidence: dict[str, Any], signer: str) -> dict[str, Any]:
    references = attachment_references(evidence)
    objects = []
    for digest in sorted(references):
        path = objects_path(bundle) / digest
        actual, size = sha256_file(path)
        if actual != digest:
            raise EvidenceError(f"cannot seal corrupt object {digest}")
        objects.append({"path": f"objects/sha256/{digest}", "sha256": digest, "size": size})
    events = evidence["events"]
    return {
        "manifest_schema_version": MANIFEST_SCHEMA,
        "evidence_schema_version": evidence["schema_version"],
        "bundle_id": evidence["bundle_id"],
        "robot_serial": evidence["robot_serial"],
        "source_commit": evidence["source_commit"],
        "source_ref": evidence["source_ref"],
        "plan_revision": evidence["plan_revision"],
        "plan_sha256": evidence["plan_sha256"],
        "evidence_sha256": sha256_file(evidence_path(bundle))[0],
        "event_count": len(events),
        "chain_head_sha256": events[-1]["event_sha256"] if events else GENESIS_HASH,
        "supersedes": evidence.get("supersedes"),
        "signer_claim": signer,
        "signing_time": now(),
        "signature_namespace": NAMESPACE,
        "objects": objects,
    }


def seal_bundle(bundle: Path, source_repo: Path, signing_key: Path, signer: str) -> Path:
    validate_signer(signer)
    openssh_version()
    with bundle_lock(bundle):
        ensure_not_sealed(bundle)
        evidence, _plan, failures = validate_unsealed(bundle, source_repo)
        if failures:
            raise EvidenceError("cannot seal blocked bundle:\n- " + "\n- ".join(failures))
        manifest = manifest_for(bundle, evidence, signer)
        manifest_path = bundle / MANIFEST_NAME
        atomic_write(manifest_path, canonical_json(manifest), mode=0o400)
        completed = subprocess.run(
            ["ssh-keygen", "-Y", "sign", "-f", str(signing_key), "-n", NAMESPACE, str(manifest_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        signature = bundle / SIGNATURE_NAME
        if completed.returncode != 0 or not signature.is_file():
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            raise EvidenceError(f"bundle manifest exists but signing failed; bundle is BLOCKED: {detail}")
        os.chmod(signature, 0o400)
        with signature.open("rb") as handle:
            os.fsync(handle.fileno())
        fsync_dir(bundle)
        return signature


def load_manifest(bundle: Path) -> tuple[dict[str, Any], bytes]:
    path = bundle / MANIFEST_NAME
    if not path.is_file() or path.is_symlink():
        raise EvidenceError("bundle manifest is missing or unsafe")
    raw = path.read_bytes()
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid bundle manifest JSON: {exc}") from exc
    if manifest.get("manifest_schema_version") != MANIFEST_SCHEMA:
        raise EvidenceError("unsupported bundle manifest schema")
    if raw != canonical_json(manifest):
        raise EvidenceError("bundle manifest is not canonical JSON")
    return manifest, raw


def verify_manifest_bytes(bundle: Path, evidence: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {
        "evidence_schema_version": evidence["schema_version"],
        "bundle_id": evidence["bundle_id"],
        "robot_serial": evidence["robot_serial"],
        "source_commit": evidence["source_commit"],
        "source_ref": evidence["source_ref"],
        "plan_revision": evidence["plan_revision"],
        "plan_sha256": evidence["plan_sha256"],
        "supersedes": evidence.get("supersedes"),
    }
    for field, expected in identity.items():
        if manifest.get(field) != expected:
            failures.append(f"manifest {field} does not match evidence")
    if manifest.get("signature_namespace") != NAMESPACE:
        failures.append("manifest signature namespace is invalid")
    actual_evidence, _size = sha256_file(evidence_path(bundle))
    if manifest.get("evidence_sha256") != actual_evidence:
        failures.append("manifest evidence hash does not match evidence.json")
    events = evidence["events"]
    if manifest.get("event_count") != len(events):
        failures.append("manifest event count does not match evidence")
    head = events[-1]["event_sha256"] if events else GENESIS_HASH
    if manifest.get("chain_head_sha256") != head:
        failures.append("manifest chain head does not match evidence")
    try:
        references = attachment_references(evidence)
    except EvidenceError as exc:
        failures.append(str(exc))
        references = {}
    expected_objects = [
        {"path": f"objects/sha256/{digest}", "sha256": digest, "size": references[digest]["size"]}
        for digest in sorted(references)
    ]
    if manifest.get("objects") != expected_objects:
        failures.append("manifest object set does not match evidence references")
    return failures


def verify_signature(
    bundle: Path,
    manifest: dict[str, Any],
    manifest_bytes: bytes,
    allowed_signers: Path,
    expected_signer: str,
    revocation_file: Path | None = None,
) -> list[str]:
    try:
        validate_signer(expected_signer)
    except EvidenceError as exc:
        return [str(exc)]
    try:
        openssh_version()
    except EvidenceError as exc:
        return [str(exc)]
    bundle_root = bundle.resolve()
    for trust_path in (allowed_signers, revocation_file):
        if trust_path is None:
            continue
        try:
            trust_path.resolve(strict=True).relative_to(bundle_root)
            return ["trusted signer/revocation policy must be supplied outside the evidence bundle"]
        except ValueError:
            pass
        except FileNotFoundError:
            return [f"trust policy file does not exist: {trust_path}"]
    signing_time = manifest.get("signing_time")
    if not isinstance(signing_time, str) or not RFC3339_RE.fullmatch(signing_time):
        return ["manifest signing_time is invalid"]
    verify_time = datetime.strptime(signing_time, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d%H%M%SZ")
    command = [
        "ssh-keygen", "-Y", "verify", "-f", str(allowed_signers),
        "-I", expected_signer, "-n", NAMESPACE,
        "-s", str(bundle / SIGNATURE_NAME), "-O", f"verify-time={verify_time}",
    ]
    if revocation_file is not None:
        command.extend(["-r", str(revocation_file)])
    completed = subprocess.run(
        command,
        input=manifest_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        return [f"OpenSSH signer verification failed: {detail}"]
    return []


def verify_sealed_bundle(
    bundle: Path,
    source_repo: Path,
    allowed_signers: Path,
    expected_signer: str,
    expected_robot_serial: str,
    revocation_file: Path | None = None,
) -> tuple[list[str], list[str], list[str]]:
    with bundle_lock(bundle, exclusive=False):
        completeness: list[str] = []
        integrity: list[str] = []
        trust: list[str] = []
        try:
            evidence = load_evidence(bundle)
            plan, provenance_failures = verify_provenance(evidence, source_repo)
            integrity.extend(verify_event_chain(evidence))
            integrity.extend(provenance_failures)
            if plan is not None:
                completeness.extend(verify_steps(plan, evidence))
            integrity.extend(verify_objects(bundle, evidence, sealed=True))
            manifest, manifest_bytes = load_manifest(bundle)
            integrity.extend(verify_manifest_bytes(bundle, evidence, manifest))
            if evidence.get("robot_serial") != expected_robot_serial:
                trust.append("expected robot serial does not match signed bundle")
            if manifest.get("signer_claim") != expected_signer:
                trust.append("expected signer principal does not match signed manifest claim")
            trust.extend(verify_signature(
                bundle, manifest, manifest_bytes, allowed_signers, expected_signer, revocation_file))
        except EvidenceError as exc:
            integrity.append(str(exc))
        return completeness, integrity, trust


def markdown_report(
    plan: dict[str, Any],
    evidence: dict[str, Any] | None,
    completeness: list[str],
    integrity: list[str],
    trust: list[str],
) -> str:
    current = latest_events(evidence) if evidence else {}
    event_counts: dict[str, int] = {}
    if evidence:
        for event in evidence["events"]:
            event_counts[event["step_id"]] = event_counts.get(event["step_id"], 0) + 1
    lines = [
        f"# Rover Bean commissioning — {plan['revision']}",
        "",
        "> A verified signature means the named signer attests to these exact bytes. It does not",
        "> prove measurements are physically true or independently authorize powered motion.",
        "",
        "| ID | Phase | Test | Latest | Superseded | Operator |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for step in plan["steps"]:
        event = current.get(step["id"], {})
        superseded = max(0, event_counts.get(step["id"], 0) - 1)
        lines.append(
            f"| {step['id']} | {step['phase']} | {step['title']} | "
            f"{event.get('result', 'OPEN')} | {superseded} | {event.get('operator', '')} |")
    axes = [
        ("Record completeness", completeness),
        ("Bundle byte integrity", integrity),
        ("Signer trust", trust),
    ]
    lines.extend(("", "## Independent verdict axes", ""))
    for title, failures in axes:
        lines.append(f"### {title}: {'PASS' if not failures else 'BLOCKED'}")
        lines.append("")
        if failures:
            lines.extend(f"- {failure}" for failure in failures)
        else:
            lines.append("- No blockers detected.")
        lines.append("")
    overall = not completeness and not integrity and not trust
    lines.extend((
        "## Evidence-bundle verdict",
        "",
        "PASS — complete bytes were verified against the out-of-band signer policy."
        if overall else "BLOCKED — one or more independent evidence axes remain open.",
        "",
        "This verdict never replaces the physical harness, safety, or powered-motion release gates.",
        "",
    ))
    return "\n".join(lines)


def current_plan_for_listing(source_repo: Path) -> dict[str, Any]:
    return plan_at(source_repo)[0]


def print_list(plan: dict[str, Any], evidence: dict[str, Any] | None) -> None:
    current = latest_events(evidence) if evidence else {}
    counts: dict[str, int] = {}
    if evidence:
        for event in evidence["events"]:
            counts[event["step_id"]] = counts.get(event["step_id"], 0) + 1
    for step in plan["steps"]:
        result = current.get(step["id"], {}).get("result", "OPEN")
        superseded = max(0, counts.get(step["id"], 0) - 1)
        print(f"{step['id']}  {result:7}  old={superseded:<2}  {step['condition']}  {step['title']}")


def print_step(plan: dict[str, Any], step_id: str) -> None:
    step = next((item for item in plan["steps"] if item["id"] == step_id), None)
    if step is None:
        raise EvidenceError(f"unknown step {step_id}")
    print(f"{step['id']} — {step['title']}")
    print(f"Condition: {step['condition']}")
    print(f"Procedure: {step['procedure']}")
    print("Measurements:")
    measurement_types = plan_measurement_types(plan)
    for field in step.get("required_measurements", []):
        print(f"- {field} ({measurement_types[field]})")
    print("Artifact roles:")
    for artifact in step.get("required_artifacts", []):
        binding = ""
        if artifact.get("measurement"):
            binding = f" -> {artifact['measurement']} ({artifact['value']})"
        print(f"- {artifact['role']}{binding}")
    for attestation in step.get("attestations", []):
        print(f"Attestation: {attestation}")
    for rule in step.get("acceptance", []):
        print(f"Acceptance: {rule['field']} {rule['op']} {rule['value']!r}")


def add_trust_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--allowed-signers", type=Path, required=True)
    parser.add_argument("--signer", required=True, help="Expected signer principal from out-of-band policy")
    parser.add_argument("--robot-serial", required=True, help="Expected physical robot identity")
    parser.add_argument("--revocation-file", type=Path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--source-repo", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--robot-serial", required=True)
    init.add_argument("--operator", required=True)
    init.add_argument("--source-ref", required=True)
    init.add_argument("--supersedes-bundle", type=Path)
    init.add_argument("--supersedes-allowed-signers", type=Path)
    init.add_argument("--supersedes-signer")
    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("step_id")
    run = sub.add_parser("run-automated")
    run.add_argument("step_id")
    run.add_argument("--operator", default="commission.py")
    run.add_argument("--measure", action="append", default=[])
    record = sub.add_parser("record")
    record.add_argument("step_id")
    record.add_argument("--result", choices=("pass", "fail", "blocked"), required=True)
    record.add_argument("--operator", required=True)
    record.add_argument("--note", default="")
    record.add_argument("--measure", action="append", default=[])
    record.add_argument("--attach", action="append", default=[])
    record.add_argument("--attest", action="append", default=[])
    seal = sub.add_parser("seal")
    seal.add_argument("--signing-key", type=Path, required=True)
    seal.add_argument("--signer", required=True)
    verify_parser = sub.add_parser("verify")
    add_trust_arguments(verify_parser)
    report = sub.add_parser("report")
    report.add_argument("--output", type=Path)
    report.add_argument("--allowed-signers", type=Path)
    report.add_argument("--signer")
    report.add_argument("--robot-serial")
    report.add_argument("--revocation-file", type=Path)
    sub.add_parser("cleanup")
    args = parser.parse_args()

    bundle = args.bundle.resolve()
    source_repo = args.source_repo.resolve()
    try:
        if args.command == "init":
            evidence = initialize_bundle(
                bundle, source_repo, args.robot_serial, args.operator,
                args.source_ref, args.supersedes_bundle,
                args.supersedes_allowed_signers, args.supersedes_signer)
            print(f"EVIDENCE_BUNDLE_INITIALIZED {evidence['bundle_id']} {bundle}")
            return
        if args.command in ("list", "show"):
            try:
                evidence = load_evidence(bundle)
                plan, failures = verify_provenance(evidence, source_repo)
                if failures or plan is None:
                    raise EvidenceError("; ".join(failures))
            except EvidenceError as exc:
                if evidence_path(bundle).exists():
                    raise
                evidence = None
                plan = current_plan_for_listing(source_repo)
                print(f"NO_BUNDLE {exc}")
            if args.command == "list":
                print_list(plan, evidence)
            else:
                print_step(plan, args.step_id)
            return
        if args.command == "record":
            event = append_event(
                bundle, source_repo, args.step_id, args.result, args.operator, args.note,
                parse_measurements(args.measure), parse_assignments(args.attach, "attachment"),
                args.attest,
            )
            print(f"RECORDED {args.step_id} event={event['sequence']} result={args.result}")
            return
        if args.command == "run-automated":
            evidence = load_evidence(bundle)
            plan, failures = verify_provenance(evidence, source_repo)
            if failures or plan is None:
                raise EvidenceError("; ".join(failures))
            steps = {step["id"]: step for step in plan["steps"]}
            step = steps.get(args.step_id)
            if not step or not step.get("command") or not step.get("automated_artifact_role"):
                raise EvidenceError("step has no safe automated command and capture role")
            completed = subprocess.run(
                step["command"], cwd=source_repo, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False)
            output = completed.stdout + (b"\n" if completed.stdout and completed.stderr else b"") + completed.stderr
            sys.stdout.buffer.write(output)
            append_event(
                bundle, source_repo, args.step_id,
                "pass" if completed.returncode == 0 else "fail",
                args.operator, "Safe automated repository check",
                parse_measurements(args.measure), {}, [],
                (step["automated_artifact_role"], output, f"{args.step_id}-command-output.txt"),
            )
            raise SystemExit(completed.returncode)
        if args.command == "cleanup":
            removed = cleanup_orphans(bundle)
            print(f"CLEANUP_PASS removed={len(removed)}")
            return
        if args.command == "seal":
            signature = seal_bundle(bundle, source_repo, args.signing_key, args.signer)
            print(f"EVIDENCE_BUNDLE_SEALED {signature}")
            return
        if args.command == "verify":
            completeness, integrity, trust = verify_sealed_bundle(
                bundle, source_repo, args.allowed_signers, args.signer,
                args.robot_serial, args.revocation_file)
            failures = completeness + integrity + trust
            if failures:
                print("COMMISSIONING_GATE_BLOCKED")
                for failure in failures:
                    print(f"- {failure}")
                raise SystemExit(1)
            print("COMMISSIONING_EVIDENCE_PASS")
            print("Physical release gates remain independent and must be run separately.")
            return
        # report
        try:
            evidence = load_evidence(bundle)
            plan, provenance_failures = verify_provenance(evidence, source_repo)
            if plan is None:
                plan = current_plan_for_listing(source_repo)
            completeness = verify_steps(plan, evidence)
            integrity = verify_event_chain(evidence) + provenance_failures
            integrity += verify_objects(
                bundle, evidence,
                sealed=(bundle / MANIFEST_NAME).exists() and (bundle / SIGNATURE_NAME).exists())
            trust = ["out-of-band signer policy was not supplied"]
            if args.allowed_signers and args.signer and args.robot_serial:
                completeness, integrity, trust = verify_sealed_bundle(
                    bundle, source_repo, args.allowed_signers, args.signer,
                    args.robot_serial, args.revocation_file)
        except EvidenceError as exc:
            evidence = None
            plan = current_plan_for_listing(source_repo)
            completeness = [f"no usable evidence bundle: {exc}"]
            integrity = [str(exc)]
            trust = ["no sealed bundle to authenticate"]
        text = markdown_report(plan, evidence, completeness, integrity, trust)
        if args.output:
            atomic_write(args.output, text.encode("utf-8"), mode=0o600)
        else:
            print(text, end="")
    except EvidenceError as exc:
        print(f"COMMISSIONING_GATE_BLOCKED\n- {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
