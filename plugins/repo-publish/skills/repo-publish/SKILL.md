---
name: repo-publish
description: >
  Get a repo ready for strangers to find, trust and install: use whenever the user wants to "облагородить
  репозиторий", "подготовить к публикации", make a project public or open-source it, make it "look like a real
  open source project", asks what's missing because the repo has few or no stars, or is about to release or
  announce it (Show HN, Reddit, Habr, awesome lists). Runs a read-only preflight (secrets and private paths in
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

## Phase 0: scope (one short exchange)

Run the preflight first; it answers most questions without bothering the user:

```bash
python3 <skill-dir>/scripts/preflight.py [project-path] [--private employer,client,internal-name]
```

It prints a read-only report: missing community files and language mirrors, secret-looking and
internal-looking tracked files (prompts, plans, agent folders), a gitleaks scan of history (when installed),
private paths and names in files and history, author emails, monorepo subfolder status, broken or
project-escaping README links, SKILL.md frontmatter that agents can't load, workflows without `permissions:`,
actions still on Node 20 (deprecated; runners force them onto Node 24 with a warning), tag-pinned third-party actions, no secret scan
in CI or pre-commit, no Scorecard,
whether the package name is free on PyPI/npm, and GitHub metadata (description vs package description, topics,
social preview, empty release notes, branch protection, private vulnerability reporting, secret scanning and push
protection).
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
  phases that have findings.

## Phase 1: security and history hygiene

Read `references/security.md`. Short version: scan the whole history for secrets (not just HEAD), make sure
`.env` and local data are ignored, check licenses of vendored or ported code (`THIRD_PARTY_NOTICES.md`),
keep heavy data out of the package. Renaming the default branch to `main` changes the remote and breaks
existing clones' tracking, so propose it and do it after a yes. Delegate a code-level review to
`security-review` (or the `code-reviewer` agent) when the project handles keys, user input, subprocesses or files.

Then keep it clean: `assets/pre-commit-config.yaml` (gitleaks, zizmor, actionlint) and
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

Before the README tells anyone to `pipx install`, `uvx` or `npx` the package, the name has to be ours on the
registry (preflight checks it). A name taken by someone else means those commands install their code: a confusing
first run and a supply-chain risk. Rename the distribution (the command can keep its name) or install from the
GitHub release only, and say so in the README.

## Phase 3: README

1. **Structure and facts**: `github-repo` skill (audit + README recipe). Keep every fact from the old README;
   check every relative link.
2. **Visual story**: `beautify-github-readme` skill (hero, proof image, badges). Use real output from the project
   (a real run, real numbers) rather than invented claims. It asks README-mode vs asset-only and pure SVG vs
   hybrid; pass the answers you already have (whole README, pure SVG unless the user wants otherwise) so it
   doesn't stall.
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
No buying stars, no star-for-star rings, no fake accounts: that breaks GitHub's terms, and public fake-star
detectors flag the pattern.

## Phase 7: release

Python package going to PyPI: set up trusted publishing with `assets/workflows/release-pypi.yml` first, so no
API token is ever stored (`references/release.md`, "Publishing without tokens"). Then bump the version, update CHANGELOG/release notes from `git log <last-tag>..HEAD`, tag, push the tag, and wait
for the release workflow to go green before announcing. Check the built artifacts' size (sdist excludes) and that the
README's install commands point at the new release.

## Phase 8: launch (advice and drafts; the user posts)

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

At the start (after preflight), give a scorecard: one row per phase, status (ok / gaps / not applicable), and the
top finding for each.
