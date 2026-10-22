"""Wide events: one JSON line per unit of work (a request, a message, a job step, a CLI run).

Template. Steps inside the unit add fields to the current
event (`add`, `add_call`) instead of writing their own lines; `wide` writes it once, in
`finally`, with duration_ms and outcome. A failure's traceback goes into the event too,
so the caller that catches it to keep the loop alive logs nothing more.
Handler + redaction: logsetup.setup_logging routes the "<APP_LOGGER>.events" logger to
logs/events.jsonl.

ContextVar is copied into asyncio.to_thread and into every asyncio task, so a field
added in a worker thread lands in the right event and parallel units never mix.
"""
import json
import logging
import os
import subprocess
import time
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path

APP_LOGGER = "app"  # keep in sync with logsetup.APP_LOGGER
ERROR_TEXT_MAX = 300
TRACEBACK_MAX = 4000  # the tail: the raising frame and the exception line matter most
log = logging.getLogger(f"{APP_LOGGER}.events")
log.setLevel(logging.INFO)  # not root's WARNING: events are INFO, even before setup_logging
_current: ContextVar[dict | None] = ContextVar("wide_event", default=None)


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], timeout=5,
                              cwd=Path(__file__).resolve().parent, capture_output=True,
                              text=True, check=False).stdout.strip() or "?"
    except (OSError, subprocess.TimeoutExpired):
        return "?"


GIT_SHA = _git_sha()


def emit(kind: str, **fields) -> None:
    """A standalone event (something that outlives its unit: a reply later, a GUI window)."""
    ev = {"ts": datetime.now(UTC).isoformat(timespec="milliseconds"), "kind": kind,
          "git_sha": GIT_SHA, "pid": os.getpid(), **fields}
    log.info(json.dumps(ev, ensure_ascii=False, default=str))


def add(**fields) -> None:
    """Fields for the current event; a no-op outside `wide`."""
    if (ev := _current.get()) is not None:
        ev.update(fields)


def add_call(**call) -> None:
    """One external call (service, ms, ok, cache_hit…) appended to the event's `calls` list."""
    if (ev := _current.get()) is not None:
        ev.setdefault("calls", []).append(call)


@contextmanager
def wide(kind: str, **fields) -> Iterator[dict]:
    """The unit's event: outcome ok/error (+ error type/message), duration_ms; re-raises."""
    ev = dict(fields)
    token = _current.set(ev)
    t0 = time.monotonic()
    try:
        yield ev
        ev.setdefault("outcome", "ok")
    except Exception as exc:
        ev["outcome"] = "error"
        # the traceback lives in the event: callers must not log the same failure again
        ev["error"] = {"type": type(exc).__name__, "message": str(exc)[:ERROR_TEXT_MAX],
                       "traceback": traceback.format_exc()[-TRACEBACK_MAX:]}
        raise
    finally:
        _current.reset(token)
        emit(kind, duration_ms=round((time.monotonic() - t0) * 1000), **ev)
