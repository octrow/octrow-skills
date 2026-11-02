# Logic map: lean-spec

How one user request ("verify with Lean", "speed it up, but prove it", "check step 18 of the logic map") becomes a
Lean model, proved theorems, differential tests and a green gate in the user's repo.
The map describes the skill as it is today, step by step: what the agent decides, where the flow branches, and
which file of the skill drives it.

Paths in `Module:` lines start at `plugins/lean-spec/skills/lean-spec/`, without the extension.
Step numbers here are the map's own; each heading names the SKILL.md section (§) it comes from. `references/map-mode.md` uses the § numbers.
Known gaps and fixes in progress are in `docs/logic-map-fixes.md`; the plugin's roadmap is `PLAN.md`.

Rule: if you change a step or a branch of the skill, update this file and `logic-map.ru.md` in the same commit.
`tests/test_lean_spec.py` (repo root) checks that every `Module:` line points to a real file or folder.
The Russian mirror is `docs/logic-map.ru.md`; this file is the source of truth.

## The flow at a glance

```
user request + a repo
  │
  ├─ 0  Preflight ............. are lake and bwrap here; which Lean; is lean/ already there
  ├─ 1  Target and pattern .... which function or map step; A, E or S; map mode or not
  ├─ 2  Template copy ......... lean/ and tests/ copied from example/, Frozen reset
  ├─ 3  Model ................. the reference in Lean (requirement, or the code's transitions for S)
  ├─ 4  Statements ............ which theorems; silent choices and false claims marked
  ├─ 5  Approval .............. user approves the statements, or approved in advance
  ├─ 6  Freeze ................ Frozen.lean + comparator.json while proofs are still sorry
  ├─ 7  Proofs ................ one sorry at a time; a false statement stops the run
  ├─ 8  Oracle ................ lake exe oracle answers the frozen reference, line by line
  ├─ 9  Differential tests .... Hypothesis: production code == oracle on whole values
  ├─ 10 Known findings ........ disagreements pinned with strict xfail, masks narrow
  ├─ 11 Mutation check ........ ≥3 mutants of the production code must fail a test
  ├─ 12 Fast path and timing .. (E only) code mirrors fast/checkInv; before/after numbers
  ├─ 13 Gate .................. lake build, cheat grep, lake comparator, tests
  ├─ 14 Report ................ Proved / Only tested, runtime check, findings
  └─ 15 Map write-back ........ (map mode only) Proved: line, map test, findings plan
  │
lean/ + tests in the user's repo, a report, and in map mode a changed logic map
```

The skill never edits production code before step 9 has run unmasked, and in map mode not at all unless asked.

## Where the flow splits by pattern

The pattern is the agent's choice at step 1, from the user's words and the code; nothing in the skill computes it.

| Pattern | Switched on by | Steps it changes | What changes |
|---|---|---|---|
| A: model + differential tests | default | 3, 4, 9, 11 | model from the requirement; tests compare code and model |
| E with a data invariant | a fast path next to a slow one, valid only on some data | 3, 4, 8, 9, 11, 12 | `spec`/`fast` pair, the oracle calls `spec` only; `fast_eq_spec : Inv → …`, `checkInv_sound`; runtime check with fallback; two strategies (any input, invariant input) |
| E with a predicate property | the fast path's condition is a property of a predicate (matches share a key) | 4, 12 | hypothesis on the predicate; no runtime guard; a property test instead |
| E with no hypothesis | the bucket key is part of the match condition | 4, 12 | `fast = spec` for all inputs; no guard, no property test |
| S: state machine under faults | a loop that reacts to failures: retries, fallback, reconnects | 3, 4, 7, 9, 10, 11, 14 | model = the code's transition function over a finite event list; false claims as `¬ Claim`; scripted fakes; event-sequence strategies |
| C: capacity and limits | a rate limiter, quota, queue or cap whose numbers matter | 3, 4, 9, 11, 14 | model = the code's transitions with time as data; counting bounds as `def Claim`; faults as a term in the bound; controlled clock, load test; capacity table |
| Map mode | the repo has `docs/logic-map.md` and the user names a step or asks to check the map | 1, 3, 4, 9, 10, 14, 15 | the step's lines are the requirement; `-- map:` quotes; findings go to the map's plan; no code changes |

