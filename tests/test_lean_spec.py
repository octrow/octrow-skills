"""lean-spec: preflight facts, and the worked example's gate when Lean is installed.
Run: python3 -m unittest discover tests"""
import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "plugins/lean-spec/skills/lean-spec"
# Own module name: repo-ready's test imports its own `preflight`, and sys.modules would mix them up.
_spec = importlib.util.spec_from_file_location("lean_spec_preflight", SKILL / "scripts/preflight.py")
preflight = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(preflight)

ELAN_LAKE = Path.home() / ".elan/bin/lake"


class PreflightTest(unittest.TestCase):
    def test_detects_python_project_and_missing_lean_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "pyproject.toml").write_text("[project]\nname='x'\n")
            found, _ = preflight.facts(Path(tmp))
        self.assertEqual(found["project_language"], "python")
        self.assertEqual(found["lean_project"], "none yet")

    def test_finds_existing_lean_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "lean").mkdir()
            (Path(tmp) / "lean/lakefile.toml").write_text('name = "spec"\n')
            found, _ = preflight.facts(Path(tmp))
        self.assertEqual(found["lean_project"], preflight.EXISTING_LEAN)

    def test_every_missing_fact_has_an_install_command(self):
        _, missing = preflight.facts(Path.cwd())
        for name in missing:
            self.assertIn(name, preflight.INSTALL)


class LogicMapTest(unittest.TestCase):
    """docs/logic-map.md names real skill files: a rename that forgets the map fails here."""

    def test_every_module_line_points_to_an_existing_file(self):
        for name in ("logic-map.md", "logic-map.ru.md"):
            text = (SKILL.parent.parent / "docs" / name).read_text(encoding="utf-8")
            lines = [line for line in text.splitlines() if line.startswith("Module:")]
            refs = [ref for line in lines for ref in re.findall(r"`([^`]+)`", line)]
            missing = [ref for ref in refs if not (SKILL / ref).is_dir() and not list(SKILL.glob(f"{ref}.*"))]
            self.assertTrue(refs, name)
            self.assertEqual(missing, [], name)


@unittest.skipUnless(
    (shutil.which("lake") or ELAN_LAKE.exists()) and shutil.which("bwrap"), "Lean or bubblewrap is not installed"
)
class ExampleGateTest(unittest.TestCase):
    def test_example_gate_passes(self):
        env = {**os.environ, "PATH": f"{ELAN_LAKE.parent}:{os.environ['PATH']}"}
        result = subprocess.run(
            ["bash", str(SKILL / "example/lean/gate.sh")],
            capture_output=True, text=True, timeout=900, env=env,
        )
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        self.assertIn("gate: ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
