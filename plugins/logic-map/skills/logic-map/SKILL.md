---
name: logic-map
description: Write, update or check a project's logic map (docs/logic-map.md) — the one key file that shows, step by step, where the main flow splits, what each step decides, what changes without the optional dependency (LLM, network, key), how it fails and which module does it; plus entry-point defaults, side flows, a "where the flow splits by <kind>" table and Known gaps linked to a numbered findings plan. Agent-first reader, under 500 lines, simple language, describes the code as it is. Kept honest by an AGENTS.md same-commit rule and a test on its `Module:` lines. Use whenever the user says «карта логики», «ключевой файл по логике проекта», «где поток делится», «на каком шаге что решается», «в какие модули идёт», «обнови карту логики», «сверь карту с кодом», "logic map", "map the pipeline", "document how a request flows through the code for agents", or changes a pipeline step in a repo that already has docs/logic-map.md — even if they don't name the file.
---

# Logic map

One file that tells an agent how the project's main flow works today: every step, every branch, the module behind it.
The map describes the code as it is. Plans, READMEs and docstrings describe intent; the map does not trust them.
Writing the map is also a bug hunt: anything wrong you find becomes a numbered finding in a plan. The map never fixes code.

Three modes. Pick by what exists:
- **Create**: no `docs/logic-map.md` yet → full method below.
- **Update**: code changed a step, a branch, a default or a module → "Update" section.
- **Check**: "сверь карту с кодом", or before trusting an old map → step 5 (review) on the existing map, then Update.

## Create

### 1. Grill first

Before writing a line, agree on these, one question at a time, each with your recommended answer. Look at the repo first so the questions carry facts (entry points, LOC of the flow, existing docs and plan conventions).

| Decision | Recommended default |
|---|---|
| Reader | an agent first, a human second → module names allowed, prose stays simple |
| Size | under 500 lines; a step is 8–12 lines, 20–25 steps ≈ 300 lines |
| Language | the language of the code and glossary (usually English) is the source of truth |
| Mirror | optional mirror in the human's language (`docs/logic-map.<lang>.md`), lower priority, edited in the same commit |
| Scope | main flow in full, plus entry points and short side flows that feed it |
| Step template | Decides / In→Out / Branches / degraded mode / Fails / Module (see template) |
| Findings | one plan file, a numbered table; the map's Known gaps links by number |
| Sync | AGENTS.md rule + a test on `Module:` lines |
| Writing mode | one pass by you, then an independent review, then the human reads the mirror |

If the user already answered some of these, don't ask again. If the user can't be reached, take the defaults and list them at the top of your report so they can overturn them.

### 2. Trace the real code, yourself

Start at every entry point (CLI commands, GUI, API, MCP, workers, cron) and follow the call chain to the output. Read the code, not the plans.

Do the trace yourself; don't hand it to a subagent. Findings appear when you compare a step with its neighbours, and a delegated summary loses that.

For each step note: what it decides, where it branches and on what signal, what changes without the optional dependency, what happens on failure (fail-open, fail-closed, stop the run, silent default), and the module.
Write down every surprise immediately as a candidate finding with `file:line`.

Look hardest at the usual misses (each one was wrong in a real first draft):
- **Entry-point defaults.** Each entry point has its own defaults: LLM on/off, sources, locale/city override, limits. A flag like `use_llm=False` may switch off far more than its name says.
- **Side effects.** What a run writes even when it looks read-only: caches, knowledge stores, snapshots, learned aliases. What `--no-save`-style flags actually skip.
- **Flags and help text that promise more than the code does.**
- **Fallback chains.** A fails → B → on B's failure keep everything / drop everything? Is a threshold applied on every path?
- **Lists that claim to be complete** (skipped steps, supported values) and aren't.
- **Config that nothing reads** (a section in a config file with no code behind it).
- **The same kind of split decided in several places** by hard-coded words or regexes. Collect these for the "where the flow splits by <kind>" table.

### 3. Write the map

Read `references/map-template.md` and follow it: header with the rules, flow diagram, the split table, entry points with their defaults, numbered steps, output, side flows, Known gaps.

