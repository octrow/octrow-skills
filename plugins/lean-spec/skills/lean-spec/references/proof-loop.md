# Proof loop (when lean4-skills is not installed)

1. **Skeleton first.** All statements with `sorry`, `lake build` green, statements approved and frozen.
2. **One `sorry` per cycle.** Pick the one with the fewest dependencies; helper lemmas go above it.
3. **Read the goal before every edit.** With lean-lsp-mcp: `lean_goal` at the line, `lean_diagnostic_messages`
   for the file. Without it: `lake env lean <file>` and read the first error only.
4. **Automation first**, in this order:
   `rfl`, `decide`, `simp`, `omega` → `simp [defs] at *; omega` for Nat/Bool goals → `grind` → `exact?`,
   `apply?`, `simp?` (keep the "Try this" result, delete the search call). With lean-lsp-mcp,
   `lean_multi_attempt` tries several of these at one spot in one call.
5. **Search before naming a lemma.** `lean_local_search`, Loogle (by type), LeanSearch (by words), or grep the
   toolchain: `grep -rn "theorem .*mergeSort" ~/.elan/toolchains/*/src/lean/Init`. Confirm with `#check @name`.
6. **Structure for list proofs that worked in the example:**
   - induction that follows the function: `fun_induction f xs with | case1 ... | case2 ...`;
   - membership to indices: `List.getElem_of_mem`, then `List.pairwise_iff_getElem` and `Nat.lt_trichotomy`;
   - equality of two orderings: `List.Perm.eq_of_pairwise` (both sorted by an antisymmetric relation, permutations
     of each other), with `mergeSort_perm`, `pairwise_mergeSort`, `reverse_perm`, `pairwise_reverse`;
   - Bool comparisons: `simp [lt, before] at *; omega` closes most of them;
   - a model with `if c then … else …`: `have h : ¬ c := by omega` (or `c`), then `simp [defn, h]; omega`.
     `if_neg`/`if_pos` rewrites work but are deprecated in 4.35, and the suggested `ite_eq_right` misleads.
   - two passes over a list equal (a fast fold with an index vs the plain fold): prove a simulation. Generalise
     over the state: `∀ st st', R st st' → run (fold … st) = run (fold … st')`, where `R` says the index is
     consistent with the plain state; then induction on the list. `List.find?_filter` and a small
     `find?_congr` helper (equal `find?` when the predicates agree on members) close the step case.
7. **Explore tactics one at a time.** `first | a | b | skip` and `all_goals sorry` hide real errors (an unknown
   constant looked like an unsolved goal in the pilot).
8. **Stuck after ~5 attempts on one goal:** split it into a helper lemma, or recheck the definition. A goal that
   looks false probably is: evaluate both sides with `#eval` on a small input and show the counterexample.
9. **Commit at every green build.**

## Typical first errors on Lean 4.35

| Error | Fix |
|---|---|
| `le` expects `α → α → Prop` but got `Bool` | `(le := fun a b => f a b = true)` |
| `Unknown constant List.Chain'` / `IsChain` | not in core; write the recursive checker and prove soundness by `fun_induction` |
| `String.trimRight` / `List.allSome` unknown | `String.replace`, `List.mapM` |
| `List.mem_of_mem_filter` unknown | `(List.mem_filter.mp h).1` |
| `unexpected token 'show'; expected identifier` | a keyword used as a name; rename the helper |
| `invalid field notation` on `{ c with f := … }` inside a lambda | add a type ascription `({ c with f := … } : Cand)` |
| `decide` gets stuck on `spec` over a concrete list | `List.mergeSort` is well-founded recursion; use `simp [spec, fast, before, lt]` on the concrete input |
| unsolved `case2` after `fun_induction` | the catch-all case: `match` the list and close the impossible branch. The hypothesis is `¬xs = a :: b :: rest` (use `absurd rfl (h a b rest)`) or `xs = a :: b :: rest → False` (use `(h a b rest rfl).elim`); print it with `trace_state` |
| `Too many variable names provided at alternative case1` | an `if a = b` in the function substitutes `a`, so that case binds fewer names; drop the substituted one |
