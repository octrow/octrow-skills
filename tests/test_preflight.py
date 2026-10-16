"""Registry rules and an end-to-end preflight run on a throwaway repo. Run: python3 -m unittest discover tests"""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins/repo-ready/skills/repo-publish/scripts"
sys.path.insert(0, str(SCRIPTS))

import catalog.core  # noqa: F401  registers the Checks the tests refer to
import preflight
import registry

GOOD = {"severity": "warning", "when": (), "scenarios": {"publish"}, "kind": "files", "why": "w",
        "procedure": "references/security.md"}


class RegistryRules(unittest.TestCase):
    def test_unknown_fact_fails_at_declaration(self):
        with self.assertRaisesRegex(ValueError, "unknown fact"):
            registry.check("t_fact", **{**GOOD, "when": ("pyhton",)})(list)

    def test_check_without_scenario_fails(self):
        with self.assertRaisesRegex(ValueError, "scenario"):
            registry.check("t_scen", **{**GOOD, "scenarios": set()})(list)

    def test_missing_procedure_file_fails(self):
        with self.assertRaisesRegex(ValueError, "procedure"):
            registry.check("t_proc", **{**GOOD, "procedure": "references/nope.md"})(list)

    def test_duplicate_id_fails(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            registry.check("secret_files_tracked", **GOOD)(list)

    def test_negated_fact_skips_with_reason(self):
        c = registry.Check("t", "info", frozenset({"!public"}), frozenset({"publish"}), "files", "w", "p")
        self.assertEqual(registry.unmet(c, {"public"}), "!public")
        self.assertEqual(registry.unmet(c, set()), "")

    def test_exemptions_need_a_reason_and_a_known_id(self):
        self.assertEqual(registry.parse_exemptions("exempt:\n  readme_demo: CLI with no visual output\n"),
                         {"readme_demo": "CLI with no visual output"})
        with self.assertRaisesRegex(ValueError, "reason"):
            registry.parse_exemptions("exempt:\n  readme_demo:\n")
        with self.assertRaisesRegex(ValueError, "unknown check"):
            registry.parse_exemptions("exempt:\n  readme_dmeo: typo\n")

    def test_exemption_reason_cannot_be_just_a_comment(self):
        with self.assertRaisesRegex(ValueError, "reason"):
            registry.parse_exemptions("exempt:\n  readme_demo: # todo\n")

    def test_duplicate_exemption_fails(self):
        with self.assertRaisesRegex(ValueError, "twice"):
            registry.parse_exemptions("exempt:\n  readme_demo: a\n  readme_demo: b\n")

    def test_unexpected_exception_is_broken_not_a_crash(self):
        def boom() -> list[str]:
            raise KeyError("nameWithOwner")
        c = registry.Check("t", "warning", frozenset(), frozenset({"publish"}), "files", "w", "p", boom)
        outcome = registry._run(c)
        self.assertEqual(outcome.state, "broken")
        self.assertIn("KeyError", outcome.lines[0])

    def test_missing_binary_reads_as_no_output(self):
        self.assertEqual(registry.run("no-such-binary-xyz"), "")


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class PreflightRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        repo = Path(cls.tmp.name)
        git(repo, "init", "-q", "-b", "main")
        (repo / "README.md").write_text("# demo\n\nSee [docs](docs/missing.md).\n")
        (repo / ".env").write_text("TOKEN=x\n")
        (repo / ".repo-ready.yml").write_text("exempt:\n  readme_demo: CLI with no visual output\n")
        git(repo, "add", "-f", ".")
        git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "init")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            preflight.main([str(repo), "--scenario", "publish"])
        cls.report = out.getvalue()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_header_names_the_mode(self):
        self.assertIn("repo: local", self.report.splitlines()[0])

    def test_error_level_failure_is_listed_first(self):
        self.assertLess(self.report.index("## Error"), self.report.index("## Warning"))
        self.assertIn("secret_files_tracked", self.report.split("## Warning")[0])

    def test_failure_carries_its_procedure(self):
        block = self.report.split("readme_links")[1].split("\n- ")[0]
        self.assertIn("docs/missing.md", block)
        self.assertIn("fix:", block)

    def test_github_checks_are_skipped_with_the_missing_fact(self):
        self.assertRegex(self.report, r"repo_topics: needs github")

    def test_exemption_is_reported_with_its_reason(self):
        self.assertIn("readme_demo: CLI with no visual output", self.report)

    def test_judgement_questions_are_listed(self):
        self.assertIn("provenance", self.report.split("## Judgement")[1])


if __name__ == "__main__":
    unittest.main()
