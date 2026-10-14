# Security policy

**English** | [Русский](SECURITY.ru.md)

## Reporting a vulnerability

Report it privately through [GitHub security advisories](https://github.com/octrow/octrow-skills/security/advisories/new),
not in a public issue. This is a one-person project: expect a reply within a few days. Fixes go into the latest
version only.

A confirmed vulnerability gets a fix within 30 days. The fix ships in a release, and a GitHub security advisory
then discloses the issue and credits the reporter, unless they ask not to be named.

## What the skills run on your machine

repo-publish is instructions for an agent plus two scripts. The agent runs commands with your permissions, so
read a skill before you install it, this one included.

- `scripts/preflight.py` is read-only. It runs `git`, `gitleaks` and `gh` against the repo you point it at, and
  makes read-only requests: the repo's metadata and the `action.yml` of each action its workflows use (GitHub API,
  through `gh`), and whether the package name is taken (PyPI or npm). It writes nothing and stores no keys.
- `scripts/shots.py` opens the pages listed in your spec in a headless browser (Playwright) and saves screenshots.
  Point it at your own local server.
- Anything visible to others (push, tag, release, visibility change, GitHub settings, posts) needs your explicit yes
  in the conversation; the skill says so in its working rules.

## In scope

The scripts, the files in `assets/` (workflow templates people copy into their repos), and instructions that could
make an agent leak secrets or publish something without asking.
