import importlib.util
import pathlib
import tempfile
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_arm64_modules", ROOT / "tools/audit-arm64-modules.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def elf(machine):
    return b"\x7fELF\x02\x01" + b"\0" * 10 + (1).to_bytes(2, "little") + machine.to_bytes(2, "little")


class ModuleAuditTests(unittest.TestCase):
    def test_accepts_matching_module_and_rejects_wrong_architecture_or_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            path = root / "driver.ko"
            path.write_bytes(elf(183))
            with mock.patch.object(AUDIT.subprocess, "run", return_value=types.SimpleNamespace(
                    returncode=0, stdout="7.3.1-test SMP aarch64\n")):
                self.assertEqual(AUDIT.inspect_module(root, "driver.o", "7.3.1-test")["path"], "driver.ko")
                with self.assertRaisesRegex(ValueError, "vermagic"):
                    AUDIT.inspect_module(root, "driver.o", "7.3.2-test")
                path.write_bytes(elf(62))
                with self.assertRaisesRegex(ValueError, "AArch64"):
                    AUDIT.inspect_module(root, "driver.o", "7.3.1-test")

    def test_rejects_paths_outside_tree_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            (root / "real.ko").write_bytes(elf(183))
            (root / "link.ko").symlink_to("real.ko")
            for entry in ("../outside.o", "/outside.o", "link.ko"):
                with self.assertRaises(ValueError):
                    AUDIT.module_path(root, entry)

    def test_rejects_incomplete_builtin_only_symbol_table(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "include/config").mkdir(parents=True)
            (root / "arch/arm64/boot").mkdir(parents=True)
            (root / "arch/arm64/boot/Image").write_bytes(b"\0" * 56 + b"ARMd" + b"\0" * 4)
            (root / "vmlinux").write_bytes(b"test vmlinux")
            (root / "include/config/kernel.release").write_text("7.3.1-test\n")
            (root / ".config").write_text("CONFIG_MODULES=y\n")
            (root / "modules.order").write_text("driver.o\n")
            (root / "Module.symvers").write_text("0x01234567 symbol vmlinux EXPORT_SYMBOL\n")
            with mock.patch.object(AUDIT, "image_matches_vmlinux", return_value=True):
                with self.assertRaisesRegex(ValueError, "vmlinux-only"):
                    AUDIT.audit(root, "7.3.1-test", 1)

    def test_full_report_requires_non_builtin_exports_and_matching_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "include/config").mkdir(parents=True)
            (root / "arch/arm64/boot").mkdir(parents=True)
            (root / "arch/arm64/boot/Image").write_bytes(b"\0" * 56 + b"ARMd" + b"\0" * 4)
            (root / "vmlinux").write_bytes(b"test vmlinux")
            (root / "include/config/kernel.release").write_text("7.3.1-test\n")
            (root / ".config").write_text("CONFIG_MODULES=y\n")
            (root / "modules.order").write_text("driver.o\n")
            (root / "Module.symvers").write_text(
                "0x01234567 symbol vmlinux EXPORT_SYMBOL\n"
                "0x12345678 driver_symbol driver EXPORT_SYMBOL\n")
            (root / "driver.ko").write_bytes(elf(183))
            with mock.patch.object(AUDIT, "image_matches_vmlinux", return_value=True), \
                 mock.patch.object(AUDIT.subprocess, "run", return_value=types.SimpleNamespace(
                    returncode=0, stdout="7.3.1-test SMP aarch64\n")):
                report = AUDIT.audit(root, "7.3.1-test", 1)
            self.assertEqual(report["module_count"], 1)
            self.assertEqual(report["module_export_count"], 1)
            with self.assertRaisesRegex(ValueError, "kernel release"):
                AUDIT.audit(root, "7.3.2-test", 1)

    def test_stale_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "include/config").mkdir(parents=True)
            (root / "arch/arm64/boot").mkdir(parents=True)
            (root / "include/config/kernel.release").write_text("7.3.1-test\n")
            (root / ".config").write_text("CONFIG_MODULES=y\n")
            (root / "modules.order").write_text("driver.o\n")
            (root / "Module.symvers").write_text("0x12345678 symbol driver EXPORT_SYMBOL\n")
            (root / "vmlinux").write_bytes(b"test vmlinux")
            (root / "arch/arm64/boot/Image").write_bytes(b"\0" * 56 + b"ARMd" + b"\0" * 4)
            with mock.patch.object(AUDIT, "image_matches_vmlinux", return_value=False):
                with self.assertRaisesRegex(ValueError, "does not match current vmlinux"):
                    AUDIT.audit(root, "7.3.1-test", 1)

    def test_image_comparison_uses_reconstructed_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            image = root / "Image"
            image.write_bytes(b"matching image")
            def fake_objcopy(command, **_kwargs):
                pathlib.Path(command[-1]).write_bytes(b"matching image")
                return types.SimpleNamespace(returncode=0)
            with mock.patch.object(AUDIT.subprocess, "run", side_effect=fake_objcopy):
                self.assertTrue(AUDIT.image_matches_vmlinux(root / "vmlinux", image))
                image.write_bytes(b"stale image")
                self.assertFalse(AUDIT.image_matches_vmlinux(root / "vmlinux", image))

    def test_dtb_identity_and_magic_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            dtb = root / "board.dtb"
            dtb.write_bytes(b"\xd0\x0d\xfe\xedtest")
            self.assertEqual(AUDIT.inspect_dtb(root, dtb)["path"], "board.dtb")
            dtb.write_bytes(b"not a dtb")
            with self.assertRaisesRegex(ValueError, "magic"):
                AUDIT.inspect_dtb(root, dtb)


if __name__ == "__main__":
    unittest.main()
