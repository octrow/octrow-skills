"""Application security pack: the handful of mistakes that burn shipped (often AI-written) web apps.

Mechanical Checks catch what a file search can prove: a secret in a variable the bundler ships to browsers, no
lockfile, nothing proposing dependency updates or auditing them. Authorization, trust in client input, rate
limits, security logging and restorable backups need a reader; their judgement questions come with evidence the
pack collects (routes that take a record id, limiter libraries, backup tooling found in the repo).
"""
import re

from catalog.core import capped, ci_text
from registry import check, judgement, read, repo, run, tracked

SEC = {"secure"}
WEB = ("web_app",)
# a variable the bundler inlines into client code, named like a secret. TOKEN and API_KEY are left out on purpose:
# most of those in client env files are public by design (maps, search, analytics) or not keys at all (TOKEN_TTL)
CLIENT_SECRET = (r"\b(NEXT_PUBLIC|VITE|REACT_APP|EXPO_PUBLIC|NUXT_PUBLIC|GATSBY|PUBLIC)_[A-Z0-9_]*"
                 r"(SECRET|PRIVATE|PASSWORD|SERVICE_ROLE)[A-Z0-9_]*")
PUBLIC_BY_DESIGN = re.compile(r"PUBLIC_KEY|SITE_KEY")
MANIFESTS = {"pyproject.toml", "requirements.txt", "package.json"}
PY_LOCKS = re.compile(r"^(uv\.lock|poetry\.lock|pdm\.lock|Pipfile\.lock|requirements[^/]*\.lock)$")
NODE_LOCKS = re.compile(r"^(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?)$")
UPDATE_BOTS = (".github/dependabot.yml", ".github/dependabot.yaml", "renovate.json", "renovate.json5",
               ".renovaterc", ".renovaterc.json", ".github/renovate.json")
AUDIT_TOOLS = re.compile(r"pip-audit|uv audit|safety check|osv-scanner|\b(npm|pnpm|yarn|bun) audit|trivy|grype|"
                         r"snyk|dependency-review-action")
# routes whose path carries a record id: FastAPI/Flask `{id}` `<id>`, Express `/:id`
# the path literal starts with `/`, so `requests.get("https://...{id}")` and `d.get("{")` are not routes
ID_ROUTE = r"""\.(get|post|put|patch|delete|route|api_route)\(\s*['"`]/[^'"`]*(\{|/:|<)"""
NEXT_ID_ROUTE = re.compile(r"\[[^/]+\]/(.+/)?route\.[jt]sx?$|(^|/)pages/api/(.+/)?\[[^/]+\]")
LIMITERS = (r"slowapi|fastapi[-_]limiter|flask[-_]limiter|django[-_]ratelimit|throttle_classes|"
            r"express-rate-limit|rate-limiter-flexible|@upstash/ratelimit|limit_req_zone|rate_limit")
ERROR_TRACKERS = r"sentry|rollbar|bugsnag|honeybadger|opentelemetry|datadog|newrelic|posthog"
BACKUP_TOOLS = r"pg_dump|pg_basebackup|pgbackrest|wal-g|barman|litestream|restic|borg |mysqldump|mongodump"
NOT_LOCKFILES = (":(exclude)*.lock", ":(exclude)*lock.json", ":(exclude)*-lock.yaml", ":(exclude)*.lockb")


def grep(pattern: str) -> list[str]:
    """`file:line content` for tracked text files matching an extended regex (git grep, case-insensitive)."""
    out = run("git", "grep", "-znIiE", pattern, "--", ".", *NOT_LOCKFILES)  # -z: file\0line\0text, any file name
    return [f"{f}:{n} {text.strip()[:100]}" for f, n, text in
            (ln.split("\0", 2) for ln in out.splitlines() if ln.count("\0") >= 2)]


# Mechanical Checks


@check("client_bundle_secrets", severity="error", scenarios=SEC, kind="files",
       why="a secret in a NEXT_PUBLIC_/VITE_/REACT_APP_ variable is shipped to every visitor's browser",
       procedure="appsec.md#6-secrets")
def client_bundle_secrets() -> list[str]:
    out = run("git", "grep", "-nIoE", CLIENT_SECRET)
    hits = {}
    for ln in out.splitlines():
        place, _, name = ln.rpartition(":")
        if not PUBLIC_BY_DESIGN.search(name):
            hits.setdefault(name, place)
    return capped([f"{name} ({place}): move it server-side and rotate it" for name, place in hits.items()])


@check("lockfile_committed", severity="warning", scenarios=SEC, kind="files",
       why="without a lockfile every install resolves fresh versions, so a hijacked release lands on the next deploy",
       procedure="appsec.md#4-supply-chain")
