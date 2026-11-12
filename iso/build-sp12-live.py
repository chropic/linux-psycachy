#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build an experimental Ubuntu 26.10 live ISO with the maintained SP12 kernel.

Private machine support is optional and must be explicitly selected. No image
with that support may be published by this project. File hashes and provenance
are pinned in config/sp121-live-support.json; machine files stay outside Git.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import struct
import sys
import tarfile
import tempfile
import uuid
import zlib

ROOT = Path(__file__).resolve().parent.parent
BASE_PIN = ROOT / 'config/arm64-iso-base.json'
KERNEL_PIN = ROOT / 'config/arm64-iso-kernel.json'
SUPPORT_PIN = ROOT / 'config/sp121-live-support.json'
LAYER = 'minimal.standard.live.sp12.squashfs'
LIVE_DTB = '/casper/x1p42100-microsoft-sp12in.dtb'
MODULES = ['overlay', 'isofs', 'usb_storage', 'uas', 'xhci_plat_hcd',
           'phy_qcom_qmp_combo', 'phy_qcom_snps_femto_v2', 'ufs_qcom',
           'phy_qcom_qmp_ufs', 'pinctrl_x1e80100', 'gcc_x1e80100',
           'qnoc_x1e80100', 'qcom_rpmh_regulator', 'msm', 'panel_edp',
           'ath12k', 'ath12k_wifi7', 'snd_soc_x1e80100', 'qcom_q6v5_pas']

VERIFY_SPEC = importlib.util.spec_from_file_location(
    'verify_arm64_packages', ROOT / 'tools/verify-arm64-packages.py')
VERIFY_MODULE = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(VERIFY_MODULE)
verify_arm64_packages = VERIFY_MODULE.verify_arm64_packages
ISO_SPEC = importlib.util.spec_from_file_location('arm64_iso', ROOT / 'iso/arm64_iso.py')
ISO_MODULE = importlib.util.module_from_spec(ISO_SPEC)
ISO_SPEC.loader.exec_module(ISO_MODULE)


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load_support_pin(path=SUPPORT_PIN):
    pin = load_json(path)
    if pin.get('schema_version') != 1 or pin.get('device') != 'sp121-arm64':
        raise ValueError('unsupported SP12 live support pin')
    commit = pin.get('support_source_commit', '')
    files = pin.get('machine_files')
    if not re.fullmatch(r'[0-9a-f]{40}', commit) or not isinstance(files, dict) or len(files) != 4:
        raise ValueError('SP12 live support pin must identify the source commit and four files')
    expected_files = {
        'usr/lib/firmware/ath12k/WCN7850/hw2.0/board.bin',
        'usr/lib/firmware/qcom/x1e80100/X1P42100-Microsoft-Surface-Pro-12in-tplg.bin',
        'usr/share/alsa/ucm2/Qualcomm/x1e80100/MICROSOFT-Surface-Pro-12in.conf',
        'usr/share/alsa/ucm2/Qualcomm/x1e80100/Surface12in-HiFi.conf',
    }
    if set(files) != expected_files:
        raise ValueError('SP12 live support pin must use the reviewed four-file allowlist')
    if pin.get('source_allowlist') != ['lib/firmware/qcom', 'usr/share/qcom']:
        raise ValueError('SP12 live support pin has an unexpected source checkout allowlist')
    if pin.get('redistribute_machine_files') is not False:
        raise ValueError('SP12 machine support files must remain local-only')
    sources = pin.get('support_sources', {})
    if sources.get('firmware_platform', {}).get('commit') != commit:
        raise ValueError('SP12 support source provenance does not match its checkout pin')
    for source in ('firmware_platform', 'audio_topology', 'wifi_board', 'alsa_ucm'):
        record = sources.get(source, {})
        if not re.fullmatch(r'[0-9a-f]{40}', record.get('commit', '')):
            raise ValueError('SP12 live support source has an invalid commit: ' + source)
    derived_outputs = {
        'audio_topology': (
            'usr/lib/firmware/qcom/x1e80100/X1P42100-Microsoft-Surface-Pro-12in-tplg.bin'),
        'wifi_board': 'usr/lib/firmware/ath12k/WCN7850/hw2.0/board.bin',
        'alsa_ucm': 'usr/share/alsa/ucm2/Qualcomm/x1e80100/Surface12in-HiFi.conf',
    }
    for source, relative in derived_outputs.items():
        if sources.get(source, {}).get('output_sha256') != files[relative]:
            raise ValueError('SP12 support source output does not match machine-file pin: ' + source)
    for relative, digest in files.items():
        if (Path(relative).is_absolute() or '..' in Path(relative).parts
                or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            raise ValueError('SP12 live support pin contains an unsafe path or invalid hash')
    return pin


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def output(*args):
    return subprocess.check_output([str(a) for a in args], text=True)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def grub_config(text, private_support=False):
    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines)
               if re.match(r'^\s*linux(?:efi)?\s+/casper/vmlinuz(?:\s|$)', line)]
    require(len(matches) == 1, 'Unexpected live kernel menu layout')
    index = matches[0]
    line = lines[index]
    require('---' in line, 'Live GRUB kernel command has no Ubuntu argument separator')
    before, after = line.split('---', 1)
    words = before.split()
    require(not any(word == 'autoinstall' or word.startswith('autoinstall=') for word in words),
            'Refusing an autoinstall live kernel command')
    words = [word for word in words if word != 'maybe-ubiquity']
    words.extend(['boot=casper', 'layerfs-path=' + LAYER, 'cma=128M', 'efi=noruntime'])
    require(words.count('boot=casper') == 1 and
            sum(word.startswith('layerfs-path=') for word in words) == 1,
            'Base live GRUB command already contains conflicting casper layer arguments')
    lines[index] = ' '.join(words) + ' ---' + after
    indentation = line[:len(line) - len(line.lstrip())]
    lines[index:index] = [indentation + 'insmod fdt\n',
                          indentation + 'devicetree ' + LIVE_DTB + '\n']
    label = ('Try SP12 Ubuntu 26.10 (private local live)' if private_support
             else 'Try SP12 Ubuntu 26.10 (experimental live)')
    result = ''.join(lines)
    require(result.count('Try or Install Ubuntu') == 1,
            'Expected exactly one Ubuntu live-session menu label')
    result = result.replace('Try or Install Ubuntu', label)
    require(not re.search(r'\bautoinstall(?:=\S+)?\b', result),
            'Autoinstall remains enabled in the SP12 live menu')
    require(result.count('devicetree ' + LIVE_DTB) == 1,
            'SP12 live menu does not select exactly one pinned DTB')
    return result


