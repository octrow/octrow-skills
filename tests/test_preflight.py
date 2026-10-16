"""Registry rules and an end-to-end preflight run on a throwaway repo. Run: python3 -m unittest discover tests"""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins/repo-ready/engine"
sys.path.insert(0, str(SCRIPTS))

import catalog.core  # noqa: F401  registers the Checks the tests refer to
import preflight
import registry

GOOD = {"severity": "warning", "when": (), "scenarios": {"publish"}, "kind": "files", "why": "w",
        "procedure": "security.md#1-secrets-in-history-not-just-head"}


class RegistryRules(unittest.TestCase):
    def test_unknown_fact_fails_at_declaration(self):
        with self.assertRaisesRegex(ValueError, "unknown fact"):
            registry.check("t_fact", **{**GOOD, "when": ("pyhton",)})(list)

    def test_check_without_scenario_fails(self):
        with self.assertRaisesRegex(ValueError, "scenario"):
            registry.check("t_scen", **{**GOOD, "scenarios": set()})(list)

    def test_missing_procedure_file_fails(self):
        with self.assertRaisesRegex(ValueError, "procedure"):
            registry.check("t_proc", **{**GOOD, "procedure": "nope.md#x"})(list)

    def test_missing_procedure_anchor_fails(self):
        with self.assertRaisesRegex(ValueError, "anchor"):
            registry.check("t_anchor", **{**GOOD, "procedure": "security.md#no-such-section"})(list)

    def test_procedure_is_shown_as_a_path_from_the_skill(self):
        self.assertEqual(registry.procedure_path("security.md#x"), "engine/procedures/security.md#x")
        self.assertEqual(registry.procedure_path("assets/dependabot.yml"), "engine/assets/dependabot.yml")
        self.assertEqual(registry.procedure_path("skill:humanizer"), "skill:humanizer")

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


def preflight_report(repo: Path, scenario: str, files: dict[str, str]) -> str:
    """Commit `files` into a fresh repo at `repo` and return the preflight report for `scenario`."""
    git(repo, "init", "-q", "-b", "main")
    for name, text in files.items():
        (repo / name).write_text(text)
    git(repo, "add", "-f", ".")
    git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "init")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        preflight.main([str(repo), "--scenario", scenario])
    return out.getvalue()


class ReportCase(unittest.TestCase):
    """A preflight report built once per class in a throwaway repo (`cls.tmp`), with section helpers."""

    report = ""

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def failed(self) -> str:
        return self.report.split("## Judgement")[0]

    def passed(self) -> str:
        return self.report.split("## Passed")[1]


