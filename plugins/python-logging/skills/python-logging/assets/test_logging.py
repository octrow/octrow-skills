"""Logging checks: size cap, wide events, one-line records, redaction.

Template. Runs under pytest (test_* functions)
or plain `python test_logging.py`. Fix the two imports for the project's package.
"""
import io
import json
import logging
import os
import tempfile
import time
from pathlib import Path

import events  # adapt: from <pkg> import events
from logsetup import MB, NEWLINE_MARK, RedactFilter, _secrets, prune_logs  # adapt


def _sparse(path: Path, size: int, mtime: float) -> None:
    with path.open("wb") as fh:
        fh.truncate(size)  # sparse: no real disk used
    os.utime(path, (mtime, mtime))


def _captured(logger: logging.Logger, write) -> list[str]:
    """Lines `write()` sends through `logger`, redaction filter applied."""
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    h.addFilter(RedactFilter())
    logger.addHandler(h)
    try:
        write()
    finally:
        logger.removeHandler(h)
    return buf.getvalue().splitlines()


def test_prune_cap() -> None:
    """1.1 GB of sparse logs -> under the cap; live files survive, the oldest go first."""
    with tempfile.TemporaryDirectory() as d:
        logs, old = Path(d), time.time() - 3600
        for i, name in enumerate(("a-cli.log", "b-cli.log", "daemon.log.1",
                                  "events.jsonl.1", "daemon.log", "events.jsonl")):
            _sparse(logs / name, 200 * MB, old + i)  # listed oldest -> newest
        _sparse(logs / "z-cli.log", 1, old - 30 * 86400)  # past keep_days
        prune_logs(logs, keep_days=14, max_bytes=500 * MB)
        left = {f.name for f in logs.iterdir()}
        assert sum(f.stat().st_size for f in logs.iterdir()) <= 500 * MB, left
        assert {"daemon.log", "events.jsonl"} <= left, left
        assert "z-cli.log" not in left and "a-cli.log" not in left, left


def _sample_events() -> None:
    with events.wide("request", ref="u42:r7", user_id=42):
        events.add(decision="sent", note="key SECRETTOKEN42")
        events.add_call(service="llm", ms=3, ok=True)
    try:
        with events.wide("request", ref="x"):
            raise ValueError("boom")
    except ValueError:
        pass
    else:
        raise AssertionError("wide must re-raise")
    events.add(ignored=True)  # outside a unit: no-op


def test_wide_events() -> None:
    _secrets.add("SECRETTOKEN42")
    try:
        lines = _captured(events.log, _sample_events)
    finally:
        _secrets.discard("SECRETTOKEN42")
    assert len(lines) == 2, lines
    ok, err = (json.loads(ln) for ln in lines)
    assert ok["outcome"] == "ok" and ok["ref"] == "u42:r7" and "duration_ms" in ok, ok
    assert ok["calls"] == [{"service": "llm", "ms": 3, "ok": True}], ok
    assert ok["note"] == "key ***" and ok["git_sha"], ok
    assert err["outcome"] == "error", err
    assert err["error"]["type"] == "ValueError" and err["error"]["message"] == "boom", err
    assert "raise ValueError" in err["error"]["traceback"], err


def test_one_line() -> None:
    lg = logging.getLogger("test.oneline")
    lg.propagate = False
    lines = _captured(lg, lambda: lg.warning("got %s", "line one\nline two"))
    assert lines == [f"got line one{NEWLINE_MARK}line two"], lines


if __name__ == "__main__":
    test_prune_cap()
    test_wide_events()
    test_one_line()
    print("logging checks ok")
