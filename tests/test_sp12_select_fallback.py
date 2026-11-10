import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
HELPER = ROOT / "targets/sp121-arm64/system/usr-local-sbin/sp12-select-fallback"
HOOK = ROOT / "targets/sp121-arm64/system/etc/kernel/prerm.d/zzzz-sp12-fallback"
ACTIVE = "7.3.1-psycachy-sp121"
FALLBACK = "7.3.0-9-generic"
OLDER = "7.2.0-sp12-old"
DTB_REL = f"/usr/lib/firmware/{FALLBACK}/device-tree/qcom/x1p42100-microsoft-sp12in.dtb"
IMAGE_DTB_REL = f"/usr/lib/linux-image-{FALLBACK}/qcom/x1p42100-microsoft-sp12in.dtb"


class SelectFallbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / "root"
        self.bin = pathlib.Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        (self.root / "etc/sp12-linux").mkdir(parents=True)
        (self.root / "boot").mkdir()
        (self.root / f"boot/vmlinuz-{OLDER}").write_bytes(b"older fallback kernel")
        (self.root / f"boot/initrd.img-{OLDER}").write_bytes(b"older fallback initrd")
        (self.root / f"usr/lib/linux-image-{OLDER}/qcom").mkdir(parents=True)
        (self.root / f"usr/lib/linux-image-{OLDER}/qcom/x1p42100-microsoft-sp12in.dtb").write_bytes(b"older sp12 dtb")
        (self.root / DTB_REL.lstrip("/")).parent.mkdir(parents=True)
        (self.root / IMAGE_DTB_REL.lstrip("/")).parent.mkdir(parents=True)
        (self.root / "etc/sp12-linux/boot.conf").write_text(
            f"KVER={ACTIVE}\nDTB=/boot/dtb-{ACTIVE}\n"
        )
        (self.root / f"boot/vmlinuz-{FALLBACK}").write_bytes(b"fallback kernel")
        (self.root / f"boot/initrd.img-{FALLBACK}").write_bytes(b"fallback initrd")
        (self.root / DTB_REL.lstrip("/")).write_bytes(b"sp12 fallback dtb")
        (self.root / IMAGE_DTB_REL.lstrip("/")).write_bytes(b"image package fallback dtb")
        self.paths_file = pathlib.Path(self.tmp.name) / "paths"
        self.paths_file.write_text(
            f"{OLDER} /boot/vmlinuz-{OLDER}\n"
            f"{FALLBACK} /boot/vmlinuz-{FALLBACK}\n"
        )
        self.sync_record = pathlib.Path(self.tmp.name) / "sync-record"
        linux_version = self.bin / "linux-version"
        linux_version.write_text(
            "#!/bin/sh\n[ \"$1\" = list ] && [ \"$2\" = --paths ] || exit 2\n"
            f"cat {self.paths_file}\n"
        )
        linux_version.chmod(0o755)
        dpkg_query = self.bin / "dpkg-query"
        dpkg_query.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = -S ]; then\n"
            "  case \"$2\" in\n"
            f"    /boot/vmlinuz-{FALLBACK}) [ \"${{SP12_TEST_IMAGE_OWNER:-1}}\" = 1 ] || exit 1; printf 'linux-image-{FALLBACK}: %s\\n' \"$2\" ;;\n"
            f"    /boot/vmlinuz-{OLDER}) [ \"${{SP12_TEST_OLDER_OWNER:-1}}\" = 1 ] || exit 1; printf 'linux-image-{OLDER}: %s\\n' \"$2\" ;;\n"
            f"    {DTB_REL}) [ \"${{SP12_TEST_DTB_OWNER:-1}}\" = 1 ] || exit 1; printf 'linux-modules-{FALLBACK}: %s\\n' \"$2\" ;;\n"
            f"    {IMAGE_DTB_REL}) [ \"${{SP12_TEST_IMAGE_DTB_OWNER:-1}}\" = 1 ] || exit 1; printf 'linux-image-{FALLBACK}: %s\\n' \"$2\" ;;\n"
            f"    /usr/lib/linux-image-{OLDER}/qcom/x1p42100-microsoft-sp12in.dtb) [ \"${{SP12_TEST_OLDER_OWNER:-1}}\" = 1 ] || exit 1; printf 'linux-image-{OLDER}: %s\\n' \"$2\" ;;\n"
            "    *) exit 1 ;;\n"
            "  esac\n"
            "elif [ \"$1\" = -W ]; then\n"
            "  printf 'ii '\n"
            "else exit 2; fi\n"
        )
        dpkg_query.chmod(0o755)
        sync_helper = self.bin / "sp12-sync-boot"
        sync_helper.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$(cat \"$SP12_TEST_ROOT/etc/sp12-linux/boot.conf\")\" > \"$SP12_TEST_SYNC_RECORD\"\n"
            "exit \"${SP12_TEST_SYNC_RC:-0}\"\n"
        )
        sync_helper.chmod(0o755)
        self.env = dict(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            SP12_TEST_ROOT=str(self.root),
            SP12_TEST_SYNC_HELPER=str(sync_helper),
            SP12_TEST_SYNC_RECORD=str(self.sync_record),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def run_helper(self, env=None):
        return subprocess.run(
            ["sh", str(HELPER), ACTIVE],
            env=dict(self.env, **(env or {})),
            capture_output=True,
            text=True,
        )

    def test_selects_owned_sp12_fallback_and_syncs_before_returning(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = f"KVER={FALLBACK}\nDTB=/boot/dtb-{FALLBACK}\n"
        self.assertEqual((self.root / "etc/sp12-linux/boot.conf").read_text(), expected)
        self.assertEqual(self.sync_record.read_text(), expected)
        self.assertEqual((self.root / f"boot/dtb-{FALLBACK}").read_bytes(), b"sp12 fallback dtb")
        self.assertIn(f"selected package-owned kernel {FALLBACK}", result.stdout)

    def test_restores_active_config_when_payload_sync_fails(self):
        result = self.run_helper({"SP12_TEST_SYNC_RC": "1"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            (self.root / "etc/sp12-linux/boot.conf").read_text(),
            f"KVER={ACTIVE}\nDTB=/boot/dtb-{ACTIVE}\n",
        )

    def test_rejects_unowned_fallback(self):
        result = self.run_helper({"SP12_TEST_IMAGE_OWNER": "0", "SP12_TEST_OLDER_OWNER": "0"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no package-owned SP12 fallback", result.stderr)
        self.assertEqual(
            (self.root / "etc/sp12-linux/boot.conf").read_text(),
            f"KVER={ACTIVE}\nDTB=/boot/dtb-{ACTIVE}\n",
        )

    def test_selects_owned_dtbs_installed_under_linux_image_package_path(self):
        result = self.run_helper({"SP12_TEST_DTB_OWNER": "0"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.root / f"boot/dtb-{FALLBACK}").read_bytes(),
            b"image package fallback dtb",
        )

    def test_selects_newest_valid_fallback_from_linux_version_order(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.root / f"boot/dtb-{FALLBACK}").read_bytes(),
            b"sp12 fallback dtb",
        )
        self.assertFalse((self.root / f"boot/dtb-{OLDER}").exists())
        self.assertEqual(
            (self.root / "etc/sp12-linux/boot.conf").read_text(),
            f"KVER={FALLBACK}\nDTB=/boot/dtb-{FALLBACK}\n",
        )

    def test_pre_remove_hook_ignores_upgrades(self):
        env = dict(self.env, DEB_MAINT_PARAMS="upgrade 7.3.2")
        result = subprocess.run(
            ["sh", str(HOOK), ACTIVE, f"/boot/vmlinuz-{ACTIVE}"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.sync_record.exists())


if __name__ == "__main__":
    unittest.main()
