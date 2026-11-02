# How an agent gets a green build without a proof, and what catches it

"Verified" below means it was tried on the example and the gate's result is the one shown.

| Cheat | What catches it | Verified |
|---|---|---|
| `sorry` left in a proof | gate grep; `lake comparator` (sorryAx is not a permitted axiom) | yes, grep |
| Weakened statement (extra hypothesis such as `n = 0`) | `lake comparator`: statement mismatch with `Frozen.lean` | yes |
| Model changed to make the proof trivial (`spec := fast`) | `lake comparator`: definition differs from `Frozen.lean` | yes |
| `@[implemented_by evil]` on `spec`: proofs hold, compiled oracle lies | **gate grep only.** The attribute is invisible to the kernel and to `lake comparator` | yes: comparator said okay, oracle returned wrong order |
| `@[extern]`, `unsafe` code in the oracle path | gate grep | no |
| `native_decide` (adds `Lean.ofReduceBool`) | gate grep; `lake comparator` axiom list | no |
| A new `axiom` | gate grep; `lake comparator` axiom list | no |
| `set_option debug.skipKernelTC` | gate grep | no |
| `Frozen.lean` edited to match the weakened statement | git diff of `Frozen.lean`; the rule that it changes only with consent | n/a |
| A frozen theorem left out of `comparator.json`, or a listed one missing from `Frozen.lean`: not checked, yet reported as proved | gate: the two lists must be equal | yes |
| `Frozen.lean` imports the model, so model edits move both | rule: Frozen is a self-contained copy | yes, by construction |
| Oracle calls `fast` or a helper instead of `spec` | review of `Oracle.lean`; the any-input test fails when `fast` is wrong off the invariant | no |
| Test compares less than the theorem (ids instead of records) | mutation check | yes: `<=` in the guard survived an id-only test |
| Gate script, `comparator.json` or test file loosened | git diff; never edit them to get green | n/a |

`#print axioms Name` or lean-lsp-mcp's `lean_verify` show the axioms of one theorem quickly while working; the
clean set is `propext`, `Classical.choice`, `Quot.sound`. The gate is what decides "done".
