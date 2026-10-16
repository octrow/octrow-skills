---
name: repo-publish
description: >
  Get a repo ready for strangers to find, trust and install: use whenever the user wants to "облагородить
  репозиторий", "подготовить к публикации", make a project public or open-source it, make it "look like a real
  open source project", asks what's missing because the repo has few or no stars, or is about to release or
  announce it (Show HN, Reddit, Habr, awesome lists). Also for a private or local-only repo the user wants
  prepared as far as it goes before (or without) going public. Runs a read-only preflight (secrets and private paths in
  history, code provenance, package name, broken links and skills, GitHub metadata), then orchestrates
  github-repo, beautify-github-readme, humanizer, impeccable and security-review for README, EN/RU docs,
  SEO (description, topics, social preview), screenshots, community files, CI, install and release.
  Use it even when the user names only a few of these parts together, e.g. README + topics + RU translation.
---

# Repo publish

Take a working project to a public repo that a stranger can find, trust, install and run in a few minutes.
This skill is the conductor: it decides the order, runs a read-only audit, and hands each part to the
skill that does it best. It does the glue work itself (bilingual sync, screenshots, SEO metadata, release).

The order matters. Security comes before visibility, because once a repo is public its history is
copied and indexed. Install comes before README, because the README's quick start has to describe
an install path that actually works. Screenshots come after GUI changes, so they don't go stale the same day.

## Narrow request? Do just that part

"Refresh the screenshots", "add a Russian README", "fix the topics": skip the interview and the scorecard, go
straight to the matching phase, and start by checking whether it's already done. Commit dates are a hint
(screenshots committed after the last GUI change); the proof is re-doing the work and comparing (for screenshots,
a pixel diff). Already done: say so with the evidence, leave the files untouched, and stop; a no-op is a fine
answer. Mention other preflight findings in one line at the end, at most.

## Audit-only request ("what's missing?")

Run the preflight, read what it can't check (README story, demo, alternatives, launch readiness), and answer with
the scorecard plus a ranked list of gaps, each with its fix and effort. Skip the per-phase report blocks. Small
fixes that are local, obviously safe and reversible (a broken SKILL.md frontmatter, a missing `permissions:`)
may be made in the working tree and listed; anything visible to others waits for a yes.

## Already public?

