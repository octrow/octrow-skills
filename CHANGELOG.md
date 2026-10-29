# Changelog

Versions of the repo-ready plugin (named repo-publish up to 0.4.0). Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Marketplace: `python-logging` plugin 0.1.0 with the `python-logging` skill. It sets up, fixes or improves logging
  in a Python project: a disk budget for all logs with size rotation and a start-up prune, wide events, secret
  redaction (by value, library loggers and tracebacks included), journald-friendly one-line records, and tests that
  prove the cap. Templates in `assets/`, a read-only audit in `scripts/log_audit.py`, evals in
  `evals/python-logging.json`.
- Marketplace: `llm-call-audit` plugin 0.1.0 with the `llm-call-audit` skill. It audits every model call in a
  codebase and recommends, per call site, the cheapest option that keeps quality: plain code, a TypeSafe/Jev
  classifier, a cheaper or stronger LLM, context cuts and gateway route fixes, measured from app logs, the LLM cache
  and gateway logs. Read-only report by default. A Jev cheat-sheet and a worked example in `references/`, evals in
  `evals/llm-call-audit.json`.
- Marketplace: `logic-map` plugin 0.1.0 with the `logic-map` skill. It writes, updates or checks a project's
  `docs/logic-map.md`: an agent-first map under 500 lines of where the main flow splits, what each step decides,
  what changes without the optional dependency, how it fails and which module does it, with Known gaps linked to a
  numbered findings plan. A map template and a sync-test recipe in `references/`, trigger evals and two eval cases
  in `evals/logic-map/`.
- Marketplace: `qt-ui` plugin 0.1.0 with the `qt-ui` skill. Fast, house-style visual fixes for a PySide6 / PyQt6
  desktop GUI: offscreen screenshots of every screen in both themes, a defect list, fixes through theme tokens and
  QSS that copy the neighbour screen, a before/after pixel diff in `scripts/shotdiff.py`, and a screenshot-script
  recipe with the blind spots seen in real runs in `references/`.
- CI workflow `tests.yml`: the preflight tests and the python-logging template tests run on every push and PR.

### Changed
- `private_paths_in_files` and `private_paths_in_history` treat `~/projects/<name>` as the placeholder for example
  paths, so evals and docs that use it aren't reported.

### Fixed
- `preflight.py --help` and `log_audit.py --help` print the usage instead of auditing a folder named `--help`;
  `log_audit.py` stops on a path that is not a directory instead of reporting an empty audit.

## [0.10.1] - 2026-10-17

### Added
- Evals `evals/repo-deploy.json` and `evals/repo-code-health.json`: one case that changes a project and one
  read-only assessment for each skill.

### Changed
- repo-deploy lists every judgement answer by id with a line of evidence and its file.
- repo-code-health answers "what first?" in the order of its parts (format before refactoring), and says when it
  used ruff's unsafe fixes.

## [0.10.0] - 2026-10-17

### Added
- `repo-code-health` skill (`/repo-ready:repo-code-health`), the code-health Scenario for Python projects: lint
  and format, dead code, complexity, CI wiring. Its preflight runs `--scenario code-health`.
- Stack pack `catalog/python_quality.py` with 8 Checks: `ruff_clean`, `ruff_format`, `complexity_cyclomatic`
  (radon), `complexity_cognitive` (complexipy), `dead_code` (vulture, 80%+ confidence unless `[tool.vulture]` sets
  it), `linter_in_ci`, `tests_in_ci`, `type_checker`. The tools run through `uvx` and write nothing into the
  audited repo; without `uvx` they report broken. Project thresholds in `pyproject.toml` win over the defaults.
- Procedure `python-quality.md`: what each tool finds, how to fix it, where the project sets its threshold, and
  when an exemption fits.

### Changed
- `tracked()` reads `git ls-files -z`, so files with non-ASCII names reach the Checks.
- An empty Judgement section in the report says `- none`, like the severity sections.

## [0.9.0] - 2026-10-16

### Added
- `repo-deploy` skill (`/repo-ready:repo-deploy`), the deploy Scenario: Dockerfile, health endpoints, Compose,
  image publishing, Helm with a kind smoke test, observability. Its preflight runs `--scenario deploy`.
