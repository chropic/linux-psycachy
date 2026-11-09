import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hash_source_tree", ROOT / "tools/hash-source-tree.py")
HASHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HASHER)


class SourceTreeHashTests(unittest.TestCase):
    def test_hash_tracks_contents_permissions_paths_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            file = root / "source.c"
            file.write_text("original\n")
            initial = HASHER.tree_hash(root)
            self.assertEqual(initial, HASHER.tree_hash(root))
            file.write_text("changed\n")
            self.assertNotEqual(initial, HASHER.tree_hash(root))
            file.write_text("original\n")
            file.chmod(0o755)
            self.assertNotEqual(initial, HASHER.tree_hash(root))
            file.chmod(0o644)
            self.assertEqual(initial, HASHER.tree_hash(root))
            (root / "link").symlink_to("source.c")
            with_link = HASHER.tree_hash(root)
            self.assertNotEqual(initial, with_link)
            (root / "link").unlink()
            (root / "link").symlink_to("elsewhere")
            self.assertNotEqual(with_link, HASHER.tree_hash(root))
            file.rename(root / "renamed.c")
            self.assertNotEqual(with_link, HASHER.tree_hash(root))


if __name__ == "__main__":
    unittest.main()
