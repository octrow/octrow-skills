"""Check registry: Repo facts, Checks and Outcomes (glossary: CONTEXT.md). Stack packs in catalog/ register on import.

A Check returns finding lines: none means pass. It raises Broken when it can't run (tool missing, offline).
A judgement Check has no verdict of its own: the agent answers its question, with the evidence lines it returns.
"""
import json
import re
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent  # each Scenario skill links it in as `engine/`
EXTERNAL_SKILLS = {"github-repo", "beautify-github-readme", "humanizer", "impeccable", "security-review"}
FACTS = {
    "python": "pyproject.toml at the project root",
    "python_app": "pyproject.toml declares [project.scripts]",
    "node": "package.json at the project root",
    "has_readme": "README.md at the project root",
    "bilingual": "at least one tracked *.ru.md",
    "skills": "at least one tracked SKILL.md",
    "github_actions": "workflows in .github/workflows",
    "github": "`gh repo view` answers for this repo",
    "public": "GitHub visibility is public",
    "local": "no `origin` remote",
    "subfolder": "the project is a subfolder of a bigger git repo",
}
SEVERITIES = ("error", "warning", "info")
SCENARIOS = {"publish"}
KINDS = {"files", "git", "registry", "gh_api", "judgement"}
EXEMPTIONS_FILE = ".repo-ready.yml"
HTTP_TIMEOUT = 8


class Broken(Exception):
    """The Check could not run; the message says why."""


@dataclass(frozen=True)
class Check:
    id: str
    severity: str
    when: frozenset[str]
    scenarios: frozenset[str]
    kind: str
    why: str
    procedure: str
    run: Callable[[], list[str]] = field(default=list, compare=False)
    question: str = ""


@dataclass(frozen=True)
class Outcome:
    check: Check
    state: str  # pass | fail | skipped | exempt | broken | judgement
    lines: tuple[str, ...] = ()


CHECKS: dict[str, Check] = {}


@dataclass
class Repo:
    """The project under audit; preflight.main fills it in before any Check runs."""
    root: Path = Path(".")
    top: Path = Path(".")
    rel: str = ""  # project path inside the repo; "" at the root
    vis: str = ""  # public / private / internal; "local" without `origin`, "unknown" without `gh`
    words: tuple[str, ...] = ()  # --private: employer, client, internal names


repo = Repo()


def _validate(c: Check) -> None:
    if c.id in CHECKS:
        raise ValueError(f"duplicate check id {c.id}")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", c.id):
        raise ValueError(f"{c.id}: ids are snake_case")
    unknown = {f.lstrip("!") for f in c.when} - FACTS.keys()
    if unknown:
        raise ValueError(f"{c.id}: unknown fact {', '.join(sorted(unknown))}")
    if not c.scenarios or c.scenarios - SCENARIOS:
        raise ValueError(f"{c.id}: needs a known scenario, got {sorted(c.scenarios)}")
    if c.severity not in SEVERITIES or c.kind not in KINDS:
        raise ValueError(f"{c.id}: bad severity {c.severity!r} or kind {c.kind!r}")
    if problem := procedure_problem(c.procedure):
        raise ValueError(f"{c.id}: procedure {c.procedure}: {problem}")


def procedure_problem(proc: str) -> str:
    """Why a Procedure pointer doesn't resolve: `skill:<name>`, `assets/<path>`, or `<file>.md#<heading-slug>`."""
    if proc.startswith("skill:"):
        return "" if proc[6:] in EXTERNAL_SKILLS else "unknown skill"
    if proc.startswith("assets/"):
        return "" if (ENGINE_DIR / proc).is_file() else "asset not found"
    name, _, anchor = proc.partition("#")
    path = ENGINE_DIR / "procedures" / name
    if not path.is_file():
        return "procedure file not found"
    return "" if anchor in heading_slugs(path) else "no such anchor (a GitHub heading slug is required)"


