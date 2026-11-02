# Changelog

Versions of the repo-ready plugin (named repo-publish up to 0.4.0). Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `lean-spec` 0.4.0: pattern C, capacity and limits over time. The model is the code's transitions with time as
  data; claims are counting bounds (per window, any W seconds, per day, no lockout) written first as `def Claim`,
  with faults as a term in the bound and replica interleavings in a separate op-level model; the real config gives
  the report's capacity table as `decide` corollaries. Tests control the fake store's clock and add a load test of
  a simulated day. Piloted on a Redis fixed-window limiter: 11 theorems (login ≤ 969 guesses per IP per day),
  7/8 mutants (the survivor equivalent). The proof loop gains the potential-function pattern, setup covers tests
  that need Postgres, and the patterns table is one table again; the example gate test skips without bwrap.

### Fixed
- `lean-spec` 0.3.4: pattern E measures first (one real request end to end, then the target's "before" numbers)
  and writes a missing fast path before the differential tests and mutants that need it (finding #12). The target
  rule refuses IO itself but sends logic that reacts to IO to pattern S, in the step, the description and map mode
  (finding #2). The optional Stop hook lets a repeated stop through (`stop_hook_active`) and shows the gate's last
  20 lines, so a gate that can never pass can't trap Claude (finding #11).
- `lean-spec` 0.3.3: hypothesis goes into the repo's own test dependencies whatever the tooling, so the repo's CI
  no longer fails collecting the oracle test; the `--no-project` command is for the standalone example only
  (finding #8). Pattern S: a claim found false while proving flips to `¬ Claim` in Props and Frozen together,
  proved by its witness, as the one statement change a pre-approval allows; each claim is a named `def` so the flip
  touches one line (finding #10).
- `lean-spec` 0.3.2: the template copy now builds right away: `Spec.lean` and `Oracle.lean` drop the Feed imports,
  the oracle's `answer` is a stub until the oracle step, and `comparator.json` starts empty (finding #9). Freezing
  keeps library imports (Mathlib, Std) at the top of `Frozen.lean` instead of dropping them (finding #13).
- `lean-spec` 0.3.1: a second target no longer unfreezes the first. With `lean/` already in the repo the skill adds
  the target next to it (own `Spec/<Target>/`, appended Frozen block and names, a tagged oracle branch) instead of
  copying the template, and preflight says so. The gate now fails when `comparator.json` and `Frozen.lean` name
  different theorems, the report counts only listed theorems as proved, and the function the oracle calls must
  appear in a listed theorem. Findings #7 and #1 of the skill's new logic map (`plugins/lean-spec/docs/`).

### Added
- `lean-spec` 0.3.0: pattern S, a state machine under a fault model. The environment is one finite list of events,
  the model is the code's transition function, and the requirements are safety claims and the promises in
  docstrings; a false claim is `theorem claim_false : ¬ Claim` with a witness that becomes the strict-xfail pin.
  Piloted on a draft retry loop with provider fallback: 9 theorems proved (bounded attempts, no target twice, one
  failure record on the decisive attempt only), two docstring claims refuted, 11/11 mutants caught. The skill gains
  S strategies and mutants for Hypothesis, the proof structure for event-list machines, and three Lean 4.35 errors
  (a shared `match` matcher fails `lake comparator`, inaccessible names, `dropLast_cons₂`).
- `lean-spec` 0.2.1: lessons from a proved speed-up of finance-insights' cross-bank transfer pairs (78x at 1,000
  rows, 615x at 6,200, 965x at 12,000, `fast_eq_spec` with no hypothesis, list equality with order). Pattern E
  gains the case with no hypothesis, where the bucket key is part of the match condition. The proof loop gains the
  "emit the pairs, then sort into the loop's order" pattern and three Lean 4.35 errors (`matches` is a keyword,
  a leftover `if false = true`, implicit `bne_comm`). Strategies cover maps where keys share a value, the skill
  asks for absolute paths, and the example's oracle tests skip when lake is missing.
- `lean-spec` 0.2.0: lessons from a proved speed-up of buy-smarter's cross-source dedupe (2.2x at 50 items, 74x at
  178, 526x at 962, `fast_eq_spec` for any same-product test whose matches share a key). Pattern E gains the case
  where the condition is a property of a predicate: no runtime guard, a property test instead, said in the report.
  The skill now asks for before/after timings at real and small sizes, adds index and stale-cache mutants with
  near-copy inputs and pinned examples, lets several targets share one oracle by a tag, sends a predicate the code
  computes to the oracle as a matrix, explains what a `Proved:` line claims for a fast path in map mode, and the
  proof loop gains the simulation pattern for two folds.
- Marketplace: `lean-spec` plugin 0.1.0 with the `lean-spec` skill. It checks one piece of logic against a Lean 4
  model, or proves a fast path equal to it: approved and frozen statements (`Frozen.lean`, `lake comparator`),
  proofs in Lean core without Mathlib, the model as a long-lived oracle for Hypothesis differential tests that
  compare whole values, a required mutation check, and for a fast path `fast_eq_spec` under an invariant with a
  runtime check and fallback. Map mode takes the rules of a `docs/logic-map.md` step: theorems quote their map
  lines, findings go where "Known gaps" points, pinned counterexamples with strict xfail keep the gate green, and
  the step gets a `Proved:` line. One gate: `lake build`, a grep for what the kernel cannot see (`implemented_by`
  passes the comparator), `lake comparator`, tests. A worked example in `example/` doubles as the template;
  `scripts/preflight.py`; references on patterns, the proof loop, cheats, setup, map mode and known findings; a
  test in `tests/test_lean_spec.py`; evals in `evals/lean-spec/`.
- `repo-secure` skill and the `secure` Scenario: an application security audit in the order breaches happen.
  A new `catalog/appsec.py` pack adds mechanical Checks (`client_bundle_secrets` for secrets in
  `NEXT_PUBLIC_`/`VITE_`/`REACT_APP_` variables, `lockfile_committed`, `dependency_updates`, `vuln_audit_ci`) and
  judgement Checks with evidence (`authz_per_object` lists every route that takes a record id, `authz_default_deny`,
  `server_trusts_client`, `rate_limits`, `security_logging`, `backups_restorable`). The secret, history and
  supply-chain Checks of `publish`/`deploy` run in `secure` too. New repo facts `web_app` and `database`; procedure
  `procedures/appsec.md`; evals in `evals/repo-secure.json`.
- `repo-deploy`: a "One VPS" part (`procedures/vps.md`): a hardened server, the app or Compose stack under systemd
  on 127.0.0.1, Caddy (or nginx + certbot) for TLS, a domain, and a Done-when that reboots the box.
- Marketplace: `system-design` plugin 0.1.0 with the `system-design` skill. It designs or reviews a backend's
  architecture from numbers: requirements, napkin math from `scripts/napkin.py` (RPS, app servers, cache memory,
  DB reads and writes, replicas, shards, storage, egress, and a verdict naming the scaling rung), the smallest rung
  of a seven-step scaling ladder, storage engine and cache pattern by access pattern, failure plan and trade-offs.
  References in `references/`, a test in `tests/test_napkin.py`, evals in `evals/system-design.json` and
  `evals/system-design/`.
- `qt-ui` 0.3.0: a bare run works the project's open-defects list before any new audit, with a "left on purpose"
  list beside it so known Qt limits are not reported again; reference screenshots get a name map and never show the
  user's own data. `references/qt-pitfalls.md` gains form labels pinned above their field, a capped status that
  stretches the button beside it, and thumbnails of different widths.
- `qt-ui` 0.2.0: `references/qt-pitfalls.md` (Qt quirks that look like design defects, and process traps:
  piped pytest, shared models, a shared git index); the skill also shoots the maximised window on a large screen.
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
  recipe with the blind spots seen in real runs and the UX laws, typography and grid rules translated for Qt
  in `references/`.
- Marketplace: `qt-app` plugin 0.1.0 with the `qt-app` skill, the builder paired with `qt-ui`. It adds a PySide6
  desktop GUI to a Python project or a new screen to an existing Qt app: checks how the core is called in-process,
  runs it through `CoreRunner` (an asyncio loop in a worker thread, Qt signals back, cancel and shutdown), scaffolds
  the `gui` extra, a `<app> gui` command, a sidebar window and an own light/dark token theme from a runnable template
  in `scripts/template/` (13 offscreen tests), builds screens test-first in parity with the CLI, and hands
  screenshots of both themes to `qt-ui`. The bridge, scaffold, screen, packaging guides and the pitfalls seen in real
  apps in `references/`; eval cases in `evals/qt-app/`.
- CI workflow `tests.yml`: the preflight tests and the python-logging template tests run on every push and PR.

### Changed
- `private_paths_in_files` and `private_paths_in_history` treat `~/projects/<name>` as the placeholder for example
  paths, so evals and docs that use it aren't reported.

### Fixed
- `repo-code-health`: the list of files ruff checks was cached for the whole process, so a second audit in one
  process (the test suite) ran radon, complexipy and vulture on the first repo's files and found nothing. The
  cache is now keyed by the project root.
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