Then Phase 1 is damage control, not prevention: a leaked secret is rotated now, private material in history is a
judgement call with the user (rewriting a public repo's history breaks forks). The rest applies as is.

## Private or local repo?

"Prepare it as far as it goes" for a private or local-only repo is a full run, not a lighter one: everything that
lives in files gets done now, so going public later is a settings change, not a project. The preflight header names
the mode (`repo: local` = no `origin`, `private`, `public`); Checks that only apply once public are listed as
skipped with `needs public`.

- **Do in full:** Phase 1 (cheapest now: history that never left the machine can be rewritten without breaking
  anyone's clone; a secret that left it still gets rotated), Phase 2, Phase 3 with its mirror, Phase 4, the Phase 5
  files (community files, `.pre-commit-config.yaml`, `dependabot.yml`, `security.yml`, `install.yml`, `release.yml`),
  CHANGELOG, and the description and keywords in `pyproject.toml`/`package.json` so About and topics can copy them.
- **Adapt:** the installers download from GitHub releases, which need auth while the repo is private; test them with
  `INSTALL_SOURCE=<local wheel>` and keep the README's one-line install as is. macOS and Windows runners use a
  private repo's free minutes several times faster than Linux, so run 3-OS jobs on tags or `workflow_dispatch`
  until public. `release.yml` already skips attestations while private.
- **Local only:** all of the above in the working tree. Creating the GitHub repo
  (`gh repo create NAME --private --source .`) and pushing are outward-facing: ask first.
- **Deferred until the flip** (scorecard status "deferred", not "gaps"; the preflight's `needs public` list): `scorecard.yml`, social preview upload,
  private vulnerability reporting, secret scanning and push protection, Discussions, branch protection (GitHub Free
  protects branches only on public repos), Phase 6 beyond the text, Phase 8. End the run with these as a flip
  checklist: the exact `gh` commands in order (`references/security.md` §7), visibility change first, each after a yes.

## Phase 0: scope (one short exchange)

Run the preflight first; it answers most questions without bothering the user:

```bash
python3 <skill-dir>/scripts/preflight.py [project-path] --scenario publish [--private employer,client,internal-name]
```

It prints a read-only report of named Checks (catalog in `scripts/catalog/`): history and secrets, private paths
and provenance, community files and mirrors, README links and story, SKILL.md frontmatter, CI hardening, install
and release, the package name on PyPI/npm, and GitHub metadata and settings. Failed and broken Checks come grouped
by severity, each with its finding lines and a `fix:` pointer (a reference section, an asset, or a skill):
**error** blocks every outward-facing step (visibility change, release, an install command in the README) until
fixed; a broken error-level Check (it couldn't run, e.g. no gitleaks) blocks the same way. **warning** must be fixed
or exempted before the phase is done; **info** is advice. Then judgement questions for you to answer by reading the
repo, exemptions, skipped Checks with the condition they need, and the ids that passed. A Check that doesn't fit
this repo gets an exemption in `.repo-ready.yml` (`exempt:` then `  check_id: reason`), after the user agrees.
If the user mentioned an employer or client, pass its names with `--private`.

Then ask only what the repo can't tell you, in the user's language, with a recommendation for each:
- **Audience and pitch**: who is this for, in one sentence? (Offer a draft from the code and README.)
- **Provenance** (ask whenever the code may come from a job, client or another project): does the user have the
  right to publish it, under which license? This blocks anything public; recommend staying private until
  answered. Local preparation in the working tree (README, license file, cleanup) can go on meanwhile, since it
  publishes nothing.
- **Visibility**: stays private for now, or goes public in this session? Changing visibility is outward-facing;
  never flip it without an explicit yes.
- **Languages**: which is primary on GitHub (usually EN for reach) and which mirrors exist (e.g. RU).
- **Parts**: show the phase list below with what the preflight found and let the user pick. Default: all
  phases that have findings, except Phase 8 (launch posts and articles), which runs only when the user asks for it.

## Phase 1: security and history hygiene

Read `references/security.md`. Short version: scan the whole history for secrets (not just HEAD), make sure
`.env` and local data are ignored, check licenses of vendored or ported code (`THIRD_PARTY_NOTICES.md`),
keep heavy data out of the package. Renaming the default branch to `main` changes the remote and breaks
existing clones' tracking, so propose it and do it after a yes. Delegate a code-level review to
`security-review` (or the `code-reviewer` agent) when the project handles keys, user input, subprocesses or files.

Then keep it clean: `assets/pre-commit-config.yaml` (gitleaks, zizmor, actionlint, plus checks for large files,
merge markers, case clashes and broken YAML/TOML; no auto-fixers, so the first run doesn't rewrite the repo) and
`assets/workflows/security.yml` (gitleaks over the whole history in CI), push protection after the visibility flip
(`references/security.md`, "Keep scanning after launch").

A secret found in history means rotate first, then rewrite history; rotation is the part that actually helps.
Tell the user; don't rewrite history without asking.

Private paths (`/home/<user>`, `~/work/...`), employer or client names, internal project names and work emails are
not secrets to a scanner, but they publish more than the user intends. Clean the files; for history, and for a
project that lives in a monorepo subfolder, recommend exporting it as its own repo with fresh history
(`references/security.md`, "Fresh-history export"). Internal working files (session prompts, plans, scratch notes)
either move out or get published on purpose: ask which.

## Phase 2: install, first run, releases

Read `references/release.md`. The goal is one command per OS to install and one to run, keys optional where
possible, and a `doctor`/`config` step that tells the user what is missing in plain words. Test the installers in CI
on Linux, macOS and Windows; installers break on the platform nobody ran locally (legacy code pages on Windows,
missing PATH entries).

Python + uv apps start from the templates rather than from scratch: `assets/install.sh` and `assets/install.ps1`
(uv, then the wheel from the latest GitHub release; `--version`, `--main`, `--uninstall`), `assets/workflows/install.yml`
(runs both installers on three OSes against the current commit) and `assets/workflows/release.yml` (tag → tests →
wheel, sdist, optional PyInstaller binaries for Linux x86_64/arm64, macOS arm64 and Windows → optional PyPI → one
attested GitHub release). Fill the placeholders (`OWNER/REPO`, `PKG`, `CMD`, `PKG_DIR`), then adapt or delete each
`# PROJECT:` block; https://github.com/octrow/repo-scout has every block filled in. Ask whether the project needs
standalone binaries: yes by default for GUI and heavy apps, no for a plain CLI (the wheel already installs in one
command on every OS). Other stacks: no template; follow the same shape.
Installers or a release workflow already there? Don't overwrite them: diff each against its template and list only
what's missing (options like `--uninstall`, the CI run on three OSes, the tag-matches-version check, attestation),
then add those pieces after a yes.

Before the README tells anyone to `pipx install`, `uvx` or `npx` the package, the name has to be ours on the
registry (preflight checks it). A name taken by someone else means those commands install their code: a confusing
first run and a supply-chain risk. Rename the distribution (the command can keep its name) or install from the
GitHub release only, and say so in the README.

## Phase 3: README

1. **Structure and facts**: `github-repo` skill (audit + README recipe). Keep every fact from the old README;
   check every relative link.
2. **Visual story**: `beautify-github-readme` skill (hero, proof image, badges). Use real output from the project
   (a real run, real numbers) rather than invented claims. Ask the user first whether to run it on `README.md` and
   its mirror `README.ru.md` (recommend yes for a repo going public); on a yes, run it on both so the mirror gets the
   same hero and assets. It asks README-mode vs asset-only and pure SVG vs hybrid; pass the answers you already
   have (whole README, pure SVG unless the user wants otherwise) so it doesn't stall.
   Its last step offers an attribution line and a showcase PR to its author's repo: both are optional and
   outward-facing, so they wait for the user's yes like any other post. Not installed:
   `npx skills add oil-oil/beautify-github-readme -g` (MIT; kept as a separate skill so it stays current).
   Sub-skill not in the skill list? It may be installed per project (`<repo>/.agents/skills/<name>`); read its
   SKILL.md from there, or apply the reference files here, and say which you did.
3. **Plain language**: `humanizer` skill on README and other prose. Prose should read like the author wrote it.
4. **SEO pass on the opening**: `references/seo.md`, "README opening" section.
5. **Mirror**: `references/bilingual.md`.

## Phase 4: GUI (if the project has one)

Read `references/gui.md`. Delegate the design work to `impeccable` (critique, polish, audit) or, for NiceGUI
projects on the shared kit, `nicegui-kit-gui`. The rule that came from real use: compare against the screenshots
already in the README before changing a look, and show before/after. A "best practice" is a hypothesis, and the
user may like what they have better. Then refresh the README screenshots with `scripts/shots.py`, at the same file
names, sizes and device scale, so the README needs no edits.

## Phase 5: community files and CI

`github-repo` skill covers the files: LICENSE, CONTRIBUTING, SECURITY (private advisory link), CODE_OF_CONDUCT
(Contributor Covenant 2.1), YAML issue forms with `config.yml`, PR template, Dependabot, CI with tests and lint.
Each prose file gets its mirror (`references/bilingual.md`).

CI files come from `assets/` rather than being written from scratch: `dependabot.yml`, `workflows/security.yml`,
`workflows/scorecard.yml` (public repos) and `pre-commit-config.yaml`. Actions in them are pinned to commit SHAs
with the version in a comment; adapt the details (package ecosystem, branch), keep the hardening
(`references/security.md`, §8–9). Lint the result before committing:
`uvx zizmor .github/workflows && uvx --from actionlint-py actionlint`. Settings that live on GitHub, not in files:
private vulnerability reporting, secret scanning and push protection, branch protection or a ruleset on `main`,
unused Wiki/Projects off.
These are account settings changes; list the exact `gh` commands and run them only after a yes.

Contributor on-ramp, after launch rather than on day one: open 2–3 real, small issues labelled `good first issue`
(GitHub creates the label; such issues show up on `github.com/OWNER/REPO/contribute` and in GitHub's
newcomer search). Turn on Discussions (`gh repo edit --enable-discussions`) once people ask questions, and point
`ISSUE_TEMPLATE/config.yml` `contact_links` at its Q&A category so questions stop arriving as bugs. Skip for a solo
project: a stale bot (it closes valid reports and reads as an unmaintained repo), milestones, and a docs site
(MkDocs, Docusaurus) until the README no longer fits on a few screens.

## Phase 6: discoverability (SEO)

Read `references/seo.md`. Description, topics, homepage, social preview image, README opening, release cadence.
The social preview can't be set via API; generate the 1280×640 PNG and tell the user where to upload it.
No buying stars, no star-for-star rings, no fake accounts: that breaks GitHub's terms, the burst shows on any
star chart, and stars vanish when GitHub removes the accounts.

## Phase 7: release

Python package: start from `assets/workflows/release.yml` (one workflow for wheel, binaries, PyPI and the GitHub
release). Going to PyPI: set up trusted publishing first, so no API token is ever stored (`references/release.md`, "Publishing without tokens"). Then bump the version, update CHANGELOG/release notes from `git log <last-tag>..HEAD`, tag, push the tag, and wait
for the release workflow to go green before announcing. Check the built artifacts' size (sdist excludes) and that the
README's install commands point at the new release.

## Phase 8: launch (opt-in; advice and drafts, the user posts)

Off by default: no channel plan, post or article drafts (Reddit, Habr, Product Hunt, Medium, dev.to, HN, etc.)
unless the user asks for a launch or for posts. Otherwise end with one line offering it.

Stars come from people seeing the project, not from files: a day-old repo with a perfect README still has zero.
Read `references/launch.md`: a readiness gate (install works on a clean machine, a 10–20 s demo GIF, README answers
"why not just X"), then a plan per channel with drafts written for the Phase 0 audience, and how to measure.
Drafting posts is fine; posting anything, opening PRs to awesome lists or messaging people needs a yes per item.

## Working rules

- **Read-only until scoped.** The audit and preflight change nothing. Edits start after the user picks the parts.
- **Branch, then commit by part.** If on the default branch, create a feature branch. One commit per part with
  `<type>: <description>` (docs:, feat:, chore:, ci:, fix:). Commit, merge, push, tag and release only when asked;
  after a push, check that CI went green.
- **Preserve unrelated changes.** Stage only the files of the current part; the working tree often holds the
  user's own work in progress.
- **Check before you repeat.** A claim from another README, changelog or blog post ("X stopped working",
  "Y is free") gets checked on a real run or API call before it lands in a report or a doc; vendors overstate.
- **Don't invent.** No made-up adoption numbers, benchmarks, testimonials or compatibility claims. Every number
  in the README should come from a real run, test or release.
- **Visual changes need a before/after.** Show screenshots side by side and let the user choose; save the
  user's stated taste as memory (e.g. dense tables, one value per column) so later passes respect it.
- **Length follows the reader.** README, docs and reports cover what a stranger needs to install, trust and use
  the project; no filler sections, repeated summaries or boilerplate a small project doesn't have.
- **Mirrors stay in sync.** Any change to an EN prose file lands in its RU mirror in the same commit, and the
  other way round.
- **Missing sub-skill?** Do the part inline using the reference file, and say which skill would have helped
  (and how to install it, e.g. `npx skills add jdevalk/skills --skill github-repo`).

## Report format

End each phase with a short report in the user's language:

```
## <Phase>
Before → after: <one line per change, with file paths>
Verified: <tests, links, CI run, screenshots compared>
Not done: <skipped items and why>
Next step: <recommendation>
```

(Labels translated to the user's language, e.g. Было → стало / Проверено / Не сделано / Следующий шаг.)

At the start (after preflight), give a scorecard: one row per phase, status (ok / gaps / deferred until public / not applicable), and the
top finding for each.
