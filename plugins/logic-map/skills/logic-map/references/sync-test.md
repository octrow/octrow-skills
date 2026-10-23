# Module-line test

The map stays honest about where things live: every `Module:` line must name a module or package that exists. A rename that forgets the map fails CI.
It does not catch stale logic; that is the job of the AGENTS.md rule and reviews.

Set the package root to where `Module:` paths start (e.g. `src/<package>` for a src layout). After adding the test, break one `Module:` line on purpose and confirm the test fails, then restore it.

## Python (pytest), `tests/test_logic_map.py`

```python
"""docs/logic-map.md names real modules: a rename that forgets the map fails here."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "<package>"  # where Module: paths start
MAP = ROOT / "docs" / "logic-map.md"


def _module_refs() -> list[str]:
    lines = [line for line in MAP.read_text().splitlines() if line.startswith("Module:")]
    return [ref for line in lines for ref in re.findall(r"`([^`]+)`", line)]


def test_every_module_line_points_to_an_existing_module() -> None:
    refs = _module_refs()
    missing = [
        ref
        for ref in refs
        if not (PACKAGE / f"{ref}.py").is_file() and not (PACKAGE / ref).is_dir()
    ]
    assert refs
    assert missing == []
```

`assert refs` guards against a map whose `Module:` lines were all lost: an empty list would otherwise pass.

## Other stacks: shell check (`scripts/check-logic-map.sh`, run in CI)

Change `ROOT` and the extensions to the project's layout.

```bash
#!/usr/bin/env bash
# docs/logic-map.md names real modules: a rename that forgets the map fails here.
set -euo pipefail
ROOT="${ROOT:-src}"
refs=$(grep '^Module:' docs/logic-map.md | grep -o '`[^`]*`' | tr -d '`')
[ -n "$refs" ] || { echo "no Module: lines in docs/logic-map.md"; exit 1; }
missing=0
for ref in $refs; do
  if [ -d "$ROOT/$ref" ] || ls "$ROOT/$ref".* >/dev/null 2>&1; then continue; fi
  echo "missing module: $ref"; missing=1
done
exit $missing
```