- Stack packs `catalog/docker.py`, `compose.py`, `helm.py`, `observability.py` with 24 Checks (16 mechanical, 8
  judgement), applied by the new Repo facts `dockerfile`, `compose`, `helm_chart` and `metrics`; procedures
  `docker.md`, `compose.md`, `helm.md`, `observability.md` from the buy-smarter playbook.
- Secrets, `.gitignore` and CI-hardening Checks from core run in both Scenarios.

## [0.8.0] - 2026-10-16

### Changed
- The preflight, the Check catalog, the procedures (formerly `references/`) and the templates (`assets/`) move to
  `plugins/repo-ready/engine/`, shared by every Scenario skill through an `engine/` symlink in the skill. The
  Claude Code plugin keeps the link; `npx skills add` copies the folder in its place. On Windows, `npx` needs
  `git config --global core.symlinks true` (README).
- Every Check points at an exact section (`security.md#8-workflow-hardening`), and registration fails when the
  heading doesn't exist; the report prints the path from the skill folder (`engine/procedures/...`).

### Fixed
- A pointer to a section that never existed (`#fresh-history-export`) and a duplicated line in `security.md`.
- `language_mirrors` treats everything under `plugins/` as agent material (EN only), like `skills/`.

## [0.7.0] - 2026-10-16

### Added
- Seven judgement Checks that used to live only as prose in SKILL.md: `third_party_code`, `code_security_review`,
  `first_run`, `readme_claims_real`, `readme_plain_language`, `readme_visual_story`, `gui_screenshots_fresh`. The
  preflight lists them with their severity and fix, so the agent answers them in every run, and the skill counts
  each answer in the scorecard like a mechanical Check.

## [0.6.0] - 2026-10-16

### Changed
- The preflight is a catalog of named Checks (`scripts/catalog/core.py`, model in `scripts/registry.py`). Each has
  an id, a severity, the Repo facts it needs, a one-line why and a `fix:` pointer. The report groups failures by
  severity: **error** blocks every outward-facing step, and an error-level Check that couldn't run (no gitleaks)
  blocks too. Then judgement questions for the agent, exemptions, skipped Checks with the condition they need
  (`needs public` is the flip checklist), and the ids that passed. `--scenario publish` runs one Scenario.
- Without gitleaks, the weak history grep finding nothing is reported as broken, not as clean.

### Added
- `.repo-ready.yml` in the audited repo excuses a Check: `exempt:` then `  check_id: reason`. A missing reason or an
  unknown id is an error, so a typo never exempts silently.
- `dependabot_security_updates` Check on private repos too (it was only reported together with secret scanning).
- `tests/test_preflight.py` (stdlib unittest): registry rules and a run on a throwaway repo.

### Fixed
- A Check that hits an unexpected error (an old `gh`, a rate limit, a malformed `pyproject.toml`) is reported as
  broken instead of ending the run with a traceback; a failed `gh repo view` no longer reads as "no description,
  no topics, no license".
- Importing the catalog doesn't leave `__pycache__` in an audited repo that contains the skill.

## [0.5.0] - 2026-10-16

### Changed
- The plugin is renamed `repo-publish` → `repo-ready`, to hold more scenarios than publishing (deploy readiness
  next). The skill keeps its name: `/repo-ready:repo-publish`. Reinstall with
  `claude plugin install repo-ready@octrow-skills`; the marketplace's `renames` map moves an existing `repo-publish`
  install over (fixed in 0.7.0). No behavior change.

## [0.4.0] - 2026-10-15

### Added
- Private and local-only repos get a full run: the preflight names the mode (`local`, `private`, `public`), holds back
  checks that only apply once public (Scorecard, social preview, Discussions, private vulnerability reporting), and
  warns when macOS/Windows jobs eat a private repo's free Actions minutes. The skill ends such a run with a flip
  checklist of `gh` commands.
- `assets/pre-commit-config.yaml` adds `pre-commit-hooks` checks: files over 1 MB, merge markers, case-clashing
  names, broken YAML/TOML. No auto-fixers, so the first run on an old repo doesn't rewrite it.

## [0.3.3] - 2026-10-15

### Fixed
- GitHub settings commands (`references/security.md` §7) turn on Dependabot alerts before security updates;
  without them GitHub answers 422.

## [0.3.2] - 2026-10-14

