# Jev / TypeSafe System One cheat-sheet

Source: https://docs.typesafe.ai (read 2026-10-23: primitives, choice, score, noul, models, request rules, confidence, fan-out, parallel-questions cookbook, jev-1.13 jaggedness). Docs are the source of truth — re-check `https://docs.typesafe.ai/llms.txt` when a number matters; append `.md` to any page path for Markdown.

## What Jev is
A System One model: takes `state` (string, JSON object or array) plus typed questions, returns typed answers with probabilities. It does **not** generate text, chat, or reason in steps. One endpoint `POST /v1/systemone`; Python `typesafe_sdk` (`TypeSafeClient` / `AsyncTypeSafeClient`, `client.system_one(state, questions)`).

## Question types
| Type | Use for | Returns |
|------|---------|---------|
| `choice` | one of a defined set (category, route, which item in a list) | `choice`, `probabilities` per option, `confidence` |
| `noul` | does condition X hold (yes/no) | `noul` = P(yes), 0..1; no separate confidence |
| `score` | position on ordered, described levels (severity, relevance, quality) | `score`, `probabilities` per level, `legend`, `confidence` |
| `box` | where something is in an image | four edges as fractions |

- Choice: up to **255 options**; options cost a few tokens each, so give the full list; add `other`/`none of the above` when the list may not cover the input.
- Noul near 0.5 means "unsure", not "medium". Starting thresholds: yes ≥ 0.7, no ≤ 0.3 (tune on your data).
- Several labels may apply → one Noul per label, not a Choice.
- Question IDs are not sent to the model: put the full meaning in `instructions`. Reference state fields by backticked path (`ticket.messages[0].text`).

## Limits and price (jev-1.13 / jev-1.14)
- Context: **64k tokens per request** (state + all questions), **32k per question** (state + one question). Long-context header `TypeSafe-Danger-Zone-Long-Context: true` raises both to 262k but is slower and less accurate.
- No limit on question count — only the context limits.
- Price: $0.042 per Mtok input; output free.
- Body ≤ 32 MiB; nesting ≤ 64 levels; finite numbers only (send IDs as strings). 429/529 → backoff (SDK retries).
- Aliases: `jev-latest` (stable), `jev-preview` (newest). Pin a versioned ID if confidence thresholds were tuned on it.
- English is the primary language; Russian/other works but with lower accuracy — test on real data and watch confidence.

## Batching
Put every question about the same state in **one request** — they run in parallel, latency barely changes, extra questions cost only their tokens. Include speculative questions (e.g. severity even if it may not be a bug) and let code ignore unused answers. The parallel-questions cookbook measured 13 questions batched vs one-per-call: 12.2x cheaper, 10.0x faster, same answers. A second request is justified only when an answer is needed to build the next state or options.

## Select, don't generate
For extraction: find candidates in code (regex, parser, catalog lookup), then a Choice picks the right one; code copies/normalizes the verbatim value. Jev cannot pick a value that is not in the options — check candidate coverage.

## Jaggedness (jev-1.13, where it fails)
1. Literal reading — write the exact condition; put boundary cases in criteria.
2. Math, counting, numeric closeness — do it in code.
3. Date/time comparison — extract parts (Choice), compare in code.
4. Indirection / double negation — reduce hops, name the state field.
5. Large irrelevant state — filter in code first; context rot hurts accuracy.
6. Adversarial content in state can steer it.
7. Instructions and criteria that contradict each other.
8. Choice option order bias toward the first option — reorder to check consistency.
9. Generation — use an LLM.

## Good Jev candidates in an LLM audit
- LLM prompt that returns a label/enum/bool/index → Choice/Noul.
- "Pick the matching item from this list" (category match, model/alias match, rerank) → Choice over the list (≤255) or per-item Noul/Score.
- Relevance filtering of N items → per-item Noul/Score in one batched request.
- Guardrail or verification of an LLM answer → Noul.
- Not a candidate: free text, summaries, web-grounded facts, multi-step reasoning, arithmetic.

## Confidence
Choice/Score `confidence` = how peaked the distribution is (1 = all on one, 0 = flat). Thresholds scale with the cost of a wrong action. Low confidence with "no match" available often means "no match", not "ask an LLM".
