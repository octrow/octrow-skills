# Patterns: where Lean sits next to production code

| | Pattern | When | Cost | Reference |
|---|---|---|---|---|
| **A** | Lean model + differential tests of the production code | A rule-heavy core (authz, pricing, parsers, state machines) whose production code stays in Python/Go/Rust | A second, small implementation and a test harness. Proofs cover the model only | AWS Cedar: Lean models ~10x smaller than the Rust; proofs found 4 bugs, differential tests 21 more (arXiv:2407.01688) |
| **E** | Proved fast path + runtime guard + fallback | A shortcut that is right only under a data invariant (a scan instead of a sort, a cached aggregate, a skipped check) | A, plus an invariant, its checker and two theorems | lean-derive-hargup: `feedPlan_eq` under `Db.Inv`, startup check, fallback to the spec's SQL |

This skill does A and E. The rest, for when the user asks:

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

## Choosing the invariant (E)

- Make it the weakest fact the shortcut needs. Strict or non-strict depends on the data: for records with equal
  keys and a stable sort it must be strict (equal keys keep their order under the sort and flip under a reverse);
  for dropping repeats from sorted numbers it must be non-strict, because the input has repeats.
- The checker is linear and local (neighbours, counts, a version number) so it can run at startup or per call.
- Say who can break it: other writers, migrations, manual edits. The guard runs where that can happen.

## What the model is not

Not the production algorithm in Lean. The model is the obvious version: sort and take, filter and check,
recursion over a list. Optimisation lives in `fast`, never in `spec`.
