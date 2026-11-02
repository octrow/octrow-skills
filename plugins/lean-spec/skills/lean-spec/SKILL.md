---
name: lean-spec
description: "Check or speed up one piece of logic against a Lean 4 model: write the simplest executable model of it in Lean, have the user approve the theorem statements, prove them, freeze them, then test the production code (Python first) against the model as an oracle with Hypothesis, and for a fast path prove fast = spec under an invariant that the code checks at runtime with a fallback; for a retry loop or state machine, prove its safety claims under any sequence of failures; for a rate limiter, quota or queue, prove its capacity bounds over time. Done means one gate passes: lake build, a grep for cheats the kernel cannot see, lake comparator against the frozen statements, and the differential tests. Use whenever the user says «проверь через lean», «докажи на lean», «формально проверь эту функцию», «ускорь, но докажи», «докажи, что оптимизация правильная», «модель на lean», «оракул», \"verify with Lean\", \"prove this optimization\", \"Lean spec\", \"Lean model as an oracle\", \"differential test against a model\", or wants an LLM-written fast path checked against a proved reference; also «докажи цикл повторов», «проверь автомат состояний через lean», «докажи лимиты», «сколько пропустит rate limit», "prove the rate limiter's bounds", "prove the retry/fallback logic", "verify a state machine with Lean"; also «проверь шаг карты логики через lean», «докажи правила из logic-map», \"check a logic-map step with Lean\", where the rules come from docs/logic-map.md. Use it even if they name only one of these pieces. Not for pure math formalization (use lean4-skills) or for IO itself; logic that reacts to IO failures is pattern S."
---

# lean-spec

The production code stays where it is. Lean holds a short executable model of one piece of logic, the theorems
about it, and an oracle the production code is tested against. Proofs cover the model; tests tie the code to it.
The pattern comes from lean-derive-hargup (280k users on a $12 VPS), where Lean proved one query shortcut equal
to the spec under an invariant, and the server checked the invariant at startup and fell back to plain SQL.

`example/` is a complete project in the layout a repo gets (`lean/`, `tests/`). Copy from it; don't write the
lakefile, gate, oracle loop or test fixture from scratch. Its gate passes on Lean 4.35.0.

## 0. Preflight

```bash
python3 scripts/preflight.py [repo-root]
```

Path is relative to this skill's folder. Lake and bwrap are hard requirements (exit 1); show the install lines
and stop if they are missing. If `lake` was found under `~/.elan/bin` but is not on PATH, start every later shell
command with `export PATH="$HOME/.elan/bin:$PATH"`. Without lean-lsp-mcp you are proving blind: offer its install line before step 3.
lean4-skills is optional.

## 1. Pick the target

One pure function or rule: authorization, pricing, a parser, a state machine, a query plan, a fast path next to
a slow one. Not IO itself (the network, the database driver); logic that reacts to IO (retries, fallbacks,
reconnects) is pattern S with the IO faked. Read the code and its callers first.

**Low-hanging fruit first (80/20).** When the user names an area rather than one function, list 2-4 candidates
with value (a bug the user would feel, time saved per request, a limit that guards money or abuse) and effort (model
size, how much IO to fake), and take the one with the most value per effort: a small model with a big payoff beats a
big model with a nice theorem. Say the pick in one line; the rest go to the report as next targets.

**Map mode.** If the repo has `docs/logic-map.md` and the user names a step (or asks to check the map), the
requirement is that step's lines and the code is its `Module:`. Read `references/map-mode.md` now; it adds to
steps 2, 5, 8 and 9 below. Pick only steps that decide something purely (filters, priorities, roles, dedupe), not
collection, IO or the browser. A step whose pure part is several functions of one module (a diff parser, a coverage
rule, a path rule) is one target while the model stays under ~200 lines; the oracle gets one tag per function.

Refuse or split a target whose model would pass ~200 lines. Say which pattern applies
(`references/patterns.md`): a model checked by differential tests (A), a proved fast path with a runtime guard
(E), a state machine under a fault model (S: retries, fallbacks, connections, a protocol loop), or capacity and
limits over time (C: rate limiters, quotas, queues, caps). Pick A unless there is a fast path to justify, a loop
that reacts to failures, or a limit whose numbers matter.

**Pattern E: measure first.** Before choosing an E target, time one real request end to end and see where the
time goes; a 500x faster step that is 0.1% of a network-bound request is a correct result, but say so. Then
take the "before" numbers of the target itself (step 6 says how), while the old code is still the only code.

