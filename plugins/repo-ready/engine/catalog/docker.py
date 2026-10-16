"""Docker stack pack: the Dockerfile, the build context and the image-publishing workflow."""
import re
import shutil
import subprocess
from pathlib import PurePosixPath

from catalog.core import workflow_texts
from registry import DOCKERFILE, Broken, check, judgement, read, repo, tracked

DEP = {"deploy"}
FROM = re.compile(r"^FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", re.I | re.M)
USER = re.compile(r"^USER\s+(\S+)", re.I | re.M)
CONTEXT_MUST_IGNORE = (".git", ".env")
LINT_TIMEOUT = 60
# a `push:` input with any value but false publishes; `[ \t]` keeps `on: push:` (value on the next line) out
PUSHES = re.compile(r"^[ \t]*push:[ \t]*(?!false\b)[^\s#]", re.M)


def dockerfiles() -> dict[str, str]:
    return {f: read(f) for f in tracked() if DOCKERFILE.search(f)}


def stages(text: str) -> list[tuple[str, str, str]]:
    """(base, name, body) of each build stage, from its FROM line to the next one."""
    marks = list(FROM.finditer(text))
    ends = [m.start() for m in marks[1:]] + [len(text)]
    return [(m.group(1), (m.group(2) or "").lower(), text[m.start():end]) for m, end in zip(marks, ends)]


def final_user(text: str) -> str:
    """The USER the final stage runs as, following `FROM <stage>` to the stage it inherits from."""
    by_name = {name: (base, body) for base, name, body in stages(text) if name}
    base, _, body = stages(text)[-1]
    for _ in range(len(by_name) + 1):  # a chain is never longer than the stages
        users = USER.findall(body)
        if users or base.lower() not in by_name:
            return users[-1] if users else ""
        base, body = by_name[base.lower()]
    return ""


@check("dockerfile_multistage", severity="info", when=("dockerfile",), scenarios=DEP, kind="files",
       why="a build stage keeps compilers, caches and source out of the image that runs",
       procedure="docker.md#multi-stage-build")
def dockerfile_multistage() -> list[str]:
    return [f"{f}: one stage" for f, t in dockerfiles().items() if len(stages(t)) < 2]


@check("dockerfile_numeric_user", severity="warning", when=("dockerfile",), scenarios=DEP, kind="files",
       why="root in the container is root on a shared kernel; a named user breaks Kubernetes runAsNonRoot",
       procedure="docker.md#runtime-stage")
def dockerfile_numeric_user() -> list[str]:
    out = []
    for f, t in dockerfiles().items():
        user = final_user(t) if stages(t) else ""
        if not user:
            out.append(f"{f}: the final stage runs as root (no USER)")
        elif not re.fullmatch(r"\d+(:\d+)?", user) or user.split(":")[0] == "0":
            out.append(f"{f}: final USER is `{user}`; use a non-zero number such as 10001:10001"
                       + (" (a build ARG can't be checked here)" if "$" in user else ""))
    return out


@check("dockerfile_base_digest", severity="warning", when=("dockerfile",), scenarios=DEP, kind="files",
       why="a tag can be moved to other content; a digest can't",
       procedure="docker.md#base-images-pinned-by-digest")
def dockerfile_base_digest() -> list[str]:
    out = []
    for f, t in dockerfiles().items():
        names = {name for _, name, _ in stages(t) if name} | {"scratch"}
        # ponytail: `FROM ${BASE}` is skipped, not resolved through its ARG default
        out += [f"{f}: FROM {base}" for base, _, _ in stages(t)
                if "@sha256:" not in base and "$" not in base and base.lower() not in names]
    return out


@check("dockerfile_healthcheck", severity="info", when=("dockerfile",), scenarios=DEP, kind="files",
       why="`docker compose --wait` and plain Docker know the service is up only from a HEALTHCHECK",
       procedure="docker.md#runtime-stage")
def dockerfile_healthcheck() -> list[str]:
    return [f"{f}: no HEALTHCHECK" for f, t in dockerfiles().items()
            if not re.search(r"^HEALTHCHECK\s+(?!NONE\b)", t, re.I | re.M)]


def ignore_patterns(dockerfile: str) -> set[str]:
    """Normalised patterns of the ignore file Docker uses for this Dockerfile (its own one first)."""
    folder = str(PurePosixPath(dockerfile).parent)
    for candidate in (f"{dockerfile}.dockerignore", f"{folder}/.dockerignore", ".dockerignore"):
        text = read(candidate.removeprefix("./"))
        if text:
            return {ln.strip().removeprefix("**/").removeprefix("/").rstrip("/") for ln in text.splitlines()}
    return set()


