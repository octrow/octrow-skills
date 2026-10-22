---
name: python-logging
description: Set up, fix or improve logging in a Python project — size-capped log files (a total disk budget such as "logs under 1 GB"), rotation, wide events / canonical log lines (one JSON line per request, message or job), secret redaction, one-line records, excepthooks for threads and asyncio, journald/systemd limits, and a selftest that proves the cap. Use whenever the user asks to "настроить логирование", "починить логи", "логи растут / забили диск", "сделай нормальные логи", "почему в логах ничего не видно", wants structured or JSON logs, wants to trace what happened to one request/message, adds a daemon or systemd service that needs logs, or reviews logging code — even if they never say the word "logging" but complain that a failure left no trace.
---

# Python logging: set up, fix, improve

Goal: when something goes wrong, the answer is one `grep`/`jq` away, and the logs can
never fill the disk. The templates in `assets/` come from a long-running Telegram monitor
(a daemon plus CLI runs beside it) where every rule below was needed.
Background: [wide events / canonical log lines](https://stripe.com/blog/canonical-log-lines),
[logging-best-practices](https://github.com/boristane/agent-skills/blob/main/skills/logging-best-practices/SKILL.md).

## 1. Audit first (read-only)

```bash
python3 <skill-dir>/scripts/log_audit.py <repo>
```

It reports basicConfig calls, file handlers without a size cap, time-only rotation,
logger names, excepthooks, redaction filters, print() counts, log files on disk and
journald usage. Then read the project's actual logging setup and one hot path end to
end (a request handler, a message consumer). Note:
- where logs go now (stderr → journald? files? which processes write them?);
- whether several processes write one file (CLI runs beside a daemon);
- what a unit of work is here (HTTP request, incoming message, job step, CLI run);
- which data is private (chat text, prompts, PII) and which secrets live in config/env;
- anything that already parses log lines (dashboards, health checks) — keep it working.

`print()` in a CLI command that prints its result is output, not logging; only flag
prints used as diagnostics.

## 2. Pick the scope with the user

Say what the audit found in a few lines and propose the smallest set that fixes the
real problem. "Fix" requests (a bug left no trace, logs filled the disk) usually need
one or two items, not the whole list. Full set-up for a new service is everything below.

## 3. Implement

Copy from `assets/` and adapt; don't rewrite from memory — the templates carry fixes
for traps that are easy to reintroduce (see "Traps").

| Need | Template | What to adapt |
|---|---|---|
| One logger, caps, rotation, redaction, excepthooks | `assets/logsetup.py` | CONFIG block: logger name, logs dir, daemon commands, budget, library levels, secret env vars |
| Wide events | `assets/events.py` | `APP_LOGGER`; then wrap units of work |
| Proof | `assets/test_logging.py` | imports; run under pytest or the project's selftest |

**Size budget.** Agree on one number for everything (default 1 GB) and split it in
named constants: the daemon's own rotating files must fit by themselves
(`RotatingFileHandler(maxBytes, backupCount)`, not `TimedRotatingFileHandler`); CLI runs
get one file each and are trimmed at start-up (`prune_logs`: age first, then oldest
until under the cap, never the live files); sibling services get their share through
their own setting (e.g. `Environment=BOT_LOGS_MAX_BYTES=…` in the unit). journald is
system-wide (`SystemMaxUse=` in `/etc/systemd/journald.conf`, needs sudo): report it as
a manual step, don't edit `/etc` yourself.

**Wide events.** One event per unit of work, written once in `finally` by `wide(...)`.
Steps add fields with `add(...)` instead of writing their own lines; external calls go
into a list with `add_call(...)`. Put in: correlation keys (`ref`, user/chat/request
ids — they link the event to the DB), business decisions and their reason, outcome,
external calls (service/model, ms, ok, cache hit), `git_sha`, `pid`. Leave out private
text already stored elsewhere — log its length. Remove the per-step lines the event now
carries — at every level, DEBUG included; a step that matters is a field. A failure's
traceback goes into the event (`error.traceback`, the template does it), so the code that
catches the error to keep a loop alive must not `log.exception` the same failure again:
two records for one failure, one of them multi-line, is the noise this replaces. Something that outlives the unit (a GUI window, a later reply)
writes its own `emit(kind, ref=…)`. Don't wrap a whole long-running command in one
event — wrap its units.

**Hygiene.** One record = one line (newlines → `⏎`). Tracebacks may stay multi-line in
files, but not where stderr goes to journald: journald splits multi-line output into
separate entries, so there the console formatter folds the whole record, traceback
included (the template switches on `JOURNAL_STREAM`, which systemd sets). A process that
logs only to journald folds everything.
The redaction filter sits on every handler, including the events file. Register
secrets by value after the config is read — values not shaped like a known token (API
keys, passwords) are invisible to regex masking. Third-party loggers leak too: they log
URLs and headers at DEBUG and put URLs in exception args. Route them through the same
filtered handlers with an explicit level (`LIB_LEVELS`), mask the formatted record
(traceback text included), and never edit vendored library code to hide a secret. Uncaught exceptions in main, threads and asyncio go
through the logger. Levels: INFO happened, WARNING degraded with a workaround, ERROR
not done; DEBUG only to the file.

## 4. Verify

1. The tests from `assets/test_logging.py` pass: the cap test (1.1 GB of sparse files
   trimmed under the cap, live files kept), the event test (fields, outcome, error,
   re-raise, redaction, `add` outside a unit is a no-op), the one-line test.
2. Restart the service, trigger one real unit of work, show the event line
   (`tail -1 logs/events.jsonl`) and confirm no traceback in the console/journald.
3. Anything that parsed old log lines still works.
4. Document in the project's docs: which files, their caps, how to find everything
   about one unit (`jq -c 'select(.ref=="…")' logs/events.jsonl`).

Report: what changed, the budget split, the manual journald step if any, and what was
verified live vs only by tests.

## Traps (each one happened in the project the templates come from)

- **Events silently dropped:** a child logger with no level inherits root's WARNING, so
  `log.info(event)` vanishes until `setup_logging` runs. The template sets INFO on the
  events logger at import.
- **Several processes, one rotating file:** stdlib rotation is not multi-process safe.
  Daemon gets the rotating file; each CLI run gets its own.
- **A failure that looks like a normal result:** a subprocess (GUI window, helper)
  that crashes with the same exit code as a normal "no" gets journaled as a decision.
  Give crashes their own code and log them as errors.
- **Different env under systemd:** a service started before login has no `DISPLAY`;
  PATH lacks `~/.local/bin`. Log the environment-dependent failure, not just the exit code.
- **Tracebacks bypassing redaction:** the default `sys.excepthook` prints raw tracebacks
  to stderr → journald, secrets included. Route through the logger.
- **Multi-line chat text in records** breaks grep and line parsers (dashboards).

## Not by default

Loki/Grafana/OTel, structlog/loguru: only when the user asks or the service runs as
several processes across machines. stdlib `logging` + JSON Lines covers one host.
GUI apps (PySide6, GTK main loop) need a signal bridge into the UI thread; regular
services don't.
