#!/usr/bin/env python3
"""Read-only pre-publication report for a project in a git repo. Changes nothing.

usage: preflight.py [project-path] [--private word1,word2]

project-path may be the repo root or a subfolder of a monorepo (then history checks cover that folder only).
--private: extra words that must not be published (employer, client, internal project names).
Needs git; uses gitleaks (full secret scan) and `gh` (GitHub metadata) when available; asks PyPI/npm whether the
package name is taken (network, read-only).
"""
import base64
import json
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

COMMUNITY = ["README.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md",
             ".github/ISSUE_TEMPLATE", ".github/pull_request_template.md", ".github/dependabot.yml",
             ".github/workflows"]
SECRET_FILES = re.compile(r"(^|/)(\.env(\.[^/]*)?|id_rsa[^/]*|[^/]*\.pem|[^/]*\.key|credentials[^/]*\.json)$")
MONO_LANG = re.compile(r"(^|/)skills/|(^|/)CHANGELOG\.md$")  # agent instructions, release notes: EN only
SAFE_ENV = re.compile(r"\.env\.(example|sample|template)$")
# ponytail: a few well-known token shapes, used only when gitleaks isn't installed
TOKENS = r"(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{32,}|AKIA[0-9A-Z]{16}|xox[bp]-[A-Za-z0-9-]{20,})"
# `~/work/...` and `/home/<user>/` placeholders in docs don't match
PRIVATE_PATHS = r"(/home/[a-z][a-z0-9_-]+/|/Users/[A-Za-z][^/ ]+/|C:\\\\Users\\\\|~/(dev|work|src|projects)/[A-Za-z0-9_.-]*[A-Za-z0-9])"
INTERNAL = re.compile(r"(^|/)(prompts?/|\.claude/|\.agents/|\.cursor/|scratch[^/]*|HANDOFF[^/]*|continue-[^/]*\.md|"
                      r"PLAN(\.[a-z]{2})?\.md|TODO[^/]*\.md|notes?/)", re.I)
EMPTY_NOTES = re.compile(r"^\s*(\*\*Full Changelog\*\*:?\s*\S+)?\s*$")
NOT_BRANCH = re.compile(r"golden[- ]master|master[- ](key|password|copy|data|list|class|plan)|mastermind|webmaster|"
                        r"\"master\"|`master` mention|replace `master`", re.I)  # last three: code and advice about it
PREVIEW = re.compile(r"(social[-_]?preview|og[-_]?image|opengraph)[^/]*\.(png|jpe?g)$", re.I)
DEMO = re.compile(r"\.(gif|webp|mp4|webm)\b|asciinema\.org", re.I)
VERSUS = re.compile(r"^#+ .*(alternativ|compar|\bvs\.?\b|differ|аналог|отлич|сравн)", re.I | re.M)
PROBES_ANY = [".env", ".env.local"]
PROBES_PY = [".venv/x", "__pycache__/x.pyc", "dist/x.whl", "x.egg-info/PKG-INFO"]
PROBES_NODE = ["node_modules/x", ".next/x"]
USES = re.compile(r"^\s*-?\s*uses:\s*['\"]?([\w.-]+/[\w./-]+@[\w./-]+)", re.M)  # remote actions; skips ./local, docker://
SHA = re.compile(r"@[0-9a-f]{40}$")
NODE_MIN = 24  # older runtimes are deprecated; runners force them onto Node 24 with a warning
BIG_FILE = 1_000_000
TOPICS_MIN = 5
DESC_MAX = 120
HTTP_TIMEOUT = 8

ROOT = Path(".")
TOP = Path(".")
REL = ""  # project path inside the repo; "" at the root


def run(*cmd: str, cwd: Path | None = None) -> str:
    r = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def section(title: str, lines: list[str]) -> None:
    print(f"\n## {title}")
    print("\n".join(f"- {x}" for x in lines) if lines else "- ok")


def tracked() -> list[str]:
    return run("git", "ls-files").splitlines()  # relative to ROOT


