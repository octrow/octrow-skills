# Setup

## Toolchain

```bash
curl -sSfL https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain leanprover/lean4:v4.35.0
export PATH="$HOME/.elan/bin:$PATH"      # add to the shell profile
sudo apt install bubblewrap              # lake comparator and lake check build inside bwrap
```

`lean/lean-toolchain` pins the version per repo; elan downloads it on first `lake build`.

## Agent tooling

```bash
claude mcp add lean-lsp -s project uvx lean-lsp-mcp      # goals, diagnostics, search, multi-attempt, axioms
```

Project scope so subagents see it. Optional, in Claude Code:

```
/plugin marketplace add cameronfreer/lean4-skills
/plugin install lean4
```

Optional escalation for a hard lemma: Harmonic's Aristotle (`aristotlelib`); treat its output as untrusted and
run the gate.

## CLAUDE.md lines for a repo that has `lean/`

```markdown
## Lean spec
- `lean/` holds models and proofs for the logic named in `lean/Spec/`. Done means `lean/gate.sh` passes.
- Theorem statements and `lean/Frozen.lean` change only with my explicit consent.
- No sorry, native_decide, axiom, implemented_by, extern or unsafe outside Frozen.lean.
- Read the goal before editing a proof; search and #check a lemma before using it.
- Changing code that a `lean/Spec/*` model covers: run `lean/gate.sh` before saying done.
```

## Tests that need a database or Redis

If the repo's conftest needs Postgres for every test, start a throwaway cluster inside the working copy (trust
auth, a free port, `-c unix_socket_directories=''` when the path is too long for a socket) and point the test URL
at it (`TEST_DATABASE_URL`); stop it after the gate. Tests that need a real Redis stay out of `TEST_CMD` with a
comment saying so; the spec tests use a fake with a controlled clock.

## Stop hook (optional)

Blocks "done" while the gate fails, and shows the last 20 lines of its output. It runs the whole gate, tests
included, on every stop: use it where the gate takes seconds, not minutes. When the agent is already continuing
because of this hook (`stop_hook_active`), it lets the stop through, so a gate that can never pass here (no bwrap,
a broken toolchain) can't keep Claude from stopping. In `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "test ! -d lean || grep -q \"\\\"stop_hook_active\\\": *true\" || { out=$(lean/gate.sh 2>&1) || { printf \"%s\\n\" \"$out\" | tail -20 >&2; echo \"lean/gate.sh fails\" >&2; exit 2; }; }"
          }
        ]
      }
    ]
  }
}
```

## CI (GitHub Actions)

```yaml
  lean-spec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get install -y bubblewrap
      - run: curl -sSfL https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain none
      - run: echo "$HOME/.elan/bin" >> "$GITHUB_PATH"
      - uses: astral-sh/setup-uv@v6
      - run: lean/gate.sh
```

Ubuntu 24.04 runners restrict unprivileged user namespaces; if bwrap fails there, add
`sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` before the gate.
