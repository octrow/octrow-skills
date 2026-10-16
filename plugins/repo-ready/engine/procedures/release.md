# Install, first run, releases

## One-command install

- Linux/macOS: `curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/install.sh | sh`
- Windows: `irm https://raw.githubusercontent.com/OWNER/REPO/main/install.ps1 | iex`
- Also show the "review first" variant (download, read, run) for people who don't pipe to a shell.
- The installer: checks prerequisites and says how to get each one, installs into the user's space (no sudo),
  prints the exact command to start and the full path if PATH isn't updated yet.
- Python tools: `uv tool install` of the wheel attached to the GitHub release (works with or without PyPI, and
  with a package name someone else holds there); a standalone binary per OS for GUI and heavy apps.
- Templates: `engine/assets/install.sh`, `engine/assets/install.ps1` (Python + uv; filled-in example: octrow/repo-scout).
  Options go in as flags for `sh -s --` and as environment variables for `irm | iex`, which can't pass arguments.

## First run

- Works without optional API keys; features that need a key say so and degrade, not crash.
- A `doctor`/`config` command checks the environment and fills the config interactively, in plain words, with
  where to get each key and what it's for.
- Error messages say what to do next, not a traceback.
- Everything the app writes for the user (reports, logs, caches, keys, saved sessions) goes to per-user dirs
  (`~/.config/<app>`, `~/.cache/<app>`, `~/.local/share/<app>`), never the folder it runs from: after a
  `uv tool install` that folder is the user's home or a project of theirs. Settings read the user config `.env`
  too, so an installed app has a place for keys. Check by running the installed command in an empty folder and
  listing it afterwards. Tests that write files point these dirs at a tmp path.

## CI for the install path

- Run the installers on `ubuntu-latest`, `macos-latest`, `windows-latest` (`engine/assets/workflows/install.yml`), then run
  the installed command once (`--help` or `doctor`). `INSTALL_SOURCE` points the installer at the checked-out commit,
  so CI tests the change instead of the last release.
- Windows pitfalls seen in practice: legacy console code pages crash on non-ASCII output (reconfigure stdout to
  UTF-8 with `errors="replace"`), PATH not refreshed in the same session.

## Release

1. `git log <last-tag>..HEAD --oneline` → release notes grouped by feat/fix/docs; user-facing wording.
2. Bump the version in the package metadata (and lock file if it records it).
3. Commit `chore: release X.Y.Z`, tag `vX.Y.Z`, push commit and tag (only when asked).
4. The release workflow builds artifacts (sdist, wheel, binaries) and attaches them; wait for green, then check
   the release page lists them and the sizes are sane.
5. README install commands and badges point at `releases/latest`, so they don't need edits per release.
6. Default branch `main`; replace `master` everywhere (docs, prompts, workflows, badges) when renaming.

## Publishing without tokens, with provenance

`engine/assets/workflows/release.yml` is the Python shape: tag `vX.Y.Z` → tests and a tag-matches-version check → wheel,
sdist and optional binaries → PyPI (optional) + GitHub release with every file attested. A push to `main` that
changes the workflow runs it as a build-only dry run. Binaries: PyInstaller on `ubuntu-22.04` (old glibc, wide reach),
`ubuntu-22.04-arm`, `macos-latest` (arm64) and `windows-latest`, each smoke-tested with `--help`; Intel Macs use the
wheel. Dependencies with data files or native libraries need `--collect-all <pkg>`. Other stacks have no template:
keep the same shape (build once, attest, one release).

- **Trusted publishing (OIDC)**: PyPI trusts this repo's workflow directly, so there's no `PYPI_API_TOKEN` to leak
  or rotate. One-time setup on PyPI → project → Publishing (a "pending publisher" for a name not yet on PyPI):
  owner, repo, workflow file name, environment `pypi`. npm has the same (`npm publish --provenance` with
  `id-token: write`, plus a trusted publisher on npmjs.com).
- **Build provenance**: `actions/attest-build-provenance` signs which commit and workflow built each file;
  users check with `gh attestation verify dist/<file> -R OWNER/REPO`. Attestations need a public repo (a private personal repo
  gets "Feature not available"); the template skips the step while the repo is private. PyPI also gets PEP 740 attestations from
  the publish action. Say so in SECURITY.md, it's what a careful installer looks for.
- Build in one job, publish in others that only download the artifact; the publish job gets `id-token: write`
  and nothing else, behind the `pypi` environment (add required reviewers there for a manual gate).

## Automated changelog (optional)

For a project with regular releases, `googleapis/release-please-action` (v5) replaces steps 1–3: it reads
conventional commits on `main`, keeps a "release PR" with the version bump and CHANGELOG, and tags on merge.
Worth it from the third or fourth release; before that the manual steps above are less to set up and explain.

## Agent skills (SKILL.md)

An agent loads a skill only from valid frontmatter: `---` on the first line, then `name:` and `description:`, then
`---`. A value with `: ` in it needs quotes or `>`, or the YAML breaks and the skill silently disappears. A language
switcher line goes below the frontmatter, never above it.
