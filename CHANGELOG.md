# Changelog

Versions of the repo-publish plugin. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.7] - 2026-10-14

### Fixed
- Preflight no longer reports its own examples: placeholder paths (`~/work/...`), code and advice about `master`,
  agent instructions under `skills/` and CHANGELOG as missing RU mirrors. Real paths and `git push origin master`
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
