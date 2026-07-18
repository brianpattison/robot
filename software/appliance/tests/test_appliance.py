from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

APPLIANCE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APPLIANCE_DIR))

import appliance  # noqa: E402


def public_key() -> str:
    key_type = b"ssh-ed25519"
    key = b"K" * 32
    wire = len(key_type).to_bytes(4, "big") + key_type + len(key).to_bytes(4, "big") + key
    blob = base64.b64encode(wire).decode()
    return f"ssh-ed25519 {blob} brian@test\n"


class ApplianceTests(unittest.TestCase):
    def stage_inputs(self, temp: Path) -> tuple[Path, Path, Path]:
        root = temp / "root"
        boot = root / "boot/firmware/config.txt"
        boot.parent.mkdir(parents=True)
        boot.write_text("# preserve me\ndtparam=audio=on\n", encoding="utf-8")
        cmdline = root / "boot/firmware/cmdline.txt"
        cmdline.write_text("console=ttyAMA10,115200 root=PARTUUID=tiny-robot\n",
                           encoding="utf-8")
        key = temp / "agent.pub"
        key.write_text(public_key(), encoding="utf-8")
        token = temp / "tunnel.token"
        token.write_text("T" * 80 + "\n", encoding="utf-8")
        return root, key, token

    @staticmethod
    def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
        return {
            str(path.relative_to(root)): (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
            for path in root.rglob("*") if path.is_file()
        }

    def test_manifest_is_closed_world(self) -> None:
        appliance.validate_manifest(appliance.load_manifest())
        manifest_paths = {row["path"] for row in appliance.load_manifest()["files"]}
        self.assertEqual(
            manifest_paths,
            set(appliance.rendered_files()) | {
                "/opt/rover-bean/appliance/appliance.py",
                "/opt/rover-bean/appliance/appliance-v1.json",
                "/opt/rover-bean/appliance/audit_backup.py",
            },
        )

    def test_stage_is_idempotent_preserves_cmdline_and_redacts_token(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            root, key, token = self.stage_inputs(temp)
            before_cmdline = (root / "boot/firmware/cmdline.txt").read_bytes()
            appliance.stage_root(root, key, token)
            first = self.snapshot(root)
            appliance.stage_root(root, key, token)
            self.assertEqual(first, self.snapshot(root))
            self.assertEqual(before_cmdline, (root / "boot/firmware/cmdline.txt").read_bytes())
            boot = (root / "boot/firmware/config.txt").read_text(encoding="utf-8")
            self.assertEqual(boot.count(appliance.BEGIN_MARKER), 1)
            self.assertIn("dtoverlay=uart0-pi5", boot)
            self.assertEqual([], appliance.static_findings(root))
            self.assertEqual(
                0o400,
                stat.S_IMODE((root / "etc/cloudflared/rover-bean.token").stat().st_mode),
            )
            generated = b"".join(
                path.read_bytes() for path in (root / "etc").rglob("*") if path.is_file()
                and path.name != "rover-bean.token"
            )
            self.assertNotIn(("T" * 80).encode(), generated)

    def test_live_install_can_defer_validated_security_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root, key, token = self.stage_inputs(Path(raw))
            appliance.stage_root(root, key, token, skip_security_files=True)
            self.assertFalse((root / "etc/sudoers.d/rover-bean-agent").exists())
            self.assertFalse((root / "etc/ssh/sshd_config.d/10-rover-bean.conf").exists())
            self.assertTrue((root / "etc/udev/rules.d/70-rover-pico-uart.rules").exists())

    def test_rejects_options_private_keys_and_weak_tokens(self) -> None:
        with self.assertRaises(appliance.ApplianceError):
            appliance.validate_public_key("command=oops " + public_key())
        with self.assertRaises(appliance.ApplianceError):
            appliance.validate_public_key("-----BEGIN OPENSSH PRIVATE KEY-----\n")
        with self.assertRaises(appliance.ApplianceError):
            appliance.validate_public_key(public_key() + public_key())
        with self.assertRaises(appliance.ApplianceError):
            appliance.validate_tunnel_token("short token")
        valid_hash = "$y$j9T$" + "s" * 16 + "$" + "h" * 43
        self.assertTrue(appliance.validate_console_password_hash(valid_hash + "\n"))
        with self.assertRaises(appliance.ApplianceError):
            appliance.validate_console_password_hash("plaintext")
        with self.assertRaises(appliance.ApplianceError):
            appliance.validate_public_key(
                "ssh-ed25519 " + base64.b64encode(b"not-an-ssh-wire-key" * 3).decode()
            )

    def test_versions_are_numeric(self) -> None:
        self.assertGreater(appliance.parse_version("cloudflared version 2025.10.1"),
                           appliance.parse_version("2025.4.0"))
        with self.assertRaises(appliance.ApplianceError):
            appliance.parse_version("cloudflared banana")

    def test_ssh_attestation_uses_exposed_authenticated_key(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            auth_info = temp / "auth-info"
            auth_info.write_text("publickey " + public_key(), encoding="utf-8")
            record = appliance.attest_ssh(
                temp,
                {"SSH_CONNECTION": "192.0.2.2 123 192.0.2.3 22",
                 "SSH_USER_AUTH": str(auth_info)},
                username="agent",
            )
            self.assertEqual(record["kind"], "fresh_ssh_pubkey_session")
            stored = json.loads(
                (temp / "var/lib/rover-bean-attest/ssh.json").read_text(encoding="utf-8")
            )
            self.assertEqual(stored["fingerprint"], record["fingerprint"])

    def test_console_attestation_requires_debug_uart(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            record = appliance.attest_console(root, "/dev/ttyAMA10", username="agent")
            self.assertEqual(record["tty"], "/dev/ttyAMA10")
            with self.assertRaises(appliance.ApplianceError):
                appliance.attest_console(root, "/dev/ttyAMA0", username="agent")

    def test_access_attestation_requires_fresh_ssh_and_edge_log(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            record = appliance.attest_access(
                root,
                "rover.example.com",
                "edge-event-12345",
                {"SSH_CONNECTION": "192.0.2.2 123 127.0.0.1 22"},
                username="agent",
            )
            self.assertEqual(record["kind"], "cloudflare_access_proxycommand_session")
            self.assertTrue((root / "var/lib/rover-bean-attest/access.json").exists())
            with self.assertRaises(appliance.ApplianceError):
                appliance.attest_access(
                    root, "rover.example.com", "short", {}, username="agent"
                )

    def test_login_wrapper_propagates_recorded_command_failure_without_replay(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            wrapper = temp / "login"
            wrapper.write_text(appliance.rendered_files()["/usr/local/libexec/rover-bean-login"])
            wrapper.chmod(0o755)
            session_dir = temp / "sessions"
            session_dir.mkdir()
            config = temp / "tlog.conf"
            config.write_text("{}\n", encoding="utf-8")
            calls = temp / "calls"
            recorder = temp / "recorder"
            recorder.write_text(
                "#!/usr/bin/env bash\nprintf 'recorder\\n' >> \"$ROVER_TEST_CALLS\"\n"
                "printf '{\\\"rec\\\":\\\"bootcurrent-1\\\",\\\"session\\\":4242,\\\"record\\\":true}\\n' >> \"$ROVER_BEAN_SESSION_DIR/tlog.jsonl\"\nexit 7\n",
                encoding="utf-8",
            )
            recorder.chmod(0o755)
            fallback = temp / "fallback"
            fallback.write_text(
                "#!/usr/bin/env bash\nprintf 'fallback\\n' >> \"$ROVER_TEST_CALLS\"\n",
                encoding="utf-8",
            )
            fallback.chmod(0o755)
            logger = temp / "logger"
            logger.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            logger.chmod(0o755)
            env = {
                **os.environ,
                "ROVER_BEAN_LOGIN_TEST": "1",
                "ROVER_BEAN_TLOG": str(recorder),
                "ROVER_BEAN_TLOG_CONFIG": str(config),
                "ROVER_BEAN_SESSION_DIR": str(session_dir),
                "ROVER_BEAN_EVENT_FILE": str(temp / "events.jsonl"),
                "ROVER_BEAN_LOGGER": str(logger),
                "ROVER_BEAN_FALLBACK_SHELL": str(fallback),
                "ROVER_BEAN_AUDIT_SESSION": "4242",
                "ROVER_BEAN_BOOT_ID": "bootcurrent",
                "ROVER_TEST_CALLS": str(calls),
            }
            result = subprocess.run([str(wrapper), "-c", "false"], env=env, check=False)
            self.assertEqual(result.returncode, 7)
            self.assertEqual(calls.read_text(encoding="utf-8"), "recorder\n")

    def test_login_wrapper_fails_open_and_emits_event_when_capture_does_not_start(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            wrapper = temp / "login"
            wrapper.write_text(appliance.rendered_files()["/usr/local/libexec/rover-bean-login"])
            wrapper.chmod(0o755)
            session_dir = temp / "sessions"
            session_dir.mkdir()
            config = temp / "tlog.conf"
            config.write_text("{}\n", encoding="utf-8")
            calls = temp / "calls"
            recorder = temp / "recorder"
            recorder.write_text("#!/usr/bin/env bash\nexit 23\n", encoding="utf-8")
            recorder.chmod(0o755)
            fallback = temp / "fallback"
            fallback.write_text(
                "#!/usr/bin/env bash\nprintf 'fallback %s\\n' \"$*\" >> \"$ROVER_TEST_CALLS\"\n",
                encoding="utf-8",
            )
            fallback.chmod(0o755)
            logger = temp / "logger"
            logger.write_text(
                "#!/usr/bin/env bash\nprintf 'alert %s\\n' \"$*\" >> \"$ROVER_TEST_CALLS\"\n",
                encoding="utf-8",
            )
            logger.chmod(0o755)
            env = {
                **os.environ,
                "ROVER_BEAN_LOGIN_TEST": "1",
                "ROVER_BEAN_TLOG": str(recorder),
                "ROVER_BEAN_TLOG_CONFIG": str(config),
                "ROVER_BEAN_SESSION_DIR": str(session_dir),
                "ROVER_BEAN_EVENT_FILE": str(temp / "events.jsonl"),
                "ROVER_BEAN_LOGGER": str(logger),
                "ROVER_BEAN_FALLBACK_SHELL": str(fallback),
                "ROVER_BEAN_AUDIT_SESSION": "4242",
                "ROVER_BEAN_BOOT_ID": "bootcurrent",
                "ROVER_TEST_CALLS": str(calls),
            }
            result = subprocess.run([str(wrapper)], env=env, check=False)
            self.assertEqual(result.returncode, 0)
            captured = calls.read_text(encoding="utf-8")
            self.assertIn("capture_failure status=23", captured)
            self.assertIn("fallback ", captured)
            event = json.loads((temp / "events.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(event, {"kind": "capture_failure", "status": 23})

    def test_login_wrapper_does_not_replay_nested_same_audit_session(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            wrapper = temp / "login"
            wrapper.write_text(appliance.rendered_files()["/usr/local/libexec/rover-bean-login"])
            wrapper.chmod(0o755)
            session_dir = temp / "sessions"
            session_dir.mkdir()
            (session_dir / "tlog.jsonl").write_text(
                '{"rec":"bootcurrent-1","session":4242,"record":true}\n'
            )
            config = temp / "tlog.conf"
            config.write_text("{}\n")
            calls = temp / "calls"
            recorder = temp / "recorder"
            recorder.write_text(
                "#!/usr/bin/env bash\nprintf 'recorder\\n' >> \"$ROVER_TEST_CALLS\"\nexit 8\n"
            )
            recorder.chmod(0o755)
            fallback = temp / "fallback"
            fallback.write_text(
                "#!/usr/bin/env bash\nprintf 'fallback\\n' >> \"$ROVER_TEST_CALLS\"\n"
            )
            fallback.chmod(0o755)
            logger = temp / "logger"
            logger.write_text("#!/usr/bin/env bash\nexit 0\n")
            logger.chmod(0o755)
            env = {
                **os.environ,
                "ROVER_BEAN_LOGIN_TEST": "1",
                "ROVER_BEAN_TLOG": str(recorder),
                "ROVER_BEAN_TLOG_CONFIG": str(config),
                "ROVER_BEAN_SESSION_DIR": str(session_dir),
                "ROVER_BEAN_EVENT_FILE": str(temp / "events.jsonl"),
                "ROVER_BEAN_LOGGER": str(logger),
                "ROVER_BEAN_FALLBACK_SHELL": str(fallback),
                "ROVER_BEAN_AUDIT_SESSION": "4242",
                "ROVER_BEAN_BOOT_ID": "bootcurrent",
                "ROVER_TEST_CALLS": str(calls),
            }
            result = subprocess.run([str(wrapper), "-c", "false"], env=env, check=False)
            self.assertEqual(result.returncode, 8)
            self.assertEqual(calls.read_text(), "recorder\n")
            self.assertFalse((temp / "events.jsonl").exists())

    def test_login_wrapper_does_not_deduplicate_a_prior_boot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            wrapper = temp / "login"
            wrapper.write_text(appliance.rendered_files()["/usr/local/libexec/rover-bean-login"])
            wrapper.chmod(0o755)
            session_dir = temp / "sessions"
            session_dir.mkdir()
            (session_dir / "tlog.jsonl").write_text(
                '{"rec":"bootprevious-1","session":4242,"record":true}\n'
            )
            config = temp / "tlog.conf"
            config.write_text("{}\n")
            calls = temp / "calls"
            recorder = temp / "recorder"
            recorder.write_text("#!/usr/bin/env bash\nexit 29\n")
            recorder.chmod(0o755)
            fallback = temp / "fallback"
            fallback.write_text(
                "#!/usr/bin/env bash\nprintf 'fallback\\n' >> \"$ROVER_TEST_CALLS\"\n"
            )
            fallback.chmod(0o755)
            logger = temp / "logger"
            logger.write_text("#!/usr/bin/env bash\nexit 0\n")
            logger.chmod(0o755)
            env = {
                **os.environ,
                "ROVER_BEAN_LOGIN_TEST": "1",
                "ROVER_BEAN_TLOG": str(recorder),
                "ROVER_BEAN_TLOG_CONFIG": str(config),
                "ROVER_BEAN_SESSION_DIR": str(session_dir),
                "ROVER_BEAN_EVENT_FILE": str(temp / "events.jsonl"),
                "ROVER_BEAN_LOGGER": str(logger),
                "ROVER_BEAN_FALLBACK_SHELL": str(fallback),
                "ROVER_BEAN_AUDIT_SESSION": "4242",
                "ROVER_BEAN_BOOT_ID": "bootcurrent",
                "ROVER_TEST_CALLS": str(calls),
            }
            result = subprocess.run([str(wrapper)], env=env, check=False)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(calls.read_text(), "fallback\n")
            self.assertEqual(
                json.loads((temp / "events.jsonl").read_text())["status"], 29
            )

    def test_login_wrapper_never_replays_failed_remote_command(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            wrapper = temp / "login"
            wrapper.write_text(appliance.rendered_files()["/usr/local/libexec/rover-bean-login"])
            wrapper.chmod(0o755)
            session_dir = temp / "sessions"
            session_dir.mkdir()
            config = temp / "tlog.conf"
            config.write_text("{}\n")
            calls = temp / "calls"
            recorder = temp / "recorder"
            recorder.write_text(
                "#!/usr/bin/env bash\nprintf 'recorder\\n' >> \"$ROVER_TEST_CALLS\"\nexit 31\n"
            )
            recorder.chmod(0o755)
            fallback = temp / "fallback"
            fallback.write_text(
                "#!/usr/bin/env bash\nprintf 'fallback\\n' >> \"$ROVER_TEST_CALLS\"\n"
            )
            fallback.chmod(0o755)
            logger = temp / "logger"
            logger.write_text("#!/usr/bin/env bash\nexit 0\n")
            logger.chmod(0o755)
            env = {
                **os.environ,
                "ROVER_BEAN_LOGIN_TEST": "1",
                "ROVER_BEAN_TLOG": str(recorder),
                "ROVER_BEAN_TLOG_CONFIG": str(config),
                "ROVER_BEAN_SESSION_DIR": str(session_dir),
                "ROVER_BEAN_EVENT_FILE": str(temp / "events.jsonl"),
                "ROVER_BEAN_LOGGER": str(logger),
                "ROVER_BEAN_FALLBACK_SHELL": str(fallback),
                "ROVER_BEAN_AUDIT_SESSION": "4242",
                "ROVER_BEAN_BOOT_ID": "bootcurrent",
                "ROVER_TEST_CALLS": str(calls),
            }
            result = subprocess.run([str(wrapper), "-c", "do-something"],
                                    env=env, check=False)
            self.assertEqual(result.returncode, 31)
            self.assertEqual(calls.read_text(), "recorder\n")
            self.assertEqual(
                json.loads((temp / "events.jsonl").read_text())["status"], 31
            )

    def test_pi_to_pico_artifacts_contain_no_flash_path(self) -> None:
        payload = "\n".join(appliance.rendered_files().values()).lower()
        for forbidden in ("picotool", "openocd", "flash firmware", "/dev/swd"):
            self.assertNotIn(forbidden, payload)
        rule = appliance.rendered_files()["/etc/udev/rules.d/70-rover-pico-uart.rules"]
        self.assertIn('PROGRAM=="/usr/bin/readlink -f /sys%p/device/of_node"', rule)
        self.assertIn('RESULT=="*/rp1/serial@30000"', rule)
        self.assertNotIn("of_node/full_name", rule)
        self.assertIn('SYMLINK+="rover-pico"', rule)

    def test_services_and_installer_preserve_the_reviewed_boundaries(self) -> None:
        files = appliance.rendered_files()
        tunnel = files["/etc/systemd/system/rover-cloudflared.service"]
        self.assertIn("User=cloudflared", tunnel)
        self.assertIn("--token-file /etc/cloudflared/rover-bean.token", tunnel)
        self.assertIn("AF_NETLINK", tunnel)
        self.assertIn("ProtectSystem=strict", tunnel)
        backup = files["/etc/systemd/system/rover-audit-backup.service"]
        self.assertIn("/opt/rover-bean/appliance/audit_backup.py", backup)
        self.assertIn("/mnt/robot-audit", backup)
        manifest = appliance.load_manifest()
        self.assertEqual(
            manifest["secrets"]["tunnel_token"],
            "/etc/cloudflared/rover-bean.token",
        )
        installer = (appliance.ROOT / "software/install.sh").read_text(encoding="utf-8")
        self.assertIn("--access-ready", installer)
        self.assertIn("visudo -cf", installer)
        self.assertIn("rollback_sshd", installer)
        self.assertIn("chpasswd -e", installer)
        self.assertNotIn("usermod --password", installer)
        self.assertIn("robotd_was_enabled", installer)
        self.assertNotIn("systemctl enable --now robotd", installer)
        self.assertNotIn("cmdline.txt", installer)
        self.assertNotIn("set -x", installer)
        unit = (appliance.ROOT / "software/systemd/robotd.service").read_text()
        self.assertIn("ExecStartPre=/usr/bin/test -c /dev/rover-pico", unit)
        self.assertIn("--device /dev/rover-pico", unit)


if __name__ == "__main__":
    unittest.main()
