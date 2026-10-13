# Contributing

**English** | [Русский](CONTRIBUTING.ru.md)

Bug reports, wrong advice and missing checks are welcome as issues. For a change to a skill:

1. Fork, branch from `main`, and keep one change per pull request.
2. Run the checks:
   ```bash
   pre-commit install && pre-commit run --all-files   # gitleaks, zizmor, actionlint
   claude plugin validate .
   ```
3. A change to what a skill does needs an eval case in `evals/<name>.json`: a prompt and the assertions that show
   the new behavior. A claim about a tool or platform ("X stopped working") needs a source or a real run.
4. Skill files are English-only. README, SECURITY and CONTRIBUTING have RU mirrors; change both in the same commit.
5. Commit messages: `<type>: <description>` with feat, fix, docs, chore, ci or refactor. Add a line to
   CHANGELOG.md under the next version.
