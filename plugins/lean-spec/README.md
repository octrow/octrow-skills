# lean-spec

**English** | [Русский](README.ru.md)

A skill that checks one piece of logic against a short Lean 4 model, or makes it faster with a proof that the result does not change.

## Install

```bash
claude plugin install lean-spec@octrow-skills
npx skills add octrow/octrow-skills --skill lean-spec -g
```

Linux only. Needs Lean 4.35 (elan) and bubblewrap.

## How it works

- The theorem statements are approved and frozen.
- Lean's kernel checks the proofs.
- The production code (Python first) is tested against the model as an oracle, with Hypothesis.

## What it covers

- A fast path gets a theorem "fast = spec under an invariant", a runtime check and a fallback. Example: lean-derive-hargup (280k users on a $12 VPS).
- A retry loop or state machine gets its safety claims proved under any sequence of failures.
- A rate limiter or quota gets its capacity proved, for example how many attempts per IP per day.
- The rules can come from a step of the logic map. Each theorem quotes its line, and whatever the map leaves vague becomes a finding.

## Done means one gate

1. `lake build`
2. a grep for cheats the kernel cannot see
3. `lake comparator` against the frozen statements
4. the tests

## Ask

- "verify feed_fast with Lean"
- "check step 18 of the logic map with Lean"
