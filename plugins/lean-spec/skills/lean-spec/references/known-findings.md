# Known findings: a green gate while the code still disagrees

Use when a differential test found a real disagreement and the code must not change now (map mode, or the user
decides later). The gate stays green, every known disagreement stays visible, and fixing the code forces the tests
to be updated.

## Order

1. Write the plain differential test and run it with no masks. Record each shrunk counterexample.
2. Only then add a mask and a pin per finding.
3. Rerun the mutation check.

## Three pieces in the test file

1. **A classifier for the property tests.** A table of named predicates, each true only for its finding:
   ```python
   KNOWN_FINDINGS = (
       ("#27 best skips a price-0 listing", _price_zero_best),
       ("#28 premium outside the top quarter", _premium_outside_quarter),
   )

   def known_finding(inputs, code, model) -> str | None:
       return next((name for name, hit in KNOWN_FINDINGS if hit(inputs, code, model)), None)

   def check(oracle, inputs):
       code, model = run_code(inputs), ask(oracle, inputs)
       if code != model:
           name = known_finding(inputs, code, model)
           assert name, f"new disagreement: code {code}, model {model}"
           hypothesis.event(name)          # counts show in `pytest --hypothesis-show-statistics`
   ```
   A narrow mask often needs the oracle too ("the code equals the model's price at `total - 1`"); pass it in as a
   fourth argument rather than widening the mask.
2. **Pinned counterexamples.** One shrunk input per finding, re-minimised by hand with realistic numbers, in a
   dict next to the tests.
3. **Strict xfail on the pins.** `@pytest.mark.xfail(strict=True, reason="#28 ...")` on a test that asserts the
   code equals the model for that pin. When someone fixes the code, the pin passes, strict xfail turns that into a
   failure, and they remove the mask and the pin together.

## A claim the code breaks (pattern S)

When the model is the code and the finding is a false claim (from a docstring or the docs), the proof of
`¬ Claim` names its witness. Pin exactly that witness with strict xfail on a test that asserts the claim on the
real code, and keep a plain test that the code still equals the model there, so the pin fails for the right
reason. No classifier mask is needed: the differential test agrees everywhere.

## Masks must be as narrow as the finding

A mask that matches more than its finding hides mutants. In the pilot two of three surviving mutants sat inside
masks:
- a float-rounding finding was masked for any value-pick mismatch; narrowed to cases where the float comparison
  really differs from the exact one;
- a premium-fallback finding was masked for any premium mismatch; narrowed to "the code's pick is the priciest
  free A/B candidate".

After adding or changing a mask, rerun the mutation check.
