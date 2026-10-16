"""Core Checks: history, secrets, community files, README, CI, install and GitHub metadata."""
import base64
import functools
import json
import re
import shutil
import subprocess
import tomllib

from registry import Broken, check, http_json, judgement, read, repo, run, tracked

PUB = {"publish"}
BOTH = {"publish", "deploy"}  # history, secrets and CI hardening matter however the code ships
COMMUNITY = ["README.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md",
             ".github/ISSUE_TEMPLATE", ".github/pull_request_template.md", ".github/dependabot.yml",
             ".github/workflows"]
SECRET_FILES = re.compile(r"(^|/)(\.env(\.[^/]*)?|id_rsa[^/]*|[^/]*\.pem|[^/]*\.key|credentials[^/]*\.json)$")
# agent material (skills, plugins, the CONTEXT.md glossary) and release notes: EN only
MONO_LANG = re.compile(r"(^|/)(skills|plugins)/|(^|/)(CHANGELOG|CONTEXT|CONTEXT-MAP)\.md$")
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
VERSUS = re.compile(r"^#+ .*(alternativ|compar|\bvs\.?\b|differ|why not|аналог|отлич|сравн|почему не)", re.I | re.M)
PROBES_ANY = [".env", ".env.local"]
PROBES = {"Python": ("pyproject.toml", [".venv/x", "__pycache__/x.pyc", "dist/x.whl", "x.egg-info/PKG-INFO"]),
          "Node": ("package.json", ["node_modules/x", ".next/x"])}
USES = re.compile(r"^\s*-?\s*uses:\s*['\"]?([\w.-]+/[\w./-]+@[\w./-]+)", re.M)  # remote actions; skips ./local, docker://
SHA = re.compile(r"@[0-9a-f]{40}$")
NODE_MIN = 24  # older runtimes are deprecated; runners force them onto Node 24 with a warning
BIG_FILE = 1_000_000
TOPICS_MIN = 5
DESC_MAX = 120
SHOW_MAX = 10


def capped(lines: list[str], limit: int = SHOW_MAX) -> list[str]:
    return lines[:limit] + ([f"… {len(lines) - limit} more"] if len(lines) > limit else [])


def history_of(pattern: str, *opts: str) -> str:
    return run("git", "log", "--all", *opts, "-E", "-G", pattern, "--format=%h", "--", repo.rel or ".", cwd=repo.top)


# Files and history


@check("community_files", severity="warning", scenarios=PUB, kind="files",
       why="strangers look for a license, how to contribute and how to report a vulnerability",
       procedure="skill:github-repo")
def community_files() -> list[str]:
    return [f"missing: {f}" for f in COMMUNITY if not (repo.root / f).exists()]


@check("language_mirrors", severity="warning", when=("bilingual",), scenarios=PUB, kind="files",
       why="a bilingual repo where some docs exist in one language only reads as abandoned halfway",
       procedure="bilingual.md#docs-layout")
def language_mirrors() -> list[str]:
    docs = [f for f in tracked() if f.endswith(".md") and "/." not in f and not f.startswith(".")]
    stems, out = {f[:-3] for f in docs}, []
    for f in docs:
        stem = f[:-3]
        if stem.endswith(".ru"):
            if stem[:-3] not in stems:
                out.append(f"{f}: no primary-language original")
        elif f"{stem}.ru" not in stems and not f.startswith((".github/", "tests/")) and not MONO_LANG.search(f):
            out.append(f"{f}: no .ru.md mirror")
    return out


@check("secret_files_tracked", severity="error", scenarios=BOTH, kind="files",
       why="a tracked .env or key file is published with the first push",
       procedure="security.md#2-files-that-shouldnt-be-tracked")
def secret_files_tracked() -> list[str]:
    return [f for f in tracked() if SECRET_FILES.search(f) and not SAFE_ENV.search(f)]


@check("internal_files_tracked", severity="warning", scenarios=PUB, kind="files",
       why="session prompts, plans and agent folders publish more than intended",
       procedure="security.md#3-provenance-private-names-fresh-history")
def internal_files_tracked() -> list[str]:
    return [f"{f} (publish on purpose or remove)" for f in tracked() if INTERNAL.search(f)]