class PreflightRun(ReportCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.report = preflight_report(Path(cls.tmp.name), "publish", {
            "README.md": "# demo\n\nSee [docs](docs/missing.md).\n",
            ".env": "TOKEN=x\n",
            ".repo-ready.yml": "exempt:\n  readme_demo: CLI with no visual output\n",
        })

    def test_header_names_the_mode(self):
        self.assertIn("repo: local", self.report.splitlines()[0])

    def test_error_level_failure_is_listed_first(self):
        self.assertLess(self.report.index("## Error"), self.report.index("## Warning"))
        self.assertIn("secret_files_tracked", self.report.split("## Warning")[0])

    def test_failure_carries_its_procedure(self):
        block = self.report.split("readme_links")[1].split("\n- ")[0]
        self.assertIn("docs/missing.md", block)
        self.assertIn("fix: skill:github-repo", block)

    def test_github_checks_are_skipped_with_the_missing_fact(self):
        self.assertRegex(self.report, r"repo_topics: needs github")

    def test_exemption_is_reported_with_its_reason(self):
        self.assertIn("readme_demo: CLI with no visual output", self.report)

    def test_judgement_questions_are_listed(self):
        judged = self.report.split("## Judgement")[1].split("\n## ")[0]
        for cid in ("provenance", "third_party_code", "first_run", "readme_claims_real", "readme_plain_language"):
            self.assertIn(f"- {cid} [", judged)


class DeployRun(ReportCase):
    """A container project with the classic gaps: named user, unpinned base, infra ports open to the network."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.report = preflight_report(Path(cls.tmp.name), "deploy", {
            "Dockerfile": "FROM python:3.12-slim AS builder\nRUN true\n"
                          "FROM python:3.12-slim\nCOPY --from=builder /x /x\nUSER app\n",
            "docker-compose.yml": "services:\n  db:\n    image: postgres\n    ports:\n      - \"5432:5432\"\n",
            "README.md": "# svc\n",
        })

    def test_container_gaps_are_found(self):
        for cid in ("dockerfile_numeric_user", "dockerfile_base_digest", "dockerignore", "compose_infra_ports"):
            self.assertIn(f"- {cid}", self.failed())

    def test_multistage_build_passes(self):
        self.assertIn("dockerfile_multistage", self.report.split("## Passed")[1])

    def test_shared_core_checks_run_but_publish_only_ones_do_not(self):
        self.assertIn("secret_files_tracked", self.report)
        self.assertNotIn("readme_demo", self.report)

    def test_helm_checks_skip_without_a_chart(self):
        self.assertRegex(self.report, r"helm_pod_security: needs helm_chart")


class DeployEdgeCases(ReportCase):
    """Real-world shapes the first version misread (code review, 2026-10-16)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        repo = Path(cls.tmp.name)
        (repo / ".github/workflows").mkdir(parents=True)
        (repo / "templates").mkdir()
        cls.report = preflight_report(repo, "deploy", {
            "Dockerfile.prod": "ARG BASE=python:3.12-slim@sha256:" + "a" * 64 + "\nFROM ${BASE} AS runtime\n"
                               "USER 10001:10001\nHEALTHCHECK CMD true\nFROM runtime AS browser\nUSER 0\nRUN true\n"
                               "USER 10001:10001\nFROM runtime AS slim\n",
            ".dockerignore": "**/.git\n/.env\n",
            "docker-compose.yml": "services:\n  db:\n    ports:\n      - \"${DB_PORT:-5432}:5432\"  # dev db\n",
            "Chart.yaml": "apiVersion: v2\nname: svc\nversion: 0.1.0\n",
            "templates/deployment.yaml": "runAsNonRoot: true\nreadOnlyRootFilesystem: true\ndrop: [ALL]\n"
                                         "type: RuntimeDefault\nlivenessProbe: {}\nreadinessProbe: {}\n"
                                         "automountServiceAccountToken: {{ .Values.sa.automount }}\n",
            ".github/workflows/image.yml": "permissions: {}\njobs:\n  b:\n    steps:\n"
                                          "      - uses: docker/build-push-action@v6\n        with:\n"
                                          "          push: ${{ github.event_name != 'pull_request' }}\n"
                                          "          provenance: false\n          sbom: true\n"
                                          "      - uses: actions/attest@v1\n",
        })

    def test_variant_stage_inherits_the_user_and_arg_base_is_not_judged(self):
        for cid in ("dockerfile_numeric_user", "dockerfile_base_digest", "dockerfile_healthcheck", "dockerignore"):
            self.assertIn(cid, self.passed())

    def test_variable_host_port_with_a_comment_is_still_caught(self):
        self.assertIn("- compose_infra_ports", self.failed())

    def test_chart_at_the_repo_root_is_read(self):
        for cid in ("helm_pod_security", "helm_probes", "helm_service_account_token"):
            self.assertIn(cid, self.passed())

    def test_expression_push_counts_as_publishing(self):
        block = self.failed().split("- image_supply_chain")[1].split("\n- ")[0]
        self.assertIn("provenance", block)
        self.assertNotIn("no an attestation", block)
        self.assertIn("image_workflow,", self.passed())


if __name__ == "__main__":
    unittest.main()
