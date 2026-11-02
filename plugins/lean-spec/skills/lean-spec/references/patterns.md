# Patterns: where Lean sits next to production code

| | Pattern | When | Cost | Reference |
|---|---|---|---|---|
| **A** | Lean model + differential tests of the production code | A rule-heavy core (authz, pricing, parsers, state machines) whose production code stays in Python/Go/Rust | A second, small implementation and a test harness. Proofs cover the model only | AWS Cedar: Lean models ~10x smaller than the Rust; proofs found 4 bugs, differential tests 21 more (arXiv:2407.01688) |
| **E** | Proved fast path + runtime guard + fallback | A shortcut that is right only under a data invariant (a scan instead of a sort, a cached aggregate, a skipped check) | A, plus an invariant, its checker and two theorems | lean-derive-hargup: `feedPlan_eq` under `Db.Inv`, startup check, fallback to the spec's SQL |
| **S** | Model of a state machine under a fault model + differential tests on event sequences | A loop that reacts to failures: retries, provider fallback, reconnects, a protocol or job state machine | A model of the transition function, an event encoding, scripted fakes for every collaborator | jobs' draft retry loop (below); for distributed protocols Veil (CAV 2025) |
| **C** | Capacity and limits over time: counting bounds under a fault model + timeline and load tests | Rate limiters, quotas, queues, caps whose numbers matter (attempts per IP per day, calls per token) | A model of the store with time as data, a controlled clock in the tests, a capacity table | persona-crm's Redis fixed-window limiter (below) |

This skill does A, E, S and C. The rest, for when the user asks:

- **B. Logic written in Lean, called through the C ABI.** Small, high-stakes pure functions. FFI is unstable
  across releases; a binary that carries the Lean runtime is tens of MB. Go: LeanPort (cgo). Python: Nerodia
  (Lean FRO, proof of concept, Lean ≥ 4.35, CPython ≥ 3.14).
- **C. Translate existing code into Lean and prove it there.** Rust: Aeneas (and h5i for Axum apps). TypeScript:
  LemmaScript. Python/C++: lean-surfaces (young). The highest proof effort.
- **D. Write the service in Lean and prove it in place.** `vcgen` (Lean 4.35, `experimental.vcgen`, replaced
  `mvcgen`) for imperative `do` code; Velvet/Loom, Veil. Std has an HTTP/1.1 server since 4.31 and a client since
  4.34; the library ecosystem is young. Fine for a side service or CLI.