@check("big_files_tracked", severity="warning", scenarios=PUB, kind="files",
       why="heavy data bloats every clone and the package",
       procedure="security.md#5-package-contents")
def big_files_tracked() -> list[str]:
    return [f"{f} ({(repo.root / f).stat().st_size // 1024} KB)" for f in tracked()
            if (repo.root / f).is_file() and (repo.root / f).stat().st_size > BIG_FILE]


@check("gitignore_gaps", severity="warning", scenarios=BOTH, kind="git",
       why="an unignored .env or build folder gets committed by the next `git add .`",
       procedure="security.md#2-files-that-shouldnt-be-tracked")
def gitignore_gaps() -> list[str]:
    found = [name for name, (marker, _) in PROBES.items() if (repo.root / marker).exists()]
    probes = PROBES_ANY + [p for name in found for p in PROBES[name][1]]
    loose = [p for p in probes
             if subprocess.run(["git", "check-ignore", "-q", "--no-index", p], cwd=repo.root).returncode == 1]
    if not loose:
        return []
    return [f"not ignored: {', '.join(loose)}"] + (
        [f"append the template: gh api gitignore/templates/{name} --jq .source >> .gitignore" for name in found]
        or ["templates: gh api gitignore/templates (github/gitignore)"])


@check("secrets_in_history", severity="error", scenarios=BOTH, kind="git",
       why="once public, history is copied and indexed; a leaked key is only safe after rotation",
       procedure="security.md#1-secrets-in-history-not-just-head")
def secrets_in_history() -> list[str]:
    if not shutil.which("gitleaks"):
        hits = sorted(set(re.findall(TOKENS, history_of(TOKENS, "-p"))))
        if hits:
            return [f"{m[:6]}… in history (rotate it, then ask about a rewrite)" for m in hits] + [
                "gitleaks not installed: this grep is only a weak check"]
        raise Broken("gitleaks not installed: a weak grep found nothing, which proves little")
    # `detect` works on old (distro) and new gitleaks; --log-opts limits history to the project folder
    cmd = ["gitleaks", "detect", "--source", str(repo.top), "--redact", "--no-banner",
           "--report-format", "json", "--report-path", "/dev/stdout"] + ([f"--log-opts=-- {repo.rel}"] if repo.rel else [])
    raw = subprocess.run(cmd, capture_output=True, text=True).stdout
    return [f"gitleaks: {x['RuleID']} in {x['File']} at {x['Commit'][:8]} (rotate the key, then ask about a rewrite)"
            for x in json.loads(raw or "[]")]


def private_pattern() -> str:
    return PRIVATE_PATHS + ("|" + "|".join(map(re.escape, repo.words)) if repo.words else "")


@check("private_paths_in_files", severity="warning", scenarios=PUB, kind="git",
       why="home paths, employer or client names are not secrets to a scanner but publish more than intended",
       procedure="security.md#3-provenance-private-names-fresh-history")
def private_paths_in_files() -> list[str]:
    now = list(dict.fromkeys(run("git", "grep", "-n", "-I", "-i", "-o", "-E", private_pattern()).splitlines()))
    out = capped(now)
    if repo.words:
        found = {w for w in repo.words if any(w.lower() in h.lower() for h in now)}
        out.append(f"--private words found: {', '.join(sorted(found)) or 'none in current files'}")
    return out if now else []


@check("private_paths_in_history", severity="warning", scenarios=PUB, kind="git",
       why="a fix in HEAD leaves the old commits public",
       procedure="security.md#3-provenance-private-names-fresh-history")
def private_paths_in_history() -> list[str]:
    past = history_of(private_pattern(), "-i").split()
    return [f"in {len(past)} past commits (still public after a fix; a fresh-history export avoids it)"] if past else []


@check("subfolder_project", severity="warning", when=("subfolder",), scenarios=PUB, kind="git",
       why="publishing a monorepo folder publishes the whole repo's history",
       procedure="security.md#3-provenance-private-names-fresh-history")
def subfolder_project() -> list[str]:
    return [f"project is the subfolder `{repo.rel}` of {repo.top.name}: publish it as its own repo; "
            "export the folder with fresh history unless the old commits are clean"]


