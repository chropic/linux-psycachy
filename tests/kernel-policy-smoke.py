#!/usr/bin/env python3
"""Exercise lockdown, unprivileged BPF and kexec policy in generic QEMU."""
import argparse
import errno
import hashlib
import pathlib
import shutil
import stat
import subprocess
import tempfile


INIT_C = r"""
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/bpf.h>
#include <linux/reboot.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

static void stop_vm(void)
{
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_POWER_OFF, NULL);
    for (;;) pause();
}

static int read_path(const char *path, char *buf, size_t size)
{
    int fd = open(path, O_RDONLY);
    if (fd < 0) return -1;
    ssize_t n = read(fd, buf, size - 1);
    close(fd);
    if (n < 0) return -1;
    buf[n] = '\0';
    return (int)n;
}

static void fail(const char *what)
{
    printf("POLICY_CHECK_FAILED=%s errno=%d\n", what, errno);
    fflush(stdout);
    stop_vm();
}

static void check_bpf_unprivileged(void)
{
    pid_t child = fork();
    if (child < 0) fail("bpf-fork");
    if (child == 0) {
        if (setgid(65534) || setuid(65534)) {
            printf("BPF_PRIVILEGE_DROP_FAILED errno=%d\n", errno);
            _exit(1);
        }
        union bpf_attr attr;
        memset(&attr, 0, sizeof(attr));
        attr.map_type = BPF_MAP_TYPE_ARRAY;
        attr.key_size = sizeof(uint32_t);
        attr.value_size = sizeof(uint32_t);
        attr.max_entries = 1;
        errno = 0;
        long fd = syscall(SYS_bpf, BPF_MAP_CREATE, &attr, sizeof(attr));
        if (fd < 0 && errno == EPERM) {
            printf("UNPRIVILEGED_BPF_REJECTED_EPERM\n");
            fflush(stdout);
            _exit(0);
        }
        printf("UNPRIVILEGED_BPF_UNEXPECTED_RESULT fd=%ld errno=%d\n", fd, errno);
        fflush(stdout);
        _exit(1);
    }
    int status = 0;
    if (waitpid(child, &status, 0) != child || !WIFEXITED(status) || WEXITSTATUS(status))
        fail("bpf-child");
}

static void check_module(void)
{
    int fd = open("/probe.ko", O_RDONLY);
    if (fd < 0) {
        if (errno == ENOENT) return;
        fail("open-module");
    }
    off_t length = lseek(fd, 0, SEEK_END);
    if (length <= 0 || lseek(fd, 0, SEEK_SET) < 0) fail("module-size");
    char *image = malloc((size_t)length);
    if (!image) fail("module-allocation");
    ssize_t count = read(fd, image, (size_t)length);
    close(fd);
    if (count != length) fail("module-read");
    errno = 0;
    long result = syscall(SYS_init_module, image, (unsigned long)length, "");
    int module_errno = errno;
    free(image);
    if (result == 0)
        printf("MODULE_LOAD_ACCEPTED\n");
    else
        printf("MODULE_LOAD_REJECTED errno=%d\n", module_errno);
}

int main(void)
{
    mkdir("/proc", 0755);
    mkdir("/sys", 0755);
    mkdir("/sys/kernel/security", 0755);
    if (mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL) && errno != EBUSY)
        fail("mount-proc");
    if (mount("sysfs", "/sys", "sysfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL) && errno != EBUSY)
        fail("mount-sysfs");
    if (mount("securityfs", "/sys/kernel/security", "securityfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL) && errno != EBUSY)
        fail("mount-securityfs");

    char value[256];
    if (read_path("/sys/kernel/security/lockdown", value, sizeof(value)) < 0 || !strstr(value, "[integrity]"))
        fail("lockdown-integrity");
    printf("LOCKDOWN_INTEGRITY_ACTIVE=%s", value);

    if (read_path("/proc/sys/kernel/unprivileged_bpf_disabled", value, sizeof(value)) < 0 || value[0] != '2')
        fail("bpf-default");
    printf("UNPRIVILEGED_BPF_SYSCTL=%s", value);
    check_bpf_unprivileged();
    check_module();

#ifdef SYS_kexec_load
    errno = 0;
    long legacy = syscall(SYS_kexec_load, 0, 0, NULL, 0);
    if (legacy < 0 && errno == ENOSYS)
        printf("LEGACY_KEXEC_DISABLED_ENOSYS\n");
    else {
        printf("LEGACY_KEXEC_UNEXPECTED_RESULT rc=%ld errno=%d\n", legacy, errno);
        fail("legacy-kexec");
    }
#else
    fail("legacy-kexec-syscall-unavailable");
#endif

#ifdef SYS_kexec_file_load
    int kernel_fd = open("/kernel", O_RDONLY);
    if (kernel_fd < 0) fail("open-kernel-image");
    const char cmdline[] = "console=ttyAMA0 rdinit=/init panic=-1";
    errno = 0;
    long file_rc = syscall(SYS_kexec_file_load, kernel_fd, -1,
                           sizeof(cmdline), cmdline, 0);
    int file_errno = errno;
    close(kernel_fd);
    if (file_rc == 0) {
        printf("UNSIGNED_KEXEC_FILE_ACCEPTED\n");
        fail("unsigned-kexec-accepted");
    }
    if (file_errno == EKEYREJECTED || file_errno == ENOKEY || file_errno == ENODATA)
        printf("KEXEC_SIGNATURE_REJECTED errno=%d\n", file_errno);
    else if (file_errno == EPERM)
        printf("KEXEC_FILE_BLOCKED_BY_LOCKDOWN errno=%d\n", file_errno);
    else {
        printf("KEXEC_FILE_UNQUALIFIED errno=%d\n", file_errno);
        fail("kexec-file-rejection-reason");
    }
#else
    fail("kexec-file-syscall-unavailable");
#endif

    printf("KERNEL_POLICY_PROBE_OK\n");
    fflush(stdout);
    stop_vm();
    return 0;
}
"""


