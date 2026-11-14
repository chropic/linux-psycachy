"""Pure validation tests for the dedicated SP12 live-image builder."""
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sp12_live_builder", ROOT / "iso/build-sp12-live.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class Sp12LiveBuilderTests(unittest.TestCase):
    def test_esp_snapshot_requires_exact_read_only_fat_mount(self):
        mount = '/dev/sda1 /boot/efi vfat ro,relatime\n'
        self.assertEqual(BUILDER.validate_esp_mount(mount), mount)
        for invalid, message in (
                ('/dev/root / ext4 rw,relatime\n', 'not mounted exactly'),
                ('/dev/sda1 /boot/efi vfat rw,relatime\n', 'read-only'),
                ('/dev/sda1 /boot/efi ext4 ro,relatime\n', 'not FAT')):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(RuntimeError, message):
                BUILDER.validate_esp_mount(invalid)

    def test_base_and_kernel_pins_identify_current_arm64_inputs(self):
        base = BUILDER.load_json(BUILDER.BASE_PIN)
        kernel = BUILDER.ISO_MODULE.validate_pin_pair(BUILDER.load_json(BUILDER.KERNEL_PIN))
        support = BUILDER.load_support_pin()
        self.assertEqual((base["release"], base["architecture"]), ("26.10", "arm64"))
        self.assertEqual(kernel["kernel_release"], "7.3.1-psycachy-sp121")
        self.assertEqual(kernel["dtb_path"], "qcom/x1p42100-microsoft-sp12in.dtb")
        self.assertEqual(kernel["dtb_sha256"], "5690bc3a88b4ecd5d844cb8e32b4b7192f7e8665a22b6053c938b941468ccabc")
        self.assertEqual(support["support_source_commit"], "ea0f07e66beea95898d96fbeb6daa472f4735af3")
        self.assertFalse(support["redistribute_machine_files"])

    def test_build_metadata_is_tied_to_current_kernel_pin(self):
        pin = BUILDER.load_json(BUILDER.KERNEL_PIN)
        metadata = {
            "source_sha256": pin["source_archive_sha256"],
            "source_tree_sha256": pin["source_tree_sha256"],
            "config_sha256": pin["resolved_config_sha256"],
            "kconfig_resolved_config_sha256": pin["resolved_config_sha256"],
            "policy_fragment_sha256": pin["policy_fragment_sha256"],
            "cpu_target": "arm64; packages are for Surface Pro 12 (Qualcomm SC8280XP)",
        }
        self.assertEqual(BUILDER.validate_build_metadata(metadata, pin), metadata)
        metadata["source_tree_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "source_tree_sha256"):
            BUILDER.validate_build_metadata(metadata, pin)

    def test_kernel_input_validation_requires_exact_pin_and_matching_manifest(self):
        pin = BUILDER.load_json(BUILDER.KERNEL_PIN)
        package_report = {"status": "verified-package-structure"}
        metadata = {
            "source_sha256": pin["source_archive_sha256"],
            "source_tree_sha256": pin["source_tree_sha256"],
            "config_sha256": pin["resolved_config_sha256"],
            "kconfig_resolved_config_sha256": pin["resolved_config_sha256"],
            "policy_fragment_sha256": pin["policy_fragment_sha256"],
            "cpu_target": "arm64; packages are for Surface Pro 12",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            packages = root / "packages"
            packages.mkdir()
            for item in pin["packages"]:
                (packages / item["filename"]).write_bytes(b"fixture")
            certificate = root / "module-signing-cert.x509"
            certificate.write_bytes(b"fixture certificate")
            verification = root / "package-verification.json"
            verification.write_text(json.dumps(package_report))
            build_metadata = root / "build-metadata.txt"
            build_metadata.write_text("".join(f"{key}={value}\n" for key, value in metadata.items()))
            hash_by_name = {item["filename"]: item["sha256"] for item in pin["packages"]}
            hash_by_name[certificate.name] = pin["module_signing_certificate_sha256"]
            with mock.patch.object(BUILDER, "sha", side_effect=lambda path: hash_by_name[pathlib.Path(path).name]), \
                    mock.patch.object(BUILDER, "verify_arm64_packages", return_value=package_report) as verify_packages:
                validated_pin, report, validated_metadata = BUILDER.validate_kernel_inputs(
                    packages, verification, build_metadata, certificate)
            verify_packages.assert_called_once_with(
                packages, expected_release=pin["kernel_release"],
                expected_dtb=pin["dtb_path"],
                expected_version=pin["debian_version"],
                expected_dtb_build_id=pin.get("dtb_build_id"))
            self.assertEqual(validated_pin["kernel_release"], pin["kernel_release"])
            self.assertEqual(report, package_report)
            self.assertEqual(validated_metadata, metadata)

            verification.write_text(json.dumps({"status": "stale-report"}))
            with mock.patch.object(BUILDER, "sha", side_effect=lambda path: hash_by_name[pathlib.Path(path).name]), \
                    mock.patch.object(BUILDER, "verify_arm64_packages", return_value=package_report):
                with self.assertRaisesRegex(RuntimeError, "does not match"):
                    BUILDER.validate_kernel_inputs(packages, verification, build_metadata, certificate)

    def test_live_grub_is_explicit_and_non_autoinstall(self):
        source = (
            'set timeout=30\n'
            'menuentry "Try or Install Ubuntu" {\n'
            '  linux /casper/vmlinuz quiet maybe-ubiquity splash ---\n'
            '  initrd /casper/initrd\n'
            '}\n'
        )
        result = BUILDER.grub_config(source, private_support=True)
        live_line = next(line for line in result.splitlines() if "linux /casper/vmlinuz" in line)
        self.assertIn("Try SP12 Ubuntu 26.10 (private local live)", result)
        self.assertIn("boot=casper", live_line)
        self.assertIn("layerfs-path=" + BUILDER.LAYER, live_line)
        self.assertIn("insmod fdt\n", result)
        self.assertNotIn("insmod devicetree", result)
        self.assertIn("devicetree " + BUILDER.LIVE_DTB, result)
        self.assertNotIn("maybe-ubiquity", live_line)
        self.assertNotIn("autoinstall", live_line)
        self.assertNotIn("Install Ubuntu", result)

    def test_live_grub_rejects_autoinstall_and_ambiguous_layout(self):
        with self.assertRaisesRegex(RuntimeError, "Refusing an autoinstall"):
            BUILDER.grub_config(
                'menuentry "Try or Install Ubuntu" {\n'
                ' linux /casper/vmlinuz autoinstall --- quiet\n}\n')
        with self.assertRaisesRegex(RuntimeError, "Unexpected live kernel menu layout"):
            BUILDER.grub_config(
                'menuentry "Try or Install Ubuntu" {\n'
                ' linux /casper/vmlinuz --- quiet\n'
                ' linux /casper/vmlinuz --- quiet\n}\n')
        with self.assertRaisesRegex(RuntimeError, "separator"):
            BUILDER.grub_config(
                'menuentry "Try or Install Ubuntu" {\n'
                ' linux /casper/vmlinuz quiet\n}\n')
        with self.assertRaisesRegex(RuntimeError, "Autoinstall remains"):
            BUILDER.grub_config(
                'menuentry "Try or Install Ubuntu" {\n'
                ' linux /casper/vmlinuz --- quiet\n}\n'
                'menuentry "Other" {\n'
                ' set autoinstall=quiet\n}\n')

    def test_kernel_module_and_dtb_identity_are_checked(self):
        kernel_bytes = b"pinned kernel fixture"
        dtb_bytes = b"pinned dtb fixture"
        release = "7.3.1-test"
        pin = {
            "kernel_release": release,
            "kernel_payload_sha256": hashlib.sha256(kernel_bytes).hexdigest(),
            "dtb_path": "qcom/test.dtb",
            "dtb_sha256": hashlib.sha256(dtb_bytes).hexdigest(),
        }
        report = {"dtb": {"sha256": pin["dtb_sha256"]}}
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            kernel_image = root / "boot" / ("vmlinuz-" + release)
            kernel_image.parent.mkdir()
            kernel_image.write_bytes(kernel_bytes)
            dtb = root / "usr/lib" / ("linux-image-" + release) / pin["dtb_path"]
            dtb.parent.mkdir(parents=True)
            dtb.write_bytes(dtb_bytes)
            modules = root / "usr/lib/modules" / release
            modules.mkdir(parents=True)
            result = BUILDER.verify_kernel_tree(root, pin, report)
            self.assertEqual(result[0], kernel_image)
            self.assertEqual(result[1], dtb)
            self.assertEqual(result[2], modules)

            dtb.write_bytes(b"wrong DTB")
            with self.assertRaisesRegex(RuntimeError, "DTB is missing or differs"):
                BUILDER.verify_kernel_tree(root, pin, report)

    def test_private_support_is_only_read_when_explicit_and_hash_pinned(self):
        support_pin = BUILDER.load_support_pin()
        files = support_pin["machine_files"]
        self.assertEqual(len(files), 4)
        self.assertEqual(support_pin["source_allowlist"], ["lib/firmware/qcom", "usr/share/qcom"])
        with mock.patch.object(BUILDER, "validate_private_support") as validate:
            self.assertEqual(BUILDER.resolve_support_inputs(False, "/missing", "/missing"), (None, {}))
            validate.assert_not_called()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            support = root / "source"
            machine_root = root / "machine"
            support.mkdir()
            machine_root.mkdir()
            for relative, expected in files.items():
                # Exercise the explicit path/commit gate with fixture-owned bytes.
                path = machine_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"private support fixture")
                files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            with mock.patch.object(BUILDER, "output", return_value=support_pin["support_source_commit"]):
                result_pin, checked = BUILDER.validate_private_support(
                    support, machine_root, support_pin)
            self.assertEqual(result_pin, support_pin)
            self.assertEqual(checked, files)

            path = machine_root / next(iter(files))
            path.write_bytes(b"modified")
            with mock.patch.object(BUILDER, "output", return_value=support_pin["support_source_commit"]):
                with self.assertRaisesRegex(RuntimeError, "differs from pin"):
                    BUILDER.validate_private_support(support, machine_root, support_pin)

    def test_publish_outputs_is_transactional_and_refuses_existing_sidecars(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            buildinfo = root / 'buildinfo.json'
            buildinfo.write_text('{"status":"verified"}\n', encoding='utf-8')
            partial = root / 'candidate.iso.partial'
            partial.write_bytes(b'complete audited image bytes')
            final = root / 'candidate.iso'
            owner = (partial.stat().st_uid, partial.stat().st_gid)
            expected = hashlib.sha256(partial.read_bytes()).hexdigest()

            digest = BUILDER.publish_outputs(partial, final, buildinfo, owner)
            self.assertEqual(digest, expected)
            self.assertEqual(final.read_bytes(), b'complete audited image bytes')
            self.assertEqual(pathlib.Path(str(final) + '.sha256').read_text(),
                             f'{expected}  {final.name}\n')
            self.assertEqual(pathlib.Path(str(final) + '.buildinfo.json').read_bytes(),
                             buildinfo.read_bytes())
            self.assertFalse(partial.exists())

            blocked_partial = root / 'blocked.iso.partial'
            blocked_partial.write_bytes(b'audited bytes')
            blocked_final = root / 'blocked.iso'
            pathlib.Path(str(blocked_final) + '.sha256').write_text('preserve me')
            with self.assertRaisesRegex(RuntimeError, 'Refusing to overwrite'):
                BUILDER.publish_outputs(blocked_partial, blocked_final, buildinfo, owner)
            self.assertTrue(blocked_partial.exists())
            self.assertFalse(blocked_final.exists())

            rollback_partial = root / 'rollback.iso.partial'
            rollback_partial.write_bytes(b'audited bytes')
            rollback_final = root / 'rollback.iso'
            real_link = BUILDER.os.link
            calls = 0

            def fail_sidecar_link(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('injected sidecar publication failure')
                return real_link(source, destination)

            with mock.patch.object(BUILDER.os, 'link', side_effect=fail_sidecar_link):
                with self.assertRaisesRegex(OSError, 'injected sidecar'):
                    BUILDER.publish_outputs(rollback_partial, rollback_final, buildinfo, owner)
            self.assertTrue(rollback_partial.exists())
            self.assertFalse(rollback_final.exists())
            self.assertFalse(pathlib.Path(str(rollback_final) + '.sha256').exists())


if __name__ == "__main__":
    unittest.main()
