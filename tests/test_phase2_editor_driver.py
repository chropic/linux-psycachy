import importlib.util
import pathlib
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
DRIVER_PATH = ROOT / "tools/phase2-editor-driver.py"
SPEC = importlib.util.spec_from_file_location("phase2_editor_driver", DRIVER_PATH)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)


class EditorDriverFieldSelectionTests(unittest.TestCase):
    def test_excludes_document_by_text_not_proxy_identity(self):
        fixture = "fixed fixture contents"
        document_proxy = object()
        find_entry = object()
        replace_entry = object()
        controls = [
            (document_proxy, "text", ""),
            (find_entry, "entry", ""),
            (replace_entry, "entry", ""),
        ]
        accessible_text = {
            document_proxy: fixture,
            find_entry: "",
            replace_entry: "",
        }
        with patch.object(DRIVER, "node_text", side_effect=accessible_text.get):
            fields = DRIVER.find_replace_fields(controls, fixture)

        self.assertEqual(fields, [find_entry, replace_entry])


if __name__ == "__main__":
    unittest.main()