## 2. Model and statements (stop for approval)

**If `lean/` already exists** (preflight says `lean_project: lean/`), another target is frozen there: do not copy
the template and never reset `Frozen.lean`. Add `lean/Spec/<Target>/`, import it in `lean/Spec.lean`, later append
its block to `Frozen.lean` and its names to `comparator.json` (step "freeze"), give the oracle a tag for the new
target while untagged lines keep their meaning, and add the new test file to `TEST_CMD`. If the repo's `gate.sh`
lacks the `comparator.json` check, copy that block from `example/lean/gate.sh`. Then continue from the model below.

Otherwise copy `example/lean/` to `<repo>/lean/` (without `.lake`), and `example/tests/test_spec_oracle.py` to
`<repo>/tests/`. If the repo's tests can't import its modules from the root, copy `example/tests/conftest.py` too.
Add `lean/.lake/` and `.hypothesis/` to the repo's `.gitignore`. Delete the example's `Spec/Feed/` and reset
`Frozen.lean` to its two-line header comment, then write `lean/Spec/<Target>/Model.lean`: the most obvious executable version, on
`List` and `Nat`, no optimisation. Name the reference after the production function (`canEdit` for `can_edit`);
for a fast path name the pair `spec` and `fast`. Replace the Feed imports in `lean/Spec.lean` with the target's,
and in `lean/Oracle.lean` import the target's model, drop `open Feed` and `parsePosts`, and stub
`def answer (_ : String) : String := "error: no oracle yet"` until step 4; empty `theorem_names` in
`lean/comparator.json`. Without this the build below fails on the deleted Feed.

