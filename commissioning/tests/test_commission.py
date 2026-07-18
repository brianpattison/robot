from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import commission  # noqa: E402


AUTO_FIELDS = [
    "guide_sha256",
    "body_3mf_sha256",
    "coupon_3mf_sha256",
    "fixture_sha256",
    "firmware_tree_sha256",
    "robotd_tree_sha256",
    "appliance_tree_sha256",
]


def synthetic_plan() -> dict:
    return {
        "schema_version": 2,
        "revision": "synthetic-C3",
        "status": "synthetic test plan; no physical evidence",
        "measurement_types": {
            "string": [
                "robot_serial", *AUTO_FIELDS, "battery_serial", "harness_revision",
                "record_uri", "binary_sha256",
            ],
            "boolean": ["confirmed"],
            "integer": ["count"],
            "number": [],
        },
        "steps": [
            {
                "id": "C001",
                "title": "Identity",
                "phase": "records",
                "condition": "unpowered",
                "procedure": "Synthetic identity only.",
                "required_measurements": [
                    "robot_serial", *AUTO_FIELDS, "battery_serial", "harness_revision",
                ],
                "required_artifacts": [{"role": "first_article_identity_photo"}],
            },
            {
                "id": "C002",
                "title": "Captured record",
                "phase": "mechanical",
                "condition": "unpowered",
                "procedure": "Synthetic record only.",
                "required_measurements": ["record_uri", "binary_sha256", "count"],
                "required_artifacts": [
                    {"role": "record", "measurement": "record_uri", "value": "uri"},
                    {"role": "binary", "measurement": "binary_sha256", "value": "sha256"},
                ],
                "acceptance": [{"field": "count", "op": "gte", "value": 1}],
            },
            {
                "id": "C003",
                "title": "Attestation",
                "phase": "records",
                "condition": "unpowered",
                "procedure": "Synthetic attestation only.",
                "required_measurements": ["confirmed"],
                "attestations": ["procedure_performed"],
                "acceptance": [{"field": "confirmed", "op": "eq", "value": True}],
            },
        ],
    }


class SyntheticRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo = root / "repo"
        self.bundle = root / "bundle"
        self.inputs = root / "inputs"
        self.repo.mkdir()
        self.inputs.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "synthetic@example.invalid")
        self._git("config", "user.name", "Synthetic Test")
        self._git("remote", "add", "origin", "https://example.invalid/synthetic/robot.git")
        files: dict[str, bytes] = {
            commission.PLAN_PATH.as_posix(): commission.canonical_json(synthetic_plan()),
            "output/pdf/codex_robot_body_v2_assembly_guide.pdf": b"synthetic-guide\x00",
            "cad/bambu/codex_robot_body_v2_p1s.3mf": b"synthetic-body-3mf\x00",
            "cad/bambu/codex_robot_body_v2_coupons_p1s.3mf": b"synthetic-coupon-3mf\x00",
            "commissioning/fixture-v1.json": b'{"synthetic":true}',
            "firmware/pico2-safety/main.c": b"int synthetic_firmware;\n",
            "software/robotd/daemon.py": b"SYNTHETIC = True\n",
            "software/appliance/appliance.py": b"SYNTHETIC = True\n",
        }
        for relative, data in files.items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self._git("add", ".")
        self._git("commit", "-q", "-m", "synthetic source")
        self._git("tag", "synthetic-release")
        self.commit = self._git("rev-parse", "HEAD").stdout.strip()
        self.identity = self.write_input("identity.jpg", b"synthetic identity photo")
        self.record = self.write_input("record.json", b'{"synthetic":"record"}')
        self.binary = self.write_input("capture.bin", bytes(range(64)))

    def _git(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *arguments], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check,
        )

    def write_input(self, name: str, data: bytes) -> Path:
        path = self.inputs / name
        path.write_bytes(data)
        return path

    def initialize(self) -> dict:
        return commission.initialize_bundle(
            self.bundle,
            self.repo,
            "RB-SYNTHETIC-001",
            "Synthetic Operator",
            "refs/tags/synthetic-release",
        )

    def append(self, step: str, result: str = "pass", **kwargs) -> dict:
        defaults = {
            "operator": "Synthetic Operator",
            "note": "Synthetic test evidence; not a physical result.",
            "measurements": {},
            "attachment_paths": {},
            "attestations": [],
        }
        defaults.update(kwargs)
        return commission.append_event(
            self.bundle, self.repo, step, result, **defaults)

    def complete(self) -> None:
        self.append(
            "C001",
            measurements={"battery_serial": "BAT-SYNTH", "harness_revision": "H-SYNTH"},
            attachment_paths={"first_article_identity_photo": str(self.identity)},
        )
        self.append(
            "C002",
            measurements={"count": 1},
            attachment_paths={"record": str(self.record), "binary": str(self.binary)},
        )
        self.append(
            "C003",
            measurements={"confirmed": True},
            attestations=["procedure_performed"],
        )

    def signing_material(self) -> tuple[Path, Path, str]:
        key = self.root / "signing-key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
            check=True,
        )
        principal = "synthetic-signer@example.invalid"
        public_parts = (key.with_suffix(".pub")).read_text(encoding="ascii").split()
        allowed = self.root / "allowed_signers"
        allowed.write_text(
            f"{principal} {public_parts[0]} {public_parts[1]}\n", encoding="ascii")
        return key, allowed, principal

    def seal(self) -> tuple[Path, Path, str]:
        key, allowed, principal = self.signing_material()
        commission.seal_bundle(self.bundle, self.repo, key, principal)
        return key, allowed, principal


