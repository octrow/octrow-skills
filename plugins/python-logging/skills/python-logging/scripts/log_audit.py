#!/usr/bin/env python3
"""Read-only logging audit of a Python repo: prints a Markdown report.

Usage: python3 log_audit.py [repo_dir]   (default: current directory)
In a git repo only files git does not ignore are scanned.

Finds: print() calls outside tests, basicConfig calls, file handlers without a size cap,
logger names in use, excepthook / asyncio handler presence, secret-redaction filters,
log files on disk and their total size, journald usage. Changes nothing.
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", "build", "dist",
             ".tox", ".mypy_cache", ".ruff_cache", "site-packages"}
PATTERNS = {
    "basicConfig": re.compile(r"logging\.basicConfig\("),
    "FileHandler (no cap)": re.compile(r"\bFileHandler\("),
    "TimedRotatingFileHandler (time only)": re.compile(r"TimedRotatingFileHandler\("),
    "RotatingFileHandler": re.compile(r"(?<!Timed)RotatingFileHandler\("),
    "sys.excepthook": re.compile(r"sys\.excepthook\s*="),
    "threading.excepthook": re.compile(r"threading\.excepthook\s*="),
    "asyncio exception handler": re.compile(r"set_exception_handler\("),
    "logging.Filter subclass": re.compile(r"\(logging\.Filter\)"),
    "structlog / loguru": re.compile(r"^\s*(import|from)\s+(structlog|loguru)", re.MULTILINE),
    "contextvars": re.compile(r"ContextVar\("),
}
PRINT_RE = re.compile(r"^\s*print\(", re.MULTILINE)
LOGGER_RE = re.compile(r"getLogger\(\s*(?:f?[\"']([^\"']*)[\"']|(__name__))?\s*\)")
MB = 1024 * 1024
TOP = 8


def py_files(root: Path) -> list[Path]:
    """Tracked + untracked-but-not-ignored files in a git repo (vendored examples drop
    out via .gitignore); else every *.py outside SKIP_DIRS."""
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "*.py"],
                             cwd=root, capture_output=True, text=True, timeout=30, check=True)
        return [root / line for line in out.stdout.splitlines() if (root / line).is_file()]
    except (OSError, subprocess.SubprocessError):
        return [p for p in root.rglob("*.py") if not SKIP_DIRS & set(p.relative_to(root).parts)]


def is_test(p: Path) -> bool:
    return "test" in p.name or any(part in ("tests", "test", "selftest") for part in p.parts)


def scan(root: Path) -> tuple[dict[str, list[str]], Counter, Counter]:
    hits: dict[str, list[str]] = {k: [] for k in PATTERNS}
    prints: Counter = Counter()
    loggers: Counter = Counter()
    for p in py_files(root):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(p.relative_to(root))
        for name, rx in PATTERNS.items():
            hits[name] += [f"{rel}:{text.count(chr(10), 0, m.start()) + 1}"
                           for m in rx.finditer(text)]
        if not is_test(p):
            prints[rel] = len(PRINT_RE.findall(text))
        for lit, dunder in LOGGER_RE.findall(text):
            loggers[lit or ("__name__" if dunder else "<root>")] += 1
    return hits, +prints, loggers


def log_files(root: Path) -> list[tuple[int, Path]]:
    found = [p for p in root.rglob("*") if p.is_file()
             and not SKIP_DIRS & set(p.relative_to(root).parts)
             and (".log" in p.name or p.name.endswith(".jsonl") or p.parent.name == "logs")]
    return sorted(((p.stat().st_size, p) for p in found), reverse=True)


def journald() -> str:
    try:
        out = subprocess.run(["journalctl", "--disk-usage"], capture_output=True, text=True,
                             timeout=10, check=False)
        return (out.stdout or out.stderr).strip() or "n/a"
    except (OSError, subprocess.TimeoutExpired):
        return "n/a (no journalctl)"


def report(root: Path) -> str:
    hits, prints, loggers = scan(root)
    files = log_files(root)
    total = sum(s for s, _ in files)
    out = [f"# Logging audit: {root}", "", "## Code", ""]
    for name, where in hits.items():
        shown = ", ".join(where[:TOP]) + (" …" if len(where) > TOP else "")
        out.append(f"- **{name}**: {len(where)}" + (f" ({shown})" if where else ""))
    out += ["", f"- **print() outside tests**: {sum(prints.values())}"]
    out += [f"  - {f}: {n}" for f, n in prints.most_common(TOP)]
    out += ["", f"- **logger names** ({len(loggers)}): "
            + ", ".join(f"`{k}`×{v}" for k, v in loggers.most_common(TOP))]
    out += ["", "## Disk", "", f"- log files: {len(files)}, total {total / MB:.1f} MB"]
    out += [f"  - {p.relative_to(root)}: {s / MB:.1f} MB" for s, p in files[:TOP]]
    out += [f"- journald: {journald()}", ""]
    return "\n".join(out)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "."
    if arg in ("-h", "--help"):
        sys.exit(print(__doc__))
    if not Path(arg).is_dir():
        sys.exit(f"log_audit: not a directory: {arg}")
    print(report(Path(arg).resolve()))
