# repo-ready

**English** | [Русский](README.ru.md)

A plugin for Claude Code and Claude Tag with four skills. Each one takes a working project to the state a goal needs.

All four start with the same read-only preflight. It lists the gaps as named Checks, each with a severity and a pointer to its fix. The skill then fixes only the parts you pick.

| Skill | Use it when | What it looks at |
|---|---|---|
| `repo-publish` | a repo is about to go public | history and secrets, install, README, CI, SEO, release |
| `repo-deploy` | a service should run as containers | Dockerfile, health endpoints, Compose, image publishing, Helm, metrics |
| `repo-code-health` | Python code is harder to change than it should be | ruff, complexity, dead code, CI for lint, tests and types |
| `repo-secure` | an app is live or about to be | authorization, trusted client input, rate limits, supply chain, logging, secrets, backups |

## Install

Claude Code:

```bash
claude plugin marketplace add octrow/octrow-skills
claude plugin install repo-ready@octrow-skills
```

Other agents (Codex, Cursor, Gemini CLI and more) via [skills](https://github.com/vercel-labs/skills):

```bash
npx skills add octrow/octrow-skills --skill repo-publish -g
npx skills add octrow/octrow-skills --skill repo-deploy -g
npx skills add octrow/octrow-skills --skill repo-code-health -g
npx skills add octrow/octrow-skills --skill repo-secure -g
```

On Windows, run `git config --global core.symlinks true` first. Each skill links in the shared `engine/` folder, and Git for Windows checks symlinks out as plain text files by default.

Then ask in a project:

- "prepare this repo for publishing"
- "add a Russian README"
- "is this service ready for Kubernetes?"
- "put it in Docker"
- "clean up the code"
- "find the dead code"
- "is my app secure?"

Requests in Russian work too.

## What the preflight finds

Every skill starts with `preflight.py --scenario publish`, `deploy`, `code-health` or `secure`. It changes nothing.

It reads the repo, its history and its GitHub settings. The code-health tools run through `uvx` without writing into the project.

An excerpt from a publish run on a test repo:

```text
## Error (blocks outward-facing steps)
- secrets_in_history: once public, history is copied and indexed; a leaked key is only safe after rotation
  - gitleaks: github-pat in config.ini at 94d0ab7f (rotate the key, then ask about a rewrite)
  fix: engine/procedures/security.md#1-secrets-in-history-not-just-head

## Warning (fix or exempt before done)
- actions_node_runtime: runners force Node 20 actions onto Node 24 with a warning; bump the major
  - actions/checkout@v4: targets node20, deprecated; bump the major
  fix: engine/procedures/security.md#8-workflow-hardening
- dependabot_cooldown: a release-day dependency update is how a hijacked package reaches you
  - dependabot.yml: no `cooldown` (wait ~7 days before proposing a release)
  fix: engine/assets/dependabot.yml

## Skipped (condition not met)
- scorecard_workflow: needs public
```

Severities:

- An error blocks every outward-facing step (visibility change, release, an install command in the README) until it is fixed.
- A warning has to be fixed or exempted before the part is done.
- Info is advice.

A Check that doesn't fit the repo is skipped with the condition it needs (no Helm chart, no Helm Checks). Or it is exempted with a reason in `.repo-ready.yml`.

For publishing it also checks:

- secrets in the whole history (gitleaks);
- private paths, employer names and author emails;
- code provenance;
- whether the package name is free on PyPI/npm;
- broken README links;
- SKILL.md frontmatter that agents can't load;
- failing Dependabot PRs;
- the repo's description, topics, social preview, branch protection, secret scanning and private vulnerability reporting.

## Publishing: repo-publish

repo-publish reads the repo and its history before anything goes public. It does the publishing work in a safe order and hands parts to other skills when they're installed.

After the preflight and a few questions (audience, right to publish, visibility, languages), it works through the phases you pick, in this order:

1. Security and history: secrets in history get rotated first, private material gets a fresh-history export, and the repo gets pre-commit and CI scanning so it stays clean.
2. Install: one command to install and one to run, with the installers tested in CI on Linux, macOS and Windows, and releases built for all three (wheel, optional standalone binaries). The package name is checked before the README tells anyone to `pipx install` it.
3. README and docs: structure via `github-repo`, length, plain language and visuals via `beautify-github-readme`, other prose via `humanizer`, EN/RU mirrors kept in sync.
4. GUI, if there is one: before/after screenshots, then refreshed README shots.
5. Community files and CI: SECURITY, CONTRIBUTING, issue forms and the workflow templates below.
6. Discoverability: description, topics, social preview, the README's first 200 words.
7. Release: version, changelog, tag, and trusted publishing to PyPI.
8. Launch, only on request: a readiness check and drafts per channel; you post them.

Anything other people can see (push, tag, release, visibility, GitHub settings, posts) waits for your yes.

A private or local-only repo gets the same run. Everything that lives in files is done now. The settings that only work once public (Scorecard, social preview, private vulnerability reporting, push protection) end up in a checklist of `gh` commands for the day you flip it.

The fixes come as ready files in [`assets/`](../../plugins/repo-ready/engine/assets):

- a pre-commit config (gitleaks, zizmor, actionlint, large-file and merge-marker checks);
- a security workflow (gitleaks over the whole history);
- OpenSSF Scorecard;
- `install.sh`/`install.ps1` installers with a CI check on three OSes;
- a release workflow (wheel, binaries for Linux/macOS/Windows, PyPI via trusted publishing, build provenance);
- Dependabot with a cooldown.

Actions are pinned to commit SHAs, and every file passes zizmor and actionlint. [repo-scout](https://github.com/octrow/repo-scout) uses all of them, filled in for a real Python app.

## Deploy readiness: repo-deploy

`/repo-ready:repo-deploy` gets a service ready to run as containers, or on one VPS behind Caddy or nginx with TLS.

Its preflight (`--scenario deploy`) checks:

- the Dockerfile (multi-stage, a numeric non-root user, base images by digest, `.dockerignore`);
- Compose (database and queue ports bound to 127.0.0.1);
- the image workflow (provenance, SBOM, attestation, a scan, no layer cache);
- a Helm chart (Pod Security `restricted`, probes, `helm test`, a kind smoke test in CI).

The procedures come from taking [buy-smarter](https://github.com/octrow/buy-smarter) from a CLI to a chart, and that repo passes every check.

The skill builds the image and brings the stack up for real before it calls a part done. Pushing an image or deploying waits for your yes.

## Code health: repo-code-health

`/repo-ready:repo-code-health` cleans up a Python codebase and wires CI so it stays that way. It needs [uv](https://docs.astral.sh/uv/).

Its preflight (`--scenario code-health`) runs these through `uvx`, without installing anything in the project or writing into it:

- ruff (lint and format);
- radon (cyclomatic complexity);
- complexipy (cognitive complexity);
- vulture (dead code).

It also checks that CI runs the linter, the tests and a type checker. Thresholds are the tools' defaults unless `pyproject.toml` sets its own.

Fixes go in this order: format in a commit of its own, lint, dead code, then complex functions one per commit and only where tests cover them.

## Application security: repo-secure

`/repo-ready:repo-secure` audits a live or nearly live app for the mistakes that burn shipped, often AI-written, apps, in the order breaches happen:

1. authorization (IDOR, private by default, row-level security);
2. trusting the client (prices, roles, owner ids);
3. rate limits on login, signup, email and LLM endpoints;
4. the supply chain (a lockfile, Dependabot, an audit step in CI);
5. security logging;
6. secrets, including keys in `NEXT_PUBLIC_`/`VITE_` variables the bundler ships to browsers;
7. backups with a rehearsed restore.

Its preflight (`--scenario secure`) proves what a file search can. The rest becomes questions with evidence: every route that takes a record id, the rate limiter and backup tooling it found.

Each fix comes with a test that failed before it (user A reads user B's record and gets 404). The rest of OWASP goes to `security-review`.
