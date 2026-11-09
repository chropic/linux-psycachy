#!/usr/bin/env python3
"""Boot an ARM64 kernel on QEMU's generic virt machine.

This exercises only generic kernel boot and userspace execution; it does not
emulate SP12 hardware or validate an installer or an SP12 device tree.
The optional UEFI mode uses only disposable firmware variables and virtual FAT.
"""
import argparse
import hashlib
import pathlib
import shutil
import stat
import subprocess
import tempfile


ASSEMBLY = r"""
.global _start
.text
_start:
    mov x0, #1
    adr x1, msg
    mov x2, #20
    mov x8, #64
    svc #0
shutdown:
    movz x0, #0xdead
    movk x0, #0xfee1, lsl #16
    movz x1, #0x1969
    movk x1, #0x2812, lsl #16
    movz x2, #0xfedc
    movk x2, #0x4321, lsl #16
    mov x3, #0
    mov x8, #142
    svc #0
1:  b 1b
msg: .ascii "PSYCACHY_VM_INIT_OK\n"
"""
MARKER = "PSYCACHY_VM_INIT_OK"
MODULE_SETUP = r"""
    mov x0, #-100
    adr x1, module_name
    mov x2, #0
    mov x3, #0
    mov x8, #56
    svc #0
    tbnz x0, #63, module_failed
    adr x1, empty_string
    mov x2, #0
    mov x8, #273
    svc #0
    tbnz x0, #63, module_failed
"""
MODULE_TAIL = r"""
module_failed:
    mov x0, #1
    adr x1, module_error
    mov x2, #20
    mov x8, #64
    svc #0
    b shutdown
module_name: .asciz "/probe.ko"
empty_string: .asciz ""
module_error: .ascii "PSYCACHY_MODULE_ERR\n"
"""


