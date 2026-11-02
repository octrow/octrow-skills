"""lean-spec: preflight facts, and the worked example's gate when Lean is installed.
Run: python3 -m unittest discover tests"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import unittest.mock
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

    def agent_facts_with(self, files: dict[str, object], repo: Path) -> dict[str, str]:
        """preflight.agent_facts with CLAUDE_CONFIG_DIR pointing at a config holding `files` (path -> JSON)."""
        with tempfile.TemporaryDirectory() as config:
            for name, data in files.items():
                (Path(config) / name).parent.mkdir(parents=True, exist_ok=True)
                (Path(config) / name).write_text(json.dumps(data))
            with unittest.mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": config}):
                return preflight.agent_facts(repo)

    def test_lean4_skills_read_from_claude_config_dir(self):
        registry = {"plugins/installed_plugins.json": {"plugins": {"lean4@x": []}}}
        self.assertEqual(self.agent_facts_with(registry, Path.cwd())["lean4-skills"], "installed")

    def test_lean_lsp_counts_only_when_set_up_for_this_project(self):
        server = {"mcpServers": {"lean-lsp": {}}}
        with tempfile.TemporaryDirectory() as tmp:  # an empty repo: no .mcp.json of its own
            repo = Path(tmp).resolve()
            elsewhere = {".claude.json": {"projects": {"/elsewhere": server}}}
            here = {".claude.json": {"projects": {str(repo): server}}}
            self.assertEqual(self.agent_facts_with(elsewhere, repo)["lean-lsp-mcp"], "missing")
            self.assertEqual(self.agent_facts_with(here, repo)["lean-lsp-mcp"], "configured")

    def test_macos_is_refused_with_a_reason(self):
        with unittest.mock.patch.object(preflight.sys, "platform", "darwin"), \
                unittest.mock.patch.object(preflight.sys, "argv", ["preflight.py", str(Path.cwd())]), \
                unittest.mock.patch("builtins.print") as printed:
            self.assertEqual(preflight.main(), 1)
        self.assertIn("macOS is not supported", " ".join(str(c.args[0]) for c in printed.call_args_list))

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