### Changed
- Launch (Phase 8) is opt-in: no channel plan or post/article drafts (Reddit, Habr, Product Hunt, Medium, dev.to)
  unless the user asks for them.

## [0.3.1] - 2026-10-14

### Added
- Preflight lists dependencies taken from git, path or url in `[tool.uv.sources]`: a built wheel installs them from
  PyPI by name, so it reports a name missing from PyPI and the PyPI version the wheel would get, and suggests a
  minimum version when the dependency has none.

### Changed
- First run: files the app writes for the user go to per-user dirs, never the folder it runs from.

### Fixed
- `release.yml` no longer fails in a private personal repo: build provenance is skipped until the repo is public
  (GitHub stores attestations only for public repos there).
- A README heading "Why not …" / "Почему не …" counts as the alternatives section.

## [0.3.0] - 2026-10-14

### Added
- `assets/install.sh` and `assets/install.ps1`: one-command installers for Python + uv apps (wheel from the latest
  GitHub release; `--version`, `--main`, `--uninstall`), with marked spots for project-specific first-run steps.
- `assets/workflows/install.yml`: runs both installers on Linux, macOS and Windows against the current commit.
- Preflight reports a Python app with a command but no installer or release workflow.
- Phase 3 asks before running `beautify-github-readme` on `README.md` and `README.ru.md`.
- Existing installers and release workflows are diffed against the templates; only the missing pieces are proposed.

### Changed
- `assets/workflows/release-pypi.yml` is now `assets/workflows/release.yml`: tests and a tag-matches-version check,
  then wheel, sdist and optional PyInstaller binaries (Linux x86_64/arm64, macOS arm64, Windows), optional PyPI and
  one GitHub release with every file attested.

## [0.2.7] - 2026-10-14

### Fixed
- Preflight no longer reports its own examples: placeholder paths (`~/work/...`), code and advice about `master`,
  agent instructions under `skills/` and CHANGELOG as missing RU mirrors, and `master` in CHANGELOG. Real paths and `git push origin master`
  are still reported.

### Changed
- Agent instructions (`SKILL.md`, references) and CHANGELOG stay English-only; RU mirrors are for files people read.

## [0.2.6] - 2026-10-14

### Added
- Preflight reports open Dependabot PRs with failing checks and a `dependabot.yml` without `cooldown`.
- `assets/dependabot.yml`: a commented `ignore` for major versions, for apps tied to a framework's peer ranges.
- Rule: check a claim copied from another README or blog on a real run before repeating it.

## [0.2.5] - 2026-10-14

### Added
- How to install `beautify-github-readme`; its attribution and showcase PR wait for the user's yes.

## [0.2.4] - 2026-10-14

### Changed
- Launch metrics no longer rely on star-history charts: since 2026-06-30 only admins and collaborators can list a
  repo's stargazers. Stars and traffic come from `gh api`, with a snapshot before the 14-day traffic window closes.

## [0.2.3] - 2026-10-14

### Added
- Contributor on-ramp in phase 5: `good first issue`, Discussions with a Q&A link; no stale bot for solo projects.

## [0.2.2] - 2026-10-14

### Added
- Code review items for LLM tools and web apps (LLM output in shell or SQL, client-side secrets, SSRF, typosquatting).
- One workflow per purpose; length of README and docs follows the reader.

## [0.2.1] - 2026-10-14

### Fixed
- Node 20 actions are reported as deprecated (runners force them onto Node 24), not as broken.

## [0.2.0] - 2026-10-14

### Added
- `assets/`: pre-commit (gitleaks, zizmor, actionlint), `security.yml` (gitleaks over the whole history), OpenSSF
  Scorecard, PyPI release with trusted publishing and build provenance, Dependabot with cooldown. Actions pinned to
  commit SHAs.
- Preflight: Node 20 actions, tag-pinned third-party actions, no secret scan in CI or pre-commit, no Scorecard,
  secret scanning and push protection status, `.gitignore` gaps with the github/gitignore template to add.
- Docs: continuous secret scanning, workflow hardening, Scorecard, token-free publishing, release-please.

## [0.1.0] - 2026-10-13

### Added
- repo-publish: read-only preflight and phases for security, install, README, GUI, community files and CI, SEO,
  release and launch.
