# Container image: Dockerfile and publishing

Worked through on a Python + uv service (octrow/buy-smarter: `Dockerfile`, `.github/workflows/image.yml`). Other
stacks keep the shape: a build stage with the toolchain, a runtime stage with only what runs.

## Multi-stage build

1. **Builder**: slim base + git + uv copied from `ghcr.io/astral-sh/uv:<ver>@<digest>`. Install dependencies first
   (`uv sync --locked --no-dev --no-editable --no-install-project` with a bind mount of `pyproject.toml`/`uv.lock` and
   a cache mount), then `COPY src` and a second `uv sync`. `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`. Editing
   `src/` must leave the dependency layer `CACHED`.
2. **Runtime**: only `.venv` plus what runs (migrations config, `alembic/`). A variant (a browser, a GPU build) is
   `FROM runtime AS <variant>`, not a copy of the whole file.
3. Migrations are not in the entrypoint: they run as a separate command from the same image.

Done when: `docker image ls` shows a size you chose on purpose, `<cli> --help` runs in the container, and `hadolint`
is clean.

Pitfalls: heavy optional parts (Playwright's 131 MB Node driver) go to the variant stage only; `--only-shell`
(headless shell) instead of full Chromium saves ~400 MB.

## Runtime stage

- `USER 10001:10001`, by number. A name (`USER app`) breaks Kubernetes `runAsNonRoot`: the kubelet can't verify a
  name. A root step in a variant is `USER 0`, then back to the number.
- `HEALTHCHECK` without curl in slim images: `python -c "import urllib.request; ..."`. A worker that serves no HTTP
  API overrides it (check its `/metrics` instead).
- `VOLUME` for caches, OCI labels (`org.opencontainers.image.source`, `.version` from `ARG VERSION`).

Done when: `id -u` in the container prints 10001 and `docker inspect` shows `healthy`.

## Base images pinned by digest

`FROM image:tag@sha256:<digest>`: a tag can be moved to other content, a digest can't. Get it with
`docker inspect --format '{{index .RepoDigests 0}}' <image>` after a pull. Pick a version at least two weeks old and
check the image's incident history first (Trivy's tags were replaced in March 2026, visible as duplicate releases).
Dependabot (`package-ecosystem: docker`) keeps digests current.

## Build context

`.dockerignore`: `.git`, `.venv`, `.env*` (except `.env.example`), `tests`, `docs`, `assets`, caches. Without it the
build context ships the repo's history and local secrets into a layer.

Done when: `docker run --rm <image> ls -a /app` shows no `.env` and no `.git`.

## Publishing the image

A separate workflow on `push: main` and `tags: v*`; pull requests only build (a job in `ci.yml`).

1. `permissions: {}` at the top; on the job `contents: read, packages: write, id-token: write, attestations: write`;
   log in with `GITHUB_TOKEN`.
2. `docker/metadata-action`: `type=sha,prefix=sha-`, `type=ref,event=branch`, semver `{{version}}` and
   `{{major}}.{{minor}}`, `latest` only on tags. A matrix over targets (`runtime`, `browser` with a suffix).
3. `docker/build-push-action` with `provenance: mode=max`, `sbom: true`, `build-args: VERSION=<meta.version>`.
4. `actions/attest-build-provenance` with `push-to-registry: true`.
5. A vulnerability scan (Trivy run as an image pinned by digest): print HIGH, fail on fixable CRITICAL
   (`--ignore-unfixed --exit-code 1`). Run it locally before turning it on, so the first release doesn't go red.
6. No layer cache (`cache-from: type=gha`, `actions/cache`) in a workflow that publishes: a poisoned cache ships in
   the image.

Done when: an anonymous `docker pull` works (the package is public), `gh attestation verify oci://<image> -R <repo>`
passes, the SBOM shows in `docker buildx imagetools inspect --format '{{json .SBOM}}'`, and a tag produces `X.Y.Z`,
`X.Y` and `latest`.

Pitfalls: a network failure at the GHCR login (`context deadline exceeded`) is not the code:
`gh run rerun <id> --failed`.

## Health endpoints

Before any orchestrator: `/health` with no dependencies (liveness), `/ready` that checks the database and the queue
(readiness), logs to stdout, the version read from package metadata. Liveness that checks the database restarts
every pod when the database blinks.
