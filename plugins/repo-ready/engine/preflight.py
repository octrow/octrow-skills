#!/usr/bin/env python3
"""Read-only readiness report for a project in a git repo. Changes nothing.

usage: preflight.py [project-path] [--private word1,word2] [--scenario publish]

project-path may be the repo root or a subfolder of a monorepo (then history checks cover that folder only).
--private: extra words that must not be published (employer, client, internal project names).
--scenario: publish or deploy, to run only that Scenario's Checks; without it every Check runs (audit mode).
Checks live in catalog/*.py, their Procedures in procedures/*.md and assets/.
A repo excuses a Check in .repo-ready.yml (`exempt:` then `  check_id: reason`).
Needs git; uses gitleaks (full secret scan) and `gh` (GitHub metadata) when available; asks PyPI/npm whether the
package name is taken (network, read-only).
"""
import importlib
import re
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True  # importing the catalog must not leave __pycache__ in an audited repo that holds it
import registry  # noqa: E402  (after dont_write_bytecode on purpose)
from registry import (COMPOSE, DOCKERFILE, EXEMPTIONS_FILE, FACTS, Outcome, evaluate, parse_exemptions,  # noqa: E402
                      procedure_path, read, repo, run, tracked)

PACKS = ["catalog.core", "catalog.docker", "catalog.compose", "catalog.helm", "catalog.observability"]
METRICS = re.compile(r"opentelemetry|prometheus[-_](client|fastapi)|prom-client", re.I)
STATES = ("fail", "broken")
TITLES = {"error": "Error (blocks outward-facing steps)", "warning": "Warning (fix or exempt before done)",
          "info": "Info (advice)"}


def pyproject_scripts() -> bool:
    """Whether pyproject.toml declares commands; a malformed file reads as no, and its Checks report it broken."""
    py = repo.root / "pyproject.toml"
    try:
        meta = tomllib.loads(py.read_text(encoding="utf-8")) if py.exists() else {}
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        return False
    return bool(meta.get("project", {}).get("scripts"))


def detect_facts() -> set[str]:
    names = tracked()
    found = {
        "python": (repo.root / "pyproject.toml").exists(),
        "python_app": pyproject_scripts(),
        "node": (repo.root / "package.json").exists(),
        "has_readme": (repo.root / "README.md").exists(),
        "bilingual": any(f.endswith(".ru.md") and "/." not in f and not f.startswith(".") for f in names),
        "skills": any(f.endswith("SKILL.md") for f in names),
        "github_actions": any((repo.root / ".github/workflows").glob("*.y*ml")),
        "github": repo.vis not in ("local", "unknown"),
        "public": repo.vis == "public",
        "local": repo.vis == "local",
        "subfolder": bool(repo.rel),
        "dockerfile": any(DOCKERFILE.search(f) for f in names),
        "compose": any(COMPOSE.search(f) for f in names),
        "helm_chart": any(f.endswith("Chart.yaml") for f in names),
        "metrics": bool(METRICS.search(read("pyproject.toml") + read("package.json") + read("requirements.txt"))),
    }
    assert found.keys() <= FACTS.keys()
    return {f for f, ok in found.items() if ok}


def visibility() -> str:
    if not run("git", "remote", "get-url", "origin").strip():
        return "local"
    return run("gh", "repo", "view", "--json", "visibility", "--jq", ".visibility").strip().lower() or "unknown"


def exemptions() -> dict[str, str]:
    path = repo.root / EXEMPTIONS_FILE
    try:
        return parse_exemptions(path.read_text(encoding="utf-8")) if path.exists() else {}
    except ValueError as e:
        sys.exit(str(e))


def finding(o: Outcome) -> str:
    c = o.check
    head = f"- {c.id}{' (broken: could not run)' if o.state == 'broken' else ''}: {c.why}"
    return "\n".join([head, *(f"  - {x}" for x in o.lines), f"  fix: {procedure_path(c.procedure)}"])


def report(outcomes: list[Outcome]) -> None:
    print_findings(outcomes)
    print_judgements([o for o in outcomes if o.state == "judgement"])
    print_rest(outcomes)


def print_findings(outcomes: list[Outcome]) -> None:
    for sev, title in TITLES.items():
        found = [o for o in outcomes if o.state in STATES and o.check.severity == sev]
        print(f"\n## {title}")
        print("\n".join(map(finding, found)) or "- none")


def print_judgements(outcomes: list[Outcome]) -> None:
    print("\n## Judgement (answer by reading the repo)")
    for o in outcomes:
        print("\n".join([f"- {o.check.id} [{o.check.severity}]: {o.check.question}",
                         *(f"  - {x}" for x in o.lines), f"  fix: {procedure_path(o.check.procedure)}"]))


def print_rest(outcomes: list[Outcome]) -> None:
    exempt = [o for o in outcomes if o.state == "exempt"]
    skipped = [o for o in outcomes if o.state == "skipped"]
    passed = [o.check.id for o in outcomes if o.state == "pass"]
    if exempt:
        print("\n## Exempt")
        print("\n".join(f"- {o.check.id}: {o.lines[0]}" for o in exempt))
    if skipped:
        print("\n## Skipped (condition not met)")
        print("\n".join(f"- {o.check.id}: needs {o.lines[0]}" for o in skipped))
    print(f"\n## Passed ({len(passed)})")
    print(", ".join(passed) or "- none")


def parse_args(argv: list[str]) -> tuple[str, dict[str, str]]:
    """(project path, {--private, --scenario}); exits on an unknown scenario."""
    opts = {"--private": "", "--scenario": ""}
    for flag in opts:
        if flag in argv:
            i = argv.index(flag)
            if i + 1 == len(argv):
                sys.exit(f"{flag} needs a value")
            opts[flag] = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
    if opts["--scenario"] and opts["--scenario"] not in registry.SCENARIOS:
        sys.exit(f"unknown scenario {opts['--scenario']}; known: {', '.join(sorted(registry.SCENARIOS))}")
    return (argv[0] if argv else "."), opts


def locate(path: str, private: str) -> None:
    """Fill in `repo` for the project at `path`; exits outside git."""
    repo.root = Path(path).resolve()
    top = run("git", "rev-parse", "--show-toplevel").strip()
    if not top:
        sys.exit(f"{repo.root} is not in a git repo")
    repo.top = Path(top)
    repo.rel = "" if repo.top == repo.root else str(repo.root.relative_to(repo.top))
    repo.vis = visibility()
    repo.words = tuple(w for w in private.split(",") if w)


def main(argv: list[str]) -> None:
    path, opts = parse_args(argv)
    locate(path, opts["--private"])
    packs = [importlib.import_module(p) for p in PACKS]
    facts, exempt = detect_facts(), exemptions()
    print(f"# Preflight: {repo.root}" + (f" (subfolder of {repo.top})" if repo.rel else "") + f", repo: {repo.vis}")
    print(f"Scenario: {opts['--scenario'] or 'all (audit)'}. Facts: {', '.join(sorted(facts)) or 'none'}")
    print("\n## Context")
    print("\n".join(f"- {x}" for p in packs if hasattr(p, "context") for x in p.context()))
    report(evaluate(facts, opts["--scenario"], exempt))


if __name__ == "__main__":
    main(sys.argv[1:])
