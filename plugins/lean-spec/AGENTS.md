# Agents: start here (lean-spec plugin)

1. `docs/logic-map.md`: how a request becomes a Lean model, proofs, differential tests and a green gate: every
   step, every branch, the skill file behind it.
2. `docs/logic-map-fixes.md`: the known gaps in the skill, numbered.
3. `PLAN.md`: the roadmap and what each pilot showed.

Rules:
- Change a step or a branch of the skill (`skills/lean-spec/SKILL.md`, `references/`, `scripts/`, `example/`) →
  update `docs/logic-map.md` and `docs/logic-map.ru.md` in the same commit.
- `tests/test_lean_spec.py` (repo root) fails when a `Module:` line in the map points to a file that is gone.
