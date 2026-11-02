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
lake comparator   # statements and model definitions match Frozen.lean, standard axioms, kernel accepts
(cd .. && "${TEST_CMD[@]}")
echo "gate: ok"