def files() -> None:
    section("Community files (missing)", [f for f in COMMUNITY if not (ROOT / f).exists()])
    names = tracked()
    docs = [f for f in names if f.endswith(".md") and "/." not in f and not f.startswith(".")]
    stems = {f[:-3] for f in docs}
    lone = []
    for f in docs:
        stem = f[:-3]
        if stem.endswith(".ru"):
            if stem[:-3] not in stems:
                lone.append(f"{f}: no primary-language original")
        elif f"{stem}.ru" not in stems and not f.startswith((".github/", "tests/")) and not MONO_LANG.search(f):
            lone.append(f"{f}: no .ru.md mirror")
    section("Language mirrors (only if the repo is bilingual)", lone if any(s.endswith(".ru") for s in stems) else [])
    section("Tracked files that look secret", [f for f in names if SECRET_FILES.search(f) and not SAFE_ENV.search(f)])
    section("Internal-looking files (publish on purpose or remove)", [f for f in names if INTERNAL.search(f)])
    big = [f"{f} ({(ROOT / f).stat().st_size // 1024} KB)" for f in names
           if (ROOT / f).is_file() and (ROOT / f).stat().st_size > BIG_FILE]
    section(f"Tracked files over {BIG_FILE // 1_000_000} MB", big)


def gitignore() -> None:
    """Paths that should be ignored but aren't; the fix is a github/gitignore template for the stack."""
    stacks = [("Python", "pyproject.toml", PROBES_PY), ("Node", "package.json", PROBES_NODE)]
    found = [(name, probes) for name, marker, probes in stacks if (ROOT / marker).exists()]
    probes = PROBES_ANY + [p for _, ps in found for p in ps]
    loose = [p for p in probes
             if subprocess.run(["git", "check-ignore", "-q", "--no-index", p], cwd=ROOT).returncode == 1]
    out = [f"not ignored: {', '.join(loose)}"] if loose else []
    if loose:
        out += [f"append the template: gh api gitignore/templates/{name} --jq .source >> .gitignore"
                for name, _ in found] or ["templates: gh api gitignore/templates (github/gitignore)"]
    section(".gitignore", out)


def secrets() -> None:
    out = []
    if shutil.which("gitleaks"):
        # `detect` works on old (distro) and new gitleaks; --log-opts limits history to the project folder
        cmd = ["gitleaks", "detect", "--source", str(TOP), "--redact", "--no-banner",
               "--report-format", "json", "--report-path", "/dev/stdout"]
        if REL:
            cmd.append(f"--log-opts=-- {REL}")
        raw = subprocess.run(cmd, capture_output=True, text=True).stdout
        leaks = json.loads(raw or "[]")
        out += [f"gitleaks: {x['RuleID']} in {x['File']} at {x['Commit'][:8]} (rotate the key, then ask about a rewrite)"
                for x in leaks] or ["gitleaks: no leaks in history"]
    else:
        hits = run("git", "log", "--all", "-p", "-E", "-G", TOKENS, "--format=%h", "--", REL or ".", cwd=TOP)
        out += [f"{m[:6]}… in history (rotate it, then ask about a rewrite)" for m in sorted(set(re.findall(TOKENS, hits)))]
        out.append("gitleaks not installed: this grep is only a weak check")
    section("Secrets in history", out)


def private(words: list[str]) -> None:
    pattern = PRIVATE_PATHS + ("|" + "|".join(map(re.escape, words)) if words else "")
    now = list(dict.fromkeys(run("git", "grep", "-n", "-I", "-i", "-o", "-E", pattern).splitlines()))
    past = run("git", "log", "--all", "-i", "-E", "-G", pattern, "--format=%h", "--", REL or ".", cwd=TOP).split()
    emails = sorted(set(run("git", "log", "--all", "--format=%ae", "--", REL or ".", cwd=TOP).split()))
    out = [f"now: {h}" for h in now[:10]] + ([f"… {len(now) - 10} more matches"] if len(now) > 10 else [])
    if words:
        found = {w for w in words if any(w.lower() in h.lower() for h in now)}
        out.append(f"--private words found: {', '.join(sorted(found)) or 'none in current files'}")
    if past:
        out.append(f"in {len(past)} past commits (still public after a fix; a fresh-history export avoids it)")
    out.append(f"author emails in history: {', '.join(emails)} (a work email here is published too)")
    if REL:
        out.append(f"project is the subfolder `{REL}` of {TOP.name}: publish it as its own repo; "
                   "export the folder with fresh history unless the old commits are clean")
    out.append("provenance: was any of this code written for an employer or client? Ask before publishing")
    section("Private paths, names and provenance", out)


def history() -> None:
    branch = run("git", "symbolic-ref", "--short", "HEAD").strip()
    hits = [h for h in run("git", "grep", "-n", "-I", "-w", "master", "--", ".", ":!CHANGELOG.md").splitlines() if not NOT_BRANCH.search(h)]
    section("Branch", ([f"current branch is `{branch}`, default should be `main`"] if branch == "master" else [])
            + [f"`master` mention: {h[:110]}" for h in hits[:6]] + ([f"… {len(hits) - 6} more"] if len(hits) > 6 else []))


