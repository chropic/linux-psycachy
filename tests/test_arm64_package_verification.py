import hashlib
import importlib.util
import json
import os
import pathlib
import struct
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_arm64_packages", ROOT / "tools/verify-arm64-packages.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)
FDT_MAGIC = VERIFY.FDT_MAGIC
verify_arm64_packages = VERIFY.verify_arm64_packages


ROOT = pathlib.Path(__file__).resolve().parents[1]


def make_dummy_dtb(path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write 0xd00dfeed followed by dummy content
    data = struct.pack(">I", FDT_MAGIC) + b"\x00" * 64
    path.write_bytes(data)


def make_dummy_elf(machine: int) -> bytes:
    ident = b"\x7fELF" + bytes((2, 1, 1, 0, 0)) + b"\x00" * 7
    return struct.pack("<16sHHIQQQIHHHHHH", ident, 3, machine, 1, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0)


def build_deb(stage_dir: pathlib.Path, output_deb: pathlib.Path):
    subprocess.run(["dpkg-deb", "-b", str(stage_dir), str(output_deb)], check=True, capture_output=True)


class Arm64PackageVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = pathlib.Path(self.temp_dir.name)
        self.release = "7.3.1-psycachy-sp121"
        self.version = "7.3.1-1psycachy1"

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_valid_packages(self, pkg_dir: pathlib.Path = None) -> tuple:
        target_dir = pkg_dir or self.packages_dir

        # 1. Build image deb
        img_stage = target_dir / "img-stage"
        img_stage.mkdir(parents=True, exist_ok=True)
        (img_stage / "DEBIAN").mkdir(parents=True, exist_ok=True)
        (img_stage / "DEBIAN" / "control").write_text(
            f"Package: linux-image-{self.release}\n"
            f"Version: {self.version}\n"
            f"Architecture: arm64\n"
            f"Maintainer: PsyCachy Builder <builder@example.invalid>\n"
            f"Depends: kmod, linux-base\n"
            f"Description: Linux kernel image for {self.release}\n"
        )
        # Add boot kernel
        boot_dir = img_stage / "boot"
        boot_dir.mkdir(parents=True, exist_ok=True)
        (boot_dir / f"vmlinuz-{self.release}").write_bytes(b"MZ\x00\x00kernel-payload")
        # Add DTB
        dtb_path = img_stage / f"usr/lib/linux-image-{self.release}/qcom/x1p42100-microsoft-sp12in.dtb"
        make_dummy_dtb(dtb_path)

        img_deb = target_dir / f"linux-image-{self.release}_{self.version}_arm64.deb"
        build_deb(img_stage, img_deb)

        # 2. Build headers deb
        hdr_stage = target_dir / "hdr-stage"
        hdr_stage.mkdir(parents=True, exist_ok=True)
        (hdr_stage / "DEBIAN").mkdir(parents=True, exist_ok=True)
        (hdr_stage / "DEBIAN" / "control").write_text(
            f"Package: linux-headers-{self.release}\n"
            f"Version: {self.version}\n"
            f"Architecture: arm64\n"
            f"Maintainer: PsyCachy Builder <builder@example.invalid>\n"
            f"Description: Linux kernel headers for {self.release}\n"
        )
        hdr_prefix = hdr_stage / f"usr/src/linux-headers-{self.release}"
        (hdr_prefix / "include/config").mkdir(parents=True, exist_ok=True)
        (hdr_prefix / "include/generated").mkdir(parents=True, exist_ok=True)
        (hdr_prefix / "scripts/mod").mkdir(parents=True, exist_ok=True)
        (hdr_prefix / ".config").write_text("CONFIG_ARM64=y\n")
        (hdr_prefix / "Module.symvers").write_text("0x00000000\tmodule_layout\tvmlinux\tEXPORT_SYMBOL\n")
        (hdr_prefix / "include/config/auto.conf").write_text("CONFIG_ARM64=y\n")
        (hdr_prefix / "include/generated/autoconf.h").write_text("#define CONFIG_ARM64 1\n")
        (hdr_prefix / "scripts/sign-file").write_bytes(make_dummy_elf(VERIFY.ELF_MACHINE_AARCH64))
        (hdr_prefix / "scripts/sign-file").chmod(0o755)
        (hdr_prefix / "scripts/mod/modpost").write_bytes(make_dummy_elf(VERIFY.ELF_MACHINE_AARCH64))
        (hdr_prefix / "scripts/mod/modpost").chmod(0o755)
        (hdr_prefix / "scripts/basic/fixdep").parent.mkdir(parents=True, exist_ok=True)
        (hdr_prefix / "scripts/basic/fixdep").write_bytes(make_dummy_elf(VERIFY.ELF_MACHINE_AARCH64))
        (hdr_prefix / "scripts/basic/fixdep").chmod(0o755)
        for relative_tool in (
            "scripts/gendwarfksyms/gendwarfksyms",
            "tools/bpf/resolve_btfids/resolve_btfids",
        ):
            tool = hdr_prefix / relative_tool
            tool.parent.mkdir(parents=True, exist_ok=True)
            tool.write_bytes(make_dummy_elf(VERIFY.ELF_MACHINE_AARCH64))
            tool.chmod(0o755)

        # Build symlink
        mod_dir = hdr_stage / f"lib/modules/{self.release}"
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "build").symlink_to(f"/usr/src/linux-headers-{self.release}")

        hdr_deb = target_dir / f"linux-headers-{self.release}_{self.version}_arm64.deb"
        build_deb(hdr_stage, hdr_deb)

        # Clean up staging directories so glob finds only the debs
        for item in (img_stage, hdr_stage):
            subprocess.run(["rm", "-rf", str(item)], check=True)

        return img_deb, hdr_deb

    def repack(self, package: pathlib.Path, stage_name: str, edit):
        stage = self.packages_dir / stage_name
        subprocess.run(["dpkg-deb", "-R", str(package), str(stage)], check=True)
        edit(stage)
        package.unlink()
        build_deb(stage, package)
        subprocess.run(["rm", "-rf", str(stage)], check=True)

    def test_valid_package_pair_passes_verification(self):
        self.create_valid_packages()
        report = verify_arm64_packages(self.packages_dir, expected_release=self.release)
        self.assertEqual(report["status"], "verified-package-structure")
        self.assertEqual(report["architecture"], "arm64")
        self.assertEqual(report["kernel_release"], self.release)
        self.assertEqual(
            report["headers_tools_verified"],
            [
                "scripts/basic/fixdep:AArch64-ELF",
                "scripts/gendwarfksyms/gendwarfksyms:AArch64-ELF",
                "scripts/mod/modpost:AArch64-ELF",
                "scripts/sign-file:AArch64-ELF",
                "tools/bpf/resolve_btfids/resolve_btfids:AArch64-ELF",
            ],
        )
        self.assertTrue(report["dtb"]["fdt_magic_valid"])

    def test_rejects_wrong_architecture(self):
        self.create_valid_packages()
        # Repack image with amd64 architecture
        stage = self.packages_dir / "mod-stage"
        img_deb = list(self.packages_dir.glob("linux-image-*_*.deb"))[0]
        subprocess.run(["dpkg-deb", "-R", str(img_deb), str(stage)], check=True)
        control = stage / "DEBIAN/control"
        control.write_text(control.read_text().replace("Architecture: arm64", "Architecture: amd64"))
        img_deb.unlink()
        build_deb(stage, img_deb)
        subprocess.run(["rm", "-rf", str(stage)], check=True)

        with self.assertRaises(ValueError) as ctx:
            verify_arm64_packages(self.packages_dir, expected_release=self.release)
        self.assertIn("architecture must be arm64", str(ctx.exception).lower())

    def test_rejects_missing_dtb(self):
        self.create_valid_packages()
        stage = self.packages_dir / "mod-stage"
        img_deb = list(self.packages_dir.glob("linux-image-*_*.deb"))[0]
        subprocess.run(["dpkg-deb", "-R", str(img_deb), str(stage)], check=True)
        dtb = stage / f"usr/lib/linux-image-{self.release}/qcom/x1p42100-microsoft-sp12in.dtb"
        dtb.unlink()
        img_deb.unlink()
        build_deb(stage, img_deb)
        subprocess.run(["rm", "-rf", str(stage)], check=True)

        with self.assertRaises(ValueError) as ctx:
            verify_arm64_packages(self.packages_dir, expected_release=self.release)
        self.assertIn("does not contain required dtb", str(ctx.exception).lower())

    def test_rejects_corrupted_dtb_magic(self):
        self.create_valid_packages()
        stage = self.packages_dir / "mod-stage"
        img_deb = list(self.packages_dir.glob("linux-image-*_*.deb"))[0]
        subprocess.run(["dpkg-deb", "-R", str(img_deb), str(stage)], check=True)
        dtb = stage / f"usr/lib/linux-image-{self.release}/qcom/x1p42100-microsoft-sp12in.dtb"
        dtb.write_bytes(b"\x00\x00\x00\x00corrupt-magic")
        img_deb.unlink()
        build_deb(stage, img_deb)
        subprocess.run(["rm", "-rf", str(stage)], check=True)

        with self.assertRaises(ValueError) as ctx:
            verify_arm64_packages(self.packages_dir, expected_release=self.release)
        self.assertIn("invalid fdt magic", str(ctx.exception).lower())

    def test_rejects_missing_dependencies(self):
        self.create_valid_packages()
        stage = self.packages_dir / "mod-stage"
        img_deb = list(self.packages_dir.glob("linux-image-*_*.deb"))[0]
        subprocess.run(["dpkg-deb", "-R", str(img_deb), str(stage)], check=True)
        control = stage / "DEBIAN/control"
        control.write_text(control.read_text().replace("Depends: kmod, linux-base", "Depends: something-else"))
        img_deb.unlink()
        build_deb(stage, img_deb)
        subprocess.run(["rm", "-rf", str(stage)], check=True)

        with self.assertRaises(ValueError) as ctx:
            verify_arm64_packages(self.packages_dir, expected_release=self.release)
        self.assertIn("missing required dependency", str(ctx.exception).lower())

    def test_rejects_version_mismatch(self):
        self.create_valid_packages()
        stage = self.packages_dir / "mod-stage"
        hdr_deb = list(self.packages_dir.glob("linux-headers-*_*.deb"))[0]
        subprocess.run(["dpkg-deb", "-R", str(hdr_deb), str(stage)], check=True)
        control = stage / "DEBIAN/control"
        control.write_text(control.read_text().replace(f"Version: {self.version}", "Version: 9.9.9-different"))
        hdr_deb.unlink()
        build_deb(stage, hdr_deb)
        subprocess.run(["rm", "-rf", str(stage)], check=True)

        with self.assertRaises(ValueError) as ctx:
            verify_arm64_packages(self.packages_dir, expected_release=self.release)
        self.assertIn("version mismatch", str(ctx.exception).lower())

    def test_rejects_matching_but_unexpected_package_versions(self):
        self.create_valid_packages()
        for package in self.packages_dir.glob("linux-*_*.deb"):
            self.repack(
                package,
                f"repack-{package.name}",
                lambda stage: (stage / "DEBIAN/control").write_text(
                    (stage / "DEBIAN/control").read_text().replace(self.version, "9.9.9-unexpected")
                ),
            )
        with self.assertRaisesRegex(ValueError, "Package version must be"):
            verify_arm64_packages(self.packages_dir, expected_release=self.release)

    def test_rejects_dependency_substring_false_positive(self):
        self.create_valid_packages()
        image = next(self.packages_dir.glob("linux-image-*_*.deb"))
        self.repack(
            image,
            "repack-dependencies",
            lambda stage: (stage / "DEBIAN/control").write_text(
                (stage / "DEBIAN/control").read_text().replace(
                    "Depends: kmod, linux-base", "Depends: notkmod, linux-base"
                )
            ),
        )
        with self.assertRaisesRegex(ValueError, "missing required dependency: kmod"):
            verify_arm64_packages(self.packages_dir, expected_release=self.release)

    def test_rejects_wrong_headers_build_symlink_target(self):
        self.create_valid_packages()
        headers = next(self.packages_dir.glob("linux-headers-*_*.deb"))

        def change_link(stage):
            link = stage / f"lib/modules/{self.release}/build"
            link.unlink()
            link.symlink_to("/usr/src/wrong-headers")

        self.repack(headers, "repack-build-link", change_link)
        with self.assertRaisesRegex(ValueError, "must be a symlink to"):
            verify_arm64_packages(self.packages_dir, expected_release=self.release)

    def test_rejects_non_executable_header_tools(self):
        self.create_valid_packages()
        headers = next(self.packages_dir.glob("linux-headers-*_*.deb"))

        def remove_executable_bit(stage):
            (stage / f"usr/src/linux-headers-{self.release}/scripts/sign-file").chmod(0o644)

        self.repack(headers, "repack-sign-file", remove_executable_bit)
        with self.assertRaisesRegex(ValueError, "scripts/sign-file.*not executable"):
            verify_arm64_packages(self.packages_dir, expected_release=self.release)

    def test_rejects_x86_host_tool_in_arm64_headers(self):
        self.create_valid_packages()
        headers = next(self.packages_dir.glob("linux-headers-*_*.deb"))

        def replace_with_host_binary(stage):
            tool = stage / f"usr/src/linux-headers-{self.release}/scripts/sign-file"
            tool.write_bytes(make_dummy_elf(62))
            tool.chmod(0o755)

        self.repack(headers, "repack-x86-sign-file", replace_with_host_binary)
        with self.assertRaisesRegex(ValueError, "scripts/sign-file.*not AArch64"):
            verify_arm64_packages(self.packages_dir, expected_release=self.release)

    def test_rejects_x86_elf_at_any_executable_header_path(self):
        self.create_valid_packages()
        headers = next(self.packages_dir.glob("linux-headers-*_*.deb"))

        def add_host_tool(stage):
            tool = stage / f"usr/src/linux-headers-{self.release}/tools/bpf/resolve_btfids/resolve_btfids"
            tool.parent.mkdir(parents=True, exist_ok=True)
            tool.write_bytes(make_dummy_elf(62))
            tool.chmod(0o755)

        self.repack(headers, "repack-x86-resolve-btfids", add_host_tool)
        with self.assertRaisesRegex(ValueError, "resolve_btfids.*not AArch64"):
            verify_arm64_packages(self.packages_dir, expected_release=self.release)


if __name__ == "__main__":
    unittest.main()