Examples:
- "make `normalize` faster but prove it" → E; which E depends on whether the fast path needs a data invariant.
- "prove the retry loop never pins a provider twice" → S.
- "how many password guesses does the login limiter let through per day" → C.
- "check step 18 of the logic map with Lean" → map mode with A.

Module: `SKILL`, `references/patterns`, `references/map-mode`

## Entry points

| Entry | Approval at step 5 | Gate tests | Notes |
|---|---|---|---|
| Skill trigger (description phrases, `/lean-spec:lean-spec`) | stops for the user | the repo's CI tests | the main flow, steps 0–14 |
| Map mode trigger («проверь шаг карты логики через lean», or asks to check the map) | stops for the user | the repo's CI tests | adds step 15; findings, not fixes |
| Request that pre-approves ("формулировки утверждаю заранее") | **skipped**; statements listed in the report | same | freeze right after writing them; a false statement in step 7 still says "stop and show it" |
| `scripts/preflight.py [repo]` | n/a | n/a | read-only; exit 1 only when lake or bwrap is missing |
| `lean/gate.sh` by hand, Stop hook or CI | n/a | `TEST_CMD` at its top | the same script in all three; Stop hook and CI snippets in `references/setup.md` |
| `tests/test_lean_spec.py` (this repo) | n/a | example's own test | preflight facts; runs the example gate only when lake exists |
| Evals `evals/lean-spec/*` | per prompt | per case | run by hand as a subagent on a scratch copy (plugin eval can't run Bash on the dev machine) |

Module: `SKILL`, `scripts/preflight`, `example/lean/gate`, `references/setup`

## Steps

### 0. Preflight (§0)

Decides: whether the run can start and what to install.
In: repo root. Out: `name: value` facts, `install …` lines.
Branches:
- lake or bwrap missing → exit 1; the skill shows install lines and stops;
- lake only under `~/.elan/bin` → every later shell command starts with `export PATH="$HOME/.elan/bin:$PATH"`;
- Lean version ≠ 4.35.0 → warning "API drift is likely", the run continues;
- lean-lsp-mcp missing → offered before proofs (step 7); lean4-skills missing → optional;
- `lean_project: lean/ (exists …)` → step 2 adds a target next to the frozen one instead of copying the template.
Fails: a crash of `lean --version` → `unknown (…)`, the run continues.
Module: `scripts/preflight`, `SKILL`, `references/setup`

### 1. Target and pattern (§1)

Decides: one target, its pattern (A, E, S, C) and whether map mode is on.
Branches:
- `docs/logic-map.md` exists and the user names a step → map mode; target = the step's `Module:`; only steps that
  decide from data in memory;
- a model that would pass ~200 lines → refuse or split;
- IO itself (network, DB driver) → refused; logic that reacts to IO (retries, fallbacks, reconnects) → S with the
  IO faked;
- E → one real request timed end to end first (where the time goes), then the target's "before" numbers.
Module: `SKILL`, `references/patterns`, `references/map-mode`

### 2. Template copy (§2)

Decides: the layout of `lean/` and the test file in the user's repo.
Out: `lean/` (lakefile, toolchain v4.35.0, gate, oracle, comparator.json), `tests/test_spec_oracle.py`, maybe
`tests/conftest.py`; `.gitignore` gains `lean/.lake/` and `.hypothesis/`; `Spec/Feed/` deleted; `Frozen.lean`
reset to its header; `lean/Spec.lean` imports the target instead of Feed; `Oracle.lean` imports the target's model
with `answer` stubbed to `error: no oracle yet` until step 8; `comparator.json` has no theorem names.
Branches:
- `lean/` already there → no copy, `Frozen.lean` never reset: a new `lean/Spec/<Target>/`, an import in `Spec.lean`,
  a tagged oracle branch, the test file added to `TEST_CMD`, the `comparator.json` check copied into an older `gate.sh`;
- repo tests can't import modules from the root → `conftest.py` copied too.
Module: `SKILL`, `example/lean`, `example/tests`

### 3. Model (§2)

Decides: what the reference is.
Out: `lean/Spec/<Target>/Model.lean` on `List` and `Nat`, no optimisation; `spec`/`fast` for E.
Branches:
- A, E: written from the requirement (map lines, docstring, ticket), not from the code body;
- the requirement is silent (ties, rounding, what is maximised) → the code's choice, `-- silent:`, a finding;
- E with a predicate property: `spec` is the existing algorithm, most of the model is `-- silent:`;
- S: the code's own transition function; the environment is one finite list of events, recursion structural;
- C: the same, with time a number on each event and the store (keys, counters, a queue) a value; replica
  interleavings in a separate op-level model.
Module: `SKILL`, `references/patterns`

### 4. Statements (§2)

Decides: what will be proved.
Out: `Props.lean` with every theorem and `sorry`; `lake build` green with only `sorry` warnings.
Branches:
- E: `fast_eq_spec` (with `Inv`, a predicate hypothesis, or none) and `checkInv_sound` when there is a guard;
- map mode: one theorem per rule line with a `-- map: "…"` quote; `Decides:` gets none;
- S: safety claims (bounded steps, no repeat, record once) and docstring promises; a false one becomes
  `def Claim : Prop` + `theorem claim_false : ¬ Claim` with a concrete witness;
- C: counting bounds (per window, any W seconds, per day, no lockout), each first as `def Claim`; faults as a
  term in the bound; the real config as `decide` corollaries.
Module: `SKILL`, `references/map-mode`, `references/patterns`

### 5. Approval (§2)

Decides: whether the statements say what the user means.
Branches:
- default → the model and each statement in plain words, then wait;
- approved in advance → no stop; the report lists them in plain words.
Module: `SKILL`

### 6. Freeze (§2)

Decides: what the comparator holds the proofs to.
Out: `Frozen.lean` += model + props without `Spec` imports (one block per target), library imports (Mathlib,
Std) lifted to the top; `comparator.json` lists the theorem
names; standard axioms only.
Branches:
- a second target → its block appended, its names added; the first target's block untouched;
- the function the oracle calls is in no listed theorem → a theorem that mentions it is added before freezing;
- helper lemmas added later stay out of Frozen and are never claims; statements or Frozen change only with consent, together.
Module: `SKILL`, `example/lean/Frozen`, `example/lean/comparator`

### 7. Proofs (§3)

Decides: whether every frozen statement holds for the model.
Branches:
- lean4-skills installed → `/lean4:prove` per `sorry`; else the proof loop (goal first, automation, search, `#check`);
- a counterexample appears → the statement is false: stop and show it (a requirement finding);
- stuck ~5 attempts on one goal → helper lemma or recheck the definition;
- S: a counterexample is a code (or docstring) bug: shown, then that statement flips to `¬ Claim` in Props and
  Frozen together, proved by the witness; pre-approved runs flip without asking, others ask first.
Fails: in A and E code-vs-requirement bugs don't show here (the model follows the requirement), step 9 finds them;
in S the findings come from the theorems.
Module: `SKILL`, `references/proof-loop`

### 8. Oracle (§4)

Decides: how the tests reach the frozen reference.
In: one line of whitespace-separated naturals. Out: the reference's whole result, or `error: …`.
Branches:
- several targets → a tag at the start of the line, dispatch in `answer`;
- a predicate the code computes → sent as data (an n×n 0/1 matrix).
Fails: EOF → the loop ends; a malformed line → `error: …`, the test's `int()` raises.
Module: `SKILL`, `example/lean/Oracle`

### 9. Differential tests (§5)

Decides: whether the production code agrees with the model.
In: Hypothesis inputs. Out: pass, or a shrunk counterexample (input, code, model).
Branches:
- E with no fast path in the code yet → step 12 writes it first (fast branch, guard, `_x_reference`);
- E: one strategy for any input (fallback) and one for invariant inputs (fast path);
- S: event sequences, collaborators faked inside `MonkeyPatch.context()`, `BaseException` when events run out,
  weighted branches, run lengths via `hypothesis.event`;
- C: the fake store's clock patched (1 µs per command), timelines with bursts on window edges, and a load test of
  a simulated day at the real config;
- hypothesis goes into the repo's test dependencies (uv dev group, dev requirements, test extra or CI install);
  the `--no-project` command is for the standalone example only; a missing hypothesis fails, never skips;
- lake missing → the oracle module is skipped (`pytestmark`), CI needs the lean job.
Fails: a disagreement → reported before any code change; the user decides unless they already said to fix; in
map mode the code is not changed.
Module: `example/tests/test_spec_oracle`, `SKILL`

### 10. Known findings (§5)

Decides: how a known disagreement stays visible with a green gate.
Branches:
- A, E, map mode: a classifier of narrow masks + one pinned counterexample per finding with `xfail(strict=True)`;
- S: no mask; the `¬ Claim` witness is the strict-xfail pin, plus a test that code equals model there.
Fails: someone fixes the code → the strict xfail fails → mask and pin are removed together.
Module: `references/known-findings`, `references/patterns`

### 11. Mutation check (§5)

Decides: whether the tests compare as much as the theorems.
Branches:
- ≥3 mutants per pattern (A: condition, comparison, order; E: guard, key, invariant check; S: tried-mark, retry
  kind, intermediate record, wrong target, counter, flag reset; C: limit comparison, expiry repair, expiry reset
  on every hit, fail closed/open, key namespace; index/cache: stale state);
- a survivor → the test compares less than the theorem → fix the test;
- an index or cache in the fast path → near-copy inputs and an `@example` per killed mutant;
- an equivalent mutant (changes only the branch, not the result) → named in the report.
After any mask change the check runs again; each mutant is restored with `cp` + `cmp`.
Module: `SKILL`

### 12. Fast path and timing (§6, E only)

Decides: what runs in production and whether it is faster.
Branches:
- data invariant → the check runs where the invariant can break (per call, startup + writes); fallback = reference;
- predicate property → no guard, property test; no hypothesis → nothing to check;
- the old code stays as `_x_reference` for the tests.
Timing: median and p95, warm-up, GC off, same inputs, real sizes + one larger + the small size; "before" from
step 1, "after" here.
Module: `SKILL`, `references/patterns`

### 13. Gate (§7)

Decides: done or not.
Order: `lake build` → grep (`sorry`, `native_decide`, `axiom`, `implemented_by`, `@[extern`, `unsafe`,
`skipKernelTC`, `debug.`; Frozen.lean and `.lake` excluded) → `comparator.json` names exactly the theorems of
`Frozen.lean` → `lake comparator` → `TEST_CMD` from the repo root.
Branches: `TEST_CMD` = the repo's CI test command, or all of `tests/`; exclusions commented in the script.
Grep details: `axiom` only at line start; `Frozen.lean` excluded by file name in any folder (#14).
Fails: any stage → non-zero exit, no `gate: ok`; never weaken the gate, Frozen or comparator.json to get green.
Module: `SKILL`, `example/lean/gate`, `references/cheating`

### 14. Report (§8)

Decides: what is claimed.
Out: **Proved:** each theorem named in `comparator.json`, in one sentence; **Only tested:** agreement with the model (examples, mutants
caught) and everything outside the model; the runtime check and its failure path; findings with numbers; for S and C the
fault model (what is in, what is not); for C the capacity table at the real config.
Fails: without the two lists the task is not done.
Module: `SKILL`

### 15. Map write-back (§9, map mode only)

Decides: what the logic map learns from the run.
Out: a `Proved:` line at the end of the step; the map's test checks that the path exists; findings in the plan
Known gaps points to; a note that the mirror needs the same line; once, the same-commit rule about `Proved:` steps
and the header line that says what the map test checks.
Branches: a fast path → `Proved:` says what equals what under which condition.
Fails: never rewrite map lines to match the code; a wrong line is a finding.
Module: `SKILL`, `references/map-mode`

### Output

In the user's repo: `lean/` (Spec, Frozen, comparator.json, Oracle, gate.sh), `tests/test_spec_*.py`, for E a
changed production module with `_x_reference`; the report; in map mode a changed `docs/logic-map.md` and plan.

## Side flows

### Setup for a repo that keeps the gate

CLAUDE.md lines, an optional Stop hook running `lean/gate.sh` (blocks a stop once and shows the gate's tail; a
repeated stop goes through), a CI job (bubblewrap, elan, uv, gate). Started when
the user wants the result to stay true.
Feeds: step 13.
Module: `references/setup`

### Cheat catalogue

Which shortcut an agent may take to a green build and which gate stage catches it; `implemented_by` is caught by
the grep only.
Feeds: step 13.
Module: `references/cheating`

## Known gaps

Details and fixes are in `docs/logic-map-fixes.md`.
No open HIGH or MEDIUM findings; open LOW ones (#3, #5, #14), the macOS question (#4) and the CI run (#6) are in the plan.