@check("dockerignore", severity="warning", when=("dockerfile",), scenarios=DEP, kind="files",
       why="without it the build context copies history and local secrets into a layer",
       procedure="docker.md#build-context")
def dockerignore() -> list[str]:
    out = []
    for f in dockerfiles():
        pats = ignore_patterns(f)
        if not pats:
            out.append(f"{f}: no .dockerignore")
        elif "*" not in pats:  # an allowlist (`*` then `!src`) excludes everything else
            out += [f"{f}: the ignore file doesn't exclude {p}" for p in CONTEXT_MUST_IGNORE
                    if p not in pats and f"{p}*" not in pats]
    return out


@check("dockerfile_lint", severity="info", when=("dockerfile",), scenarios=DEP, kind="files",
       why="hadolint catches unpinned packages, root steps and shell mistakes in RUN",
       procedure="docker.md#multi-stage-build")
def dockerfile_lint() -> list[str]:
    if not shutil.which("hadolint"):
        raise Broken("hadolint not installed")
    out = []
    for f in dockerfiles():
        r = subprocess.run(["hadolint", "--no-color", f], cwd=repo.root, capture_output=True, text=True,
                           timeout=LINT_TIMEOUT)
        if r.returncode not in (0, 1) or (r.stderr.strip() and not r.stdout.strip()):
            raise Broken(f"hadolint failed on {f}: {r.stderr.strip()[:200]}")
        out += r.stdout.splitlines()[:10]
    return out


judgement("migrations_outside_entrypoint", severity="warning", when=("dockerfile",), scenarios=DEP,
          question="Do schema migrations run as a separate command or job from the same image, not in the "
                   "entrypoint (where every replica would race to run them)?",
          procedure="docker.md#multi-stage-build")

judgement("health_endpoints", severity="warning", when=("dockerfile",), scenarios=DEP,
          question="Is there a `/health` with no dependencies (liveness) and a `/ready` that checks the database "
                   "and queue (readiness), with logs to stdout?",
          procedure="docker.md#health-endpoints")


# Publishing the image


def image_workflows() -> dict[str, str]:
    """Workflows that publish an image; one that only builds it (for a PR or a kind test) ships nothing."""
    return {n: t for n, t in workflow_texts().items() if "docker/build-push-action" in t and PUSHES.search(t)}


@check("image_workflow", severity="warning", when=("dockerfile", "github_actions"), scenarios=DEP, kind="files",
       why="an image built by CI from a tag is the one artifact every environment runs",
       procedure="docker.md#publishing-the-image")
def image_workflow() -> list[str]:
    return [] if image_workflows() else ["no workflow publishes the image with docker/build-push-action"]


SUPPLY_CHAIN = {"provenance": r"^[ \t]*provenance:[ \t]*(?!false\b)\S", "sbom": r"^[ \t]*sbom:[ \t]*(?!false\b)\S",
                "an attestation": r"actions/attest(-build-provenance)?@"}


@check("image_supply_chain", severity="warning", when=("dockerfile", "github_actions"), scenarios=DEP, kind="files",
       why="provenance, an SBOM and an attestation let anyone verify what built the image",
       procedure="docker.md#publishing-the-image")
def image_supply_chain() -> list[str]:
    return [f"{n}: no {what}" for n, t in image_workflows().items()
            for what, pattern in SUPPLY_CHAIN.items() if not re.search(pattern, t, re.M)]


@check("image_scan", severity="warning", when=("dockerfile", "github_actions"), scenarios=DEP, kind="files",
       why="a fixable CRITICAL in the base image ships unless something scans the built image",
       procedure="docker.md#publishing-the-image")
def image_scan() -> list[str]:
    texts = image_workflows()
    return [f"{n}: no image scan (Trivy or Grype)" for n, t in texts.items() if not re.search(r"trivy|grype", t, re.I)]


@check("image_no_cache", severity="error", when=("dockerfile", "github_actions"), scenarios=DEP, kind="files",
       why="a layer cache in a publishing workflow can be poisoned, and the poison ships in the image",
       procedure="docker.md#publishing-the-image")
def image_no_cache() -> list[str]:
    return [f"{n}: publishes with a layer cache (type=gha / actions/cache)" for n, t in image_workflows().items()
            if re.search(r"type=gha|actions/cache@", t)]
