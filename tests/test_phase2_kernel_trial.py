#!/usr/bin/env python3
import importlib.util
import gzip
import json
import pathlib
import hashlib
import io
import lzma
import shutil
import subprocess
import struct
import tarfile
import tempfile
import threading
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "phase2_kernel_trial", ROOT / "tools/phase2-kernel-trial.py"
)
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


class GrubEntryDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.config = """\
submenu 'Advanced options for Ubuntu' $menuentry_id_option 'gnulinux-advanced-abc123' {
    menuentry 'Ubuntu, with Linux 7.3.0-10-generic' --class ubuntu $menuentry_id_option 'gnulinux-7.3.0-10-generic-advanced-abc123' {
        linux /vmlinuz-7.3.0-10-generic root=UUID=root
    }
    menuentry 'Ubuntu, with Linux 7.3.1-psycachy' --class ubuntu $menuentry_id_option 'gnulinux-7.3.1-psycachy-advanced-abc123' {
        linux /vmlinuz-7.3.1-psycachy root=UUID=root
    }
    menuentry 'Ubuntu, with Linux 7.3.1-psycachy (recovery mode)' --class ubuntu $menuentry_id_option 'gnulinux-7.3.1-psycachy-recovery-abc123' {
        linux /vmlinuz-7.3.1-psycachy root=UUID=root recovery
    }
}
"""

    def test_discovers_candidate_and_fallback_under_submenu(self):
        entries = trial.discover_grub_entries(
            self.config, {"7.3.0-10-generic", "7.3.1-psycachy"}
        )
        self.assertEqual(
            entries["7.3.0-10-generic"],
            "gnulinux-advanced-abc123>gnulinux-7.3.0-10-generic-advanced-abc123",
        )
        self.assertEqual(
            entries["7.3.1-psycachy"],
            "gnulinux-advanced-abc123>gnulinux-7.3.1-psycachy-advanced-abc123",
        )

    def test_refuses_missing_or_ambiguous_entry(self):
        with self.assertRaises(trial.TrialError):
            trial.discover_grub_entries(self.config, {"7.3.2-unknown"})
        duplicate = self.config.replace(
            "\n}\n",
            "\n    menuentry 'Ubuntu, with Linux 7.3.1-psycachy' --class ubuntu $menuentry_id_option 'gnulinux-7.3.1-psycachy-alt-abc123' {\n    }\n}\n",
        )
        with self.assertRaises(trial.TrialError):
            trial.discover_grub_entries(duplicate, {"7.3.1-psycachy"})

    def test_top_level_entry_is_not_given_a_false_submenu_prefix(self):
        config = "menuentry 'Ubuntu, with Linux 7.3.1-psycachy' $menuentry_id_option 'gnulinux-7.3.1-psycachy-abc123' {\n}\n"
        self.assertEqual(
            trial.discover_grub_entries(config, {"7.3.1-psycachy"})[
                "7.3.1-psycachy"
            ],
            "gnulinux-7.3.1-psycachy-abc123",
        )

    def test_nested_submenus_are_qualified_and_comments_are_ignored(self):
        config = """\
# menuentry 'Ubuntu, with Linux 7.3.1-psycachy' $menuentry_id_option 'gnulinux-7.3.1-psycachy-fake' {
submenu 'Outer' $menuentry_id_option 'gnulinux-advanced-outer' {
    submenu 'Inner' $menuentry_id_option 'gnulinux-advanced-inner' {
        menuentry 'Ubuntu, with Linux 7.3.1-psycachy' $menuentry_id_option 'gnulinux-7.3.1-psycachy-advanced-real' {
        }
    }
}
"""
        self.assertEqual(
            trial.discover_grub_entries(config, {"7.3.1-psycachy"})[
                "7.3.1-psycachy"
            ],
            "gnulinux-advanced-outer>gnulinux-advanced-inner>gnulinux-7.3.1-psycachy-advanced-real",
        )

    def test_wrapped_entry_and_release_prefix_collision_fail_closed(self):
        wrapped = "submenu 'Options' $menuentry_id_option 'gnulinux-advanced-a' {\nmenuentry 'Ubuntu Linux 7.3.1-psycachy' {\n}\n}\n"
        with self.assertRaisesRegex(trial.TrialError, "malformed GRUB menuentry"):
            trial.discover_grub_entries(wrapped, {"7.3.1-psycachy"})
        collision = "menuentry 'Ubuntu, with Linux 7.3.1-psycachy-debug' $menuentry_id_option 'gnulinux-7.3.1-psycachy-debug-a' {\n}\n"
        with self.assertRaises(trial.TrialError):
            trial.discover_grub_entries(collision, {"7.3.1-psycachy"})

    def test_fallback_entry_block_is_bound_to_kernel_and_initrd(self):
        block = """menuentry 'Ubuntu, with Linux 7.3.0-10-generic' $menuentry_id_option 'gnulinux-7.3.0-10-generic-a' {
    linux /boot/vmlinuz-7.3.0-10-generic root=UUID=root
    initrd /boot/initrd.img-7.3.0-10-generic
}
"""
        self.assertEqual(len(trial.verify_grub_entry_payloads(block, "7.3.0-10-generic")), 64)
        with self.assertRaisesRegex(trial.TrialError, "pinned kernel"):
            trial.verify_grub_entry_payloads(block.replace("vmlinuz-7.3.0-10-generic", "vmlinuz-other"),
                                             "7.3.0-10-generic")
        with self.assertRaisesRegex(trial.TrialError, "pinned initrd"):
            trial.verify_grub_entry_payloads(block.replace("initrd.img-7.3.0-10-generic", "initrd-other"),
                                             "7.3.0-10-generic")


