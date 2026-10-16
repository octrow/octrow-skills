# Python code health: lint, format, complexity, dead code

The tools run through `uvx`, so nothing is added to the project to audit it. To keep the result, add them to the
dev dependencies (`uv add --dev ruff`) and to CI ("CI wiring" below). Thresholds are the tools' defaults; a project
sets its own in `pyproject.toml`, and the preflight reads it.

Work in this order: format, lint, dead code, complexity. Formatting first keeps the later diffs readable, and
deleting dead code first means nobody refactors a function that should have been removed.

## Ruff format

`ruff format --check` lists files the formatter would change. Fix: `uvx ruff format .` in a commit of its own, with
no other changes, and add the commit to `.git-blame-ignore-revs` so `git blame` skips it. Line length and quotes
come from `[tool.ruff]` (`line-length = 120`); pick them once, before the first format run.

Exempt when the project uses another formatter (black with settings ruff can't match) and CI already runs it.

## Ruff lint

`ruff check` with the default rules (pyflakes `F` and the `E4`, `E7`, `E9` pycodestyle errors) finds mistakes:
unused imports and variables, undefined names, `==` against None, bare `except`. The report shows the rules with the
most hits first.

Fix: `uvx ruff check --fix .` handles the safe fixes; read the diff, then fix the rest by hand. When a rule fires on
code that is right (a re-export in `__init__.py`), add `# noqa: F401` with the reason on that line, or
`[tool.ruff.lint.per-file-ignores]` for a whole file pattern.

To raise the bar later, add rule families one at a time in `[tool.ruff.lint] extend-select`: `B` (bugbear), `UP`
(pyupgrade), `SIM`, `PL` (the pylint rules, so there is no need for pylint itself), `C90` (mccabe, the same measure
as radon below). Each family is its own commit.

Exempt only when the code isn't the project's (vendored or generated): exclude those paths in `[tool.ruff]
extend-exclude` instead, which also keeps them out of the editor's warnings.

## Cyclomatic complexity

radon counts independent paths through each function (every `if`, loop, `and`/`or`, `except`). Above 10 a function
has more paths than its tests cover; the report lists the worst first.

Fix, in this order:

1. A chain of `if x == ...` returning values: a dict lookup.
2. Validation at the top: guard clauses with early returns, which also flattens the nesting.
3. A loop body doing two jobs: extract the body into a named function.
4. Branches by type or kind that keep growing: one function per kind, chosen from a dict.

Refactor only with tests that cover the function; write them first if they don't exist.

Threshold: `[tool.ruff.lint.mccabe] max-complexity = 12` (or `[lint.mccabe]` in `ruff.toml`); the preflight uses
the same number for radon. Exempt a
function that is a flat dispatch table by nature (a CLI argument parser, a protocol state machine) rather than
raising the limit for the whole project: add `# noqa: C901` on it when ruff's `C90` is on, and exempt the Check in
`.repo-ready.yml` naming that function.

## Cognitive complexity

complexipy measures how hard a function is to read: nesting costs more the deeper it goes, and a flat `match`
costs less than nested `if`s. A function can be low on cyclomatic complexity and still high here. The default limit
is 15.

Fix: the same moves as above, with the focus on depth. Invert conditions to return early, move the inner loop into
a function, and replace a flag variable that steers later branches with two functions.

Threshold: `[tool.complexipy] max-complexity-allowed = 20`. For one function that has to stay as it is, put
`# complexipy: ignore` on its `def` line.

## Dead code

vulture lists definitions nothing refers to: unused functions, classes, variables, imports, and code after a
`return`. The preflight shows only 80%+ confidence hits by default, because 60% hits are mostly entry points a
framework calls by name (FastAPI routes, Typer commands, pydantic fields, pytest fixtures).

Fix: delete it; git keeps the history. Before deleting, search for the name as a string too (`getattr`, entry
points in `pyproject.toml`, templates). A definition that is used dynamically goes into a whitelist file:
`uvx vulture --make-whitelist src > vulture_whitelist.py`, trim it to the real cases, and commit it.

Project settings go in `[tool.vulture]` (`min_confidence = 60`, `paths`, `exclude`, `ignore_names`,
`ignore_decorators = ["@app.get", "@app.command"]`); when that table exists the preflight leaves the confidence to
it.

## CI wiring

The fixes above stay fixed only if every push runs the same tools. One job in `.github/workflows/ci.yml`:

```yaml
- uses: astral-sh/setup-uv@<sha> # vX
- run: uv sync --dev
- run: uv run ruff check .
- run: uv run ruff format --check .
- run: uv run pytest
```

Add the same ruff hooks to `.pre-commit-config.yaml` (`astral-sh/ruff-pre-commit`, `ruff-check` and `ruff-format`)
so problems are caught before the commit. Complexity and dead code are advice, not gates: keep them out of CI until
the project is clean, then add them with the project's threshold.

Exempt `tests_in_ci` only for a project with no tests by design (a single-file script); say so in the reason.

## Type checker

Type hints are documentation until something checks them. Pick one: mypy (`[tool.mypy]`, the most widely used),
pyright (`[tool.pyright]`, faster and stricter about inference) or ty (`[tool.ty]`, Astral's, still young). Start
with the defaults, fix what they find, add the run to CI, and only then turn on `strict` module by module.

Exempt for a project without type hints whose authors don't plan to add them.
