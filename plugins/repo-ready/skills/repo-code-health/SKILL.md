---
name: repo-code-health
description: >
  Clean up a Python codebase and keep it clean: ruff lint and format, cyclomatic complexity (radon), cognitive
  complexity (complexipy), dead code (vulture), and CI that runs the linter, the tests and a type checker. Use
  whenever the user says "почисти код", "проверь качество кода", "мёртвый код", "сложность", "рефакторинг сложных
  функций", "clean up the code", "code quality", "dead code", "too complex", or names ruff, radon, vulture or
  complexipy. Runs a read-only preflight first and fixes only the parts the user picks.
---

# Repo code health

Find what makes the code harder to change than it needs to be, fix the parts the user picks, and wire CI so it
stays fixed. Read-only first: the preflight runs the tools through `uvx` and writes nothing into the project.

## Phase 0: preflight and scope

```bash
python3 <skill-dir>/engine/preflight.py [project-path] --scenario code-health
```

The tools need `uvx` ([uv](https://docs.astral.sh/uv/)); without it the tool Checks report broken, and the CI
Checks still run. The report groups failed and broken Checks by severity, each with a `fix:` path from this skill's
folder (`engine/procedures/python-quality.md#<section>`). **warning** must be fixed or exempted before the part is
done; **info** is advice. Findings are capped at ten per Check, worst first; run the tool itself (the procedure
names the command) for the full list. Thresholds are the tools' defaults unless `pyproject.toml` sets its own. A
Check that doesn't fit gets an exemption in `.repo-ready.yml` (`exempt:` then `  check_id: reason`), after the
user agrees.

Then ask only what the code can't tell, with a recommendation each: which parts to do, and for complexity, which
functions (default: the worst three, each only if tests cover it). Default parts: every part with findings.

## Parts, in this order

Formatting first keeps later diffs readable; dead code goes before complexity so nobody refactors a function that
should be deleted.

1. **Lint and format** (`#ruff-format`, `#ruff-lint`): the format run in a commit of its own, listed in
   `.git-blame-ignore-revs`; then `ruff check --fix`, the rest by hand.
2. **Dead code** (`#dead-code`): delete what nothing uses after searching for the name as a string too; dynamic
   uses go to a vulture whitelist.
3. **Complexity** (`#cyclomatic-complexity`, `#cognitive-complexity`): one function per commit, tests first if it
   has none, behaviour unchanged.
4. **CI wiring** (`#ci-wiring`, `#type-checker`): ruff and the tests in a workflow and pre-commit, then a type
   checker with its defaults.

Each part ends with its tools run again and the tests green. Done when the preflight shows the part's Checks
passed or exempted with a reason.

## Working rules

- **Read-only until scoped.** The preflight changes nothing; edits start after the user picks the parts.
- **Behaviour stays.** Cleanup is not a feature change: run the tests before and after each commit, and stop
  to ask when a fix would change what the code does (a "dead" function that turns out to be an entry point).
- **Small commits by kind.** Formatting, lint fixes, deletions and each refactor go in separate commits,
  `<type>: <description>`, so any one of them can be reverted alone.
- **Project config over flags.** Thresholds and rule choices go in `pyproject.toml`, where the editor, CI and the
  preflight all read them; a limit is raised only when the user decides, with the reason written down.
- **Pin what you add.** Tools as dev dependencies with a version, actions by commit SHA with the version in a
  comment.
- **Outward-facing needs a yes.** Pushing and opening a PR wait for the user's explicit yes.

## Report format

End each part with a short report in the user's language:

```
## <Part>
Before → after: <counts per tool, e.g. ruff 42 → 0, cc>10: 16 → 13; files and functions touched>
Verified: <tools re-run, tests, CI run>
Not done: <skipped items and why>
Next step: <recommendation>
```

At the start, after the preflight, give a scorecard: one row per part, status (ok / gaps / not applicable), and
the top finding for each.
