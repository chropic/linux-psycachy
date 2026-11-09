import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("deb_dependencies", ROOT / "tools/deb_dependencies.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DebianDependencyTests(unittest.TestCase):
    def test_matches_exact_package_tokens(self):
        field = "notkmod, linux-basex (>= 1), linux-headers-7.3 (= 7.3.1-1)"
        self.assertEqual(
            ["kmod", "linux-base"],
            MODULE.missing_dependencies(field, ["kmod", "linux-base"], "amd64"),
        )

    def test_parses_arch_qualified_versioned_alternatives_and_continuations(self):
        field = "libc6:arm64 (>= 2.43) | libc6:any,\n kmod [arm64], linux-base"
        self.assertEqual(
            {
                ("libc6", "arm64", None), ("libc6", "any", None),
                ("kmod", None, ("arm64",)), ("linux-base", None, None),
            },
            MODULE.dependency_tokens(field),
        )

    def test_architecture_qualified_dependencies_must_match_native_target(self):
        self.assertEqual([], MODULE.missing_dependencies("kmod:amd64, linux-base:native", ["kmod", "linux-base"], "amd64"))
        self.assertEqual(["kmod"], MODULE.missing_dependencies("kmod:arm64, linux-base", ["kmod", "linux-base"], "amd64"))
        self.assertEqual(["kmod"], MODULE.missing_dependencies("kmod:any, linux-base", ["kmod", "linux-base"], "amd64"))

    def test_architecture_restrictions_are_evaluated_for_each_target(self):
        required = ["kmod", "linux-base"]
        self.assertEqual(
            ["kmod"],
            MODULE.missing_dependencies("kmod [arm64], linux-base", required, "amd64"),
        )
        self.assertEqual(
            [],
            MODULE.missing_dependencies("kmod [amd64], linux-base [linux-any]", required, "amd64"),
        )
        self.assertEqual(
            [],
            MODULE.missing_dependencies("kmod [!arm64], linux-base", required, "amd64"),
        )
        self.assertEqual(
            ["kmod"],
            MODULE.missing_dependencies("kmod [!amd64], linux-base", required, "amd64"),
        )

    def test_cli_reports_missing_names(self):
        import subprocess

        result = subprocess.run(
            ["python3", str(ROOT / "tools/deb_dependencies.py"), "amd64", "notkmod", "kmod"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("kmod", result.stderr)


if __name__ == "__main__":
    unittest.main()