class CanonicalAndStepTests(unittest.TestCase):
    def test_checked_in_plan_validates_all_steps_and_measurement_types(self) -> None:
        plan, plan_hash = commission.plan_at(commission.ROOT)
        self.assertEqual(len(plan["steps"]), 27)
        self.assertRegex(plan_hash, r"^[0-9a-f]{64}$")
        declared = commission.plan_measurement_types(plan)
        required = {
            field
            for step in plan["steps"]
            for field in step.get("required_measurements", [])
        }
        self.assertEqual(set(declared), required)
        self.assertEqual(declared["lease_stop_latency_ms"], "number")

    def test_canonical_json_is_stable_and_has_no_trailing_newline(self) -> None:
        value = {"z": "café", "a": [1, True, 1.25]}
        self.assertEqual(
            commission.canonical_json(value),
            '{"a":[1,true,1.25],"z":"café"}'.encode(),
        )

    def test_nonfinite_measurement_is_rejected(self) -> None:
        with self.assertRaisesRegex(commission.EvidenceError, "canonical finite number"):
            commission.coerce_measurements({"volts": "nan"}, {"volts": "number"})

    def test_event_chain_detects_tamper_gap_and_bad_genesis(self) -> None:
        event = {
            "sequence": 2,
            "step_id": "C001",
            "result": "blocked",
            "operator": "Synthetic",
            "recorded_at": "2026-07-18T00:00:00Z",
            "note": "",
            "measurements": {},
            "attachments": [],
            "attestations": [],
            "previous_event_sha256": "f" * 64,
        }
        event["event_sha256"] = commission.event_digest(event)
        failures = commission.verify_event_chain({"events": [event]})
        self.assertTrue(any("sequence" in failure for failure in failures))
        self.assertTrue(any("previous hash" in failure for failure in failures))
        event["note"] = "tampered"
        self.assertTrue(any("event hash" in failure for failure in commission.verify_event_chain({"events": [event]})))

    def test_latest_failure_blocks_and_later_pass_supersedes(self) -> None:
        plan = {
            "measurement_types": {
                "string": [], "boolean": ["confirmed"], "integer": [], "number": [],
            },
            "steps": [{
                "id": "C001", "required_measurements": ["confirmed"],
                "acceptance": [{"field": "confirmed", "op": "eq", "value": True}],
            }],
        }
        fail = {"step_id": "C001", "result": "fail", "measurements": {"confirmed": False}}
        passed = {"step_id": "C001", "result": "pass", "measurements": {"confirmed": True}}
        evidence = {"robot_serial": None, "events": [fail]}
        self.assertTrue(any("result is 'fail'" in item for item in commission.verify_steps(plan, evidence)))
        evidence["events"].append(passed)
        self.assertEqual(commission.verify_steps(plan, evidence), [])
        evidence["events"].append(fail)
        self.assertTrue(any("result is 'fail'" in item for item in commission.verify_steps(plan, evidence)))

    def test_measurement_types_keep_identities_and_booleans_strict(self) -> None:
        parsed = commission.parse_measurements([
            "battery_serial=00123", "protocol_clear_succeeded=false", "latency_ms=10.5",
        ])
        typed = commission.coerce_measurements(
            parsed,
            {
                "battery_serial": "string",
                "protocol_clear_succeeded": "boolean",
                "latency_ms": "number",
            },
        )
        self.assertEqual(typed["battery_serial"], "00123")
        self.assertIs(typed["protocol_clear_succeeded"], False)
        self.assertEqual(typed["latency_ms"], 10.5)
        with self.assertRaisesRegex(commission.EvidenceError, "exactly true or false"):
            commission.coerce_measurements(
                {"protocol_clear_succeeded": "0"},
                {"protocol_clear_succeeded": "boolean"},
            )

    def test_plan_rejects_missing_acceptance_value(self) -> None:
        plan = synthetic_plan()
        del plan["steps"][1]["acceptance"][0]["value"]
        with self.assertRaisesRegex(commission.EvidenceError, "malformed acceptance"):
            commission.validate_plan_schema(plan)

    def test_unknown_acceptance_operator_fails(self) -> None:
        step = {
            "id": "C002",
            "acceptance": [{"field": "count", "op": "approximately", "value": 1}],
        }
        self.assertEqual(
            commission.validate_acceptance(step, {"count": 1}),
            ["C002: count=1 fails approximately 1"],
        )


class BundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.synthetic = SyntheticRepository(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_init_binds_clean_source_ref_plan_and_provenance(self) -> None:
        evidence = self.synthetic.initialize()
        self.assertEqual(evidence["source_commit"], self.synthetic.commit)
        self.assertEqual(evidence["source_ref_commit"], self.synthetic.commit)
        self.assertEqual(set(evidence["source_provenance"]), set(AUTO_FIELDS))
        self.assertEqual(oct(self.synthetic.bundle.stat().st_mode & 0o777), "0o700")

    def test_init_rejects_dirty_tracked_tree(self) -> None:
        tracked = self.synthetic.repo / "software/robotd/daemon.py"
        tracked.write_text("DIRTY = True\n", encoding="utf-8")
        with self.assertRaisesRegex(commission.EvidenceError, "tracked changes"):
            self.synthetic.initialize()

    def test_init_rejects_unreachable_source_ref(self) -> None:
        self.synthetic._git("checkout", "-q", "--orphan", "unrelated")
        self.synthetic._git("rm", "-q", "-rf", ".")
        unrelated = self.synthetic.repo / "unrelated.txt"
        unrelated.write_text("unrelated\n", encoding="utf-8")
        self.synthetic._git("add", ".")
        self.synthetic._git("commit", "-q", "-m", "unrelated")
        with self.assertRaisesRegex(commission.EvidenceError, "not reachable"):
            self.synthetic.initialize()

    def test_init_requires_immutable_tag_and_origin(self) -> None:
        with self.assertRaisesRegex(commission.EvidenceError, "immutable release tag"):
            commission.initialize_bundle(
                self.synthetic.bundle, self.synthetic.repo, "RB-SYNTHETIC-001",
                "Synthetic", "HEAD")
        self.synthetic._git("remote", "remove", "origin")
        with self.assertRaisesRegex(commission.EvidenceError, "remote get-url origin"):
            self.synthetic.initialize()

    def test_legacy_schema_and_noncanonical_json_are_rejected(self) -> None:
        commission.ensure_bundle_layout(self.synthetic.bundle)
        path = commission.evidence_path(self.synthetic.bundle)
        path.write_bytes(b'{"schema_version":1}')
        with self.assertRaisesRegex(commission.EvidenceError, "legacy evidence schema v1"):
            commission.load_evidence(self.synthetic.bundle)
        path.write_text('{ "schema_version": 2 }\n', encoding="utf-8")
        with self.assertRaisesRegex(commission.EvidenceError, "not canonical"):
            commission.load_evidence(self.synthetic.bundle)

    def test_record_auto_derives_identity_and_artifact_values(self) -> None:
        evidence = self.synthetic.initialize()
        first = self.synthetic.append(
            "C001",
            measurements={"battery_serial": "BAT-SYNTH", "harness_revision": "H-SYNTH"},
            attachment_paths={"first_article_identity_photo": str(self.synthetic.identity)},
        )
        self.assertEqual(first["measurements"]["robot_serial"], evidence["robot_serial"])
        self.assertEqual(first["measurements"]["guide_sha256"], evidence["source_provenance"]["guide_sha256"])
        second = self.synthetic.append(
            "C002",
            measurements={"count": 1},
            attachment_paths={"record": str(self.synthetic.record), "binary": str(self.synthetic.binary)},
        )
        by_role = {item["role"]: item for item in second["attachments"]}
        self.assertEqual(second["measurements"]["record_uri"], by_role["record"]["uri"])
        self.assertEqual(second["measurements"]["binary_sha256"], by_role["binary"]["sha256"])

    def test_source_controlled_measurement_cannot_be_transcribed(self) -> None:
        self.synthetic.initialize()
        with self.assertRaisesRegex(commission.EvidenceError, "auto-derived"):
            self.synthetic.append(
                "C001",
                measurements={
                    "battery_serial": "BAT", "harness_revision": "H",
                    "guide_sha256": "0" * 64,
                },
                attachment_paths={"first_article_identity_photo": str(self.synthetic.identity)},
            )

    def test_symlink_fifo_and_directory_attachments_are_rejected(self) -> None:
        self.synthetic.initialize()
        symlink = self.synthetic.inputs / "link"
        symlink.symlink_to(self.synthetic.record)
        fifo = self.synthetic.inputs / "fifo"
        os.mkfifo(fifo)
        for unsafe in (symlink, fifo, self.synthetic.inputs):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(commission.EvidenceError):
                    self.synthetic.append(
                        "C002", result="blocked",
                        attachment_paths={"record": str(unsafe)},
                    )

    def test_attachment_size_bound_is_enforced(self) -> None:
        self.synthetic.initialize()
        with mock.patch.object(commission, "MAX_ATTACHMENT_BYTES", 3):
            with self.assertRaisesRegex(commission.EvidenceError, "exceeds"):
                self.synthetic.append(
                    "C002", result="blocked",
                    attachment_paths={"record": str(self.synthetic.record)},
                )

    def test_object_tamper_extra_file_and_hardlink_are_detected(self) -> None:
        self.synthetic.initialize()
        self.synthetic.complete()
        evidence = commission.load_evidence(self.synthetic.bundle)
        self.assertEqual(commission.verify_objects(self.synthetic.bundle, evidence, sealed=False), [])
        digest = evidence["events"][0]["attachments"][0]["sha256"]
        object_path = commission.objects_path(self.synthetic.bundle) / digest
        os.chmod(object_path, 0o600)
        object_path.write_bytes(b"tampered")
        failures = commission.verify_objects(self.synthetic.bundle, evidence, sealed=False)
        self.assertTrue(any("content hash" in item for item in failures))
        # Restore the exact bytes, then prove an external hard link and an extra file are visible.
        object_path.write_bytes(self.synthetic.identity.read_bytes())
        os.chmod(object_path, 0o400)
        os.link(object_path, self.synthetic.root / "outside-hardlink")
        (self.synthetic.bundle / "unlisted.txt").write_text("extra", encoding="utf-8")
        failures = commission.verify_objects(self.synthetic.bundle, evidence, sealed=False)
        self.assertTrue(any("hard links" in item for item in failures))
        self.assertTrue(any("unlisted bundle file" in item for item in failures))

    def test_bundle_symlink_is_rejected(self) -> None:
        self.synthetic.initialize()
        self.synthetic.complete()
        (self.synthetic.bundle / "unsafe-link").symlink_to(self.synthetic.record)
        evidence = commission.load_evidence(self.synthetic.bundle)
        failures = commission.verify_objects(self.synthetic.bundle, evidence, sealed=False)
        self.assertTrue(any("symlink is forbidden" in item for item in failures))

    def test_duplicate_artifact_reuse_across_roles_is_rejected(self) -> None:
        self.synthetic.initialize()
        same = self.synthetic.write_input("same.bin", b"same artifact")
        self.synthetic.append(
            "C002", measurements={"count": 1},
            attachment_paths={"record": str(same), "binary": str(same)},
        )
        evidence = commission.load_evidence(self.synthetic.bundle)
        plan = synthetic_plan()
        failures = commission.verify_steps(plan, evidence)
        self.assertTrue(any("reuses C002/record" in item for item in failures))

    def test_source_blob_drift_is_detected_even_if_evidence_is_rehashed(self) -> None:
        self.synthetic.initialize()
        evidence = commission.load_evidence(self.synthetic.bundle)
        evidence["source_provenance"]["guide_sha256"] = "0" * 64
        commission.save_evidence(self.synthetic.bundle, evidence)
        _plan, failures = commission.verify_provenance(evidence, self.synthetic.repo)
        self.assertTrue(any("provenance" in item for item in failures))

    def test_atomic_write_failure_preserves_old_evidence(self) -> None:
        self.synthetic.initialize()
        before = commission.evidence_path(self.synthetic.bundle).read_bytes()
        original_replace = os.replace

        def fail_replace(source: str | bytes | os.PathLike, destination: str | bytes | os.PathLike) -> None:
            if Path(destination) == commission.evidence_path(self.synthetic.bundle):
                raise OSError("synthetic crash before rename")
            original_replace(source, destination)

        with mock.patch.object(commission.os, "replace", side_effect=fail_replace):
            with self.assertRaisesRegex(OSError, "synthetic crash"):
                self.synthetic.append(
                    "C002", result="blocked",
                    attachment_paths={"record": str(self.synthetic.record)},
                )
        self.assertEqual(commission.evidence_path(self.synthetic.bundle).read_bytes(), before)
        commission.load_evidence(self.synthetic.bundle)
        removed = commission.cleanup_orphans(self.synthetic.bundle)
        self.assertEqual(len([name for name in removed if commission.OBJECT_RE.fullmatch(name)]), 1)

    def test_concurrent_recording_has_gap_free_unique_sequences(self) -> None:
        self.synthetic.initialize()
        command = [
            sys.executable,
            str(Path(commission.__file__)),
            "--bundle", str(self.synthetic.bundle),
            "--source-repo", str(self.synthetic.repo),
            "record", "C003", "--result", "blocked", "--operator", "Synthetic",
        ]
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        second = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        first_stdout, first_stderr = first.communicate(timeout=20)
        second_stdout, second_stderr = second.communicate(timeout=20)
        self.assertEqual(first.returncode, 0, (first_stdout + first_stderr).decode())
        self.assertEqual(second.returncode, 0, (second_stdout + second_stderr).decode())
        events = commission.load_evidence(self.synthetic.bundle)["events"]
        self.assertEqual([event["sequence"] for event in events], [1, 2])
        self.assertEqual(commission.verify_event_chain({"events": events}), [])

    def test_partial_seal_blocks_mutation_and_cleanup_recovers(self) -> None:
        self.synthetic.initialize()
        (self.synthetic.bundle / commission.MANIFEST_NAME).write_text("partial", encoding="utf-8")
        with self.assertRaisesRegex(commission.EvidenceError, "seal material"):
            self.synthetic.append("C003", result="blocked")
        removed = commission.cleanup_orphans(self.synthetic.bundle)
        self.assertIn(commission.MANIFEST_NAME, removed)
        self.synthetic.append("C003", result="blocked")

    @unittest.skipUnless(shutil.which("ssh-keygen") and shutil.which("ssh"), "OpenSSH unavailable")
    def test_valid_seal_requires_out_of_band_signer_and_expected_robot(self) -> None:
        self.synthetic.initialize()
        self.synthetic.complete()
        _key, allowed, principal = self.synthetic.seal()
        axes = commission.verify_sealed_bundle(
            self.synthetic.bundle, self.synthetic.repo, allowed, principal, "RB-SYNTHETIC-001")
        self.assertEqual(axes, ([], [], []))
        wrong = commission.verify_sealed_bundle(
            self.synthetic.bundle, self.synthetic.repo, allowed, "wrong@example.invalid", "RB-WRONG")
        self.assertTrue(any("robot serial" in item for item in wrong[2]))
        self.assertTrue(any("signer verification failed" in item for item in wrong[2]))
        with self.assertRaisesRegex(commission.EvidenceError, "seal material"):
            self.synthetic.append("C003", result="blocked")

    @unittest.skipUnless(shutil.which("ssh-keygen") and shutil.which("ssh"), "OpenSSH unavailable")
    def test_signer_claim_and_verify_time_policy_are_enforced(self) -> None:
        self.synthetic.initialize()
        self.synthetic.complete()
        _key, allowed, principal = self.synthetic.seal()
        manifest_path = self.synthetic.bundle / commission.MANIFEST_NAME
        evidence = commission.load_evidence(self.synthetic.bundle)
        manifest, manifest_bytes = commission.load_manifest(self.synthetic.bundle)
        manifest["signer_claim"] = "different@example.invalid"
        os.chmod(manifest_path, 0o600)
        commission.atomic_write(manifest_path, commission.canonical_json(manifest), mode=0o400)
        integrity = commission.verify_manifest_bytes(self.synthetic.bundle, evidence, manifest)
        self.assertEqual(integrity, [])
        # The old signature no longer covers the edited claim, and the explicit claim check also blocks.
        axes = commission.verify_sealed_bundle(
            self.synthetic.bundle, self.synthetic.repo, allowed, principal, "RB-SYNTHETIC-001")
        self.assertTrue(any("manifest claim" in item for item in axes[2]))
        self.assertTrue(any("signer verification failed" in item for item in axes[2]))
        # Directly verify the original bytes against a policy not yet valid at the signed time.
        public_parts = (self.synthetic.root / "signing-key.pub").read_text(encoding="ascii").split()
        future_policy = self.synthetic.root / "future_allowed_signers"
        future_policy.write_text(
            f'{principal} valid-after="20990101Z" {public_parts[0]} {public_parts[1]}\n',
            encoding="ascii",
        )
        trust = commission.verify_signature(
            self.synthetic.bundle, manifest, manifest_bytes, future_policy, principal)
        self.assertTrue(any("signer verification failed" in item for item in trust))

    @unittest.skipUnless(shutil.which("ssh-keygen") and shutil.which("ssh"), "OpenSSH unavailable")
    def test_signature_transplant_is_rejected(self) -> None:
        self.synthetic.initialize()
        self.synthetic.complete()
        _key, allowed, principal = self.synthetic.seal()
        second_root = self.synthetic.root / "second"
        second_root.mkdir()
        second = SyntheticRepository(second_root)
        second.initialize()
        second.complete()
        second_key, _second_allowed, _second_principal = second.signing_material()
        commission.seal_bundle(second.bundle, second.repo, second_key, principal)
        os.chmod(second.bundle / commission.SIGNATURE_NAME, 0o600)
        shutil.copyfile(
            self.synthetic.bundle / commission.SIGNATURE_NAME,
            second.bundle / commission.SIGNATURE_NAME,
        )
        axes = commission.verify_sealed_bundle(
            second.bundle, second.repo, allowed, principal, "RB-SYNTHETIC-001")
        self.assertTrue(any("signer verification failed" in item for item in axes[2]))

    @unittest.skipUnless(shutil.which("ssh-keygen") and shutil.which("ssh"), "OpenSSH unavailable")
    def test_trust_policy_inside_bundle_is_rejected(self) -> None:
        self.synthetic.initialize()
        self.synthetic.complete()
        _key, allowed, principal = self.synthetic.seal()
        inside = self.synthetic.bundle / "bundled_allowed_signers"
        inside.write_bytes(allowed.read_bytes())
        axes = commission.verify_sealed_bundle(
            self.synthetic.bundle, self.synthetic.repo, inside, principal, "RB-SYNTHETIC-001")
        self.assertTrue(any("outside the evidence bundle" in item for item in axes[2]))

    @unittest.skipUnless(shutil.which("ssh-keygen") and shutil.which("ssh"), "OpenSSH unavailable")
    def test_superseding_bundle_records_prior_identity(self) -> None:
        self.synthetic.initialize()
        self.synthetic.complete()
        _key, allowed, principal = self.synthetic.seal()
        superseding = self.synthetic.root / "superseding"
        evidence = commission.initialize_bundle(
            superseding,
            self.synthetic.repo,
            "RB-SYNTHETIC-001",
            "Synthetic Corrector",
            "refs/tags/synthetic-release",
            self.synthetic.bundle,
            allowed,
            principal,
        )
        self.assertEqual(evidence["supersedes"]["bundle_id"], commission.load_evidence(self.synthetic.bundle)["bundle_id"])
        self.assertRegex(evidence["supersedes"]["manifest_sha256"], r"^[0-9a-f]{64}$")

    def test_report_keeps_three_verdict_axes_separate(self) -> None:
        report = commission.markdown_report(
            synthetic_plan(), None,
            ["missing step"], [], ["no trusted signer"],
        )
        self.assertIn("Record completeness: BLOCKED", report)
        self.assertIn("Bundle byte integrity: PASS", report)
        self.assertIn("Signer trust: BLOCKED", report)
        self.assertIn("does not", report)
        self.assertIn("powered motion", report)

    def test_missing_openssh_fails_closed(self) -> None:
        with mock.patch.object(commission.shutil, "which", return_value=None):
            with self.assertRaisesRegex(commission.EvidenceError, "OpenSSH"):
                commission.openssh_version()

    def test_default_repository_has_no_physical_evidence_pass(self) -> None:
        missing = self.synthetic.root / "missing-bundle"
        completed = subprocess.run(
            [
                sys.executable, str(Path(commission.__file__)),
                "--bundle", str(missing), "--source-repo", str(self.synthetic.repo),
                "verify", "--allowed-signers", str(self.synthetic.root / "missing-policy"),
                "--signer", "nobody@example.invalid", "--robot-serial", "RB-NONE",
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(b"COMMISSIONING_GATE_BLOCKED", completed.stdout)


if __name__ == "__main__":
    unittest.main()
