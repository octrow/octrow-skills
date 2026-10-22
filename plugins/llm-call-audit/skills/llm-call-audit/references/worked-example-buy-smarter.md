# Worked example: buy-smarter audit (2026-10-22)

Repo: `~/projects/buy-smarter` (Python, marketplace product recommender). Use this to calibrate how deep to go and what a finding looks like; the specific files and numbers belong to that repo, not to yours.

## Setup that the audit found
- Entry points: `llm/adapter.py::generate(prompt, response_model, model=...)` (Pydantic-validated JSON, mandatory cache, one retry on validation error) and `llm/jev.py::system_one(state, questions)` (TypeSafe).
- Providers: OmniRoute OpenAI-compatible gateway, combo `free-stack` (first rung a fast flash model); `claude` CLI for `opus`/`sonnet` (web-search grounding via `cli_tools="WebSearch"`).
- Evidence sources: app log (per-call tokens, latency, `cache hit`/`cache store` lines, stage timers), the sqlite LLM cache `~/.cache/buysmarter/llm_cache.db` (table `llm_cache`: provider, model, prompt_version, prompt_text, response_text, structured_json, cost_usd, latency_ms), OmniRoute call logs (answering model, timeouts/499, finish_reason).

## Inventory (call sites at the time; line numbers drift)
| Site | Decides | Path |
|------|---------|------|
| `llm/prompts.py` parse_query | free-text query → constraints (category, budget, city, features) | LLM `free-stack`; regex fallback |
| `llm/relevance.py` filter_relevant | is each search hit the product or an accessory | code heuristic → Jev Noul per title → LLM fallback |
| `llm/canonicalize.py` | which known model an OLX title names | Jev Choice over known models + "none" → LLM fallback |
| `llm/ingredients.py` | which active substance/concentration a cosmetic contains | Jev Noul per (candidate, substance) + Choice over code-found percentages → LLM fallback |
| `llm/review_summary.py` | pros/cons/verdict from ≤30 reviews; feature checks | LLM summary; Jev for per-sentence feature labels |
| `knowledge/store.py` resolve_profile | which stored category profile matches a new category | exact → synonyms → Jev Choice → LLM fallback |
| `knowledge/generate.py` | build brand/model books for a category | `opus` + web search (generate), `sonnet` (extract from notes) |

## Findings that turned into shipped changes (see the repo's CHANGELOG 0.6.0–0.6.1)
1. **Dead first gateway rung** — the first rung of the combo timed out at 40 s on every call before the next rung answered. Biggest single latency cost. Evidence: gateway logs (timeouts, answering model ≠ first rung). Fix: route change in the gateway, no code.
2. **Weak LLM fallback on "Jev unsure" (category match)** — cost 40–60 s per call and answered «чехол для iPhone 15» → «смартфон». Fix: unsure Jev means "no related category". Evidence: cache rows for the fallback prompt + the wrong answer.
3. **Weak LLM fallback on unsure model names (OLX)** — 40–60 s per search, and once named every «iPhone 13» ad «Apple iPhone 17 Pro Max». Fix: take only confident Jev picks; LLM runs only when Jev itself fails. Plus a **model guard**: drop an LLM name whose model number/line/storage contradicts the ad title, so it is never learned as an alias.
4. **Output cap truncated JSON** — `learn` on notes listing ~30 phone models came back cut off (`finish_reason=length`). Fix: chunk in code (10 list items per call, each with the notes' intro) and merge; short notes keep the same single prompt (so their cache stays valid).
5. **Code rule over model** — model title resolution picks the entry with the longest matching alias («Galaxy S24 FE» is the S24 FE, not the S24): a deterministic rule, no model needed.
6. **Code prefilter checked against positives** — substring category matching was removed («чай» borrowed «чайник»'s brands), but a stem-only prefilter was rejected because legit matches like «солнцезащитный крем» → «косметика» share no stem.
7. **Named-model relevance bypass** — a title that names the queried model skips the relevance pass entirely (skip a call when cheap code already decides).

## What the report looked like per site (shape, condensed)
```
### Related category match — knowledge/store.py:367
Decides: which stored category profile a new category inherits from
Now: Jev Choice; on low confidence → free-stack LLM · once per run · LLM fallback 40–60 s [measured: app log stage timer + cache latency_ms]
Recommend: drop the LLM fallback; unsure Jev = no related category
Why quality holds: the fallback's cached answers include «чехол для iPhone 15» → «смартфон»; Jev's confident picks were right on the checked cases
Risk: a real but unusual match is missed → category runs without a parent (degrades, doesn't break)
Regression check: unit test "unsure Jev returns no related category"; live query «чехол для iPhone 15»
```

## Lessons to carry to other repos
- Fallbacks are where the time and the wrong answers hide; audit them first.
- A stage timer that starts after the classifier already ran makes the classifier look free — read where timers begin.
- Distinguish measured numbers (log/cache/gateway rows) from estimates in every line.
