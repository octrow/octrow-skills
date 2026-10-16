---
name: repo-deploy
description: >
  Get a project ready to run as containers: a hardened multi-stage Dockerfile, a Compose stack that comes up
  healthy, an image published to GHCR with provenance, SBOM and a scan, a Helm chart under Pod Security
  `restricted` with a kind smoke test in CI, and metrics that won't melt the backend. Use whenever the user wants
  to "подготовить к деплою", "контейнеризировать", "завернуть в Docker", add or review a Dockerfile, docker
  compose, a Helm chart or Kubernetes manifests, publish an image, or asks whether a service is ready for
  production. Runs a read-only preflight first and fixes only the parts the user picks.
---

# Repo deploy

Take a working service to an image that any environment can run the same way, and to a chart a hardened cluster
admits. Read-only first: the preflight finds the gaps, the user picks the parts, then each part closes its gaps
with the procedure the preflight points to.

## Phase 0: preflight and scope

```bash
python3 <skill-dir>/engine/preflight.py [project-path] --scenario deploy
```

The report groups failed and broken Checks by severity, each with a `fix:` path from this skill's folder
(`engine/procedures/<topic>.md#<section>` or `engine/assets/...`). **error** blocks every outward-facing step
(pushing an image, a release, a deploy) until fixed; a broken error-level Check blocks the same way. **warning**
must be fixed or exempted before the part is done; **info** is advice. Judgement questions are Checks you answer
by reading the code; count each as passed or failed at its severity, with one line of evidence. A Check that
doesn't fit gets an exemption in `.repo-ready.yml` (`exempt:` then `  check_id: reason`), after the user agrees.
Skipped Checks name the fact they need: no `helm_chart`, no Helm part.

Then ask only what the code can't tell, with a recommendation each: where it runs (a VPS with Compose, Kubernetes,
both), the registry (GHCR by default), and which parts to do. Default: every part with findings.

## Parts, in this order

The order follows dependencies: a chart needs an image, an image needs a Dockerfile, probes need health endpoints.

1. **Dockerfile** (`docker.md`): multi-stage build, numeric non-root user, base images by digest,
   `.dockerignore`, HEALTHCHECK, migrations as their own command.
2. **Health endpoints** (`docker.md#health-endpoints`): liveness without dependencies, readiness that checks them.
3. **Compose** (`compose.md`): the whole stack with one `docker compose up -d --build --wait`; infrastructure ports
   on 127.0.0.1.
4. **Image publishing** (`docker.md#publishing-the-image`): a workflow on main and tags, provenance, SBOM,
   attestation, a scan that fails on fixable CRITICAL, no layer cache.
5. **Helm and kind** (`helm.md`): chart contents, Pod Security `restricted`, probes, a smoke test in a clean kind
   cluster, and CI that runs it.
6. **Observability** (`observability.md`): one `instrument_app`, low-cardinality labels, probes excluded.

Each part ends with its "Done when" from the procedure, run for real: build the image, bring the stack up, run the
smoke test. A part isn't done on a green unit test; containers are checked by running them.

## Working rules

- **Read-only until scoped.** The preflight changes nothing; edits start after the user picks the parts.
- **Check locally before CI.** Build the image, bring the stack up, run kind; only what passed locally goes to CI.
  Run local stacks under their own `COMPOSE_PROJECT_NAME` and end with `down -v`, so the user's dev stack is untouched.
- **Pin what you add.** Actions by commit SHA with the version in a comment, images by digest, versions at least
  two weeks old; tools for local checks (kind, kubeconform) go to a scratch folder with a checksum, not the system.
- **Outward-facing needs a yes.** Pushing an image, making a package public, a release tag and a deploy each wait
  for the user's explicit yes.
- **Targets are decisions.** If a goal misses (image 335 MB against a 300 MB target), say so with the options;
  change the target only when the user decides, and write down why.
- **Commit by part**, `<type>: <description>`, staging only that part's files; after a push, check that CI went
  green and read the logs of the key steps, not just the badge.

## Report format

End each part with a short report in the user's language:

```
## <Part>
Before → after: <one line per change, with file paths>
Verified: <image size, `id -u`, compose healthy, smoke test, CI run>
Not done: <skipped items and why>
Next step: <recommendation>
```

At the start, after the preflight, give a scorecard: one row per part, status (ok / gaps / not applicable), and
the top finding for each.