def esp_digest(image):
    with image.open('rb') as stream:
        stream.seek(512)
        header = bytearray(stream.read(512))
        require(header[:8] == b'EFI PART', 'Missing GPT header')
        size, crc = struct.unpack_from('<II', header, 12)
        require(92 <= size <= 512, 'Invalid GPT header size')
        struct.pack_into('<I', header, 16, 0)
        require(zlib.crc32(header[:size]) == crc, 'GPT header CRC mismatch')
        lba = struct.unpack_from('<Q', header, 72)[0]
        count, entry_size, crc = struct.unpack_from('<III', header, 80)
        require(count <= 4096 and 128 <= entry_size <= 1024, 'Invalid GPT table geometry')
        stream.seek(lba * 512)
        entries = stream.read(count * entry_size)
        require(zlib.crc32(entries) == crc, 'GPT table CRC mismatch')
        hashes = []
        for n in range(count):
            entry = entries[n * entry_size:(n + 1) * entry_size]
            if uuid.UUID(bytes_le=entry[:16]) != uuid.UUID('c12a7328-f81f-11d2-ba4b-00a0c93ec93b'):
                continue
            first, last = struct.unpack_from('<QQ', entry, 32)
            require(first <= last and (last + 1) * 512 <= image.stat().st_size, 'ESP outside image')
            stream.seek(first * 512)
            hashes.append(hashlib.sha256(stream.read((last - first + 1) * 512)).hexdigest())
        require(len(hashes) == 1, 'Expected exactly one ESP')
        return hashes[0]


def validate_esp_mount(mount):
    fields = mount.strip().split()
    require(len(fields) == 4 and fields[1] == '/boot/efi',
            'Physical ESP is not mounted exactly at /boot/efi')
    require(fields[2] in {'vfat', 'fat', 'fat32'},
            'Physical ESP mount is not FAT formatted')
    require('ro' in fields[3].split(','),
            'Physical ESP must be mounted read-only during the build')
    return mount


def snapshot():
    mount = validate_esp_mount(output(
        'findmnt', '-n', '-o', 'SOURCE,TARGET,FSTYPE,OPTIONS',
        '--mountpoint', '/boot/efi'))
    files = sorted(p for p in Path('/boot/efi').rglob('*') if p.is_file())
    require(files, 'Physical ESP is unavailable for comparison')
    return {'esp': {str(p): sha(p) for p in files},
            'nvram': output('efibootmgr', '-v'),
            'mount': mount}