class TrialStateHelpersTests(unittest.TestCase):
    def test_parse_grub_environment(self):
        state = trial.parse_grubenv(
            "saved_entry=gnulinux-generic\nnext_entry=gnulinux-candidate\n"
        )
        self.assertEqual(state["saved_entry"], "gnulinux-generic")
        self.assertEqual(state["next_entry"], "gnulinux-candidate")

    def test_timeout_units_are_armed_after_userspace_and_do_not_change_default(self):
        start, timeout = trial.render_units(
            pathlib.Path("/var/lib/psycachy/kernel-trial.json"), 120
        )
        self.assertIn("After=multi-user.target", start)
        self.assertIn("arm-timeout", start)
        self.assertIn("OnActiveSec=120s", timeout)
        self.assertIn("ExecStart=/usr/local/sbin/phase2-kernel-trial", timeout)
        self.assertNotIn("grub-set-default", start + timeout)

    def test_secure_boot_enabled_is_detected_before_owner_identity_checks(self):
        result = subprocess.CompletedProcess(
            ["mokutil", "--sb-state"], 0, "SecureBoot enabled\n", ""
        )
        with mock.patch.object(trial, "command", return_value=result):
            self.assertEqual(trial.secure_boot_state(), "enabled")

    def test_secure_boot_enabled_requires_separate_owner_certificate_pins(self):
        secure = subprocess.CompletedProcess(
            ["mokutil", "--sb-state"], 0, "SecureBoot enabled\n", ""
        )
        with mock.patch.object(trial, "command", return_value=secure):
            self.assertEqual(trial.secure_boot_state(), "enabled")
            with self.assertRaisesRegex(trial.TrialError, "identities are not pinned"):
                trial.verify_secure_boot_identity(
                    {"module_signing_certificate_sha256": "a" * 64},
                    "7.3.1-psycachy",
                )

    def test_secure_boot_unenrolled_owner_certificate_is_refused(self):
        result = subprocess.CompletedProcess(
            ["mokutil", "--test-key", "/tmp/module.der"], 1, "", "not enrolled\n"
        )
        with mock.patch.object(trial, "command", return_value=result):
            with self.assertRaisesRegex(trial.TrialError, "not confirmed enrolled"):
                trial._require_enrolled_certificate(pathlib.Path("/tmp/module.der"))

    def test_secure_boot_enrollment_accepts_known_keyring_diagnostic_with_exact_success(self):
        cert = pathlib.Path("/tmp/owner module.der")
        result = subprocess.CompletedProcess(
            ["mokutil", "--test-key", str(cert)], 1,
            f"{cert} is already enrolled\n",
            "Failed to access kernel trusted keyring: Required key not available\n",
        )
        with mock.patch.object(trial, "command", return_value=result):
            trial._require_enrolled_certificate(cert)

        alternate = subprocess.CompletedProcess(
            ["mokutil", "--test-key", str(cert)], 1,
            "Failed to access kernel trusted keyring: Required key not available\n",
            f"{cert} is already in db\n",
        )
        with mock.patch.object(trial, "command", return_value=alternate):
            trial._require_enrolled_certificate(cert)

        ambiguous = subprocess.CompletedProcess(
            ["mokutil", "--test-key", str(cert)], 0,
            f"{cert} is already enrolled\nUnexpected extra output\n", "",
        )
        with mock.patch.object(trial, "command", return_value=ambiguous):
            with self.assertRaisesRegex(trial.TrialError, "not confirmed enrolled"):
                trial._require_enrolled_certificate(cert)

    def test_module_signature_rejects_different_certificate_with_the_same_cn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for label in ("expected", "same-cn-other-key"):
                subprocess.run(
                    ["openssl", "req", "-new", "-x509", "-newkey", "rsa:2048",
                     "-nodes", "-keyout", str(root / f"{label}.key"),
                     "-out", str(root / f"{label}.pem"),
                     "-subj", "/CN=Same Module Signer", "-days", "1"],
                    check=True, capture_output=True,
                )
                subprocess.run(
                    ["openssl", "x509", "-in", str(root / f"{label}.pem"),
                     "-outform", "DER", "-out", str(root / f"{label}.der")],
                    check=True, capture_output=True,
                )
            payload_path = root / "module.payload"
            payload_path.write_bytes(b"module bytes bound to the expected signing key")
            signature_path = root / "module.p7s"
            subprocess.run(
                ["openssl", "cms", "-sign", "-binary", "-noattr", "-nosmimecap",
                 "-nocerts", "-in", str(payload_path), "-signer", str(root / "expected.pem"),
                 "-inkey", str(root / "expected.key"), "-outform", "DER",
                 "-out", str(signature_path)],
                check=True, capture_output=True,
            )
            signature = signature_path.read_bytes()
            header = struct.pack(
                ">BBBBB3sI", 0, 0, trial.MODULE_SIGNATURE_TYPE_PKCS7,
                0, 0, b"\0\0\0", len(signature),
            )
            module_path = root / "nvidia.ko"
            module_path.write_bytes(
                payload_path.read_bytes() + signature + header + trial.MODULE_SIGNATURE_MARKER
            )

            trial._verify_module_signature(module_path, root / "expected.der")
            metadata_header = struct.pack(
                ">BBBBB3sI", 0, 0, trial.MODULE_SIGNATURE_TYPE_PKCS7,
                3, 2, b"\0\0\0", len(signature),
            )
            metadata_module = root / "metadata-fields.ko"
            metadata_module.write_bytes(
                payload_path.read_bytes() + b"sigid" + signature
                + metadata_header + trial.MODULE_SIGNATURE_MARKER
            )
            trial._verify_module_signature(metadata_module, root / "expected.der")
            malformed = root / "malformed.ko"
            malformed_header = struct.pack(
                ">BBBBB3sI", 0, 0, trial.MODULE_SIGNATURE_TYPE_PKCS7,
                0, 0, b"\0\0\0", len(module_path.read_bytes()) + 1,
            )
            malformed.write_bytes(
                payload_path.read_bytes() + signature + malformed_header
                + trial.MODULE_SIGNATURE_MARKER
            )
            with self.assertRaisesRegex(trial.TrialError, "invalid signature lengths"):
                trial._verify_module_signature(malformed, root / "expected.der")
            with self.assertRaisesRegex(trial.TrialError, "does not verify with the pinned certificate"):
                trial._verify_module_signature(module_path, root / "same-cn-other-key.der")
            for suffix, packed in (
                (".ko.gz", gzip.compress(module_path.read_bytes())),
                (".ko.xz", lzma.compress(module_path.read_bytes())),
            ):
                compressed = root / f"nvidia{suffix}"
                compressed.write_bytes(packed)
                trial._verify_module_signature(compressed, root / "expected.der")
                with self.assertRaisesRegex(trial.TrialError, "does not verify with the pinned certificate"):
                    trial._verify_module_signature(compressed, root / "same-cn-other-key.der")
            if shutil.which("zstd"):
                compressed = root / "nvidia.ko.zst"
                packed = subprocess.run(
                    ["zstd", "-q", "-c", str(module_path)],
                    check=True, capture_output=True,
                )
                compressed.write_bytes(packed.stdout)
                trial._verify_module_signature(compressed, root / "expected.der")
                with self.assertRaisesRegex(trial.TrialError, "does not verify with the pinned certificate"):
                    trial._verify_module_signature(compressed, root / "same-cn-other-key.der")

    def test_secure_boot_module_path_must_be_regular_and_confined(self):
        for case in ("outside", "symlink"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                boot = root / "boot"
                boot.mkdir()
                (boot / "config-7.3.1-psycachy").write_text(
                    "CONFIG_MODULE_SIG=y\nCONFIG_MODULE_SIG_ALL=y\nCONFIG_MODULE_SIG_FORCE=y\n",
                    encoding="ascii",
                )
                module_root = root / "modules" / "7.3.1-psycachy"
                module_root.mkdir(parents=True)
                outside = root / "outside.ko"
                outside.write_bytes(b"signed module placeholder")
                if case == "symlink":
                    listed_path = module_root / "nvidia.ko"
                    listed_path.symlink_to(outside)
                    expected_error = "missing or unsafe"
                else:
                    listed_path = outside
                    expected_error = "outside its pinned module tree"

                def fake_command(argv, *, allow_failure=False):
                    if argv[3] == "-n":
                        value = str(listed_path)
                    else:
                        value = "Test DKMS Signer" if argv[4] == "signer" else "PKCS#7"
                    return subprocess.CompletedProcess(argv, 0, value + "\n", "")

                with mock.patch.object(trial, "BOOT_DIR", boot), \
                        mock.patch.object(trial, "MODULES_DIR", root / "modules"), \
                        mock.patch.object(trial, "command", side_effect=fake_command):
                    with self.assertRaisesRegex(trial.TrialError, expected_error):
                        trial._verify_required_module_signers(
                            "7.3.1-psycachy", {"nvidia": "Test DKMS Signer"},
                            module_certificate=root / "module.der",
                            loaded_modules=["nvidia"], runtime=False,
                        )

    def test_secure_boot_identity_checks_certificates_signature_and_transformed_bytes(self):
        kernel_digest = "a" * 64
        module_digest = "b" * 64
        payload = b"exact unsigned package kernel payload"
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            boot = root / "boot"
            boot.mkdir()
            kernel_cert = root / "kernel.pem"
            kernel_cert.write_bytes(b"kernel certificate")
            kernel_der = root / "kernel.der"
            kernel_der.write_bytes(b"kernel certificate DER")
            module_cert = root / "module.der"
            module_cert.write_bytes(b"module certificate DER")
            image = boot / "vmlinuz-7.3.1-psycachy"
            image.write_bytes(payload + b"--SIGNATURE--")
            (boot / "config-7.3.1-psycachy").write_text(
                "CONFIG_MODULE_SIG=y\nCONFIG_MODULE_SIG_ALL=y\nCONFIG_MODULE_SIG_FORCE=y\n",
                encoding="ascii",
            )
            pin = {
                "kernel_payload_sha256": hashlib.sha256(payload).hexdigest(),
                "secure_boot": {
                    "kernel_certificate_sha256": kernel_digest,
                    "module_certificate_sha256": module_digest,
                    "required_module_signers": {"nvidia": "Test DKMS Signer"},
                    "required_loaded_modules": ["nvidia"],
                },
            }
            module_root = root / "modules" / "7.3.1-psycachy"
            module_root.mkdir(parents=True)
            module_path = module_root / "nvidia.ko"
            module_path.write_bytes(b"test module")

            def fake_command(argv, *, allow_failure=False):
                if argv[0] == "openssl":
                    path = pathlib.Path(argv[3])
                    digest = module_digest if path == module_cert else kernel_digest
                    fingerprint = ":".join(digest[index:index + 2].upper()
                                            for index in range(0, len(digest), 2))
                    return subprocess.CompletedProcess(argv, 0,
                                                        f"sha256 Fingerprint={fingerprint}\n", "")
                if argv[:2] == ["mokutil", "--test-key"]:
                    return subprocess.CompletedProcess(argv, 1, f"{argv[2]} is already enrolled\n", "")
                if argv[0] == "sbverify":
                    return subprocess.CompletedProcess(argv, 0, "Signature verification OK\n", "")
                if argv[0] == "sbattach":
                    path = pathlib.Path(argv[-1])
                    path.write_bytes(path.read_bytes().removesuffix(b"--SIGNATURE--"))
                    return subprocess.CompletedProcess(argv, 0, "", "")
                if argv[0] == "modinfo":
                    if argv[3] == "-n":
                        value = str(module_path)
                    else:
                        value = "Test DKMS Signer" if argv[4] == "signer" else "PKCS#7"
                    return subprocess.CompletedProcess(argv, 0, value + "\n", "")
                raise AssertionError(argv)

            with mock.patch.object(trial, "BOOT_DIR", boot), \
                    mock.patch.object(trial, "MODULES_DIR", root / "modules"), \
                    mock.patch.object(trial, "_verify_module_signature"), \
                    mock.patch.object(trial, "command", side_effect=fake_command):
                identity = trial.verify_secure_boot_identity(
                    pin, "7.3.1-psycachy", image_path=image,
                    kernel_certificate=kernel_cert, module_certificate=module_cert,
                )
            self.assertEqual(identity["owner_kernel_certificate_sha256"], kernel_digest)
            self.assertEqual(identity["enrolled_kernel_certificate_sha256"], kernel_digest)
            self.assertEqual(identity["owner_module_certificate_sha256"], module_digest)
            self.assertEqual(identity["enrolled_module_certificate_sha256"], module_digest)
            self.assertEqual(identity["unsigned_kernel_payload_sha256"], pin["kernel_payload_sha256"])
            self.assertEqual(identity["signed_kernel_payload_sha256"], hashlib.sha256(image.read_bytes()).hexdigest())
            self.assertEqual(identity["required_module_signers"], {"nvidia": "Test DKMS Signer"})

    def test_secure_boot_module_runtime_requires_lockdown_enforcement_and_loaded_signer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            boot = root / "boot"
            boot.mkdir()
            (boot / "config-7.3.1-psycachy").write_text(
                "CONFIG_MODULE_SIG=y\nCONFIG_MODULE_SIG_ALL=y\nCONFIG_MODULE_SIG_FORCE=y\n",
                encoding="ascii",
            )
            lockdown = root / "lockdown"
            lockdown.write_text("none [integrity] confidentiality\n", encoding="ascii")
            enforce = root / "sig_enforce"
            enforce.write_text("Y\n", encoding="ascii")
            modules = root / "sys-module"
            (modules / "nvidia").mkdir(parents=True)
            module_root = root / "modules" / "7.3.1-psycachy"
            module_root.mkdir(parents=True)
            module_path = module_root / "nvidia.ko"
            module_path.write_bytes(b"test module")
            commands = []

            def fake_command(argv, *, allow_failure=False):
                commands.append(argv)
                if argv[3] == "-n":
                    value = str(module_path)
                else:
                    field = argv[4]
                    value = "Test DKMS Signer" if field == "signer" else "PKCS#7"
                return subprocess.CompletedProcess(argv, 0, value + "\n", "")

            with mock.patch.object(trial, "BOOT_DIR", boot), \
                    mock.patch.object(trial, "MODULES_DIR", root / "modules"), \
                    mock.patch.object(trial, "LOCKDOWN_STATUS", lockdown), \
                    mock.patch.object(trial, "MODULE_ENFORCE_STATUS", enforce), \
                    mock.patch.object(trial, "SYS_MODULE_DIR", modules), \
                    mock.patch.object(trial, "_verify_module_signature"), \
                    mock.patch.object(trial, "command", side_effect=fake_command):
                trial._verify_required_module_signers(
                    "7.3.1-psycachy", {"nvidia": "Test DKMS Signer"},
                    module_certificate=root / "module.der",
                    loaded_modules=["nvidia"], runtime=True,
                )
            self.assertEqual(len(commands), 3)

            enforce.write_text("N\n", encoding="ascii")
            with mock.patch.object(trial, "BOOT_DIR", boot), \
                    mock.patch.object(trial, "LOCKDOWN_STATUS", lockdown), \
                    mock.patch.object(trial, "MODULE_ENFORCE_STATUS", enforce), \
                    mock.patch.object(trial, "SYS_MODULE_DIR", modules):
                with self.assertRaisesRegex(trial.TrialError, "not enforcing module signatures"):
                    trial._verify_required_module_signers(
                        "7.3.1-psycachy", {"nvidia": "Test DKMS Signer"},
                        module_certificate=root / "module.der",
                        loaded_modules=["nvidia"], runtime=True,
                    )

    def test_secure_boot_candidate_verification_failure_requests_automatic_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = pathlib.Path(directory) / "state.json"
            state = {
                "schema_version": 1,
                "state": "pending",
                "kernel_release": "7.3.1-psycachy",
                "fallback_release": "7.3.0-10-generic",
                "fallback_entry": "fallback-entry",
                "secure_boot_mode": "enabled",
                "secure_boot_identity": {"owner_kernel_certificate_sha256": "a" * 64},
                "required_units": [],
                "runtime": {},
            }
            trial.write_state(state_file, state)
            rollback = {"state": "timeout_reboot_requested"}
            with mock.patch.object(trial, "verify_fallback_unchanged"), \
                    mock.patch.object(trial, "verify_candidate_integrity",
                                      side_effect=trial.TrialError("module trust check failed")), \
                    mock.patch.object(trial, "rollback_locked", return_value=rollback) as request_rollback, \
                    mock.patch.object(trial.os, "uname",
                                      return_value=types.SimpleNamespace(release="7.3.1-psycachy")):
                result = trial.arm_timeout_locked(state_file)
            self.assertEqual(result, rollback)
            request_rollback.assert_called_once_with(state_file, expired=True)
            self.assertEqual(
                trial.read_state(state_file)["security_verification_error"],
                "module trust check failed",
            )

    def test_secure_boot_disabled_is_recorded(self):
        result = subprocess.CompletedProcess(
            ["mokutil", "--sb-state"], 0, "SecureBoot disabled\n", ""
        )
        with mock.patch.object(trial, "command", return_value=result):
            self.assertEqual(trial.secure_boot_state(), "disabled")

    def test_secure_boot_unknown_or_unreadable_fails_closed(self):
        unknown = subprocess.CompletedProcess(["mokutil"], 0, "state unavailable\n", "")
        unreadable = subprocess.CompletedProcess(["mokutil"], 1, "", "permission denied")
        for result in (unknown, unreadable):
            with mock.patch.object(trial, "command", return_value=result):
                with self.assertRaisesRegex(trial.TrialError, "refusing"):
                    trial.secure_boot_state()

    def test_fallback_identity_change_is_refused(self):
        state = {
            "architecture": "amd64",
            "fallback_release": "7.3.0-10-generic",
            "fallback_image_package_version": "1.0",
            "fallback_headers_package_version": "1.0",
            "fallback_payload_hashes": {"vmlinuz": "a" * 64},
        }
        changed = {
            "image_package_version": "1.0",
            "headers_package_version": "1.0",
            "payload_hashes": {"vmlinuz": "b" * 64},
        }
        with mock.patch.object(trial, "fallback_identity", return_value=changed):
            with self.assertRaisesRegex(trial.TrialError, "fallback payload changed"):
                trial.verify_fallback_unchanged(state)

    def _make_backup(self, directory, *, corrupt_payload=False):
        pin = trial.read_pin(ROOT / "config/amd64-iso-kernel.json")
        root = pathlib.Path(directory)
        archive_path = root / "displaced.tar"
        backup_root = root / "backup-tree"
        members = {
            "image_deb": "backup/image.deb",
            "headers_deb": "backup/headers.deb",
            "vmlinuz": "backup/vmlinuz",
            "initrd": "backup/initrd",
            "kernel_config": "backup/config",
            "system_map": "backup/System.map",
            "modules_tree": "backup/modules",
            "headers_tree": "backup/headers-tree",
            "signed_payload": "backup/signed.efi",
            "grub_config": "backup/grub.cfg",
        }
        files = {
            "image_deb": b"image-deb-bytes",
            "headers_deb": b"headers-deb-bytes",
            "vmlinuz": b"old-kernel",
            "initrd": b"old-initrd",
            "kernel_config": b"old-config",
            "system_map": b"old-system-map",
            "signed_payload": b"old-signed-image",
            "grub_config": b"old-grub-config",
        }
        trees = {
            "modules_tree": ("backup/modules", {"kernel/module.ko": b"old-module"}),
            "headers_tree": ("backup/headers-tree", {"include/linux/test.h": b"old-header"}),
        }
        records = {}
        for semantic, content in files.items():
            records[semantic] = (content, 0o644, "file")
        for semantic, (archive_root, tree_files) in trees.items():
            local_root = backup_root / semantic
            local_root.mkdir(parents=True)
            for relative, content in tree_files.items():
                local_path = local_root / relative
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(content)
                local_path.chmod(0o644)
                local_dir = local_path.parent
                while local_dir != local_root:
                    local_dir.chmod(0o755)
                    local_dir = local_dir.parent
            records[semantic] = (local_root, 0o755, "tree")

        with tarfile.open(archive_path, "w") as archive:
            parent = tarfile.TarInfo("backup")
            parent.type = tarfile.DIRTYPE
            parent.mode = 0o755
            archive.addfile(parent)
            for semantic, content in files.items():
                if corrupt_payload and semantic == "vmlinuz":
                    content = b"wrong-kernel"
                info = tarfile.TarInfo(members[semantic])
                info.size = len(content)
                info.mode = 0o644
                archive.addfile(info, io.BytesIO(content))
            for semantic, (archive_root, tree_files) in trees.items():
                root_info = tarfile.TarInfo(archive_root)
                root_info.type = tarfile.DIRTYPE
                root_info.mode = 0o755
                archive.addfile(root_info)
                dirs = set()
                for relative in tree_files:
                    parent = pathlib.PurePosixPath(relative).parent
                    while str(parent) != ".":
                        dirs.add(str(parent))
                        parent = parent.parent
                for relative_dir in sorted(dirs, key=lambda item: (item.count("/"), item)):
                    directory_info = tarfile.TarInfo(archive_root + "/" + relative_dir)
                    directory_info.type = tarfile.DIRTYPE
                    directory_info.mode = 0o755
                    archive.addfile(directory_info)
                for relative, content in tree_files.items():
                    info = tarfile.TarInfo(archive_root + "/" + relative)
                    info.size = len(content)
                    info.mode = 0o644
                    archive.addfile(info, io.BytesIO(content))

        payloads = {}
        for semantic, value in records.items():
            content, mode, kind = value
            if kind == "file":
                payloads[semantic] = hashlib.sha256(content).hexdigest()
            else:
                payloads[semantic] = trial.hash_tree(content)
        manifest = {
            "schema_version": 1,
            "architecture": pin["architecture"],
            "kernel_release": pin["kernel_release"],
            "backup_volume_id": "approved-backup-uuid",
            "archive_path": str(archive_path),
            "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
            "archive_members": members,
            "payloads": payloads,
            "displaced_package_versions": {
                f"linux-image-{pin['kernel_release']}": "7.2.0-1",
                f"linux-headers-{pin['kernel_release']}": "7.2.0-1",
            },
        }
        manifest_path = root / "backup.json"
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        expected_manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        return pin, manifest_path, expected_manifest_hash, payloads

    def _backup_commands(self, argv, *, allow_failure=False):
        if argv[0] == "findmnt":
            volume = "approved-backup-uuid" if argv[-1] != "/" else "root-volume-uuid"
            return subprocess.CompletedProcess(argv, 0, volume + "\n", "")
        if argv[0] == "dpkg-deb":
            pin = trial.read_pin(ROOT / "config/amd64-iso-kernel.json")
            package_type = "image" if b"image-deb" in pathlib.Path(argv[2]).read_bytes() else "headers"
            package = f"linux-{package_type}-{pin['kernel_release']}"
            return subprocess.CompletedProcess(
                argv, 0,
                f"Package: {package}\nVersion: 7.2.0-1\nArchitecture: amd64\n", "",
            )
        self.fail(f"Unexpected backup verification command: {argv}")

    def test_displaced_backup_verifies_reviewed_volume_archive_and_members(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            pin, manifest_path, expected_hash, payloads = self._make_backup(directory)
            with mock.patch.object(trial, "command", side_effect=self._backup_commands):
                result = trial.verify_displaced_backup(
                    manifest_path, pin,
                    expected_manifest_sha256=expected_hash,
                    approved_volume_id="approved-backup-uuid",
                )
            self.assertEqual(result["backup_volume_id"], "approved-backup-uuid")
            self.assertEqual(result["payloads"]["vmlinuz"], payloads["vmlinuz"])

    def test_displaced_backup_rejects_archive_bytes_not_bound_to_payload_hash(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            pin, manifest_path, expected_hash, _ = self._make_backup(directory, corrupt_payload=True)
            with mock.patch.object(trial, "command", side_effect=self._backup_commands):
                with self.assertRaisesRegex(trial.TrialError, "archive hash mismatch for vmlinuz"):
                    trial.verify_displaced_backup(
                        manifest_path, pin,
                        expected_manifest_sha256=expected_hash,
                        approved_volume_id="approved-backup-uuid",
                    )

    def test_displaced_backup_rejects_unreviewed_manifest_or_volume(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            pin, manifest_path, expected_hash, _ = self._make_backup(directory)
            with self.assertRaisesRegex(trial.TrialError, "reviewed hash"):
                trial.verify_displaced_backup(
                    manifest_path, pin,
                    expected_manifest_sha256="0" * 64,
                    approved_volume_id="approved-backup-uuid",
                )
            with self.assertRaisesRegex(trial.TrialError, "reviewed volume identity"):
                trial.verify_displaced_backup(
                    manifest_path, pin,
                    expected_manifest_sha256=expected_hash,
                    approved_volume_id="other-volume-uuid",
                )

    def test_ack_and_expire_transitions_are_serialized(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = pathlib.Path(directory) / "state.json"
            state = {
                "schema_version": 1,
                "state": "pending",
                "kernel_release": "7.3.1-psycachy",
                "fallback_release": "7.3.0-10-generic",
                "fallback_entry": "fallback-entry",
                "required_units": ["ssh.service"],
                "runtime": {"script_created": False, "unit_files_created": []},
            }
            trial.write_state(state_file, state)
            reboots = []
            command_lock = threading.Lock()

            def fake_command(argv, *, allow_failure=False):
                with command_lock:
                    if argv[:3] == ["grub-editenv", "/boot/grub/grubenv", "list"]:
                        output = "saved_entry=fallback-entry\n"
                        return subprocess.CompletedProcess(argv, 0, output, "")
                    if argv[:2] == ["systemctl", "reboot"]:
                        reboots.append(True)
                    return subprocess.CompletedProcess(argv, 0, "", "")

            barrier = threading.Barrier(3)
            errors = []

            def run_ack():
                barrier.wait()
                try:
                    with trial.lock_state(state_file):
                        trial.acknowledge_locked(state_file)
                except trial.TrialError as exc:
                    errors.append(str(exc))

            def run_expire():
                barrier.wait()
                try:
                    with trial.lock_state(state_file):
                        trial.rollback_locked(state_file, expired=True)
                except trial.TrialError as exc:
                    errors.append(str(exc))

            with mock.patch.object(trial, "command", side_effect=fake_command), \
                    mock.patch.object(trial.os, "uname", return_value=types.SimpleNamespace(release="7.3.1-psycachy")), \
                    mock.patch.object(trial.os, "geteuid", return_value=0), \
                    mock.patch.object(trial, "verify_fallback_unchanged"):
                threads = [threading.Thread(target=run_ack), threading.Thread(target=run_expire)]
                for thread in threads:
                    thread.start()
                barrier.wait()
                for thread in threads:
                    thread.join(timeout=5)

            final = trial.read_state(state_file)
            self.assertIn(final["state"], {"acknowledged", "timeout_reboot_requested"})
            self.assertLessEqual(len(reboots), 1)
            self.assertEqual(len(errors), 1)

    def test_rollback_request_is_finalized_only_after_fallback_boots(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = pathlib.Path(directory) / "state.json"
            state = {
                "schema_version": 1,
                "state": "pending",
                "kernel_release": "7.3.1-psycachy",
                "fallback_release": "7.3.0-10-generic",
                "fallback_entry": "fallback-entry",
                "required_units": [],
                "runtime": {},
            }
            trial.write_state(state_file, state)
            commands = []
            reboot_attempts = []

            def fake_command(argv, *, allow_failure=False):
                commands.append(argv)
                if argv[:3] == ["grub-editenv", "/boot/grub/grubenv", "list"]:
                    return subprocess.CompletedProcess(argv, 0, "saved_entry=fallback-entry\n", "")
                if argv[:2] == ["systemctl", "reboot"]:
                    reboot_attempts.append(True)
                    if len(reboot_attempts) == 1:
                        raise trial.TrialError("simulated reboot command failure")
                return subprocess.CompletedProcess(argv, 0, "", "")

            with mock.patch.object(trial, "verify_fallback_unchanged"), \
                    mock.patch.object(trial, "grub_state", return_value={"saved_entry": "fallback-entry"}), \
                    mock.patch.object(trial, "command", side_effect=fake_command), \
                    mock.patch.object(trial.os, "uname", return_value=types.SimpleNamespace(release="7.3.1-psycachy")):
                with self.assertRaisesRegex(trial.TrialError, "simulated reboot"):
                    trial.rollback_locked(state_file)
                self.assertEqual(trial.read_state(state_file)["state"], "rollback_requested")
                trial.arm_timeout_locked(state_file)
                self.assertEqual(trial.read_state(state_file)["state"], "rollback_requested")

                with mock.patch.object(trial.os, "uname", return_value=types.SimpleNamespace(release="7.3.0-10-generic")), \
                        mock.patch.object(trial, "cleanup_runtime"):
                    final = trial.arm_timeout_locked(state_file)
            self.assertEqual(final["state"], "rolled_back")
            self.assertEqual(final["observed_kernel_release"], "7.3.0-10-generic")


class PinValidationTests(unittest.TestCase):
    def test_current_amd64_pin_parses_as_candidate(self):
        pin = trial.read_pin(ROOT / "config/amd64-iso-kernel.json")
        self.assertEqual(pin["architecture"], "amd64")
        self.assertEqual(pin["kernel_release"], "7.3.1-psycachy")
        self.assertEqual(len(pin["packages"]), 2)
        self.assertEqual(
            pin["secure_boot"]["kernel_certificate_sha256"],
            "83b6a49f440a53cf6e08bae05a99ce6c6d11d2a47cd7130f1f95ef2b40f4e2da",
        )
        self.assertEqual(pin["secure_boot"]["required_loaded_modules"], ["nvidia"])

    def test_current_arm64_pin_parses_as_candidate(self):
        pin = trial.read_pin(ROOT / "config/arm64-iso-kernel.json")
        self.assertEqual(pin["architecture"], "arm64")
        self.assertEqual(pin["kernel_release"], "7.3.1-psycachy-sp121")


if __name__ == "__main__":
    unittest.main()
