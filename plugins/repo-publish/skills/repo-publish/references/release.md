# Install, first run, releases

## One-command install

- Linux/macOS: `curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/install.sh | sh`
- Windows: `irm https://raw.githubusercontent.com/OWNER/REPO/main/install.ps1 | iex`
- Also show the "review first" variant (download, read, run) for people who don't pipe to a shell.
- The installer: checks prerequisites and says how to get each one, installs into the user's space (no sudo),
  prints the exact command to start and the full path if PATH isn't updated yet.
- Python tools: `uv tool install` or `pipx install` from the release; a standalone binary per OS for people
  without Python.

## First run

- Works without optional API keys; features that need a key say so and degrade, not crash.
- A `doctor`/`config` command checks the environment and fills the config interactively, in plain words, with
  where to get each key and what it's for.
- Error messages say what to do next, not a traceback.

## CI for the install path

- Run the installers on `ubuntu-latest`, `macos-latest`, `windows-latest` (install workflow), then run the
  installed command once (`--version` or `doctor`).
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

`assets/workflows/release-pypi.yml` is the Python shape: tag `vX.Y.Z` → build once → attest → PyPI + GitHub release.

- **Trusted publishing (OIDC)**: PyPI trusts this repo's workflow directly, so there's no `PYPI_API_TOKEN` to leak
  or rotate. One-time setup on PyPI → project → Publishing (a "pending publisher" for a name not yet on PyPI):
  owner, repo, workflow file name, environment `pypi`. npm has the same (`npm publish --provenance` with
  `id-token: write`, plus a trusted publisher on npmjs.com).
- **Build provenance**: `actions/attest-build-provenance` signs which commit and workflow built each file;
  users check with `gh attestation verify dist/<file> -R OWNER/REPO`. PyPI also gets PEP 740 attestations from
  the publish action. Say so in SECURITY.md, it's what a careful installer looks for.
- Build in one job, publish in others that only download the artifact; the publish job gets `id-token: write`
  and nothing else, behind the `pypi` environment (add required reviewers there for a manual gate).

## Automated changelog (optional)

For a project with regular releases, `googleapis/release-please-action` (v5) replaces steps 1–3: it reads
conventional commits on `main`, keeps a "release PR" with the version bump and CHANGELOG, and tags on merge.
Worth it from the third or fourth release; before that the manual steps above are less to set up and explain.