def cpio_entry(name, mode, data=b"", major=0, minor=0):
    name = name.encode("ascii") + b"\0"
    fields = [0, mode, 0, 0, 1, 0, len(data), 0, 0, major, minor, len(name), 0]
    result = b"070701" + b"".join(f"{value:08x}".encode("ascii") for value in fields) + name
    result += b"\0" * (-len(result) % 4)
    result += data
    return result + b"\0" * (-len(result) % 4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kernel", type=pathlib.Path, help="built ARM64 Image")
    parser.add_argument("--qemu", default="qemu-system-aarch64")
    parser.add_argument("--clang", default="clang-22")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--uefi", action="store_true", help="boot through a disposable ARM64 UEFI/GRUB image")
    parser.add_argument("--firmware-code", type=pathlib.Path)
    parser.add_argument("--firmware-vars", type=pathlib.Path)
    parser.add_argument("--grub-directory", type=pathlib.Path, help="ARM64 EFI GRUB modules")
    parser.add_argument("--grub-mkstandalone", default="grub-mkstandalone")
    parser.add_argument("--module", type=pathlib.Path,
                        help="signed test module that prints PSYCACHY_MODULE_LOADED when loaded")
    args = parser.parse_args()
    if not args.kernel.is_file() or args.timeout <= 0:
        parser.error("kernel must exist and timeout must be positive")
    if args.uefi and (not args.firmware_code or not args.firmware_code.is_file() or
                      not args.firmware_vars or not args.firmware_vars.is_file() or
                      not args.grub_directory or not args.grub_directory.is_dir()):
        parser.error("UEFI mode needs --firmware-code, --firmware-vars and --grub-directory")
    if not args.uefi and (args.firmware_code or args.firmware_vars or args.grub_directory):
        parser.error("firmware and GRUB options require --uefi")
    if args.uefi and "," in str(args.firmware_code.resolve()):
        parser.error("UEFI firmware path must not contain a comma")
    if args.module and not args.module.is_file():
        parser.error("test module must be an existing file")

    digest = hashlib.sha256()
    with args.kernel.open("rb") as image:
        for chunk in iter(lambda: image.read(1024 * 1024), b""):
            digest.update(chunk)
    print(f"Kernel SHA-256: {digest.hexdigest()}", flush=True)

    with tempfile.TemporaryDirectory(prefix="psycachy-arm64-vm-") as tmp:
        root = pathlib.Path(tmp)
        if args.uefi and "," in str(root):
            parser.error("temporary directory path must not contain a comma in UEFI mode")
        assembly = ASSEMBLY
        if args.module:
            assembly = assembly.replace("_start:\n", "_start:\n" + MODULE_SETUP) + MODULE_TAIL
            print(f"Module SHA-256: {hashlib.sha256(args.module.read_bytes()).hexdigest()}", flush=True)
        (root / "init.S").write_text(assembly)
        subprocess.run([args.clang, "--target=aarch64-linux-gnu", "-fuse-ld=lld-22",
                        "-nostdlib", "-static", "-Wl,-e,_start", "-o", str(root / "init"),
                        str(root / "init.S")], check=True)
        archive = (cpio_entry("dev", stat.S_IFDIR | 0o755) +
                   cpio_entry("dev/console", stat.S_IFCHR | 0o600, major=5, minor=1) +
                   cpio_entry("init", stat.S_IFREG | 0o755, (root / "init").read_bytes()))
        if args.module:
            archive += cpio_entry("probe.ko", stat.S_IFREG | 0o644, args.module.read_bytes())
        archive += cpio_entry("TRAILER!!!", 0)
        (root / "initramfs.cpio").write_bytes(archive)
        kernel_args = "console=ttyAMA0 rdinit=/init panic=-1"
        if args.module:
            kernel_args += " module.sig_enforce=1"
        command = [args.qemu, "-machine", "virt,accel=tcg", "-cpu", "max", "-m", "1024",
                   "-nodefaults", "-display", "none", "-serial", "stdio", "-monitor", "none", "-no-reboot"]
        if args.uefi:
            disk = root / "disk"
            (disk / "EFI/BOOT").mkdir(parents=True)
            (disk / "PSY_TEST_MEDIA").write_text("disposable QEMU test only\n")
            shutil.copyfile(args.kernel, disk / "Image")
            shutil.copyfile(root / "initramfs.cpio", disk / "initramfs.cpio")
            config = root / "grub.cfg"
            config.write_text("insmod part_msdos\ninsmod part_gpt\ninsmod fat\n"
                              "insmod search_fs_file\ninsmod linux\n"
                              "search --no-floppy --file --set=root /PSY_TEST_MEDIA\n"
                              f"linux /Image {kernel_args}\n"
                              "initrd /initramfs.cpio\nboot\n")
            loader = disk / "EFI/BOOT/BOOTAA64.EFI"
            subprocess.run([args.grub_mkstandalone, f"--directory={args.grub_directory.resolve()}",
                            "--format=arm64-efi", "--modules=part_msdos part_gpt fat search search_fs_file linux",
                            f"--output={loader}", f"boot/grub/grub.cfg={config}"], check=True)
            print(f"GRUB loader SHA-256: {hashlib.sha256(loader.read_bytes()).hexdigest()}", flush=True)
            variables = root / "uefi-vars.fd"
            shutil.copyfile(args.firmware_vars, variables)
            command += ["-drive", f"if=pflash,format=raw,readonly=on,file={args.firmware_code.resolve()}",
                        "-drive", f"if=pflash,format=raw,file={variables}",
                        "-drive", f"if=none,format=raw,readonly=on,file=fat:ro:{disk},id=boot",
                        "-device", "virtio-blk-pci,drive=boot"]
        else:
            command += ["-kernel", str(args.kernel.resolve()), "-initrd", str(root / "initramfs.cpio"),
                        "-append", kernel_args]
        try:
            run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, errors="replace", timeout=args.timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            print((exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or "")
            raise SystemExit("ARM64 VM smoke test timed out") from exc
        print(run.stdout, end="")
        if (run.returncode or MARKER not in run.stdout or
                (args.module and "PSYCACHY_MODULE_LOADED" not in run.stdout)):
            raise SystemExit(f"ARM64 VM smoke test failed (QEMU exit {run.returncode})")
        print(f"PASS: generic ARM64 {'UEFI' if args.uefi else 'direct-kernel'} VM reached the test init and powered off")


if __name__ == "__main__":
    main()