judgement("author_emails", severity="info", scenarios=PUB,
          question="Are all author emails in history fine to publish? A work email here is published too.",
          procedure="security.md#3-provenance-private-names-fresh-history",
          evidence=lambda: [", ".join(sorted(set(run("git", "log", "--all", "--format=%ae", "--",
                                                     repo.rel or ".", cwd=repo.top).split())))])

judgement("provenance", severity="error", scenarios=PUB,
          question="Was any of this code written for an employer or client, or taken from another project? "
                   "Ask before publishing; it blocks anything public until answered.",
          procedure="security.md#3-provenance-private-names-fresh-history")

judgement("third_party_code", severity="warning", scenarios=PUB,
          question="Is any code vendored, ported or copied from elsewhere? If so, is its license compatible and "
                   "credited in THIRD_PARTY_NOTICES.md?",
          procedure="security.md#4-licenses-of-borrowed-code")

judgement("code_security_review", severity="warning", scenarios=PUB,
          question="Does the project handle keys, user input, subprocesses or files? Then a code-level security "
                   "review has to happen before it goes public.",
          procedure="skill:security-review")


@check("default_branch_master", severity="warning", scenarios=PUB, kind="git",
       why="`main` is the default new contributors and tools expect",
       procedure="security.md#7-github-settings-outward-facing-list-the-commands-run-after-a-yes")
def default_branch_master() -> list[str]:
    branch = run("git", "symbolic-ref", "--short", "HEAD").strip()
    return [f"current branch is `{branch}`, default should be `main` (rename after a yes)"] if branch == "master" else []


@check("master_mentions", severity="info", scenarios=PUB, kind="git",
       why="docs and scripts that name the old default branch break after the rename",
       procedure="security.md#7-github-settings-outward-facing-list-the-commands-run-after-a-yes")
def master_mentions() -> list[str]:
    hits = [h for h in run("git", "grep", "-n", "-I", "-w", "master", "--", ".", ":!CHANGELOG.md").splitlines()
            if not NOT_BRANCH.search(h)]
    return capped([h[:110] for h in hits], 6)


# README


def readme_text() -> str:
    return re.sub(r"```.*?```", "", read("README.md"), flags=re.S)  # examples, not links


@check("readme_links", severity="warning", when=("has_readme",), scenarios=PUB, kind="files",
       why="a broken link on the front page is the first thing a stranger hits",
       procedure="skill:github-repo")
def readme_links() -> list[str]:
    out = []
    for target in re.findall(r"\]\(([^)#\s]+)[^)]*\)|(?:src|href)=\"([^\"#]+)\"", readme_text()):
        link = target[0] or target[1]
        if re.match(r"[a-z]+:|//", link):
            continue
        dest = (repo.root / link.split("?")[0]).resolve()
        if not dest.exists():
            out.append(f"broken relative link: {link}")
        elif not dest.is_relative_to(repo.root):
            out.append(f"link leaves the project (breaks once it's its own repo): {link}")
    return out


@check("readme_image_alt", severity="warning", when=("has_readme",), scenarios=PUB, kind="files",
       why="images without alt text are invisible to screen readers and search",
       procedure="seo.md#readme-opening-the-first-screen")
def readme_image_alt() -> list[str]:
    text = readme_text()
    return ([f"image without alt: {m}" for m in re.findall(r"<img(?![^>]*\balt=\"[^\"]+\")[^>]*>", text)]
            + [f"markdown image without alt: {m}" for m in re.findall(r"!\[\]\(([^)]+)\)", text)])


@check("readme_demo", severity="info", when=("has_readme",), scenarios=PUB, kind="files",
       why="10–20 s of a real run under the hero shows the project works before anyone installs it",
       procedure="launch.md#1-readiness-gate-check-before-any-post")
def readme_demo() -> list[str]:
    return [] if DEMO.search(readme_text()) else ["no demo GIF/video in README"]


@check("readme_alternatives", severity="info", when=("has_readme",), scenarios=PUB, kind="files",
       why="readers ask 'why not just X?' before they install",
       procedure="launch.md#1-readiness-gate-check-before-any-post")
def readme_alternatives() -> list[str]:
    return [] if VERSUS.search(readme_text()) else ["no 'alternatives / how it differs' section"]