def lockfile_committed() -> list[str]:
    names = set(tracked())  # paths from the project root: a lock in a subfolder belongs to another project
    out = []
    if ({"pyproject.toml", "requirements.txt"} & names and not any(PY_LOCKS.match(f) for f in names)
            and not requirements_pinned()):
        out.append("Python: no uv.lock / poetry.lock beside pyproject.toml, and requirements.txt is not fully pinned")
    if "package.json" in names and not any(NODE_LOCKS.match(f) for f in names):
        out.append("Node: no package-lock.json / pnpm-lock.yaml / yarn.lock beside package.json")
    return out


def requirements_pinned() -> bool:
    reqs = [ln.split("#")[0].strip() for ln in read("requirements.txt").splitlines()]
    reqs = [r for r in reqs if r and not r.startswith("-")]
    return bool(reqs) and all("==" in r for r in reqs)


@check("dependency_updates", severity="warning", scenarios=SEC, kind="files",
       why="nobody notices a vulnerable dependency unless a bot proposes the fix",
       procedure="assets/dependabot.yml")
def dependency_updates() -> list[str]:
    nothing_to_update = not has_manifests() and not top_ci_text()  # a bot also bumps pinned actions
    if nothing_to_update or any((repo.top / f).is_file() for f in UPDATE_BOTS):
        return []
    return ["no Dependabot or Renovate config"]


@check("vuln_audit_ci", severity="warning", scenarios=SEC, kind="files",
       why="a known-vulnerable dependency should fail CI, not wait for someone to read an advisory",
       procedure="appsec.md#4-supply-chain")
def vuln_audit_ci() -> list[str]:
    if not has_manifests() or AUDIT_TOOLS.search(ci_text() + top_ci_text()):
        return []
    return ["no pip-audit / npm audit / osv-scanner step in CI"]


def has_manifests() -> bool:
    """Whether the project declares dependencies at all; a stdlib-only tool has nothing to lock or audit."""
    return bool(MANIFESTS & set(tracked()))


def top_ci_text() -> str:
    """Workflows live at the top of the git repo, also when the audited project is a subfolder of it."""
    return "".join(wf.read_text(encoding="utf-8") for wf in (repo.top / ".github/workflows").glob("*.y*ml"))


# Judgement Checks


def id_routes() -> list[str]:
    nxt = [f"{f} (route with an id segment)" for f in tracked() if NEXT_ID_ROUTE.search(f)]
    return capped(grep(ID_ROUTE) + nxt) or ["no route with an id in its path found; check ids taken from bodies"]


def found(pattern: str, none: str) -> list[str]:
    """The first hit in each file: enough to show where the thing lives."""
    first = {}
    for hit in grep(pattern):
        first.setdefault(hit.split(":", 1)[0], hit)
    return capped(list(first.values()), 5) or [none]


judgement("authz_per_object", severity="error", when=WEB, scenarios=SEC,
          question="Does every route that reads or changes one record (an id in the path, query or body) check, "
                   "server-side, that the caller owns that record or holds the role for it, not only that they are "
                   "logged in? Test it: as user A, request user B's id.",
          procedure="appsec.md#1-authorization", evidence=id_routes)

judgement("authz_default_deny", severity="warning", when=WEB, scenarios=SEC,
          question="Are routes private by default (auth on the app or router, or middleware) with public routes "
                   "listed on purpose, and admin routes behind a role check? With Supabase or Firebase: is row-level "
                   "security / are security rules on for every table the client can reach?",
          procedure="appsec.md#1-authorization")

judgement("server_trusts_client", severity="error", when=WEB, scenarios=SEC,
          question="Does the server validate every input with a schema (types, lengths, ranges, enums) and compute "
                   "or look up prices, totals, roles, owner ids and flags itself, ignoring them when a client sends "
                   "them? Client-side checks are UX, not security.",
          procedure="appsec.md#2-never-trust-the-client")

judgement("rate_limits", severity="warning", when=WEB, scenarios=SEC,
          question="Are login, signup, password reset, OTP / magic links, anything that sends email or SMS, and "
                   "anything that costs money per call (LLM, paid APIs) limited per IP and per account, with a 429?",
          procedure="appsec.md#3-rate-limiting",
          evidence=lambda: found(LIMITERS, "no rate limiter library or config found in the repo"))

judgement("security_logging", severity="warning", when=WEB, scenarios=SEC,
          question="Are failed logins, permission denials, rate-limit hits and admin actions logged with user id, "
                   "IP and request id, and never passwords, tokens or full personal data? Do errors reach a tracker "
                   "or an alert that wakes someone?",
          procedure="appsec.md#5-security-logging-and-monitoring",
          evidence=lambda: found(ERROR_TRACKERS, "no error tracker or telemetry library found"))

judgement("backups_restorable", severity="warning", when=("database",), scenarios=SEC,
          question="Is the database backed up automatically, encrypted, to another provider or account than the "
                   "one that runs it? When was a restore last rehearsed? Can a bad deploy be rolled back in minutes?",
          procedure="appsec.md#7-backups-and-recovery",
          evidence=lambda: found(BACKUP_TOOLS, "no backup tooling in the repo (it may live on the host or in a "
                                               "managed DB: ask)"))
