import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests/arm64-iso-vm.sh"


class Arm64IsoVmHarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.vm = self.root / "vm"
        self.iso = self.root / "installer.iso"
        self.iso.write_bytes(b"iso fixture")
        self.code = self.root / "firmware-code.fd"
        self.vars = self.root / "firmware-vars.fd"
        self.code.write_bytes(b"UEFI code fixture")
        self.vars.write_bytes(b"UEFI variables fixture")
        self.args_file = self.root / "qemu-args"
        self._stub("qemu-img", "touch \"${@: -2:1}\"\n")
        self._stub("qemu-io", "exit 0\n")
        self._stub("qemu-system-aarch64", "printf '%s\\n' \"$@\" > \"$QEMU_ARGS\"\n")
        self.env = dict(os.environ)
        self.env.update({
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "PSYCACHY_QEMU_IMG": "qemu-img",
            "PSYCACHY_QEMU_IO": "qemu-io",
            "PSYCACHY_QEMU_AARCH64": "qemu-system-aarch64",
            "PSYCACHY_ARM64_EFI_CODE": str(self.code),
            "PSYCACHY_ARM64_EFI_VARS": str(self.vars),
            "QEMU_ARGS": str(self.args_file),
        })

    def _stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\nset -eu\n" + body)
        path.chmod(0o755)

    def run_harness(self, *args, **env):
        merged = dict(self.env)
        merged.update(env)
        return subprocess.run(
            ["bash", str(HARNESS), *map(str, args)],
            cwd=ROOT, env=merged, text=True, capture_output=True, check=False,
        )

    def test_init_and_boot_use_disposable_no_network_vm(self):
        result = self.run_harness("init", self.vm, self.iso)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.vm / "linux.qcow2").is_file())
        self.assertTrue((self.vm / "other.qcow2").is_file())
        self.assertTrue((self.vm / "vars.fd").is_file())
        self.assertTrue((self.vm / "other.sha256").is_file())

        result = self.run_harness("run", self.vm, self.iso)
        self.assertEqual(result.returncode, 0, result.stderr)
        args = self.args_file.read_text()
        self.assertIn("virt,accel=tcg,gic-version=3", args)
        self.assertIn("media=cdrom,readonly=on", args)
        self.assertIn("readonly=on", args)
        self.assertIn("virtio-gpu-pci", args)
        self.assertIn("ramfb", args)
        self.assertIn("-nic\nnone", args)
        self.assertIn(str(self.iso), args)

    def test_refuses_existing_vm_directory_and_different_iso(self):
        self.vm.mkdir()
        result = self.run_harness("init", self.vm, self.iso)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)

        self.vm.rmdir()
        self.assertEqual(self.run_harness("init", self.vm, self.iso).returncode, 0)
        other_iso = self.root / "other.iso"
        other_iso.write_bytes(b"different iso")
        result = self.run_harness("run", self.vm, other_iso)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ISO differs", result.stderr)


if __name__ == "__main__":
    unittest.main()