def cpio_entry(name: str, mode: int, data: bytes = b"", major: int = 0, minor: int = 0) -> bytes:
    encoded = name.encode("ascii") + b"\0"
    fields = [0, mode, 0, 0, 1, 0, len(data), 0, 0, major, minor, len(encoded), 0]
    result = b"070701" + b"".join(f"{value:08x}".encode("ascii") for value in fields) + encoded
    result += b"\0" * (-len(result) % 4)
    result += data
    return result + b"\0" * (-len(result) % 4)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kernel", type=pathlib.Path, help="candidate kernel boot image")
    parser.add_argument("--arch", choices=("arm64", "x86_64"), default="arm64")
    parser.add_argument("--qemu", help="QEMU binary; selected from --arch when omitted")
    parser.add_argument("--cc", help="C compiler; selected from --arch when omitted")
    parser.add_argument("--module", type=pathlib.Path, help="optional module to load from the initramfs")
    parser.add_argument("--expect-module-rejection", action="store_true",
                        help="expect --module to be rejected by enforced signature policy")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not args.kernel.is_file() or args.timeout <= 0:
        parser.error("kernel must exist and timeout must be positive")
    if args.module and not args.module.is_file():
        parser.error("module must exist")
    if args.expect_module_rejection and not args.module:
        parser.error("--expect-module-rejection requires --module")
    qemu = args.qemu or ("qemu-system-aarch64" if args.arch == "arm64" else "qemu-system-x86_64")
    cc = args.cc or ("aarch64-linux-gnu-gcc" if args.arch == "arm64" else "gcc")

    digest = hashlib.sha256(args.kernel.read_bytes()).hexdigest()
    print(f"Kernel SHA-256: {digest}", flush=True)
    with tempfile.TemporaryDirectory(prefix=f"psycachy-{args.arch}-policy-") as tmp:
        work = pathlib.Path(tmp)
        source = work / "init.c"
        init = work / "init"
        source.write_text(INIT_C)
        subprocess.run([cc, "-static", "-O2", "-Wall", "-Werror", "-o", str(init), str(source)], check=True)
        archive = (
            cpio_entry("dev", stat.S_IFDIR | 0o755)
            + cpio_entry("dev/console", stat.S_IFCHR | 0o600, major=5, minor=1)
            + cpio_entry("init", stat.S_IFREG | 0o755, init.read_bytes())
            + cpio_entry("kernel", stat.S_IFREG | 0o644, args.kernel.read_bytes())
        )
        if args.module:
            archive += cpio_entry("probe.ko", stat.S_IFREG | 0o644, args.module.read_bytes())
        archive += cpio_entry("TRAILER!!!", 0)
        initrd = work / "initramfs.cpio"
        initrd.write_bytes(archive)
        machine = "virt,accel=tcg,gic-version=3" if args.arch == "arm64" else "q35,accel=tcg"
        console = "ttyAMA0" if args.arch == "arm64" else "ttyS0"
        command = [
            qemu, "-machine", machine, "-cpu", "max",
            "-m", "1024", "-nodefaults", "-display", "none", "-serial", "stdio",
            "-monitor", "none", "-no-reboot", "-kernel", str(args.kernel.resolve()),
            "-initrd", str(initrd), "-append", f"console={console} rdinit=/init panic=-1",
        ]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, errors="replace", timeout=args.timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
            print(output, end="")
            raise SystemExit(f"{args.arch} policy probe timed out") from exc

    print(result.stdout, end="")
    required = (
        "LOCKDOWN_INTEGRITY_ACTIVE=", "UNPRIVILEGED_BPF_SYSCTL=2",
        "UNPRIVILEGED_BPF_REJECTED_EPERM", "LEGACY_KEXEC_DISABLED_ENOSYS",
        "KERNEL_POLICY_PROBE_OK",
    )
    if result.returncode or "POLICY_CHECK_FAILED=" in result.stdout or any(item not in result.stdout for item in required):
        raise SystemExit(f"{args.arch} policy probe failed (QEMU exit {result.returncode})")
    if not any(item in result.stdout for item in ("KEXEC_SIGNATURE_REJECTED", "KEXEC_FILE_BLOCKED_BY_LOCKDOWN")):
        raise SystemExit(f"{args.arch} policy probe did not confirm kexec denial")
    if args.module:
        if args.expect_module_rejection:
            signature_error = any(
                f"MODULE_LOAD_REJECTED errno={code}" in result.stdout
                for code in (errno.EKEYREJECTED, errno.ENOKEY)
            )
            if not signature_error and not any(
                phrase in result.stdout.lower()
                for phrase in ("unsigned module", "module with unavailable key", "key was rejected", "required key")
            ):
                raise SystemExit("module was not rejected specifically for signature policy")
        elif "MODULE_LOAD_ACCEPTED" not in result.stdout:
            raise SystemExit("trusted signed module did not load")
    print(f"PASS: generic {args.arch} QEMU enforced lockdown, unprivileged BPF and kexec denial")


if __name__ == "__main__":
    main()