def heading_slugs(path: Path) -> set[str]:
    """GitHub's anchors for the headings of a Markdown file."""
    heads = re.findall(r"^#+\s+(.+?)\s*$", path.read_text(encoding="utf-8"), re.M)
    return {re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", h.lower())) for h in heads}


def procedure_path(proc: str) -> str:
    """The pointer as a path from the Scenario skill's folder, the way the agent opens it."""
    if proc.startswith("skill:"):
        return proc
    return f"engine/{proc}" if proc.startswith("assets/") else f"engine/procedures/{proc}"


def check(id: str, *, severity: str, when: tuple[str, ...] = (), scenarios: set[str], kind: str, why: str,
          procedure: str) -> Callable:
    """Register a mechanical Check: the decorated function returns finding lines, [] = pass."""
    def register(fn: Callable[[], list[str]]) -> Callable[[], list[str]]:
        c = Check(id, severity, frozenset(when), frozenset(scenarios), kind, why, procedure, fn)
        _validate(c)
        CHECKS[id] = c
        return fn
    return register


def judgement(id: str, *, severity: str, when: tuple[str, ...] = (), scenarios: set[str], question: str,
              procedure: str, why: str = "", evidence: Callable[[], list[str]] = list) -> None:
    """Register a Check the agent answers by reading the repo; `evidence` lines are shown with the question."""
    c = Check(id, severity, frozenset(when), frozenset(scenarios), "judgement", why or question, procedure,
              evidence, question)
    _validate(c)
    CHECKS[id] = c


def unmet(c: Check, facts: set[str]) -> str:
    """The first condition of `c.when` that doesn't hold, "" when the Check applies."""
    for cond in sorted(c.when):
        if (cond.startswith("!") and cond[1:] in facts) or (not cond.startswith("!") and cond not in facts):
            return cond
    return ""


def parse_exemptions(text: str) -> dict[str, str]:
    """`exempt:` then `  check_id: reason` lines; anything else is an error, so a typo never exempts silently."""
    out, lines = {}, [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines or lines[0].strip() != "exempt:":
        raise ValueError(f"{EXEMPTIONS_FILE}: must start with `exempt:`")
    for ln in lines[1:]:
        m = re.fullmatch(r"\s+([a-z][a-z0-9_]*):\s*(.*?)\s*", re.sub(r"(^|\s)#.*$", "", ln))
        if not m:
            raise ValueError(f"{EXEMPTIONS_FILE}: can't read {ln.strip()!r}; expected `  check_id: reason`")
        cid, reason = m.groups()
        if cid not in CHECKS:
            raise ValueError(f"{EXEMPTIONS_FILE}: unknown check {cid}")
        if cid in out:
            raise ValueError(f"{EXEMPTIONS_FILE}: {cid} exempted twice")
        if not reason.strip("'\""):
            raise ValueError(f"{EXEMPTIONS_FILE}: {cid} needs a reason")
        out[cid] = reason.strip("'\"")
    return out


def evaluate(facts: set[str], scenario: str, exempt: dict[str, str]) -> list[Outcome]:
    out = []
    for c in CHECKS.values():
        if scenario and scenario not in c.scenarios:
            continue
        if cond := unmet(c, facts):
            out.append(Outcome(c, "skipped", (cond,)))
        elif c.id in exempt:
            out.append(Outcome(c, "exempt", (exempt[c.id],)))
        else:
            out.append(_run(c))
    return out


def _run(c: Check) -> Outcome:
    try:
        lines = tuple(c.run())
    except Broken as e:
        return Outcome(c, "broken", (str(e),))
    except Exception as e:  # a bug or odd input in one Check must not cost the whole report
        return Outcome(c, "broken", (f"{type(e).__name__}: {e}",))
    if c.kind == "judgement":
        return Outcome(c, "judgement", lines)
    return Outcome(c, "fail" if lines else "pass", lines)


# Shared helpers for Checks


def run(*cmd: str, cwd: Path | None = None) -> str:
    """stdout of a successful command, "" on failure or when the tool isn't installed."""
    try:
        r = subprocess.run(cmd, cwd=cwd or repo.root, capture_output=True, text=True)
    except FileNotFoundError:
        return ""
    return r.stdout if r.returncode == 0 else ""


def tracked() -> list[str]:
    return run("git", "ls-files").splitlines()  # relative to repo.root


def read(path: str) -> str:
    p = repo.root / path
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def http_json(url: str) -> dict | None:
    """Parsed JSON, {} on 404, None when the registry can't be reached."""
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {} if e.code == 404 else None
    except (OSError, ValueError):  # URLError, timeouts and connection resets are all OSError
        return None
