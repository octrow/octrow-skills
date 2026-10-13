# octrow-skills

**English** | [Русский](README.ru.md)

Agent skills for Claude Code and Claude Tag, packaged as a plugin marketplace. The main one, repo-publish,
takes a working project to a public GitHub repo that a stranger can find, trust and install: it checks the
history for secrets and private data before anything goes public, then sets up CI hardening, the README,
docs, GitHub SEO and the release.

| Plugin | What it does |
|---|---|
| [repo-publish](plugins/repo-publish/skills/repo-publish/SKILL.md) | A read-only preflight, then the publishing work in a safe order: security and history, install path, README and EN/RU docs, screenshots, community files and CI, discoverability, release, launch plan. Hands parts to `github-repo`, `beautify-github-readme`, `humanizer`, `impeccable` and `security-review` when they're installed. |

## What the preflight finds

It changes nothing; it reads the repo, its history and its GitHub settings. An excerpt from a run on a test repo:

```text
## .gitignore
- not ignored: .env, .env.local, .venv/x, dist/x.whl, x.egg-info/PKG-INFO
- append the template: gh api gitignore/templates/Python --jq .source >> .gitignore

## CI workflows
- ci.yml: no top-level `permissions:` (default token may be read-write)
- third-party actions pinned by tag, not SHA: softprops/action-gh-release@v2 (zizmor flags these)
- actions/checkout@v4: targets node20, deprecated (forced onto Node 24 with a warning); bump the major
- dependabot.yml: no `cooldown` (wait ~7 days before proposing a release; assets/dependabot.yml)
```

Also checked: secrets in the whole history (gitleaks), private paths, employer names and author emails,
code provenance, whether the package name is free on PyPI/npm, broken README links, SKILL.md frontmatter
that agents can't load, failing Dependabot PRs, and the repo's description, topics, social preview, branch
protection, secret scanning and private vulnerability reporting.

The fixes come as ready files in [`assets/`](plugins/repo-publish/skills/repo-publish/assets): a pre-commit
config (gitleaks, zizmor, actionlint), a security workflow (gitleaks over the whole history), OpenSSF
Scorecard, a PyPI release with trusted publishing and build provenance, and Dependabot with a cooldown. Actions
are pinned to commit SHAs, and every file passes zizmor and actionlint.

## Install

Claude Code:

```bash
claude plugin marketplace add octrow/octrow-skills
claude plugin install repo-publish@octrow-skills
```

From a local clone: `claude plugin marketplace add ./octrow-skills`.

Claude Tag: an admin registers this repository under Organization settings → Plugins & skills → Sync from
GitHub, then adds the plugin to a bundle.

Then ask in a project: "prepare this repo for publishing", "what's missing before I open-source this?", or
just one part: "add a Russian README", "refresh the screenshots".

## How it differs from similar skills

- [github-repo](https://github.com/jdevalk/skills) audits and writes the README, community health files,
  templates and metadata. repo-publish calls it for that part and adds what comes before and after: history and
  secrets, provenance, install path, CI hardening, release and launch.
- [beautify-github-readme](https://github.com/oil-oil/beautify-github-readme) redesigns the README's visual
  story (hero, proof images, SVG). repo-publish uses it in the README phase.
- [github-morestar-skill](https://github.com/everest-an/github-morestar-skill) focuses on growth: positioning
  and a launch day across channels. repo-publish plans a launch too, but only after the repo is safe to
  publish and installs on a clean machine.

## Layout

```
.claude-plugin/marketplace.json     list of plugins
plugins/<name>/.claude-plugin/      plugin manifest
plugins/<name>/skills/<name>/       SKILL.md, references/, scripts/, assets/
evals/<name>.json                   test prompts and assertions used to tune each skill
```

Check before a commit: `claude plugin validate .` Changes per version: [CHANGELOG.md](CHANGELOG.md).

## License

MIT
