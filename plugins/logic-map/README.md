# logic-map

**English** | [Русский](README.ru.md)

A skill that writes, updates or checks `docs/logic-map.md`: one file an agent reads first.

## Install

```bash
claude plugin install logic-map@octrow-skills
npx skills add octrow/octrow-skills --skill logic-map -g
```

## What the map shows

Step by step:

- where the main flow splits;
- what each step decides;
- what changes without the LLM, network or key;
- how the step fails;
- which module does it.

## What it does with it

Logic bugs it finds go to a numbered findings plan. It does not change code.

Two things keep the map honest: a same-commit rule in `AGENTS.md`, and a test on the `Module:` lines.

## Ask

- "map this pipeline for agents: where it splits and which module does each step"
