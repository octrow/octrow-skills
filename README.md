# octrow-skills

**English** | [Русский](README.ru.md)

Agent skills for Claude Code and Claude Tag, packaged as a plugin marketplace.

| Plugin | What it does |
|---|---|
| [repo-publish](plugins/repo-publish/skills/repo-publish/SKILL.md) | Gets a repo ready for strangers to find, trust and install. A read-only preflight checks secrets and private paths in history, code provenance, the package name, broken links and skills, and GitHub metadata. Then it runs the README, EN/RU docs, GitHub SEO, screenshots, community files, CI, release and launch plan, handing parts to `github-repo`, `beautify-github-readme`, `humanizer`, `impeccable` and `security-review` when they're installed. |

## Install

Claude Code:

```bash
claude plugin marketplace add octrow/octrow-skills
claude plugin install repo-publish@octrow-skills
```

From a local clone: `claude plugin marketplace add ./octrow-skills`.

Claude Tag: an admin registers this repository (a private copy) under Organization settings → Plugins & skills →
Sync from GitHub, then adds the plugin to a bundle.

## Layout

```
.claude-plugin/marketplace.json     list of plugins
plugins/<name>/.claude-plugin/      plugin manifest
plugins/<name>/skills/<name>/       SKILL.md, references/, scripts/
evals/<name>.json                   test prompts and assertions used to tune each skill
```

Check before a commit: `claude plugin validate .`

## License

MIT
