# llm-call-audit

**English** | [Русский](README.ru.md)

A skill that goes through every model call in a codebase and finds the cheapest option that keeps quality.

## Install

```bash
claude plugin install llm-call-audit@octrow-skills
npx skills add octrow/octrow-skills --skill llm-call-audit -g
```

## What it does

For each call it suggests one of these:

- plain code;
- a TypeSafe/Jev classifier;
- a cheaper or stronger LLM;
- a smaller prompt;
- a fixed gateway route.

It takes the numbers from app logs, the LLM response cache and gateway logs. It writes a report and changes nothing.

## Ask

- "audit the LLM calls, search takes a minute"