- **Lean as a code generator** (lean-derive-hargup's `derive`): Lean emits the production code from templates,
  and the build fails if the emitted file differs from the committed one. Worth it only for a hot path in C or
  Rust; not in v0.1 of this skill.

## E with a predicate property instead of a data invariant

The fast path skips comparisons the slow path would make (buckets, an index, early exit). It is equal to the slow
path when the comparison can only succeed inside a bucket: `same a b → shares a key a b`. The theorem is generic:
`(hkey : ∀ a b, same a b = true → ∃ k ∈ keys a, k ∈ keys b) → fast keys same xs = spec same xs`, with the predicate
given as data. The production predicate's key property is checked by a property test, not at runtime. Piloted on
buy-smarter's cross-source dedupe: 2.2x at 50 items, 74x at 178, 526x at 962, same output.

Here `spec` is the existing algorithm, not a requirement written elsewhere, so most of the model is
`-- silent:` choices read from the code (first match wins, comparison against the survivor, tie rules). That is
expected: what is claimed is equality of the two algorithms.

## E with no hypothesis

When the bucket key is part of the match condition itself, nothing outside the condition can put a match in
another bucket, so `fast w xs = spec w xs` holds for every input. Piloted on finance-insights' cross-bank transfer
pairs (different account, opposite sign, equal `abs(amount)`, dates within ±3 days): sort by (amount, date), scan
forward inside the bucket while the date is in the window, then sort the pairs back into the loop's (i, j) order.
78x at 1,000 rows, 615x at 6,200, 965x at 12,000, list equality with order. No guard and no property test.

## S: state machine under a fault model

Lean cannot see the network or the clock, so the environment is an input: one finite list of events, each the
outcome of an attempt plus what the environment answers next. `run init evs : Trace` recurses on that list; the
trace records everything observable (the target of each attempt, what was recorded or recovered, events logged,
the final result), and the test compares the whole trace.

- **What the model is.** The code's own transition function, not a requirement written elsewhere. The
  requirements are safety claims (terminates within N steps, never repeats a target, records once, never retries a
  non-retryable failure) and the promises in docstrings and docs.
- **Fault model.** Any outcome sequence, any answer from the environment at each step (reordered, new entries,
  empty, raising), any initial state. Name what is left out (time, which target an unobservable call really hit,
  log text) in the report.
- **False claims.** Each claim is a named `def Claim : Prop`; one found false while proving flips from
  `theorem claim : Claim` to `theorem claim_false : ¬ Claim` with a concrete witness, in Props and Frozen together. The gate
  stays free of `sorry`, and the witness is the strict-xfail pin.
- **Expect findings from the theorems, not the tests.** The model is the code, so the differential tests confirm
  the transcription; the bugs are where the code breaks a claim.

Piloted on jobs' `_run_single_draft` (draft retry with combo-provider fallback): 9 theorems proved (attempts ≤
providers + 1, no provider pinned twice, one tally only on the decisive attempt, retries only on
`usage_limit`/`timeout`), two docstring claims refuted (a call pinned to a provider skips an untried live provider
on its first retry; intermediate attempts do recover packets), 11/11 mutants caught over 1,500 event sequences.

## C: capacity and limits over time

The store is a value and time is a number on each event; `step` is the code's own transition (INCR, TTL check,
EXPIRE, allow or deny). The claims count allowed events in an interval.

- **Bounds, not equalities.** At most L per window, at most N in any interval of length W, at most M per day, no
  permanent lockout, nothing lost under load ≤ X. Each candidate first as `def Claim : Prop`: the textbook bound
  is often wrong. Fixed window: 2L−1 in any W seconds (2L only over W+1), and L·(D/W+1) per span D is false when
  W does not divide D (the right cap is `max(L·⌈D/W⌉, L−1 + L·⌈(D−1)/W⌉)`).
- **Faults as a term.** "allowed ≤ bound + requests that hit an error" is stronger than "no faults → allowed ≤
  bound" and costs nothing. Fail-open by design is a `¬ Claim` with a witness, reported as a trade-off.
- **Interleavings.** Two replicas on one key: a separate op-level model where each Redis command is atomic. A
  false claim there needs a legal schedule, pinned on the real code with asyncio events.
- **Numbers.** The real config (10 per 900 s, …) plugs into the general theorem as `decide` corollaries; the
  report's capacity table is these corollaries. `system-design`'s napkin math adds the cost side (each denied
  request still costs the store a round-trip), not the per-subject caps.

Piloted on persona-crm's Redis fixed-window limiter: 11 theorems, login ≤ 969 password guesses per IP per day,
LLM ≤ 749 calls per stolen token per day (Redis healthy); the LLM limiter fails open, so a Redis outage removes the
cap the docstring promises (a finding); two replicas can stretch a window by the INCR→EXPIRE delay.

## Choosing the invariant (E)

- Make it the weakest fact the shortcut needs. Strict or non-strict depends on the data: for records with equal
  keys and a stable sort it must be strict (equal keys keep their order under the sort and flip under a reverse);
  for dropping repeats from sorted numbers it must be non-strict, because the input has repeats.
- The checker is linear and local (neighbours, counts, a version number) so it can run at startup or per call.
- Say who can break it: other writers, migrations, manual edits. The guard runs where that can happen.

## What the model is not

Not the production algorithm in Lean. The model is the obvious version: sort and take, filter and check,
recursion over a list. Optimisation lives in `fast`, never in `spec`.
