---
name: system-design
description: "Design or review a backend's architecture from numbers, not vibes: requirements first (functional, then non-functional as hard constraints), napkin math from a script (DAU to RPS, app servers, cache memory, DB reads and writes, replicas, shards, storage, egress), then the smallest rung of the scaling ladder that holds, the storage engine and cache pattern that fit the access pattern, failure planning and the trade-offs said out loud. Works on a blank page or on an existing repo, where it reads the real stack and metrics first. Use whenever the user says «спроектируй сервис», «архитектура для», «выдержит ли нагрузку», «сколько нужно серверов», «посчитай нагрузку», «какую БД взять», «нужен ли кэш / Redis / очередь», «как масштабировать», «что сломается первым», \"system design\", \"design X\", \"capacity planning\", \"back-of-the-envelope\", \"will this scale\", \"which database\", \"do I need a cache\", or prepares for a system design interview — even if they name only one of these pieces."
---

# System design

Turn a product description (or an existing repo) into an architecture whose every box is justified by a number
or a requirement. The usual failure is jumping to boxes: picking Kafka and Cassandra before anyone counted
requests. Do the steps in order; every step feeds the next.

Two modes, picked by what exists:
- **Blank page:** "design X", an idea, an interview question → steps 1–8.
- **Existing system:** "will it hold", "what breaks first", "how to scale" in a repo → step 0, then 1–8 with
  measured numbers instead of guessed ones.

## 0. Read what exists (existing system only)

Find the real stack before proposing anything: entry points, the web server, the DB and driver, any cache,
queue, cron and background work, how it deploys (compose, systemd, k8s). Take numbers from what runs: RPS and
p95 from logs or metrics, row counts and table sizes from the DB, the slowest queries if `pg_stat_statements`
is on. Mark which numbers are measured and which are assumed. Place the system on the ladder
(`references/scale-ladder.md`): this is the rung it is on today.

## 1. Requirements

Restate the task in one sentence. Then:
- **Functional:** the 3–5 core actions users do (post, follow, view feed). Everything else is out of scope,
  written down as such.
- **Non-functional:** ask, or assume and list, each of: scale (DAU, requests per user, growth), latency target
  (p95 per core action), availability (is downtime OK? how much?), consistency per data type, traffic spikes,
  durability (what must never be lost), security/compliance, observability. They are hard constraints: two
  apps with the same features and different NFRs get different designs.

If the user is around and a number moves the design (scale, consistency of money-like data), ask, one question
at a time, each with your recommended answer. Otherwise take defaults and list them at the top of the answer.

## 2. Napkin math

Run the script, never do the arithmetic in your head:

```bash
python3 scripts/napkin.py --dau 1e6 --req-per-user 20 [--peak 3] [--hit-rate 0.8] [--read-share 0.9] \
  [--server-rps 1000] [--object-kb 2] [--write-kb 2] [--response-kb 2] [--retention-years 5]
```

Path is relative to this skill's folder. Show the output block. Run it twice when one assumption decides the
design (with and without a cache; normal and launch-day peak). Its verdict names the ladder rung the numbers
need. What the constants mean and where they lie: `references/napkin-math.md`.

## 3. API contract

The core endpoints only: method, path, the main fields in and out, pagination, idempotency keys on anything
that creates money-like objects. Skip for a single trivial service.

## 4. High-level architecture

Start at the rung the napkin's verdict names, not higher (`references/scale-ladder.md`). Draw it as a mermaid
`flowchart LR` with only the boxes that rung needs. For each box: one line on why it exists, tied to a
requirement or a number from step 2. A box without such a line goes.

## 5. Deep dive: the data

Usually the database. Pick the engine by access pattern (`references/storage-and-cache.md`), Postgres unless an
"avoid" condition holds. Give the tables with keys and the indexes the core queries need (or the partition key
and sort key for NoSQL), and say which queries those indexes serve. If there is a cache: which pattern, what is
cached, TTL, how it is invalidated, what happens when it's down.

## 6. Scale and failure

Answer each, briefly:
- traffic ×10 overnight: what saturates first, by the napkin? What is the next rung, and its trigger metric?
- the cache dies; the DB primary dies; a third-party API takes 8 s; a region or the single VM goes away.
- what retries, with what backoff; rate limits; circuit breakers on slow upstreams; backups and a rehearsed
  restore.

## 7. Trade-offs

Name each choice and what it costs (`references/trade-offs.md`): consistency vs availability per data type,
latency vs durability for writes, cost vs performance, monolith vs services, read- vs write-optimised.

## 8. Summary

Close with: the design in three lines, the assumptions that would change it if wrong, and the next rung with
the metric that triggers it ("add a read replica when DB CPU stays over 70% at peak").

## Rules

- The smallest design that meets the numbers wins. One VPS carrying a million DAU is a correct answer when the
  napkin says so; say so plainly.
- Monolith first. A service split needs a reason from `references/trade-offs.md`.
- Never invent a measured number. "Assumed" and "measured" are labelled every time.
- Existing system: recommend changes in climbing order; never jump rungs without naming what breaks in between.
- For a review of a written design: walk it against steps 1–7 and list what's missing or unjustified, worst
  first. Don't redesign unless asked.

## Sources

The method condenses ideas from the public guides by arjaythedev on system design, napkin math, the scaling
path, databases and caching (arjaythedev.com), rewritten and adapted for real projects.