Style:
- one fact per line; the step's first line says what it decides;
- concrete over general: thresholds, defaults, counts, example inputs in quotes;
- no filler, no evaluative words ("robust", "properly"), no "not X but Y" contrasts, no recap lines;
- `Module:` names modules or packages, never functions: functions get renamed often, modules rarely;
- no plans, no "will", no TODO. What is missing goes to Known gaps.

Count lines before you finish. Over budget → cut prose, not branches.

### 4. Findings plan

Every wrong or doubtful thing becomes a row in one plan file (`docs/plans/<date>-logic-map-fixes.md` unless the repo has another convention): number, map step(s), what's wrong with `file:line`, what we propose, severity. Template in `references/map-template.md`.

- HIGH: wrong result for the user. MEDIUM: worse result than it could be. LOW: noise, debt, docs.
- Not sure if it is a bug or intent → mark it "Question" and let the owner decide. Not reproduced → "Not confirmed", needs a live run.
- Numbers are never reused. Fixed → `✅` on the number, in the commit that fixes it.
- The map's Known gaps lists every open HIGH and MEDIUM, one line each, with `(#N)`.
- Don't pad the plan with LOWs: record one only if someone would act on it, and keep its row short. Twenty LOWs bury the three HIGHs.

Don't fix the code while mapping, even when the fix is one line. A finding the owner never saw is a decision taken behind their back, and mixing fixes into the map commit hides both.

### 5. Independent review

Send a fresh subagent on the strongest model available (Opus), read-only. Give it the map, the findings plan and the code paths. Don't give it your conclusions or doubts: it should read the code, not your summary. Ask for three things:
1. every claim in the map checked against the code, with `file:line`, entry-point defaults and side effects first;
2. are the findings real and is the severity right;
3. new logic errors in the flow itself.

Check its strongest claims yourself before applying them; a reviewer can be wrong too. Corrections go into the map; new problems go into the plan as findings.

### 6. Keep it in sync

- `AGENTS.md` (create a short one if the repo has none, or add to `CLAUDE.md` if that is the agent entry point): point to the map and add the rule "change a step or a branch → update the map (and mirror) in the same commit".
- Add the `Module:` test from `references/sync-test.md`. Run it; then point one `Module:` line at a fake module and confirm it fails. The test catches renames; stale logic is caught only by the rule and reviews.

### 7. Suggest a live run

Unit tests with fakes often hand the step already-parsed input, so they miss wiring between steps. A run on real inputs catches it: in one project, 10 real queries found 5 regressions in a branch whose 1200 tests were green.

Propose a small set, one real input per branch point in the map: input → branch it should take → what to look at in the result. Keep it to 5–12 inputs. Ask before running anything that costs money, needs credentials or hits external services.

### 8. Finish

Map, mirror, plan, AGENTS.md and test go in one commit, if the user wants a commit (follow the repo's git rules). Report: line counts, number of findings by severity, the top findings, what the review changed, the live-run set, and any defaults you chose without asking.

## Update

When code changes a step, a branch, a default, a side effect or a module:
1. Re-read the changed code and its callers; don't edit the map from the diff alone. If the map turns out wrong beyond the changed step, switch to Check: trace the whole flow and run the review (step 5).
2. Update the step fields, the flow diagram, the entry-point table and the split table as needed.
3. A fixed finding → `✅` in the plan, its line leaves Known gaps. New problem → new numbered finding.
4. Edit the mirror the same way.
5. Run the `Module:` test; check the line budget.
6. Same commit as the code change.

## The map as a base for architecture

The "where the flow splits by <kind>" table shows when one kind of decision (per category, tenant, file type, channel) is made in several unrelated places by hard-coded words. That is an architecture finding: propose one seam (a registry of optional hooks the core calls at fixed points, configured per kind) and record it as an ADR if the repo keeps them. In one project this table led to replacing words like «кроссовки» and «лекарство» in the core with per-category capabilities.

## References
- `references/map-template.md` — section skeleton, step fields, the findings plan table and the AGENTS.md snippet. Read before writing or restructuring a map.
- `references/sync-test.md` — the `Module:` test for Python (pytest) and a shell variant for other stacks.