def cleanup_mounts(mounts, before):
    errors = []
    for destination in reversed(mounts):
        # Chroot initramfs hooks can create nested mounts below /sys.
        # Every destination is a mount we created inside the private scratch tree.
        result = subprocess.run(['umount', '--recursive', str(destination)])
        if result.returncode:
            errors.append(str(destination))
    # Always compare physical state, even when an unmount failed.
    require(snapshot() == before, 'Physical-device comparison failed')
    require(not errors, 'Unmount failed: ' + ', '.join(errors))


def publish_outputs(partial, final, buildinfo_source, owner):
    """Publish a validated ISO and sidecars only after cleanup has succeeded."""
    checksum = Path(str(final) + '.sha256')
    sidecar = Path(str(final) + '.buildinfo.json')
    require(partial.is_file() and not partial.is_symlink(),
            'Validated partial ISO is missing or unsafe')
    require(not any(path.exists() or path.is_symlink() for path in (final, checksum, sidecar)),
            'Refusing to overwrite a live-image output')
    digest = sha(partial)
    uid, gid = owner
    os.chmod(partial, 0o644)
    os.chown(partial, uid, gid)
    temporaries = []
    published = []
    try:
        for suffix, writer in (
                ('.sha256.tmp', lambda path: path.write_text(
                    f'{digest}  {final.name}\n', encoding='ascii')),
                ('.buildinfo.json.tmp', lambda path: shutil.copyfile(buildinfo_source, path))):
            fd, name = tempfile.mkstemp(prefix='.' + final.name + '.', suffix=suffix,
                                        dir=final.parent)
            os.close(fd)
            temporary = Path(name)
            temporaries.append(temporary)
            writer(temporary)
            os.chmod(temporary, 0o644)
            os.chown(temporary, uid, gid)
        os.link(partial, final)
        published.append(final)
        os.link(temporaries[0], checksum)
        published.append(checksum)
        os.link(temporaries[1], sidecar)
        published.append(sidecar)
        partial.unlink()
    except Exception:
        for path in reversed(published):
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in temporaries:
            path.unlink(missing_ok=True)
    return digest


def parse_build_metadata(path):
    metadata = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line or '=' not in line:
            continue
        key, value = line.split('=', 1)
        # build-metadata.txt also records compiler diagnostics; only its
        # machine-readable key=value rows participate in pin checks.
        if not re.fullmatch(r'[a-z][a-z0-9_]*', key):
            continue
        if key in metadata:
            raise ValueError('Kernel build metadata has a repeated key')
        metadata[key] = value
    return metadata


def validate_build_metadata(metadata, pin):
    expected = {
        'source_sha256': pin['source_archive_sha256'],
        'source_tree_sha256': pin['source_tree_sha256'],
        'config_sha256': pin['resolved_config_sha256'],
        'policy_fragment_sha256': pin['policy_fragment_sha256'],
        'kconfig_resolved_config_sha256': pin['resolved_config_sha256'],
    }
    for field, value in expected.items():
        require(metadata.get(field) == value,
                'Kernel build metadata differs from pin: ' + field)
    require(metadata.get('cpu_target', '').startswith('arm64;'),
            'Kernel build metadata is not for the SP12 ARM64 target')
    return metadata


def validate_kernel_inputs(package_dir, package_verification, build_metadata,
                           module_signing_certificate, kernel_pin_path=KERNEL_PIN):
    pin = ISO_MODULE.validate_pin_pair(load_json(kernel_pin_path))
    package_dir = Path(package_dir)
    expected_packages = {item['filename']: item for item in pin['packages']}
    actual_packages = {path.name for path in package_dir.glob('*.deb')}
    require(actual_packages == set(expected_packages),
            'Kernel package directory must contain exactly the pinned image and headers pair')
    for filename, item in expected_packages.items():
        require(sha(package_dir / filename) == item['sha256'],
                'Kernel package hash differs from pin: ' + filename)
    certificate = Path(module_signing_certificate)
    require(certificate.is_file() and not certificate.is_symlink(),
            'Module signing certificate must be a regular file')
    require(sha(certificate) == pin['module_signing_certificate_sha256'],
            'Module signing certificate differs from the kernel pin')
    report = verify_arm64_packages(package_dir)
    recorded_report = load_json(package_verification)
    require(recorded_report == report,
            'Package verification manifest does not match the supplied package pair')
    metadata = validate_build_metadata(parse_build_metadata(build_metadata), pin)
    return pin, report, metadata


