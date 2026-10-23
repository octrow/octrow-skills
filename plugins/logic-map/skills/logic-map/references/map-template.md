# Logic map template

Fill the skeleton with the project's own terms. Drop a section only when the project has nothing for it (no optional dependency, one entry point, no per-kind splits). Placeholders are in `<angle brackets>`.

## Map skeleton (`docs/logic-map.md`)

````markdown
# Logic map

How <one input: a request, a file, a message> becomes <the output>.
The map describes the code as it is today, step by step.
Each step says what it decides, where the flow branches, and which module does it.

Read `<glossary, e.g. CONTEXT.md>` first for the terms.
Known gaps and fixes in progress are in `<docs/plans/DATE-logic-map-fixes.md>`.

Rule: if you change a step or a branch, update this file in the same commit.
`<tests/test_logic_map.py>` checks that every `Module:` line points to a real module.
<The <language> mirror is `docs/logic-map.<lang>.md`; this file is the source of truth.>

## The flow at a glance

```
<input>
  │
  ├─ 1  <step> ............ <the question it answers, one line>
  ├─ 2  <step> ............ <...>
  │     ...
  └─ N  <step> ............ <...>
  │
<output type>
```

<One or two lines on what never enters the main path, e.g. a source that only feeds a side section.>

## Where the flow splits by <kind>

<Kind = the dimension behavior differs by: category, tenant, file type, channel, plan tier.>
<One sentence on how the split is decided today: one registry, or several independent signals.>

| <Kind / variant> | Switched on by | Steps it changes | What changes |
|---|---|---|---|
| <variant> | <signal: config, stored record, regex over input, word stem> | <step numbers> | <one line> |

Examples:
- "<real input>" → <which variants turn on and what they do>.
- <input with no known kind> → <the default path>.

Module: `<module>`, `<module>`

## Entry points

All entry points call `<core function>`. They differ in defaults.

| Entry | <Default A, e.g. sources> | <Default B, e.g. LLM> | Notes |
|---|---|---|---|
| <CLI `cmd`> | <value> | <value> | <overrides it applies, questions it asks> |
| <API / MCP / GUI / worker / cron> | <value> | **<value that differs>** | <what it overrides silently> |

Module: `<module>`, `<module>`

## Steps

### 1. <Step name>

Decides: <what this step determines, one line>.
In: <input>. Out: <output>.
Branches:
- <signal> → <path>;
- <signal> → <path>.
<No LLM / Offline / No key>: <what changes without the optional dependency>.
Fails: <fail-open / fail-closed / stops the run with X / silent default Y>.
Module: `<package/module>`, `<package/module>`

### 2. ...

### Output

`<Result type>`: <what it holds>.
Flags the surfaces show: `<flag>` (<when set>), ...
Module: `<module>`

## Side flows

### <Side flow name>

<What it builds or refreshes, how it is started, what it writes.>
Feeds: step <N>, ...
Module: `<module>`

## Known gaps

Short list; details and fixes are in the plan (number in brackets).
- <One line per open HIGH or MEDIUM finding> (#<N>).
````

## Step fields

| Field | Rule |
|---|---|
| `Decides:` | Required. What the step determines. This is the answer to "where is X decided". |
| `In:` / `Out:` | When the data changes shape. Name the types. |
| `Branches:` | Every branch with its signal: flag, config, stored record, input pattern, threshold value. |
| `<No LLM>:` | Name it after the project's main optional dependency (`No LLM:`, `Offline:`, `No key:`). Omit if the step does not change. |
| `Fails:` | What a failure does. "Fail-open" alone is not enough: say what is kept. |
| `Module:` | Required. Modules or packages relative to the package root, slash-separated, no extension, in backticks. No functions. The test reads this line. |

Write the step on one screen. A step that needs more than 15 lines is two steps, or carries detail that belongs in the code.

## Findings plan (`docs/plans/<date>-logic-map-fixes.md`)

Write it in the language the owner reads plans in.

````markdown
# Plan: logic map findings

Findings from writing `docs/logic-map.md` on <date>, plus the independent review of the map.
The map describes the code as it is; this file says what is wrong with it and what we propose. New findings are appended.
A fixed finding gets ✅ and the map is updated in the same commit.

Severity: HIGH: wrong result for the user. MEDIUM: worse result than it could be. LOW: noise, debt, docs.
"Question": not sure if bug or intent; <owner> decides. "Not confirmed": needs a live run.

## Findings

| # | Map step | What is wrong | We propose | Severity |
|---|---|---|---|---|
| 1 | <step numbers or "Entry points"> | <fact with `file:line`, an example input> | <fix, or the question to decide> | HIGH |
| 2 ✅ | ... | ... | ... | MEDIUM |

## Order of work

1. <group of findings that share files or tests>.

## Done when

- [ ] every finding has ✅ or a "keep as is" decision with a reason;
- [ ] Known gaps in the map lists every open HIGH and MEDIUM finding.
````

## AGENTS.md snippet

````markdown
# Agents: start here

1. `<glossary>`: the domain terms.
2. `docs/logic-map.md`: how <input> becomes <output>: every step, every branch, the module behind it.
3. `docs/plans/`: work in progress; `<date>-logic-map-fixes.md` lists the known logic gaps.

Rules:
- Change a step or a branch → update `docs/logic-map.md` <and the mirror> in the same commit.
- `<tests/test_logic_map.py>` fails when a `Module:` line in the map points to a module that is gone.
````

## Live-run set (in the report or the plan)

| Input | Branch it should take (step) | Look at |
|---|---|---|
| "<real input>" | <step N: branch> | <field or line in the output> |
