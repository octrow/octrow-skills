"""Python code-health pack: lint, format, complexity, dead code, and the CI that keeps them from coming back.

The tools run through `uvx`, so the audited project needs none of them installed. Nothing is written into it:
ruff runs with --no-cache, and complexipy (which always leaves a cache and a results file in its cwd) runs from a
temporary folder.
"""
import json
import re
import shutil
import subprocess
import tempfile
import tomllib
from collections import Counter
from pathlib import Path

from catalog.core import capped, ci_text, pyproject
from registry import Broken, check, read, repo, tracked

CH = {"code-health"}
TOOL_TIMEOUT = 300  # the first uvx run downloads the tool
CYCLOMATIC_MAX = 10  # radon rank C starts at 11; ruff's C901 default is 10 as well
COGNITIVE_MAX = 15  # complexipy's default
VULTURE_CONFIDENCE = "80"  # 60% hits are mostly framework entry points (routes, CLI commands, model fields)
LINTERS = re.compile(r"\bruff\b|flake8|pylint")
TEST_RUNNERS = re.compile(r"pytest|unittest|\btox\b|\bnox\b|make test|just test")
TYPE_CHECKERS = re.compile(r"mypy|pyright|\bty check|\[tool\.ty\]")


def uvx(*cmd: str, ok: tuple[int, ...] = (0,), cwd: Path | None = None) -> str:
    """stdout of `uvx <cmd>`; Broken when uvx is missing, the run times out or exits outside `ok`."""
    if not shutil.which("uvx"):
        raise Broken("uvx not installed (https://docs.astral.sh/uv/)")
    try:
        r = subprocess.run(["uvx", *cmd], check=False, cwd=cwd or repo.root, capture_output=True, text=True,
                           timeout=TOOL_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise Broken(f"{cmd[0]} took longer than {TOOL_TIMEOUT}s") from None
    if r.returncode not in ok:
        raise Broken(f"{cmd[0]} exited {r.returncode}: {r.stderr.strip()[-300:]}")
    return r.stdout


def py_files() -> list[str]:
    """Tracked Python files that exist, as `./path` so a name like `-x.py` is never read as an option.

    Only these go to the tools: CI sees the same set, and nothing comes from .venv, build output or scratch files.
    """
    return [f"./{f}" for f in tracked() if f.endswith(".py") and (repo.root / f).is_file()]


def setting(table: str, key: str, default: int, config: dict | None = None) -> int:
    """An integer threshold from a dotted table path in `config` (pyproject's [tool] by default), or the default."""
    node = pyproject().get("tool", {}) if config is None else config
    for part in table.split("."):
        node = node.get(part, {})
    value = node.get(key, default)
    return value if isinstance(value, int) else default


def rel(path: str) -> str:
    """A tool's path, absolute or relative, as a path from the project root."""
    p = Path(path)
    return str(p.relative_to(repo.root.resolve())) if p.is_absolute() else path.removeprefix("./")


def cyclomatic_limit() -> int:
    """ruff's mccabe max-complexity from ruff.toml, .ruff.toml or pyproject (ruff's own lookup order)."""
    for name in ("ruff.toml", ".ruff.toml"):
        if text := read(name):
            config = tomllib.loads(text)
            return setting("lint.mccabe", "max-complexity", setting("mccabe", "max-complexity", CYCLOMATIC_MAX,
                                                                    config), config)
    return setting("ruff.lint.mccabe", "max-complexity", setting("ruff.mccabe", "max-complexity", CYCLOMATIC_MAX))


def functions(blocks: list[dict], parent: str = "") -> list[tuple[str, dict]]:
    """(qualified name, block) of each function, method and closure; radon nests closures in their parent."""
    out = []
    for b in blocks:
        name = f"{parent or b.get('classname') or ''}.{b['name']}".lstrip(".")
        if b["type"] != "class":  # a class score is its methods' sum, and the methods are listed on their own
            out.append((name, b))
        out += functions(b.get("closures", []), name)
    return out


def worst_first(rows: list[tuple[int, str]]) -> list[str]:
    return capped([line for _, line in sorted(rows, key=lambda r: -r[0])])


# Lint and format


@check("ruff_clean", severity="warning", when=("python",), scenarios=CH, kind="files",
       why="ruff's default rules are mistakes, not style: unused imports, undefined names, shadowed builtins",
       procedure="python-quality.md#ruff-lint")
def ruff_clean() -> list[str]:
    files = py_files()
    if not files:
        return []
    found = json.loads(uvx("ruff", "check", "--no-cache", "--force-exclude", "--output-format", "json", *files,
                           ok=(0, 1)) or "[]")
    counts = Counter(f["code"] or "syntax" for f in found)
    first = {}
    for f in found:
        first.setdefault(f["code"] or "syntax", f)
    return capped([f"{code} ×{n}: {first[code]['message']} ({rel(first[code]['filename'])}:"
                   f"{first[code]['location']['row']})" for code, n in counts.most_common()])


@check("ruff_format", severity="info", when=("python",), scenarios=CH, kind="files",
       why="one formatter ends diffs that are only whitespace and review comments about style",
       procedure="python-quality.md#ruff-format")
def ruff_format() -> list[str]:
    files = py_files()
    if not files:
        return []
    # exit 2 with a syntax error in some file; ruff_clean reports that, the rest is still checked
    out = uvx("ruff", "format", "--check", "--no-cache", "--force-exclude", "--output-format", "json", *files,
              ok=(0, 1, 2))
    if not out.strip():  # a clean run prints [], a config error prints nothing
        raise Broken("ruff format printed nothing (a config error?)")
    found = json.loads(out)
    return capped(sorted({f"{rel(f['filename'])}: would be reformatted" for f in found if f["code"] == "unformatted"}))


# Complexity


@check("complexity_cyclomatic", severity="warning", when=("python",), scenarios=CH, kind="files",
       why="each branch is a path to test; past ~10 a function has more paths than anyone tests",
       procedure="python-quality.md#cyclomatic-complexity")
def complexity_cyclomatic() -> list[str]:
    files = py_files()
    if not files:
        return []
    limit = cyclomatic_limit()
    rows = []
    for path, blocks in json.loads(uvx("radon", "cc", "-j", *files)).items():
        if not isinstance(blocks, list):  # {"error": ...} for a file radon can't parse
            rows.append((0, f"{rel(path)}: radon can't parse it ({blocks.get('error', '?')})"))
            continue
        rows += [(b["complexity"], f"{rel(path)}:{b['lineno']} {name} cc={b['complexity']} (max {limit})")
                 for name, b in functions(blocks) if b["complexity"] > limit]
    return worst_first(rows)


@check("complexity_cognitive", severity="warning", when=("python",), scenarios=CH, kind="files",
       why="nesting is what makes code hard to read; cognitive complexity counts it, cyclomatic doesn't",
       procedure="python-quality.md#cognitive-complexity")
def complexity_cognitive() -> list[str]:
    files = py_files()
    if not files:
        return []
    limit = setting("complexipy", "max-complexity-allowed", COGNITIVE_MAX)
    root = repo.root.resolve()
    with tempfile.TemporaryDirectory() as tmp:  # complexipy writes its cache and results into the cwd
        result = Path(tmp) / "results.json"
        uvx("complexipy", *(str(root / f) for f in files), "--output-format", "json", "--output", str(result),
            "--cache-dir", str(Path(tmp) / "cache"), "--quiet", ok=(0, 1), cwd=Path(tmp))
        if not result.is_file():
            raise Broken("complexipy wrote no results")
        rows = json.loads(result.read_text(encoding="utf-8"))
    return worst_first([(r["complexity"], (f"{rel(r['path'])} {r['function_name']} "
                                           f"cognitive={r['complexity']} (max {limit})"))
                        for r in rows if r["complexity"] > limit])


# Dead code


@check("dead_code", severity="info", when=("python",), scenarios=CH, kind="files",
       why="code nobody calls still gets read, updated and kept compiling",
       procedure="python-quality.md#dead-code")
def dead_code() -> list[str]:
    files = py_files()
    if not files:
        return []
    # a [tool.vulture] table sets its own confidence, whitelist and excludes
    opts = () if "[tool.vulture]" in read("pyproject.toml") else ("--min-confidence", VULTURE_CONFIDENCE)
    # exit 1: a file vulture can't parse (ruff_clean reports it); the other files are still checked
    return capped([ln.removeprefix("./") for ln in uvx("vulture", *opts, *files, ok=(0, 1, 3)).splitlines()])


# CI wiring


@check("linter_in_ci", severity="warning", when=("python",), scenarios=CH, kind="files",
       why="a clean run today is lost by the next commit unless CI or pre-commit runs the linter",
       procedure="python-quality.md#ci-wiring")
def linter_in_ci() -> list[str]:
    return [] if LINTERS.search(ci_text()) else ["no ruff (or flake8/pylint) in a workflow or pre-commit"]


@check("tests_in_ci", severity="warning", when=("python",), scenarios=CH, kind="files",
       why="tests that only run on a laptop stop running",
       procedure="python-quality.md#ci-wiring")
def tests_in_ci() -> list[str]:
    return [] if TEST_RUNNERS.search(ci_text()) else ["no test run (pytest, unittest, tox, nox) in a workflow"]


@check("type_checker", severity="info", when=("python",), scenarios=CH, kind="files",
       why="type hints nobody checks drift from the code they describe",
       procedure="python-quality.md#type-checker")
def type_checker() -> list[str]:
    config = read("pyproject.toml") + read("mypy.ini") + read("pyrightconfig.json") + read("setup.cfg")
    return [] if TYPE_CHECKERS.search(ci_text() + config) else ["no mypy, pyright or ty configured or run in CI"]
