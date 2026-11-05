# system-design

**English** | [Русский](README.ru.md)

A skill that designs or reviews a backend's architecture from numbers.

## Install

```bash
claude plugin install system-design@octrow-skills
npx skills add octrow/octrow-skills --skill system-design -g
```

## What it does

1. Starts with requirements.
2. Runs napkin math from a script: DAU to requests per second, app servers, cache memory, database reads and writes, replicas, shards, storage, egress.
3. Picks the smallest rung of the scaling ladder that carries those numbers.
4. Picks the storage engine and cache pattern that fit the access pattern.
5. Writes a failure plan and says the trade-offs out loud.

On an existing repo it reads the real stack and metrics first.

## Ask

- "will this FastAPI app hold 2M DAU on one VPS?"
- "design a photo sharing backend for 20M DAU"