def verify_kernel_tree(package_root, pin, package_report):
    release = pin['kernel_release']
    kernel_image = Path(package_root) / 'boot' / ('vmlinuz-' + release)
    require(kernel_image.is_file() and not kernel_image.is_symlink(),
            'Pinned kernel package is missing its regular kernel image')
    require(sha(kernel_image) == pin['kernel_payload_sha256'],
            'Kernel image payload differs from the pinned kernel payload hash')
    dtb_relative = Path('usr/lib/linux-image-' + release) / pin['dtb_path']
    dtb = Path(package_root) / dtb_relative
    if not dtb.is_file():
        dtb = Path(package_root) / 'boot' / ('dtbs-' + release) / pin['dtb_path']
        dtb_relative = Path('boot') / ('dtbs-' + release) / pin['dtb_path']
    require(dtb.is_file() and not dtb.is_symlink() and sha(dtb) == pin['dtb_sha256'],
            'SP12 DTB is missing or differs from the pinned DTB hash')
    modules = Path(package_root) / 'lib/modules' / release
    if not modules.is_dir():
        modules = Path(package_root) / 'usr/lib/modules' / release
    require(modules.is_dir(), 'Pinned kernel package is missing its matching module tree')
    require(package_report['dtb']['sha256'] == pin['dtb_sha256'],
            'Package verification manifest DTB differs from pin')
    return kernel_image, dtb, modules


def validate_private_support(support_source, machine_root, support_pin=None):
    support_pin = support_pin or load_support_pin()
    support = Path(support_source).resolve(strict=True)
    root = Path(machine_root).resolve(strict=True)
    require(output('git', '-C', support, 'rev-parse', 'HEAD').strip() ==
            support_pin['support_source_commit'],
            'Unexpected SP12 private support checkout revision')
    checked = {}
    for relative, expected in support_pin['machine_files'].items():
        candidate = root / relative
        resolved = candidate.resolve(strict=True)
        require(resolved.is_relative_to(root), 'Private support file escapes machine root: ' + relative)
        require(candidate.is_file() and not candidate.is_symlink(),
                'Private support file is not a regular file: ' + relative)
        require(sha(candidate) == expected, 'Private support file differs from pin: ' + relative)
        checked[relative] = expected
    return support_pin, checked


def resolve_support_inputs(enabled, support_source, machine_root):
    if not enabled:
        return None, {}
    return validate_private_support(support_source, machine_root)


def preflight_tools(xorriso, private_support):
    required = {
        'gpgv', 'dpkg-deb', 'mount', 'umount', 'md5sum', 'depmod',
        'chroot', 'unmkinitramfs', 'lsinitramfs', 'modinfo', 'modprobe',
        'mksquashfs', 'unsquashfs', 'sgdisk', 'grub-file', 'efibootmgr',
        'findmnt',
    }
    if private_support:
        required.add('git')
    missing = sorted(tool for tool in required if shutil.which(tool) is None)
    if shutil.which(str(xorriso)) is None:
        missing.append(str(xorriso))
    require(not missing, 'Missing required build tools: ' + ', '.join(sorted(set(missing))))