Write the model from the requirement (the map step, docstring, ticket or the user's words), not by transcribing
the code's body: a model copied from the code proves the code's bugs. Where the requirement is silent (what is
maximised, ties, rounding), take the choice from the code, mark it with a `-- silent:` line comment of its own in
`Model.lean` (never inside a `/-- -/` doc comment: the lexer then reports an unterminated comment at the end of the
file) and list it as a finding about the requirement.

**Outside formats are requirements too.** When the code reads a format it does not own (git's diff, an HTTP
header, CSV, a log line, a protocol frame), model the input as the format's own grammar says it can look, not as
the code expects it: lines end only at `\n`, a path may hold a space (git then appends a TAB), a deleted file is
`+++ /dev/null`, an added line may itself start with `++`. On greenkeep's diff gate this found four bugs the map
never mentions, two of them letting an uncovered change through. Cite the format's source next to the model.

Write `lean/Spec/<Target>/Props.lean` with every statement and `sorry` proofs. Typical statements:
- `fast_eq_spec : Inv xs → fast xs = spec xs` for a fast path; `checkInv_sound : checkInv xs = true → Inv xs` for
  its runtime check;
- the rule's properties in words the user uses ("a non-owner never gets access to an archived doc").

**Pattern S.** The model is the code's transition function, and the environment is one finite list of events
(each attempt's outcome plus what the environment answers next: the router's listing, a reply, a timeout), so
recursion is structural and bounds are theorems, not fuel. The requirements are the safety claims (terminates
within N attempts, never picks a target twice, records a failure exactly once) and the claims the docstrings and
docs make. State each one as a named `def Claim : Prop` plus `theorem claim : Claim`, so that a claim found false
in step 3 changes only its theorem line. A false claim is `theorem claim_false : ¬ Claim`, proved by a concrete
witness: no `sorry`, and the witness becomes the pinned counterexample. Write the fault model
(which failures are in, which are not) into the report. Details: `references/patterns.md`.

**Pattern C.** As in S, the model is the code's transition function, with time a number on each event and the
store (Redis keys, counters, a queue) a value. The claims are counting bounds over time intervals: at most L per
window, at most N in any interval of length W, at most M per day, no permanent lockout, nothing lost under
load ≤ X. Write every candidate bound as `def Claim : Prop` first: textbook bounds are often off by one or false
(2L where 2L−1 holds; L·(D/W+1) when W does not divide D). Put faults into the bound as a term ("+ requests that
hit an error") instead of a "no faults" hypothesis. Model replica interleavings as a separate small op-level
model. The real limits from config become `decide` corollaries: the capacity table of the report. Details:
`references/patterns.md`.

Requirements are often constraints ("budget is cheaper than best"), not the rule that picks. Then the theorems are
weaker than the oracle comparison, and "proved" in the report covers only the constraints.

`lake build` must pass with only `sorry` warnings. **Show the user the model and each statement in plain words and
wait for approval.** The kernel cannot catch a statement that says the wrong thing; this is the step that does.
If the user approved in advance ("формулировки утверждаю заранее"), freeze right away and list the statements in
plain words in the report instead.

Before freezing, `#eval` the model on two or three inputs written by hand from the requirement (in a scratch
file that imports the model), and check the answers by eye: after the freeze a model bug needs the user's consent
to fix.

Then freeze, now, while every proof is still `sorry`: `lean/Frozen.lean` is the model and the props with their
`Spec` imports dropped and library imports at the top, one block per target, and `lean/comparator.json` lists the theorem names:

```bash
R=/abs/path/to/repo; T=$R/lean/Spec/<Target>; F=$R/lean/Frozen.lean   # absolute: the shell's directory can reset
{ sed '/^import /d' $T/Model.lean; sed '/^import /d' $T/Props.lean; } >> $F
# Lean wants every import first: lift library imports (Mathlib, Std) to the top; Spec imports stay dropped.
{ grep -h '^import ' $F $T/*.lean | grep -v '^import Spec\.' | sort -u; grep -v '^import ' $F; } > $F.new && mv $F.new $F
```

Helper lemmas you add later while proving stay out of `Frozen.lean`; the comparator checks only the named theorems.
So `comparator.json` lists exactly the theorems in `Frozen.lean`, no more and no fewer (the gate checks this), and a
theorem added to `Props.lean` after the freeze is a helper, never a claim. The comparator holds the model to Frozen
through the definitions the listed theorems use: the function the oracle calls must appear in a listed theorem;
if none mentions it, add one that does (its key property) before freezing. A Frozen file that imports
the model lets a model change slip past the comparator.

## 3. Proofs

One `sorry` at a time; statements never change. If lean4-skills is installed, hand each to `/lean4:prove`.
Otherwise follow `references/proof-loop.md`: read the goal before each edit, try automation first, search and
`#check` a lemma name before using it. Lean core already has the list, sort and permutation lemmas most models
need (`mergeSort_of_pairwise`, `pairwise_mergeSort`, `Perm.eq_of_pairwise`, `pairwise_iff_getElem`). When core lacks
a basic lemma (there is no `nodup_eraseDups`), prove it as a helper, copying the proof pattern of a neighbouring
core lemma from the toolchain source. Add Mathlib only when a proof truly needs it: the first build then takes
minutes and gigabytes.

If a proof stalls because the statement is false (a counterexample appears), stop and show it to the user; that
is a finding about the requirement, not a proof problem. A bug where the code disagrees with the requirement does
not show up here: the model follows the requirement, so its proofs go through. Step 5 finds those.

Pattern S is the other way round: the model is the code, so a false claim here is a bug in the code (or a wrong
docstring), and this step is where S finds bugs. Show the counterexample, then flip that one statement from
`theorem claim : Claim` to `theorem claim_false : ¬ Claim` in `Props.lean` and `Frozen.lean` together, and prove it
by the witness. This is the one statement change allowed without a new approval round when the user pre-approved
the statements; otherwise ask first. The flip can't fake a proof: `¬ Claim` needs a concrete witness the kernel
checks, and the gate's list check still holds both files to the same names.

## 4. Oracle

`lean/Oracle.lean` is a long-lived process: one request per line, whitespace-separated naturals in, the answer out.
Change only the parsing (`parsePosts`, or nothing for a plain list of numbers) and `answer`; keep `loop` and
`main`. Encode booleans as 0/1. Lean keywords (`show`, `from`, `at`, `fun`, `matches`) can't be helper names. The oracle
calls the frozen reference (`spec`, `canEdit`), never `fast` or a helper. It prints the whole result in the same
shape the theorems compare (whole records, not ids).

**Text inputs** (diffs, paths, names): model them as `List Char` and send each string as its length followed by
its character codes (`ord`), so spaces, tabs and newlines survive the line protocol; answers that are strings come
back the same way. Several functions of one target get a tag each (`S ...`, `C ...`), as a second target does.

A second target shares the same oracle: start each request line with a target tag (`D ...` for dedupe) and
dispatch on it in `answer`. When the model is generic over a predicate the production code computes (same
product, relevance), the test computes it with the real code and sends it as data, e.g. an n×n 0/1 matrix after
the records; memoise the pure dependencies the adapter calls n² times.

## 5. Differential tests

**Pattern E when the code has no fast path yet** ("make it faster"): write it now, before these tests, by step 6
(the fast branch, its guard, the old code kept as `_x_reference`). The tests and the mutants below need it.

In `tests/test_spec_oracle.py` keep the fixture and `ask`; write Hypothesis strategies for the inputs:
- small ranges so equal keys and duplicates are common (that is where sort and dedup bugs live);
- for a fast path, one strategy for any input (must take the fallback and still match) and one that satisfies
  the invariant (takes the fast path);
- the production numeric domain: the model is in `Nat`, the adapter scales to what the code really holds (scores
  rounded to hundredths → the model in hundredths); generate at several scales (whole numbers where floats are
  exact, and fractions), plus a strategy aimed at ties, since requirements rarely say how ties break;
- when the model folds several code conditions into one flag (`barred` for five reasons), the adapter draws which
  condition fired, so each code path is exercised;
- when the code compares values looked up through a map (account → bank), generate maps where different keys share
  a value (two banks share an account); otherwise a mutant that compares the keys instead survives;
- pattern S: generate event sequences and drive the real loop with every collaborator monkeypatched to a scripted
  fake that records the trace (`pytest.MonkeyPatch.context()` inside the `@given` test; a function-scoped fixture
  trips Hypothesis's health check). Signal "events ran out" with a `BaseException` so no `except Exception`
  swallows it, and fake every helper that calls the environment again. `st.one_of` favours its simplest branches
  (80% of runs had one attempt): weight the branches and report the run lengths with `hypothesis.event`;
- pattern C: control the fake's clock (fakeredis: patch its module-level `time`, add 1 µs per command so expiry
  at exactly c+W matches the model's [c, c+W)); generate timelines with bursts on window edges; add a load test,
  thousands of requests over a simulated day at the real config, checking the proved caps and code == oracle.
  Short Hypothesis timelines missed a mutant the load test caught.

Keep the adapter (model value ↔ production objects) in the test file. The test imports hypothesis at the top, so
hypothesis goes wherever the repo declares its test dependencies, or the repo's own CI fails collecting the file:
`uv add --dev hypothesis` in a uv project (`uv run --with` does not reach the venv's pytest), else the dev
requirements file, the pyproject test extra, or the CI install step. The example's `uv run --no-project --with
hypothesis` in `gate.sh` is for the standalone example only; set `TEST_CMD` to the repo's command. No
`importorskip`: a missing hypothesis must fail, not skip. Skip the oracle module only when lake is missing, and
then CI needs the lean job from `references/setup.md`.

Compare whole values, exactly what the theorem compares. When the code and the model hold the same content in
different containers (a set against a per-hunk list), normalise both to one form (sorted, deduplicated) and say why
in a comment. Run the plain tests, with no masks, before any other change
to the production code (a new fast path is the only one allowed first) or writing any known-finding mask: Hypothesis finds the disagreement, not your reading of the code. When
one fails, report the shrunk counterexample (input, what the code returns, what the model returns) before changing
code; wait for the user only if they have not already said to fix it. When the code must not be changed now
(map mode, or the user decides later), keep the gate green with pinned counterexamples:
`references/known-findings.md`. Hypothesis shrinks and shows one failure per test per run, so several findings
come out one round at a time; expect a few rounds of run, record, mask.

**Mutation check (required).** Break the production code at least three ways and confirm each fails a test, then
restore (`cp` a backup, `cmp` after):
- pattern A: drop one condition or branch, flip one comparison (`==` to `!=`, `<` to `<=`), reorder two checks;
- pattern E: drop the guard, weaken the key or comparison, weaken the invariant check (`<` to `<=`);
- pattern S: forget to mark a target as tried, retry on a kind that must not retry, record on an intermediate
  attempt, pick the wrong untried target, an off-by-one in a counter, a flag that is never reset;
- pattern C: `>` to `>=` on the limit, drop the expiry repair, reset the expiry on every hit, fail closed instead
  of open (or the reverse), a key without its namespace, an expiry of W+1;
- an index or cache in the fast path: forget to update the index when the state changes (a survivor is
  replaced), keep a stale cached value, pick the wrong one of several matches (max instead of min, last instead of
  first).

Default random inputs rarely reach index and cache bugs. Generate near-copies of a few base records (same brand,
small title and price changes) so states change often, and pin the minimal example that kills each mutant with
`@example`.

A mutation that survives means the test compares less than the theorem; fix the test. The exception is an
equivalent mutant: one that changes only which branch runs, not the result (`<=` to `<` in a non-strict check
sends sorted input with repeats to the fallback). Name it as such in the report instead of chasing it. Rerun the
mutation check after adding any known-finding mask: a mask wider than its finding hides mutants.

## 6. Fast path in the production code (pattern E only)

The code mirrors the model: `is_ordered` (or the target's check) mirrors `checkInv`, the fast branch mirrors
`fast`, the fallback calls the reference. Docstrings name the theorem each piece relies on. The check runs where
the invariant could break (on each call, at startup plus on each write, or when another writer is detected).

When the condition is a property of a predicate ("every pair the same-product test matches shares a brand or
model key") rather than of the data, a runtime check would cost what the fast path saves. Then there is no guard:
a property test checks the condition on real and generated inputs, and the report says the theorem's hypothesis is
only tested. When the bucket key is part of the condition itself (equal amounts, dates within a window), the
theorem needs no hypothesis at all: no guard, no property test, nothing to check at runtime. Keep the old
implementation next to the new one (`_x_reference`) for the tests.

**Measure before and after.** A speed-up is claimed only with numbers: median and p95 per call, warm-up, GC off,
same inputs, at the sizes production really sees and at least one larger size. Measure the small size too:
precomputing features or building an index can cost more than it saves on small inputs (bucketed dedupe was 2x
slower at 50 items until the model book was compiled once). The "before" numbers come from step 1; the "after"
numbers are taken here, on the same inputs.

## 7. Gate

```bash
lean/gate.sh
```

Edit `TEST_CMD` at its top to the test command the repo's CI runs, or the whole `tests/` directory when there is
no CI, so the old tests stay part of "done". If something has to be left out (a GUI extra not installed), say what and why in a comment there. It runs `lake build`, a grep for what the kernel cannot see (`sorry`, `native_decide`, `axiom`,
`implemented_by`, `extern`, `unsafe`, `skipKernelTC`, `debug.`; whole words, comments too: reword a comment that trips it),
a check that `comparator.json` names exactly the theorems in `Frozen.lean` and that every frozen definition the oracle
calls is reached from one of them, `lake comparator` (statements and model
definitions equal `Frozen.lean`, standard axioms only, kernel accepts), then the tests. The comparator's `sorry`
warnings from `Frozen.lean` and its long "Exporting" lines are expected; the verdict is the last line. Never weaken the gate or `Frozen.lean` to get green; see `references/cheating.md`.
Wire it into CI and the Stop hook (`references/setup.md`) if the user wants it to stay true. With `TEST_CMD` set to
the CI command, a CI job without lake skips the oracle tests: a green CI is not the gate until the lean job from
`setup.md` runs there. Say which one the report means.

## 8. Report

End with two lists, always:
- **Proved:** each theorem named in `comparator.json`, in one plain sentence; helper lemmas are not claims.
- **Only tested:** the production code's agreement with the model (N examples per test, the mutations caught),
  and everything outside the model (IO, parsing, the DB, concurrency).

Plus where the runtime check sits and what happens when it fails, and in map mode the findings with their
numbers. Pattern C adds a capacity table: endpoint, L, W, proved maximum per window, per any W seconds and per
day at the real config, with the faults that are added on top. Without this section the task is not done.

## 9. Map mode: write back to the map

Only in map mode, see `references/map-mode.md`: a `Proved:` line in the step, a check in the map's test that the
path exists, findings where the map's "Known gaps" points, and a note that the mirror (`logic-map.ru.md`) needs
the same line.

## Rules

- One target per run. A second target gets its own folder under `lean/Spec/` and its own approval, next to the
  first one (§2, "If `lean/` already exists").
- Absolute paths in every shell command and file write: the shell's working directory can reset between calls,
  and a relative path then lands in another repo.
- Statements and `Frozen.lean` change only with the user's explicit consent, and then both together. The one
  exception is the pattern S flip to `¬ Claim` in step 3 under a pre-approval.
- No `sorry`, `native_decide`, `axiom`, `implemented_by`, `@[extern]` or `unsafe` outside `Frozen.lean`.
- Lean 4 syntax only (`fun x =>`, `by`, no `begin ... end`, no `λ x,`). APIs drift between releases: when a name
  fails, search the toolchain source (`~/.elan/toolchains/*/src/lean/Init`) rather than guessing.
- Don't promise more than was proved: "proved" applies to the Lean model; the production code is "tested
  against the proved model".

## Sources

The pattern follows lean-derive-hargup
(github.com/arjaythedev/twelve-dollar-server-challenge, submissions/lean-derive-hargup) and AWS Cedar's
Lean model with differential testing (arXiv:2407.01688).
