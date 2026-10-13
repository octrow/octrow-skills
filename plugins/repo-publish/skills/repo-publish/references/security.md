# Security and history hygiene before going public

Once a repo is public, its whole history is cloned, mirrored and scanned by secret-harvesting bots within
minutes. Fix what's below while it's still private.

## 1. Secrets in history (not just HEAD)

The preflight runs gitleaks itself when it's installed. By hand:

```bash
gitleaks detect --source . --redact -v                    # whole history; works on old and new gitleaks
gitleaks detect --source . --redact --log-opts="-- sub/"  # one folder of a monorepo
trufflehog git file://. --only-verified
```

(`gitleaks git` exists only in 8.19+; distro packages are often older.) Not installed? Ask the user to install
gitleaks; `uvx --from detect-secrets detect-secrets scan` covers HEAD only.

Found one:
1. **Rotate the key at its provider first.** History rewrites don't un-leak a key already pushed anywhere.
2. Ask before rewriting history (`git filter-repo --replace-text` or `--path ... --invert-paths`); it changes
   every commit hash and breaks forks and open PRs.

### Keep scanning after launch

A one-off scan protects today's history; the next commit can leak again. Install both layers from `assets/`:

- **Pre-commit** (stops a leak before it's a commit): copy `assets/pre-commit-config.yaml` to
  `.pre-commit-config.yaml`, then `pre-commit install`. It runs gitleaks on staged changes plus zizmor and
  actionlint on workflows. Revs go stale; `pre-commit autoupdate` refreshes them.
- **CI** (catches what skipped the hook, `--no-verify` or a web edit): `assets/workflows/security.yml` runs
  `gitleaks-action@v3` over the whole history (`fetch-depth: 0`) on push, PR and weekly. `@v2` targets Node 20, which
  runners now force onto Node 24 with a warning. Personal repos need no license; an organization repo needs the free
  `GITLEAKS_LICENSE` secret from gitleaks.io (ask the user to request it), or swap the job for
  `trufflehog git file://. --only-verified`.
- **GitHub push protection** (server-side; free on public repos): rejects a push that contains a known token.
  Turn it on right after the visibility flip (§7).

## 2. Files that shouldn't be tracked

- `.env`, `*.pem`, `*.key`, `id_rsa*`, `credentials*.json`, local DBs, logs, caches, personal run data.
- `.gitignore` covers them; `git ls-files` confirms none is tracked already (ignoring doesn't untrack).
- Start from the github/gitignore template for the stack instead of a hand-written list; the API serves it:
  `gh api gitignore/templates/Python --jq .source >> .gitignore` (`gh api gitignore/templates` lists all 160+;
  combine several for a mixed repo, then drop duplicates and keep the project's own lines on top). Preflight
  probes `.env`, venvs, build output and `node_modules` with `git check-ignore` and prints the command.
- Keys live outside the repo (e.g. `~/.config/<app>/.env` with mode 600), and the docs say so.
- Agent folders (`.claude/`, `.agents/`, `skills-lock.json`) belong to the user's setup; ask before committing them.

## 3. Provenance, private names, fresh history

- **Who owns the code?** Code written at a job or for a client usually belongs to them. If README, comments or
  history say it came from a work project ("extracted from", a company path, a work email), ask the user whether
  they may publish it before doing anything public. Don't guess, don't "clean it up" to hide the origin.
- **Private names and paths**: `/home/<user>/`, `~/work/...`, `C:\Users\...`, employer, client and internal project
  names (`preflight.py --private name1,name2`). Replace them in files with neutral wording. Comments naming sibling
  pet projects are harmless; the user decides.
- **Author emails** in history are published with it. A work email there is a reason for a fresh export
  (or `git filter-repo --mailmap`).
- **Fresh-history export** (monorepo subfolder, or history with private material): publish a new repo whose first
  commit is the current folder.
  ```bash
  git -C <monorepo> archive HEAD:<subfolder> | tar -x -C <new-dir>
  cd <new-dir> && git init -b main && git add -A && git commit -m "chore: initial public release"
  ```
  Keep the private monorepo as is. If the old history is clean and worth keeping, `git subtree split -P <subfolder>`
  keeps it instead. Run the tests, the build and the README's install/quick-start commands **in the exported copy**:
  inside the monorepo they can pass by accident (shared venv, workspace members, parent-relative links).
- **Internal working files**: session prompts, plans, handoff notes, agent folders. Move them out or publish them on
  purpose (some projects show their plan openly); ask.

## 4. Licenses of borrowed code

Ported or vendored code keeps its license and copyright notice. List each in `THIRD_PARTY_NOTICES.md`
(source URL, license, what was taken). Pick the project license to be compatible (MIT/Apache code can go into
MIT; GPL code can't).

## 5. Package contents

Build the sdist/wheel and look at the size and file list. Test fixtures, snapshots, README images and eval data
belong in git but not in the package (`[tool.hatch.build.targets.sdist] exclude = [...]`, `MANIFEST.in`,
`.npmignore`, `files` in package.json). A root-anchored pattern (`/assets`) avoids excluding a same-named
folder the package needs.

## 6. Code-level review

When the project reads keys, runs subprocesses, writes files, serves HTTP or renders user content, run
`security-review` (or the `code-reviewer` agent). Common findings in tools like these:
- shell injection through `subprocess(..., shell=True)` or string-built commands;
- path traversal when a name from input becomes a file path;
- secrets in logs, error messages or URLs;
- a local web UI bound to `0.0.0.0` instead of `127.0.0.1`;
- unescaped HTML from READMEs or API data;
- cleanup code that deletes files still in use (e.g. log prune removing a running process's log).
- LLM output or text from a fetched page passed to a shell, SQL or file path (treat it as user input), and prompts
  built from untrusted content without a boundary (prompt injection);
- server secrets in the client bundle (`NEXT_PUBLIC_*`, `VITE_*` holding a key) and secrets echoed in CI logs;
- SSRF: a user- or LLM-supplied URL fetched from the server without an allowlist; webhooks without signature checks;
- a new dependency with a `postinstall` script, or a name one letter off a popular package (typosquatting).

The full web checklist (OWASP Top 10 2025, headers, auth, framework pitfalls) is
github/awesome-copilot `instructions/security-and-owasp.instructions.md`; hand it to `security-review` for web apps.

## 7. GitHub settings (outward-facing: list the commands, run after a yes)

```bash
gh api -X PUT repos/OWNER/REPO/private-vulnerability-reporting
gh api -X PUT repos/OWNER/REPO/branches/main/protection --input protection.json   # or a ruleset
gh repo edit OWNER/REPO --enable-wiki=false --enable-projects=false
gh api -X PATCH repos/OWNER/REPO \
  -f 'security_and_analysis[secret_scanning][status]=enabled' \
  -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'
gh api -X PUT repos/OWNER/REPO/automated-security-fixes            # Dependabot security updates
```

- `SECURITY.md` links to `https://github.com/OWNER/REPO/security/advisories/new`, states a response time and
  which versions get fixes, and says where the tool keeps keys and where it sends them.
- Dependabot for the package manager and for `github-actions`.
- Package name: free on PyPI/npm, or published from this repo (preflight). A taken name means `pipx install <name>`
  installs someone else's code.
- Dependabot (`assets/dependabot.yml`) for the package manager and for `github-actions`; the latter keeps
  SHA pins current.
- Package name: free on PyPI/npm, or published from this repo (preflight). A taken name means `pipx install <name>`
  installs someone else's code.

## 8. Workflow hardening

Workflows run with a token and often with secrets; a bad one is a supply-chain hole in a repo strangers trust.

- `permissions: contents: read` at the top of every workflow (preflight flags missing ones); write scopes only
  on the job that needs them.
- Pin every third-party action to a full commit SHA with the version in a comment
  (`uses: owner/action@<40-hex> # v1.2.3`); a moved tag can't swap the code then. Dependabot bumps both.
  `pinact run` (suzuki-shunsuke/pinact) rewrites existing tag pins.
- `actions/checkout` with `persist-credentials: false` unless a later step pushes.
- No `${{ github.event.* }}` inside `run:`: pass it through `env:` (template injection). No `pull_request_target`
  that checks out PR code.
- Node runtime: Node 20 is gone from the runners; Node 20 actions are forced onto Node 24 with a warning in
  every run. Most keep working, but bump to the major that declares node24
  (e.g. checkout v5+, setup-python v6+, upload-artifact v6+, download-artifact v7+, cache v5+, codeql-action v4,
  setup-uv v7+). Preflight checks each `uses:` against its `action.yml`.
- One workflow per purpose (`ci.yml`, `security.yml`, `release.yml`, scheduled jobs), each with its own
  permissions. A reusable workflow (`workflow_call`) or a composite action pays off once the same steps are
  copied a second time, not before; long inline bash goes to `scripts/`.
- `timeout-minutes` on every job (a hung job otherwise burns up to 6 h of minutes) and a `concurrency` group with
  `cancel-in-progress` on push/PR workflows, so a new push cancels the stale run. Not on release workflows.
- Dependabot `cooldown: { default-days: 7 }`: hijacked releases are usually caught within days; zizmor flags its
  absence. Security updates ignore the cooldown, so fixes still land at once.
- Public repos, two extras that cost one command or one job: CodeQL default setup (no workflow file;
  `gh api -X PATCH repos/OWNER/REPO/code-scanning/default-setup -f state=configured`, after a yes) and
  `actions/dependency-review-action` on `pull_request`, which fails a PR that adds a dependency with a known CVE.
  Both need the repo public or GitHub Advanced Security.
- Checklists found online (e.g. github/awesome-copilot's CI/CD instructions) agree on SHA pins, least privilege,
  OIDC and secret scanning, but their example pins can be Node 20 versions; check them like any other `uses:`.
- `zizmor` and `actionlint` catch the rest; both are in `assets/pre-commit-config.yaml`
  (or one-off: `uvx zizmor .github/workflows`, `uvx --from actionlint-py actionlint`).

## 9. OpenSSF Scorecard (public repos)

`assets/workflows/scorecard.yml` runs the Scorecard checks weekly (branch protection, pinned deps, token
permissions, SAST, signed releases…), uploads the result to Security → Code scanning and publishes it to
scorecard.dev. The badge in the README is a trust signal for people deciding whether to install. Its findings
are a to-do list, not a target: a solo project won't get "Code-Review" points, and that's fine. Keep the
workflow's shape (no top-level env, `permissions: read-all`); scorecard-action rejects changes there.