def build(args):
    preflight_tools(args.xorriso, args.private_machine_support)
    original = args.iso.resolve(strict=True)
    requested_final = args.output.absolute()
    require(not requested_final.exists() and not requested_final.is_symlink(),
            'Refusing to overwrite output')
    final = requested_final.parent.resolve(strict=True) / requested_final.name
    require(final.suffix.lower() == '.iso', 'Output path must end in .iso')
    require(final.parent.is_dir(), 'Output directory must exist')
    base_pin = ISO_MODULE.verify_base_iso(
        original, args.checksums, args.signature, args.keyring, BASE_PIN)
    package_dir = args.kernel_packages.resolve(strict=True)
    package_verification = args.package_verification.resolve(strict=True)
    build_metadata_path = args.build_metadata.resolve(strict=True)
    module_signing_certificate = args.module_signing_certificate.resolve(strict=True)
    kernel_pin, package_report, metadata = validate_kernel_inputs(
        package_dir, package_verification, build_metadata_path,
        module_signing_certificate)
    support_pin, checked_support = resolve_support_inputs(
        args.private_machine_support, args.support_source, args.machine_root)

    release = kernel_pin['kernel_release']
    if not args.apply:
        print('DRY RUN: signed Ubuntu 26.10 ARM64 base:', base_pin['sha256'])
        print('Pinned SP12 kernel release:', release)
        print('Pinned kernel package pair verified:', package_report['image_package']['sha256'])
        print('Private machine support:', args.private_machine_support)
        print('Base ISO:', original)
        print('Output:', final)
        print('No mounts or output files created. Add --apply to build.')
        return

    require(os.geteuid() == 0 and os.uname().machine == 'aarch64',
            'Native ARM64 root required')
    require(Path('/proc/self/ns/mnt').readlink() != Path('/proc/1/ns/mnt').readlink(),
            'Private mount namespace required')
    require(Path('/proc/self/ns/net').readlink() != Path('/proc/1/ns/net').readlink(),
            'Private network namespace required')
    partial = final.with_suffix('.iso.partial')
    sidecar = Path(str(final) + '.buildinfo.json')
    for path in [partial, Path(str(final) + '.sha256'), sidecar]:
        require(not path.exists() and not path.is_symlink(), 'Refusing to overwrite ' + str(path))
    require(shutil.disk_usage(final.parent).free > 24 * 1024**3,
            'Need at least 24 GiB scratch space')

    before = snapshot()
    work = Path(tempfile.mkdtemp(prefix='sp12-live-build.', dir=final.parent))
    mounts = []
    validated = False

    def mount(destination, *mount_args):
        destination.mkdir(parents=True, exist_ok=True)
        run('mount', *mount_args, destination)
        mounts.append(destination)

    try:
        print('Scratch directory:', work, flush=True)
        xorriso = args.xorriso
        tree = work / 'original'
        with (work / 'extract.log').open('w') as log:
            run(xorriso, '-osirrox', 'on', '-indev', original, '-extract', '/', tree,
                stdout=log, stderr=subprocess.STDOUT)
        run('md5sum', '--quiet', '-c', 'md5sum.txt', cwd=tree)
        fdt_module = tree / 'boot/grub/arm64-efi/fdt.mod'
        require(fdt_module.is_file() and not fdt_module.is_symlink(),
                'Base ISO GRUB FDT module is missing')
        require(not (tree / 'casper' / LAYER).exists(),
                'Base ISO already contains the SP12 live layer')

        image_item = next(item for item in kernel_pin['packages']
                          if item['name'].startswith('linux-image-'))
        image_package = package_dir / image_item['filename']
        kernel = work / 'kernel-package'
        run('dpkg-deb', '-x', image_package, kernel)
        kernel_image, package_dtb, package_modules = verify_kernel_tree(
            kernel, kernel_pin, package_report)

        stage = work / 'stage'
        (stage / 'usr/lib/modules').mkdir(parents=True)
        (stage / 'lib').symlink_to('usr/lib')
        stage_boot = stage / 'boot'
        stage_boot.mkdir()
        shutil.copy2(kernel_image, stage_boot / kernel_image.name)
        module_destination = stage / 'usr/lib/modules' / release
        shutil.copytree(package_modules, module_destination, symlinks=True)
        dtb_destination = (stage / 'usr/lib' / ('linux-image-' + release)
                           / kernel_pin['dtb_path'])
        dtb_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_dtb, dtb_destination)
        require(sha(stage_boot / kernel_image.name) == kernel_pin['kernel_payload_sha256'],
                'Staged kernel image differs from pin')
        require(sha(dtb_destination) == kernel_pin['dtb_sha256'],
                'Staged SP12 DTB differs from pin')

        if args.private_machine_support:
            # The source archive and four machine files are a narrow, local-only allowlist.
            support = args.support_source.resolve(strict=True)
            archive = work / 'private-platform.tar'
            for relative in support_pin['source_allowlist']:
                run('git', '-C', support, 'cat-file', '-e',
                    support_pin['support_source_commit'] + ':' + relative)
            archive_paths = support_pin['source_allowlist']
            run('git', '-C', support, 'archive', '--format=tar',
                '--output=' + str(archive), support_pin['support_source_commit'], *archive_paths)
            extracted = work / 'private-platform'
            with tarfile.open(archive) as bundle:
                bundle.extractall(extracted, filter='data')
            for relative in support_pin['source_allowlist']:
                source = extracted / relative
                destination = stage / relative
                if relative.startswith('lib/'):
                    destination = stage / 'usr' / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, destination, dirs_exist_ok=True, symlinks=True)
            for relative, expected in checked_support.items():
                source = Path(args.machine_root).resolve(strict=True) / relative
                destination = stage / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                destination.chmod(0o644)
                require(sha(destination) == expected,
                        'Copied private support file differs from pin: ' + relative)
        run('depmod', '-b', stage, release)

        layers = []
        for name in ['minimal', 'minimal.standard', 'minimal.standard.live']:
            layer = work / name
            mount(layer, '-t', 'squashfs', '-o', 'loop,ro,nodev,nosuid',
                  tree / ('casper/' + name + '.squashfs'))
            layers.append(layer)
        root = work / 'root'
        upper, overlay_work = work / 'upper', work / 'overlay-work'
        upper.mkdir()
        overlay_work.mkdir()
        lower = ':'.join(str(path) for path in [stage] + list(reversed(layers)))
        mount(root, '-t', 'overlay', '-o',
              f'lowerdir={lower},upperdir={upper},workdir={overlay_work}', 'overlay')
        require('VERSION_ID="26.10"' in (root / 'etc/os-release').read_text(),
                'Wrong live root version')

        # The chroot receives no physical block devices; sysfs is read-only.
        mount(root / 'dev', '-t', 'tmpfs', '-o', 'nosuid,mode=755', 'tmpfs')
        for name in ['null', 'zero', 'random', 'urandom']:
            (root / 'dev' / name).touch()
            run('mount', '--bind', '/dev/' + name, root / 'dev' / name)
            mounts.append(root / 'dev' / name)
        mount(root / 'proc', '-t', 'proc', '-o', 'nosuid,nodev,noexec', 'proc')
        mount(root / 'sys', '--bind', '/sys')
        run('mount', '-o', 'remount,bind,ro,nosuid,nodev,noexec', root / 'sys')
        generated = work / 'generated'
        generated.mkdir()
        mount(root / 'tmp/sp12-live-build', '--bind', generated)

        (root / 'etc/initramfs-tools/conf.d/sp12-live').write_text(
            'MODULES=most\nCOMPRESS=zstd\nBOOT=casper\n')
        with (root / 'etc/initramfs-tools/modules').open('a') as stream:
            stream.write('\n# SP12 live boot and hardware dependencies\n' + '\n'.join(MODULES) + '\n')
        old_initrd = work / 'original-initrd'
        run('unmkinitramfs', tree / 'casper/initrd', old_initrd)
        old_uuid_files = list(old_initrd.rglob('conf/uuid.conf'))
        require(len(old_uuid_files) == 1, 'Expected one casper media UUID')
        media_uuid = old_uuid_files[0].read_text().strip()
        require(re.fullmatch(r'[0-9a-f-]{36}', media_uuid) is not None,
                'Unexpected original casper UUID')
        hook = root / 'etc/initramfs-tools/hooks/zzzz-sp12-live'
        hook.write_text('#!/bin/sh\nset -eu\n'
                        'if [ "${1:-}" = prereqs ]; then exit 0; fi\n'
                        'mkdir -p "$DESTDIR/conf/conf.d"\n'
                        f"printf '%s\\n' '{media_uuid}' > \"$DESTDIR/conf/uuid.conf\"\n"
                        f"printf '%s\\n' 'LAYERFS_PATH={LAYER}' > \"$DESTDIR/conf/conf.d/default-layer.conf\"\n"
                        "printf '%s\\n' 'BOOT=casper' > \"$DESTDIR/conf/conf.d/default-boot-to-casper.conf\"\n")
        hook.chmod(0o755)
        print('Generating casper initramfs with the pinned SP12 modules...', flush=True)
        with (work / 'mkinitramfs.log').open('w') as log:
            run('chroot', root, '/usr/sbin/mkinitramfs', '-o',
                '/tmp/sp12-live-build/initrd', release, stdout=log,
                stderr=subprocess.STDOUT,
                env={**os.environ, 'LC_ALL': 'C', 'SYSTEMD_OFFLINE': '1'})

        listing = output('lsinitramfs', generated / 'initrd')
        initrd_names = {name.removeprefix('./').removeprefix('usr/').rstrip('/')
                        for name in listing.splitlines()}
        initrd_releases = {name.split('/')[2] for name in initrd_names
                           if name.startswith('lib/modules/') and len(name.split('/')) > 2}
        require(initrd_releases == {release},
                'Wrong initramfs module release set: ' + str(initrd_releases))
        require('scripts/casper' in initrd_names and
                'scripts/casper-bottom/25adduser' in initrd_names,
                'Missing casper live-session scripts')
        for module in MODULES:
            vermagic = output('modinfo', '-b', stage, '-k', release,
                              '-F', 'vermagic', module).split()[0]
            require(vermagic == release, 'Wrong module vermagic: ' + module)
            dependencies = output('modprobe', '-d', stage, '-S', release,
                                  '--show-depends', module)
            for line in dependencies.splitlines():
                if line.startswith('insmod '):
                    path = Path(line.split()[1])
                    relative = (str(path.relative_to(stage)) if path.is_relative_to(stage)
                                else str(path).lstrip('/'))
                    require(relative.removeprefix('usr/') in initrd_names,
                            'Missing initramfs dependency: ' + relative)

        initrd_tree = work / 'new-initrd'
        run('unmkinitramfs', generated / 'initrd', initrd_tree)
        uuid_files = list(initrd_tree.rglob('conf/uuid.conf'))
        require(len(uuid_files) == 1 and uuid_files[0].read_text().strip() == media_uuid,
                'Casper UUID mismatch')
        layer_configs = list(initrd_tree.rglob('conf/conf.d/default-layer.conf'))
        require(len(layer_configs) == 1 and LAYER in layer_configs[0].read_text(),
                'Wrong initramfs default layer')

        overlay = generated / LAYER
        run('mksquashfs', stage, overlay, '-noappend', '-comp', 'zstd',
            '-processors', '4', '-no-progress')
        overlay_manifest = {
            str(path.relative_to(stage)): sha(path)
            for path in sorted(stage.rglob('*')) if path.is_file() and not path.is_symlink()
        }
        (generated / 'sp12-live-overlay-manifest.json').write_text(
            json.dumps(overlay_manifest, indent=2) + '\n')
        grub_text = grub_config((tree / 'boot/grub/grub.cfg').read_text(),
                                args.private_machine_support)
        (generated / 'grub.cfg').write_text(grub_text)
        info = {
            'schema_version': 1,
            'status': ('private-local-testing-only-do-not-publish' if args.private_machine_support
                       else 'experimental-live-no-private-machine-support'),
            'distribution': ('private-local-testing-only-do-not-publish'
                             if args.private_machine_support else 'experimental-test-only'),
            'base_iso_sha256': base_pin['sha256'],
            'base_pin_sha256': sha(BASE_PIN),
            'kernel_pin_sha256': sha(KERNEL_PIN),
            'kernel_release': release,
            'kernel_payload_sha256': kernel_pin['kernel_payload_sha256'],
            'image_package_sha256': package_report['image_package']['sha256'],
            'headers_package_sha256': package_report['headers_package']['sha256'],
            'package_verification_sha256': sha(package_verification),
            'build_metadata_sha256': sha(build_metadata_path),
            'source_archive_sha256': metadata['source_sha256'],
            'source_tree_sha256': metadata['source_tree_sha256'],
            'resolved_config_sha256': metadata['config_sha256'],
            'policy_fragment_sha256': metadata['policy_fragment_sha256'],
            'module_signing_certificate_sha256': kernel_pin['module_signing_certificate_sha256'],
            'dtb_path': kernel_pin['dtb_path'],
            'dtb_sha256': kernel_pin['dtb_sha256'],
            'module_names': MODULES,
            'initrd_sha256': sha(generated / 'initrd'),
            'live_layer': LAYER,
            'live_layer_sha256': sha(overlay),
            'live_layer_manifest_sha256': sha(generated / 'sp12-live-overlay-manifest.json'),
            'grub_fdt_module_sha256': sha(fdt_module),
            'live_grub_sha256': sha(generated / 'grub.cfg'),
            'private_machine_support': bool(args.private_machine_support),
            'private_support_source_commit': (support_pin['support_source_commit']
                                              if support_pin else None),
            'private_support_sources': (support_pin['support_sources'] if support_pin else None),
            'private_support_file_hashes': checked_support,
            'script_sha256': sha(__file__),
        }
        (generated / 'sp12-live-buildinfo.json').write_text(
            json.dumps(info, indent=2) + '\n')

        replacements = {
            'casper/vmlinuz': stage_boot / kernel_image.name,
            'casper/initrd': generated / 'initrd',
            'casper/x1p42100-microsoft-sp12in.dtb': dtb_destination,
            'casper/' + LAYER: overlay,
            'boot/grub/grub.cfg': generated / 'grub.cfg',
            'sp12-live-buildinfo.json': generated / 'sp12-live-buildinfo.json',
            'sp12-live-overlay-manifest.json': generated / 'sp12-live-overlay-manifest.json',
            'sp12-live-build-script.py': Path(__file__),
        }
        md5_rows = []
        for line in (tree / 'md5sum.txt').read_text().splitlines():
            match = re.fullmatch(r'([0-9a-fA-F]{32})  (.+)', line)
            require(match is not None, 'Base md5sum.txt contains a malformed row')
            relative = match.group(2).removeprefix('*').removeprefix('./')
            if relative not in replacements:
                md5_rows.append(line)
        for name, path in replacements.items():
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'md5').hexdigest()
            md5_rows.append(f'{digest}  ./{name}')
        (generated / 'md5sum.txt').write_text('\n'.join(md5_rows) + '\n')
        replacements['md5sum.txt'] = generated / 'md5sum.txt'

        xorriso_args = [xorriso, '-indev', original, '-outdev', partial,
                        '-boot_image', 'any', 'replay']
        for name, path in replacements.items():
            xorriso_args.extend(['-update', path, '/' + name])
        xorriso_args.extend(['-padding', '0', '-commit'])
        with (work / 'xorriso.log').open('w') as log:
            run(*xorriso_args, stdout=log, stderr=subprocess.STDOUT)
        layout = subprocess.check_output(
            [str(xorriso), '-indev', str(partial), '-report_system_area', 'plain'],
            stderr=subprocess.STDOUT, text=True)
        sectors = re.search(r'^ISO image size/512\s*:\s*(\d+)', layout, re.M)
        require(sectors is not None, 'Cannot determine hybrid ISO size')
        os.truncate(partial, int(sectors[1]) * 512)
        run('sgdisk', '-v', partial)
        require(esp_digest(partial) == esp_digest(original), 'ISO EFI partition changed')

        audit = work / 'audit'
        with (work / 'audit-extract.log').open('w') as log:
            run(xorriso, '-osirrox', 'on', '-indev', partial, '-extract', '/', audit,
                stdout=log, stderr=subprocess.STDOUT)
        run('md5sum', '--quiet', '-c', 'md5sum.txt', cwd=audit)
        audit_grub = (audit / 'boot/grub/grub.cfg').read_text()
        require(audit_grub == grub_text and 'autoinstall' not in audit_grub
                and audit_grub.count('insmod fdt') == 1
                and audit_grub.count('devicetree ' + LIVE_DTB) == 1,
                'Audited live GRUB config enables autoinstall or differs from the generated config')
        audit_fdt_module = audit / 'boot/grub/arm64-efi/fdt.mod'
        require(audit_fdt_module.is_file() and not audit_fdt_module.is_symlink()
                and sha(audit_fdt_module) == sha(fdt_module),
                'GRUB FDT module is missing or changed in the final ISO')
        for image in audit.rglob('*'):
            if image.is_file() and image.suffix.lower() == '.efi':
                run('grub-file', '--is-arm64-efi', image)
        for name, path in replacements.items():
            require(sha(audit / name) == sha(path), 'ISO replacement mismatch: ' + name)
        for name in ['minimal.squashfs', 'minimal.standard.squashfs',
                     'minimal.standard.live.squashfs', 'install-sources.yaml']:
            require(sha(audit / 'casper' / name) == sha(tree / 'casper' / name),
                    'Base install layer changed: ' + name)
        for relative, expected in checked_support.items():
            data = subprocess.check_output(
                ['unsquashfs', '-cat', str(audit / 'casper' / LAYER), relative])
            require(hashlib.sha256(data).hexdigest() == expected,
                    'Private support payload differs in live layer: ' + relative)
        require(snapshot() == before, 'Physical ESP/NVRAM/mount state changed')

        sha(partial)
        validated = True
    finally:
        cleanup_mounts(mounts, before)
        print('Build evidence retained:', work, 'validated=' + str(validated), flush=True)

    digest = publish_outputs(
        partial, final, generated / 'sp12-live-buildinfo.json',
        (original.stat().st_uid, original.stat().st_gid))
    print('PASS: pinned base, package manifest, kernel/modules/DTB, initramfs and live layer',
          flush=True)
    print('PASS: non-autoinstall live GRUB entry and unchanged base install layers', flush=True)
    print('PASS: physical ESP, NVRAM and ESP mount state unchanged', flush=True)
    print('EXPERIMENTAL TEST IMAGE:', final, flush=True)
    print('SHA256:', digest, flush=True)
    print('Live Wi-Fi/audio and suspend remain unverified until physical boot.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True,
                        help='Canonical-signed Ubuntu 26.10 ARM64 Desktop base ISO')
    parser.add_argument('--checksums', type=Path, required=True, help='Canonical SHA256SUMS file')
    parser.add_argument('--signature', type=Path, required=True, help='Signature for SHA256SUMS')
    parser.add_argument('--keyring', type=Path, default=Path('/usr/share/keyrings/ubuntu-cdimage-keyring.gpg'))
    parser.add_argument('--kernel-packages', type=Path, required=True,
                        help='Directory containing exactly the pinned image and headers .debs')
    parser.add_argument('--package-verification', type=Path, required=True,
                        help='package-verification.json emitted by the pinned build')
    parser.add_argument('--build-metadata', type=Path, required=True,
                        help='build-metadata.txt emitted by the pinned build')
    parser.add_argument('--module-signing-certificate', type=Path, required=True,
                        help='Public module-signing X.509 certificate emitted by the pinned build')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--xorriso', default='xorriso')
    parser.add_argument('--private-machine-support', action='store_true')
    parser.add_argument('--support-source', type=Path, default=Path('/opt/surface-pro-12-linux'))
    parser.add_argument('--machine-root', type=Path, default=Path('/'),
                        help='Root containing the four verified local support files')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        build(args)
    except (OSError, ValueError, RuntimeError, KeyError,
            subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
