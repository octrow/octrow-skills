# Map mode: a logic-map step as the requirement

The logic map (`docs/logic-map.md`, from the logic-map plugin) already states each step's rules in plain lines:
`Decides:`, ordered rules, `Fails:`, `Module:`. In map mode those lines are the requirement, the `Module:` is the
code under test, and what the model can't settle becomes a finding about the map.

Piloted on buy-smarter, step 18 «Roles» (`ranking/selection`): 9 theorems, 4 findings, gate green with the
project's full suite.

## Picking steps

Good: steps that decide purely from data in memory (priorities, filters, dedupe, ranking, roles, city order).
Skip: collection, the browser, the network, persistence (a retry or fallback loop around them is pattern S, not a skip). One step per run; a step whose model passes ~200 lines is
split by rule.

## Statements

- One theorem per rule line. Above each, quote the exact map line:
  ```lean
  -- map: "Budget pick must be cheaper than best and score at least half of it."
  theorem budget_cheaper_half ...
  ```
- `Decides:` is a summary, not a rule; it gets no theorem.
- Vague words ("close to", "prefer", "top quarter") get their meaning from the code's constant or expression. State
  that meaning, mark it `-- silent:` in the model, and record "the map does not say X" as a finding.
- Things the code does and the map never mentions (one role per product, claim order, barred items excluded from
  every role) are findings too, not theorems.

## Map mode with a fast path (pattern E)

The step's lines are the requirement for `spec`, but a fast path's theorem is `fast = spec`, not the step's
rules. The `Proved:` line then says what is equal to what and under which condition:
`Proved: lean/Spec/Dedupe (2 theorems: the bucketed pass equals the plain pass for any same-product test whose
matches share a key); tests/test_spec_dedupe.py checks the code against it and that real matches share a key.`
Silent choices in the model are map findings only when the map should say them (an ordering users see), not for
internals of the algorithm.

## Where results go

1. **`Proved:` line** at the end of the step, in the map's style:
   `Proved: lean/Spec/<Target> (N theorems), checked against <module> by tests/test_spec_oracle.py`.
2. **Map test.** Extend the map's existing test (the one that checks `Module:` lines) so every `Proved:` path must
   exist. About eight lines; make sure it fails on a wrong path, then revert.
3. **Findings.** Follow the map: "Known gaps" links to a plan. Add the findings there in the project's own
   numbering, each with the shrunk counterexample (code says / model says) and a verdict: the code looks wrong, the
   map looks wrong, or the author decides. Numbering may collide with another series in the project (CHANGELOG);
   check before picking numbers.
4. **Mirror.** If the map has a translated mirror (`logic-map.ru.md`), say it needs the same `Proved:` line (and
   the gaps entry, if the mirror has a gaps section); edit it only if the project's rules say the agent keeps it in sync.
5. **Same-commit rule.** Add one line under the map's existing rule, the first time a step gets `Proved:`:
   "A step with a `Proved:` line has a Lean model: changing the step means revisiting its statements and
   `lean/Frozen.lean`, with the author's consent." Also update the header line that says what the map test checks.

## Don't

- Fix the code in map mode unless the user asked for it. Findings first; pinned counterexamples keep the gate green
  (`known-findings.md`).
- Rewrite map lines to match the code. A wrong map line is a finding for the author.