def readme() -> None:
    path = ROOT / "README.md"
    if not path.exists():
        return
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)  # examples, not links
    out = []
    for target in re.findall(r"\]\(([^)#\s]+)[^)]*\)|(?:src|href)=\"([^\"#]+)\"", text):
        link = target[0] or target[1]
        if re.match(r"[a-z]+:|//", link):
            continue
        dest = (ROOT / link.split("?")[0]).resolve()
        if not dest.exists():
            out.append(f"broken relative link: {link}")
        elif not dest.is_relative_to(ROOT):
            out.append(f"link leaves the project (breaks once it's its own repo): {link}")
    out += [f"image without alt: {m}" for m in re.findall(r"<img(?![^>]*\balt=\"[^\"]+\")[^>]*>", text)]
    out += [f"markdown image without alt: {m}" for m in re.findall(r"!\[\]\(([^)]+)\)", text)]
    if not DEMO.search(text):
        out.append("no demo GIF/video in README (launch.md: 10–20 s of a real run under the hero)")
    if not VERSUS.search(text):
        out.append("no 'alternatives / how it differs' section (answers 'why not just X?')")
    words = len(re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", " ", text).split())
    out.append(f"{words} words; check the first 200 say what it is, for whom, and show a proof")
    section("README", out)


def skills() -> None:
    out = []
    for f in [f for f in tracked() if f.endswith("SKILL.md") or f.endswith("SKILL.ru.md")]:
        text = (ROOT / f).read_text(encoding="utf-8")
        m = re.search(r"^---\n(.*?)\n---\n", text, re.S | re.M)
        if not m:
            out.append(f"{f}: no frontmatter; agents won't load the skill")
            continue
        if m.start():
            out.append(f"{f}: frontmatter is not the first thing in the file (move the language line below it)")
        for key in ("name", "description"):
            line = re.search(rf"^{key}:(.*)$", m.group(1), re.M)
            if not line:
                out.append(f"{f}: no `{key}:` in frontmatter")
            elif ": " in line.group(1).strip() and not re.match(r"\s*([\"'>|])", line.group(1)):
                out.append(f"{f}: `{key}` has an unquoted ': ' (invalid YAML); quote it or use `>`")
    section("Agent skills (SKILL.md frontmatter)", out)


def workflows() -> None:
    out, refs, text_all = [], set(), ""
    for wf in sorted((ROOT / ".github/workflows").glob("*.y*ml")):
        text = wf.read_text(encoding="utf-8")
        text_all += text
        if not re.search(r"^permissions:", text, re.M):
            out.append(f"{wf.name}: no top-level `permissions:` (default token may be read-write)")
        refs |= set(USES.findall(text))
    unpinned = sorted(r for r in refs if not SHA.search(r) and not r.startswith(("actions/", "github/")))
    if unpinned:
        out.append(f"third-party actions pinned by tag, not SHA: {', '.join(unpinned)} (zizmor flags these)")
    out += runtimes(refs)
    hooks = ROOT / ".pre-commit-config.yaml"
    out += missing_guards(text_all + (hooks.read_text(encoding="utf-8") if hooks.exists() else ""), bool(refs))
    section("CI workflows", out)


def install() -> None:
    """A Python app with a command but no one-command installer or release workflow (Phase 2)."""
    py = ROOT / "pyproject.toml"
    if not py.exists() or not tomllib.loads(py.read_text(encoding="utf-8")).get("project", {}).get("scripts"):
        return  # a library or not Python: `pip install` is the install path
    out = [f"no {f}: copy assets/{f}" for f in ("install.sh", "install.ps1") if not (ROOT / f).exists()]
    wf = ROOT / ".github/workflows"
    texts = {f.name: f.read_text(encoding="utf-8") for f in wf.glob("*.y*ml")} if wf.is_dir() else {}
    if (ROOT / "install.sh").exists() and not any("install.sh" in t for t in texts.values()):
        out.append("installers aren't run in CI on Linux/macOS/Windows: copy assets/workflows/install.yml")
    if not any(re.search(r"gh release create|action-gh-release|gh-action-pypi-publish", t) for t in texts.values()):
        out.append("no release workflow (wheel, binaries, GitHub release): copy assets/workflows/release.yml")
    section("Install and release (Phase 2)", out)


def missing_guards(ci_text: str, has_actions: bool) -> list[str]:
    """Secret scan, workflow lint and Scorecard absent from workflows + pre-commit config."""
    out = []
    if not re.search(r"gitleaks|trufflehog", ci_text):
        out.append("no secret scan in CI or pre-commit: "
                   "add assets/workflows/security.yml + assets/pre-commit-config.yaml")
    if has_actions and not re.search(r"zizmor|actionlint", ci_text):
        out.append("workflows aren't linted: zizmor + actionlint (assets/pre-commit-config.yaml)")
    bot = ROOT / ".github/dependabot.yml"
    if bot.exists() and "cooldown" not in bot.read_text(encoding="utf-8"):
        out.append("dependabot.yml: no `cooldown` (wait ~7 days before proposing a release; assets/dependabot.yml)")
    if "ossf/scorecard-action" not in ci_text:
        out.append("no OpenSSF Scorecard (assets/workflows/scorecard.yml; public repos)")
    return out


def runtimes(refs: set[str]) -> list[str]:
    if not shutil.which("gh"):
        return ["`gh` not installed: Node runtime of actions not checked"]
    out = []
    for uses in sorted(refs):
        node = re.fullmatch(r"node(\d+)", action_runtime(uses))
        if node and int(node.group(1)) < NODE_MIN:
            out.append(f"{uses}: targets {node.group(0)}, deprecated (forced onto Node 24 with a warning); bump the major")
    return out


def action_runtime(uses: str) -> str:
    """`using:` of a remote action (node20, node24, docker, composite), "" if unknown. Needs `gh`."""
    repo_path, _, ref = uses.partition("@")
    owner, repo, *sub = repo_path.split("/")
    for name in ("action.yml", "action.yaml"):
        path = "/".join([*sub, name])
        raw = run("gh", "api", f"repos/{owner}/{repo}/contents/{path}?ref={ref}", "--jq", ".content")
        if raw:
            text = base64.b64decode(raw).decode("utf-8", "replace")
            m = re.search(r"^\s+using:\s*['\"]?([\w-]+)", text, re.M)
            return m.group(1) if m else ""
    return ""


def http_json(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {} if e.code == 404 else None
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def package() -> str:
    """Report whether the package name is free on its registry; return the package description."""
    out, desc = [], ""
    if (ROOT / "pyproject.toml").exists():
        meta = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8")).get("project", {})
        name, desc, registry = meta.get("name", ""), meta.get("description", ""), "PyPI"
        info = http_json(f"https://pypi.org/pypi/{name}/json") if name else None
        owner = json.dumps((info or {}).get("info", {}).get("project_urls") or {})
    elif (ROOT / "package.json").exists():
        meta = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        name, desc, registry = meta.get("name", ""), meta.get("description", ""), "npm"
        info = http_json(f"https://registry.npmjs.org/{name}") if name else None
        owner = json.dumps((info or {}).get("repository") or {})
    else:
        return ""
    remote = run("git", "remote", "get-url", "origin").strip().removesuffix(".git")
    slug = "/".join(remote.replace(":", "/").split("/")[-2:]).lower() if remote else ""
    if info is None:
        out.append(f"{registry} `{name}`: couldn't check (offline?)")
    elif not info:
        out.append(f"{registry} `{name}`: free")
    elif slug and slug in owner.lower():
        out.append(f"{registry} `{name}`: published from this repo")
    else:
        out.append(f"{registry} `{name}`: TAKEN by another project; `pipx/uvx/npx {name}` installs theirs. Rename the "
                   "package (the command name can stay) before telling people to install it")
    section("Package name", out)
    return desc


def releases(name: str) -> list[str]:
    raw = run("gh", "api", f"repos/{name}/releases?per_page=20", "--jq", "[.[] | {t: .tag_name, b: (.body // \"\")}]")
    rels = json.loads(raw or "[]")
    empty = [r["t"] for r in rels if EMPTY_NOTES.match(r["b"])]
    return [f"releases with empty notes (only 'Full Changelog'): {', '.join(empty)}"] if empty else []


def red_bot_prs(name: str) -> list[str]:
    """Open Dependabot PRs with a failing check: they pile up unnoticed and hide real breakage."""
    raw = run("gh", "pr", "list", "-R", name, "--author", "app/dependabot", "--state", "open",
              "--json", "number,statusCheckRollup")
    red = [f"#{p['number']}" for p in json.loads(raw or "[]")
           if any(c.get("conclusion") == "FAILURE" or c.get("state") in ("FAILURE", "ERROR")
                  for c in p.get("statusCheckRollup") or [])]
    return [f"Dependabot PRs with failing checks: {', '.join(red)} (fix, close, or `ignore` the majors)"] if red else []


def github(pkg_desc: str) -> None:
    raw = run("gh", "repo", "view", "--json",
              "nameWithOwner,description,repositoryTopics,homepageUrl,visibility,usesCustomOpenGraphImage,"
              "defaultBranchRef,hasWikiEnabled,hasProjectsEnabled,hasDiscussionsEnabled,latestRelease,licenseInfo")
    if not raw:
        section("GitHub", ["no `gh` repo info (not logged in or no GitHub remote)"])
        return
    r = json.loads(raw)
    name, out = r["nameWithOwner"], []
    branch = (r.get("defaultBranchRef") or {}).get("name", "none")
    desc = r.get("description") or ""
    topics = [t["name"] for t in r.get("repositoryTopics") or []]
    out.append(f"visibility: {r['visibility']}, default branch: {branch}")
    out.append(f"description ({len(desc)} chars): {desc or 'MISSING'}" + (" — too long" if len(desc) > DESC_MAX else ""))
    if pkg_desc and pkg_desc.strip(". ").lower() != desc.strip(". ").lower():
        out.append(f"package description differs: {pkg_desc!r}; make About, package and README pitch say the same")
    out.append(f"topics ({len(topics)}): {', '.join(topics) or 'NONE'}" + (" — add more" if len(topics) < TOPICS_MIN else ""))
    out.append(f"homepage: {r.get('homepageUrl') or 'not set'}")
    ready = [f for f in tracked() if PREVIEW.search(f)]
    out.append("social preview: custom" if r["usesCustomOpenGraphImage"] else
               "social preview: GitHub default; " + (f"upload {ready[0]} (Settings → General)" if ready
                                                    else "make a 1280×640 PNG and upload it"))
    out.append(f"license: {(r.get('licenseInfo') or {}).get('name', 'NONE')}")
    out.append(f"latest release: {(r.get('latestRelease') or {}).get('tagName', 'none')}")
    out += releases(name)
    out += red_bot_prs(name)
    out += [f"{k} enabled (turn off if unused)" for k in ("hasWikiEnabled", "hasProjectsEnabled") if r.get(k)]
    out.append(f"discussions: {'on' if r.get('hasDiscussionsEnabled') else 'off'}")
    pvr = run("gh", "api", f"repos/{name}/private-vulnerability-reporting")
    out.append("private vulnerability reporting: " + ("on" if '"enabled":true' in pvr.replace(" ", "") else "off/unknown"))
    out += security_settings(name)
    protected = run("gh", "api", f"repos/{name}/branches/{branch}", "--jq", ".protected").strip()
    rules = run("gh", "api", f"repos/{name}/rules/branches/{branch}", "--jq", "length").strip()
    out.append(f"`{branch}` protected: {protected or 'unknown'}, branch rules: {rules or '0'}")
    section("GitHub", out)


def security_settings(name: str) -> list[str]:
    """Secret scanning, push protection, Dependabot updates; GitHub omits them for private repos without GHAS."""
    sa = json.loads(run("gh", "api", f"repos/{name}", "--jq", ".security_and_analysis // {}") or "{}")
    if not sa:
        return ["secret scanning / push protection: not reported (private repo without Advanced Security); "
                "free once public, turn on right after the visibility flip (security.md §7)"]
    return [f"{key}: {(sa.get(key) or {}).get('status', 'unknown')}"
            for key in ("secret_scanning", "secret_scanning_push_protection", "dependabot_security_updates")]


def main(argv: list[str]) -> None:
    global ROOT, TOP, REL
    words = []
    if "--private" in argv:
        i = argv.index("--private")
        words = [w for w in argv[i + 1].split(",") if w]
        argv = argv[:i] + argv[i + 2:]
    ROOT = Path(argv[0] if argv else ".").resolve()
    top = run("git", "rev-parse", "--show-toplevel").strip()
    if not top:
        sys.exit(f"{ROOT} is not in a git repo")
    TOP = Path(top)
    REL = "" if TOP == ROOT else str(ROOT.relative_to(TOP))
    print(f"# Preflight: {ROOT}" + (f" (subfolder of {TOP})" if REL else ""))
    files()
    gitignore()
    secrets()
    private(words)
    history()
    readme()
    skills()
    workflows()
    install()
    github(package())


if __name__ == "__main__":
    main(sys.argv[1:])
