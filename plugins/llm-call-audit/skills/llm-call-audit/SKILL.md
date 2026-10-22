---
name: llm-call-audit
description: Audit every model call in a codebase and recommend, per call site, the cheapest option that keeps quality — plain code (regex, tables, existing helpers), a TypeSafe/Jev classifier (choice/noul/score) for closed-set decisions, a cheaper vs stronger LLM, context cuts (oversized prompts, dumped schemas, unread or overridden fields, missing cache, batching/parallel/skip), and LLM gateway route/latency fixes (OmniRoute combos, dead rungs timing out). Measures from app logs, the LLM response cache DB and gateway logs instead of guessing; read-only report by default. Use whenever the user says "audit LLM calls", "where can we replace the LLM", "cheaper model", "Jev instead of LLM", "LLM is slow/expensive", "сократить контекст", "где можно код вместо LLM", "где использовать jev", "почему поиск такой медленный из-за LLM", "llm-call-audit", or asks to cut LLM cost, tokens or latency in a project — even if they name only one call site.
---

# LLM call audit

Goal: for every place the code asks a model something, find the cheapest option that keeps answer quality, backed by measured numbers. The output is a report. Stay read-only unless the user explicitly asks to implement; the report is what lets them decide, and a half-applied change set is harder to review than a clear list.

## The ladder (per call site, stop at the first rung that holds)

1. **Plain code** — regex, lookup table, an existing helper, a deterministic rule. Only if it holds on the real positives (see pitfalls).
2. **Jev / TypeSafe System One** — closed-set decision, yes/no, rating, picking one item from a list, picking a span that code already found. ~10x faster/cheaper than an LLM, typed answers with probabilities. Read `references/jev-cheatsheet.md` before recommending it.
3. **Weaker/cheaper LLM** — extraction, reformatting, short summaries where the answer is in the input.
4. **Stronger LLM** — real reasoning, open generation, web-grounded facts. Keep it here; don't downgrade what the logs show it does well.

Independently of the rung, check **context cuts** and **gateway routing** (steps 4–5 below) — they often save more than a model swap.

## Method

### 1. Inventory every call site
Grep the project's LLM entry points (its own wrappers like `generate(`, `system_one(`, plus SDK clients: `openai`, `anthropic`, `litellm`, `httpx` calls to `/chat/completions`, `claude -p` subprocesses). For each site record: `file:line`, what it decides, the response schema, model/provider (resolve config/env, not just the default arg), and when it fires (per request, per item, per run, on fallback only). Note fallback chains (Jev → LLM, cache → LLM).

### 2. Measure, don't guess
Pull numbers from what the app already writes:
- **App logs**: per-call token counts, latency, cache hit/store lines, stage timers. A stage timer can hide work done before it starts (e.g. a classifier run during setup) — check where the timer begins.
- **LLM response cache DB** (sqlite/Postgres): prompt_text, response_text, model, latency, cost per row. Group by prompt version/model; look at prompt sizes and the longest latencies.
- **Gateway call logs** (OmniRoute or similar): which model actually answered after fallbacks, timeouts/499s, `finish_reason` (`length` = output cap hit), output-token caps.
Label every number in the report as **measured** (with the source) or **estimated**. If nothing is logged for a site, say so and propose the one log line that would measure it.

### 3. Find the quality failures
Search the cache/logs for known bad answers (bug reports, changelog "Fixed" entries, user complaints). Record which model and which path produced each. A cheap model that produced the known-bad answers is a reason to remove that path, not to tune it.

### 4. Context cuts
Per prompt look for: oversized state; Pydantic/JSON schema docstrings dumped into the prompt; instructions duplicated between system and user parts; fields the LLM generates that code overrides or nobody reads (delete them from the schema — fewer output tokens, fewer failure points); missing cache or a cache key that changes every call; independent calls that could be one batched call or run in parallel; calls that can be skipped when a cheap check already decides. Remember exact-prompt caching: changing a prompt invalidates the cache once — mention it, don't let it block the change.

### 5. Gateway route and latency
Read the gateway combo (e.g. OmniRoute `free-stack`): rung order, per-rung timeout, which rung answers in practice. A dead or rate-limited first rung that times out on every call adds its full timeout (40 s in the worked example) to every request — usually the single biggest latency cost. Recommend reordering/removing the rung or a shorter timeout, with the log lines as evidence.

## Pitfalls (learned the hard way)
- **"Classifier unsure → weak LLM" fallbacks** often add 40–60 s and produce wrong answers. Check the logs for what the fallback actually returned before keeping it; "unsure means no match" is often the better default.
- **Code prefilters can break legit broad matches**: «солнцезащитный крем» → «косметика» share no stem. Verify every proposed code rule against the real positives in the cache/logs, not just the negatives you want to cut.
- **Output caps truncate JSON** on long inputs (`finish_reason=length`). Chunk the input in code and merge, rather than raising the cap and hoping.
- **A model guard is cheap insurance**: reject an LLM label that contradicts the input (e.g. its model number differs from the one in the title).
- **Remove LLM-generated fields a classifier overrides** anyway.
- Jev is literal, bad at counting/arithmetic/date comparison and generation — keep those in code (see cheat-sheet).

## Report format

Per call site:

```
### <short name> — <file:line>
Decides: <what>
Now: <model/provider> · fires <frequency> · <tokens in/out> · <latency> [measured: <source> | estimated]
Recommend: <rung / cut / route change>
Why quality holds: <evidence: cache rows, positives checked, Jev fit>
Risk: <what could regress>
Regression check: <test name or live query that would catch it>
```

Then **Top 5 changes**, ranked by saving × confidence:

| # | Change | Saving (measured/est.) | Confidence | Effort S/M/L |
|---|--------|------------------------|-----------|--------------|

Close with what was not measured and the log lines that would fill the gap. Offer implementation; don't start it unasked.

## References
- `references/jev-cheatsheet.md` — question types, limits (255 Choice options, 32k per-question / 64k per-request context), batching, "select, don't generate", jaggedness. Read before recommending Jev. For details beyond it, read the live docs at https://docs.typesafe.ai/llms.txt.
- `references/worked-example-buy-smarter.md` — a real audit (2026-10-22) with call sites, findings and the fixes that shipped. Read it once to calibrate depth and tone of the report.