def readme_words() -> int:
    return len(re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", " ", readme_text()).split())


judgement("readme_opening", severity="warning", when=("has_readme",), scenarios=PUB,
          question="Do the first 200 words say what it is, for whom, and show a proof?",
          procedure="seo.md#readme-opening-the-first-screen",
          evidence=lambda: [f"{readme_words()} words"])


judgement("readme_claims_real", severity="warning", when=("has_readme",), scenarios=PUB,
          question="Does every number, benchmark and compatibility claim in the README come from a real run, test "
                   "or release? No made-up adoption numbers or testimonials.",
          procedure="skill:github-repo")

judgement("readme_plain_language", severity="info", when=("has_readme",), scenarios=PUB,
          question="Do the README and other prose read like the author wrote it, without AI tells or sales "
                   "language?",
          procedure="skill:humanizer")

judgement("readme_visual_story", severity="info", when=("has_readme",), scenarios=PUB,
          question="Does the README open with a hero and a proof image built from real output of the project?",
          procedure="skill:beautify-github-readme")

judgement("gui_screenshots_fresh", severity="info", when=("has_readme",), scenarios=PUB,
          question="Does the project have a GUI? Then are the README screenshots newer than the last change to it, "
                   "at the same file names and sizes?",
          procedure="gui.md#refreshing-readme-screenshots")


# Agent skills


@check("skill_frontmatter", severity="warning", when=("skills",), scenarios=PUB, kind="files",
       why="a SKILL.md with broken frontmatter is silently not loaded by agents",
       procedure="release.md#agent-skills-skillmd")
def skill_frontmatter() -> list[str]:
    out = []
    for f in [f for f in tracked() if f.endswith(("SKILL.md", "SKILL.ru.md"))]:
        m = re.search(r"^---\n(.*?)\n---\n", read(f), re.S | re.M)
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
    return out


# CI


def workflow_texts() -> dict[str, str]:
    return {wf.name: wf.read_text(encoding="utf-8") for wf in sorted((repo.root / ".github/workflows").glob("*.y*ml"))}


def action_refs() -> set[str]:
    return {r for t in workflow_texts().values() for r in USES.findall(t)}


def ci_text() -> str:
    return "".join(workflow_texts().values()) + read(".pre-commit-config.yaml")


@check("workflow_permissions", severity="warning", when=("github_actions",), scenarios=BOTH, kind="files",
       why="without `permissions:` the default token may be read-write",
       procedure="security.md#8-workflow-hardening")
def workflow_permissions() -> list[str]:
    return [f"{name}: no top-level `permissions:`" for name, t in workflow_texts().items()
            if not re.search(r"^permissions:", t, re.M)]


@check("actions_pinned_sha", severity="warning", when=("github_actions",), scenarios=BOTH, kind="files",
       why="a moved tag runs someone else's code with your token (zizmor flags these)",
       procedure="security.md#8-workflow-hardening")
def actions_pinned_sha() -> list[str]:
    return [f"pinned by tag, not SHA: {r}" for r in sorted(action_refs())
            if not SHA.search(r) and not r.startswith(("actions/", "github/"))]


def action_runtime(uses: str) -> str:
    """`using:` of a remote action (node20, node24, docker, composite), "" if unknown. Needs `gh`."""
    repo_path, _, ref = uses.partition("@")
    owner, name, *sub = repo_path.split("/")
    for fname in ("action.yml", "action.yaml"):
        raw = run("gh", "api", f"repos/{owner}/{name}/contents/{'/'.join([*sub, fname])}?ref={ref}", "--jq", ".content")
        if raw:
            m = re.search(r"^\s+using:\s*['\"]?([\w-]+)", base64.b64decode(raw).decode("utf-8", "replace"), re.M)
            return m.group(1) if m else ""
    return ""


@check("actions_node_runtime", severity="warning", when=("github_actions",), scenarios=BOTH, kind="gh_api",
       why="runners force Node 20 actions onto Node 24 with a warning; bump the major",
       procedure="security.md#8-workflow-hardening")
def actions_node_runtime() -> list[str]:
    if not shutil.which("gh") or subprocess.run(["gh", "auth", "status"], capture_output=True).returncode:
        raise Broken("`gh` not installed or not logged in: Node runtime of actions not checked")
    out = []
    for uses in sorted(action_refs()):
        node = re.fullmatch(r"node(\d+)", action_runtime(uses))
        if node and int(node.group(1)) < NODE_MIN:
            out.append(f"{uses}: targets {node.group(0)}, deprecated; bump the major")
    return out


@check("private_runner_minutes", severity="info", when=("github_actions", "!public"), scenarios=PUB, kind="files",
       why="macOS/Windows runners burn a private repo's free minutes several times faster than Linux",
       procedure="release.md#ci-for-the-install-path")
def private_runner_minutes() -> list[str]:
    if not re.search(r"macos|windows", "".join(workflow_texts().values())):
        return []
    return ["until public, run the 3-OS jobs on tags or `workflow_dispatch`, not every push"]


@check("secret_scan_ci", severity="warning", scenarios=BOTH, kind="files",
       why="a key committed after launch is caught only if something scans every push",
       procedure="assets/workflows/security.yml")
def secret_scan_ci() -> list[str]:
    if re.search(r"gitleaks|trufflehog", ci_text()):
        return []
    return ["no secret scan in CI or pre-commit: add engine/assets/workflows/security.yml + engine/assets/pre-commit-config.yaml"]


@check("workflow_lint", severity="warning", when=("github_actions",), scenarios=BOTH, kind="files",
       why="zizmor and actionlint catch template injection and broken run: steps before they ship",
       procedure="assets/pre-commit-config.yaml")
def workflow_lint() -> list[str]:
    return [] if not action_refs() or re.search(r"zizmor|actionlint", ci_text()) else ["workflows aren't linted"]


@check("dependabot_cooldown", severity="warning", scenarios=BOTH, kind="files",
       why="a release-day dependency update is how a hijacked package reaches you",
       procedure="assets/dependabot.yml")
def dependabot_cooldown() -> list[str]:
    bot = read(".github/dependabot.yml")
    return ["dependabot.yml: no `cooldown` (wait ~7 days before proposing a release)"] if bot and "cooldown" not in bot else []


@check("scorecard_workflow", severity="warning", when=("public",), scenarios=PUB, kind="files",
       why="OpenSSF Scorecard shows visitors the supply-chain posture (public repos only)",
       procedure="assets/workflows/scorecard.yml")
def scorecard_workflow() -> list[str]:
    return [] if "ossf/scorecard-action" in ci_text() else ["no OpenSSF Scorecard workflow"]


# Install and release


judgement("first_run", severity="warning", scenarios=PUB,
          question="Is there one command per OS to install and one to run, keys optional where possible, and a "
                   "doctor/config step that says in plain words what is missing?",
          procedure="release.md#first-run")


def pyproject() -> dict:
    text = read("pyproject.toml")
    return tomllib.loads(text) if text else {}


def git_sources() -> list[tuple[str, str, str]]:
    """(name, kind, spec) of dependencies taken from git/path/url via [tool.uv.sources]."""
    meta = pyproject()
    deps = {re.split(r"[\[<>=!~ ;]", d, maxsplit=1)[0].lower().replace("_", "-"): d
            for d in meta.get("project", {}).get("dependencies", [])}
    out = []
    for name, src in meta.get("tool", {}).get("uv", {}).get("sources", {}).items():
        kind = next((k for k in ("git", "path", "url", "workspace") if isinstance(src, dict) and k in src), None)
        spec = deps.get(name.lower().replace("_", "-"))
        if kind and spec:
            out.append((name, kind, spec))
    return out


def pypi(name: str) -> dict:
    info = http_json(f"https://pypi.org/pypi/{name}/json")
    if info is None:
        raise Broken(f"couldn't reach PyPI for `{name}` (offline?)")
    return info


@check("deps_unpublished", severity="error", when=("python_app",), scenarios=PUB, kind="registry",
       why="a wheel resolves dependencies from PyPI by name; one that isn't there makes the install fail",
       procedure="release.md#one-command-install")
def deps_unpublished() -> list[str]:
    return [f"`{n}` comes from {k} and isn't on PyPI: a wheel of this project won't install. Publish it first"
            for n, k, _ in git_sources() if not pypi(n)]


@check("deps_drift", severity="warning", when=("python_app",), scenarios=PUB, kind="registry",
       why="the PyPI release a wheel installs may lack what the git checkout has",
       procedure="release.md#one-command-install")
def deps_drift() -> list[str]:
    out = []
    for name, kind, spec in git_sources():
        info = pypi(name)
        if info:
            latest = info["info"]["version"]
            floor = "" if re.search(r">=|==|~=", spec) else f"; require it: `{name}>={latest}`"
            out.append(f"`{name}` comes from {kind} here, but a wheel installs PyPI's {latest}: check that release "
                       f"has everything this code uses (install the built wheel with `uv tool install`){floor}")
    return out


@check("installers", severity="warning", when=("python_app",), scenarios=PUB, kind="files",
       why="one command per OS to install is what turns a visitor into a user",
       procedure="release.md#one-command-install")
def installers() -> list[str]:
    return [f"no {f}: copy engine/assets/{f}" for f in ("install.sh", "install.ps1") if not (repo.root / f).exists()]


@check("installers_ci", severity="warning", when=("python_app",), scenarios=PUB, kind="files",
       why="installers break on the OS nobody ran locally",
       procedure="assets/workflows/install.yml")
def installers_ci() -> list[str]:
    if (repo.root / "install.sh").exists() and not any("install.sh" in t for t in workflow_texts().values()):
        return ["installers aren't run in CI on Linux/macOS/Windows: copy engine/assets/workflows/install.yml"]
    return []


@check("release_workflow", severity="warning", when=("python_app",), scenarios=PUB, kind="files",
       why="a tagged release with built artifacts is what the installers download",
       procedure="assets/workflows/release.yml")
def release_workflow() -> list[str]:
    if any(re.search(r"gh release create|action-gh-release|gh-action-pypi-publish", t) for t in workflow_texts().values()):
        return []
    return ["no release workflow (wheel, binaries, GitHub release): copy engine/assets/workflows/release.yml"]


def package_meta() -> tuple[str, str, str, dict | None, str]:
    """(registry, name, description, registry answer, owner hint) for pyproject.toml or package.json."""
    return _package_meta(repo.root)


@functools.cache  # one registry request per run, however many Checks ask
def _package_meta(root: object) -> tuple[str, str, str, dict | None, str]:
    if (repo.root / "pyproject.toml").exists():
        meta = pyproject().get("project", {})
        name = meta.get("name", "")
        info = http_json(f"https://pypi.org/pypi/{name}/json") if name else {}
        return "PyPI", name, meta.get("description", ""), info, json.dumps((info or {}).get("info", {}).get("project_urls") or {})
    if (repo.root / "package.json").exists():
        meta = json.loads(read("package.json"))
        name = meta.get("name", "")
        info = http_json(f"https://registry.npmjs.org/{name}") if name else {}
        return "npm", name, meta.get("description", ""), info, json.dumps((info or {}).get("repository") or {})
    return "", "", "", {}, ""


@check("package_name_taken", severity="error", scenarios=PUB, kind="registry",
       why="if the name is someone else's, `pipx/uvx/npx NAME` installs their code",
       procedure="release.md#one-command-install")
def package_name_taken() -> list[str]:
    registry_name, name, _, info, owner = package_meta()
    if not registry_name or not name:
        return []
    if info is None:
        raise Broken(f"{registry_name} `{name}`: couldn't check (offline?)")
    remote = run("git", "remote", "get-url", "origin").strip().removesuffix(".git")
    slug = "/".join(remote.replace(":", "/").split("/")[-2:]).lower() if remote else ""
    if not info or (slug and slug in owner.lower()):
        return []
    return [f"{registry_name} `{name}`: TAKEN by another project. Rename the package (the command name can stay) "
            "before telling people to install it"]


# GitHub


def gh_repo() -> dict:
    """`gh repo view` for this repo; raises Broken when gh can't answer, so no Check reads an empty answer as data."""
    return _gh_repo(repo.root)


@functools.cache  # keyed by root, so a second run in one process (tests) never sees the first repo's answer
def _gh_repo(root: object) -> dict:  # an exception is never cached, so a failed call is retried
    raw = run("gh", "repo", "view", "--json",
              "nameWithOwner,description,repositoryTopics,homepageUrl,visibility,usesCustomOpenGraphImage,"
              "defaultBranchRef,hasWikiEnabled,hasProjectsEnabled,hasDiscussionsEnabled,latestRelease,licenseInfo")
    if not raw:
        raise Broken("`gh repo view` failed (old gh, not logged in, rate limit or offline)")
    return json.loads(raw)


def gh_json(*args: str) -> object:
    """Parsed output of a `gh` call that always prints JSON on success; Broken when it printed nothing."""
    raw = run("gh", *args)
    if not raw.strip():
        raise Broken(f"`gh {args[0]} {args[1]}` failed")
    return json.loads(raw)


def context() -> list[str]:
    """Plain facts for the report header; no verdict."""
    if repo.vis == "local":
        return ["local repo, no `origin`: GitHub checks run once it exists "
                "(`gh repo create NAME --private --source .` creates and links it; ask first)"]
    try:
        r = gh_repo()
    except Broken as e:
        return [str(e)]
    topics = [t["name"] for t in r.get("repositoryTopics") or []]
    return [f"visibility: {r['visibility']}, default branch: {(r.get('defaultBranchRef') or {}).get('name', 'none')}",
            f"description ({len(r.get('description') or '')} chars): {r.get('description') or 'MISSING'}",
            f"topics ({len(topics)}): {', '.join(topics) or 'NONE'}",
            f"homepage: {r.get('homepageUrl') or 'not set'}",
            f"license: {(r.get('licenseInfo') or {}).get('name', 'NONE')}",
            f"latest release: {(r.get('latestRelease') or {}).get('tagName', 'none')}"]


@check("repo_description", severity="warning", when=("github",), scenarios=PUB, kind="gh_api",
       why="the About line is what search results and link previews show",
       procedure="seo.md#description-about")
def repo_description() -> list[str]:
    desc = gh_repo().get("description") or ""
    return ["description: MISSING"] if not desc else [f"description is {len(desc)} chars, keep it ≤ {DESC_MAX}"] if len(desc) > DESC_MAX else []


@check("description_matches_package", severity="info", when=("github",), scenarios=PUB, kind="gh_api",
       why="About, package and README pitch should say the same thing",
       procedure="seo.md#description-about")
def description_matches_package() -> list[str]:
    pkg_desc, desc = package_meta()[2], gh_repo().get("description") or ""
    if pkg_desc and pkg_desc.strip(". ").lower() != desc.strip(". ").lower():
        return [f"package description differs: {pkg_desc!r}"]
    return []


@check("repo_topics", severity="warning", when=("github",), scenarios=PUB, kind="gh_api",
       why="topics are how GitHub search and topic pages find the repo",
       procedure="seo.md#topics")
def repo_topics() -> list[str]:
    n = len(gh_repo().get("repositoryTopics") or [])
    return [f"{n} topics, add at least {TOPICS_MIN}"] if n < TOPICS_MIN else []


@check("license_detected", severity="warning", when=("github",), scenarios=PUB, kind="gh_api",
       why="without a license GitHub can detect, the code isn't open source to anyone",
       procedure="skill:github-repo")
def license_detected() -> list[str]:
    return [] if (gh_repo().get("licenseInfo") or {}).get("name") else ["GitHub detects no license"]


@check("social_preview", severity="warning", when=("github", "public"), scenarios=PUB, kind="gh_api",
       why="links shared in chats and posts show this 1280×640 image",
       procedure="seo.md#homepage-and-social-preview")
def social_preview() -> list[str]:
    if gh_repo().get("usesCustomOpenGraphImage"):
        return []
    ready = [f for f in tracked() if PREVIEW.search(f)]
    return [f"GitHub default; upload {ready[0]} (Settings → General)" if ready else
            "GitHub default; make a 1280×640 PNG and upload it"]


@check("release_notes", severity="info", when=("github",), scenarios=PUB, kind="gh_api",
       why="a release with only 'Full Changelog' tells watchers nothing",
       procedure="release.md#release")
def release_notes() -> list[str]:
    rels = gh_json("api", f"repos/{gh_repo()['nameWithOwner']}/releases?per_page=20", "--jq",
                   "[.[] | {t: .tag_name, b: (.body // \"\")}]")
    empty = [r["t"] for r in rels if EMPTY_NOTES.match(r["b"])]
    return [f"releases with empty notes (only 'Full Changelog'): {', '.join(empty)}"] if empty else []


@check("dependabot_prs_red", severity="warning", when=("github",), scenarios=BOTH, kind="gh_api",
       why="failing bot PRs pile up unnoticed and hide real breakage",
       procedure="security.md#7-github-settings-outward-facing-list-the-commands-run-after-a-yes")
def dependabot_prs_red() -> list[str]:
    prs = gh_json("pr", "list", "-R", gh_repo()["nameWithOwner"], "--author", "app/dependabot", "--state", "open",
                  "--json", "number,statusCheckRollup")
    red = [f"#{p['number']}" for p in prs
           if any(c.get("conclusion") == "FAILURE" or c.get("state") in ("FAILURE", "ERROR")
                  for c in p.get("statusCheckRollup") or [])]
    return [f"Dependabot PRs with failing checks: {', '.join(red)} (fix, close, or `ignore` the majors)"] if red else []


@check("unused_features", severity="info", when=("github",), scenarios=PUB, kind="gh_api",
       why="an empty Wiki or Projects tab reads as an abandoned repo",
       procedure="security.md#7-github-settings-outward-facing-list-the-commands-run-after-a-yes")
def unused_features() -> list[str]:
    return [f"{k} enabled (turn off if unused)" for k in ("hasWikiEnabled", "hasProjectsEnabled") if gh_repo().get(k)]


@check("discussions", severity="info", when=("github", "public"), scenarios=PUB, kind="gh_api",
       why="turn them on once people ask questions, so questions stop arriving as bugs",
       procedure="skill:github-repo")
def discussions() -> list[str]:
    return [] if gh_repo().get("hasDiscussionsEnabled") else ["discussions: off (on once people ask questions)"]


@check("private_vuln_reporting", severity="warning", when=("github", "public"), scenarios=PUB, kind="gh_api",
       why="SECURITY.md's private advisory link works only with this on",
       procedure="security.md#7-github-settings-outward-facing-list-the-commands-run-after-a-yes")
def private_vuln_reporting() -> list[str]:
    pvr = run("gh", "api", f"repos/{gh_repo()['nameWithOwner']}/private-vulnerability-reporting")
    return [] if '"enabled":true' in pvr.replace(" ", "") else ["private vulnerability reporting: off/unknown"]


def security_and_analysis(*keys: str) -> list[str]:
    sa = gh_json("api", f"repos/{gh_repo()['nameWithOwner']}", "--jq", ".security_and_analysis // {}")
    if not sa:
        raise Broken("GitHub doesn't report these for a private repo without Advanced Security; "
                     "check Settings → Code security")
    return [f"{k}: {(sa.get(k) or {}).get('status', 'not reported')}" for k in keys
            if (sa.get(k) or {}).get("status") != "enabled"]


@check("secret_scanning", severity="warning", when=("github", "public"), scenarios=PUB, kind="gh_api",
       why="push protection stops a key at `git push`, before it is public (free once public)",
       procedure="security.md#7-github-settings-outward-facing-list-the-commands-run-after-a-yes")
def secret_scanning() -> list[str]:
    return security_and_analysis("secret_scanning", "secret_scanning_push_protection")


@check("dependabot_security_updates", severity="warning", when=("github",), scenarios=PUB, kind="gh_api",
       why="security updates open a fix PR as soon as an advisory hits a dependency",
       procedure="security.md#7-github-settings-outward-facing-list-the-commands-run-after-a-yes")
def dependabot_security_updates() -> list[str]:
    return security_and_analysis("dependabot_security_updates")


@check("branch_protection", severity="warning", when=("github", "public"), scenarios=PUB, kind="gh_api",
       why="an unprotected default branch takes force-pushes and unreviewed merges",
       procedure="security.md#7-github-settings-outward-facing-list-the-commands-run-after-a-yes")
def branch_protection() -> list[str]:
    r = gh_repo()
    branch = (r.get("defaultBranchRef") or {}).get("name", "main")
    protected = run("gh", "api", f"repos/{r['nameWithOwner']}/branches/{branch}", "--jq", ".protected").strip()
    if not protected:
        raise Broken(f"`gh api` couldn't read branch `{branch}`")
    rules = run("gh", "api", f"repos/{r['nameWithOwner']}/rules/branches/{branch}", "--jq", "length").strip()
    if protected == "true" or (rules and rules != "0"):
        return []
    return [f"`{branch}` protected: {protected or 'unknown'}, branch rules: {rules or '0'}"]
