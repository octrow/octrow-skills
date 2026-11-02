#!/usr/bin/env bash
# Done means this passes. Same script locally, in the Stop hook and in CI.
set -euo pipefail
cd "$(dirname "$0")"
TEST_CMD=(uv run -q --no-project --with pytest --with hypothesis pytest -q tests/test_spec_oracle.py)  # from the repo root

lake build
# Cheats the kernel cannot see: compiled code that differs from the definition, skipped checks.
# lake comparator does not see implemented_by/extern (verified), so this grep is load-bearing.
if grep -rnE '\bsorry\b|native_decide|^\s*axiom\b|implemented_by|@\[extern|\bunsafe\b|skipKernelTC|debug\.' \
     --include='*.lean' --exclude=Frozen.lean --exclude-dir=.lake .; then
  echo "gate: forbidden construct" >&2; exit 1
fi
# lake comparator checks only the theorems comparator.json names: an unlisted frozen theorem is not checked,
# and a listed one missing from Frozen.lean is not frozen.
comparator_list_matches_frozen() {
python3 - <<'PY'
import json, re
names = set(json.load(open("comparator.json"))["theorem_names"])
scope, frozen = [], set()
for line in open("Frozen.lean", encoding="utf-8"):
    if m := re.match(r"(namespace|section)\b\s*(\S*)", line):
        scope.append(m.group(2))
    elif re.match(r"end\b", line) and scope:
        scope.pop()
    elif m := re.match(r"(?:private\s+)?theorem\s+(\S+)", line):
        frozen.add(".".join([*filter(None, scope), m.group(1)]))
if frozen != names:
    raise SystemExit(f"gate: comparator.json and Frozen.lean disagree; only in Frozen: {sorted(frozen - names)}, "
                     f"only in comparator.json: {sorted(names - frozen)}")
PY
}
comparator_list_matches_frozen
lake comparator   # statements and model definitions match Frozen.lean, standard axioms, kernel accepts
(cd .. && "${TEST_CMD[@]}")
echo "gate: ok"
