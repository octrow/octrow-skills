# The bridge: core work off the GUI thread, results back as signals

Read this at step 1, before writing any screen. Every crash, hang and "Event loop is closed" seen in real apps
came from this layer, not from widgets.

Worked code: [`buy-smarter/src/buysmarter/gui/bridge.py`](https://github.com/octrow/buy-smarter/blob/main/src/buysmarter/gui/bridge.py)
and its tests [`tests/gui/test_bridge.py`](https://github.com/octrow/buy-smarter/blob/main/tests/gui/test_bridge.py).
The template copy is `scripts/template/gui/bridge.py` in this skill.

## Pick one

| The core is | Use | Why |
|---|---|---|
| asyncio (httpx, aiohttp, asyncpg, aiosqlite, Playwright async, subprocess) | **CoreRunner**: one asyncio loop in a daemon thread, `submit(coro) -> Job` | The core runs as-is, on a real loop with sockets and subprocesses |
| sync, calls that block for seconds or minutes (subprocess, HTTP, LLM CLI) | **CoreRunner** with `submit(in_daemon_thread(fn, stop))` | One pattern for the whole app, same `Job` signals; a daemon thread, so quitting never waits for the step to end |
| sync and CPU-heavy, or a library that owns its own thread | `QThreadPool` + `QRunnable` with a separate `QObject` for signals | No loop needed; see "Variant D" below |

Not used, with the reasons (buy-smarter ADR 0001):
- **`PySide6.QtAsyncio`**: a technical preview that implements only futures, tasks and `call_soon`. No transports,
  sockets or subprocesses, so httpx, curl_cffi, aiohttp and asyncpg don't run on it.
- **qasync**: an extra dependency sharing one loop with Qt: any blocking slot freezes both the UI and the network,
  and its subprocess and websocket behaviour was never verified.
- **The CLI as a subprocess with JSON on stdout**: progress and cancel become a protocol of their own.

If the user asks for one of these anyway, say the reason in one line and do what they decide.

## Ownership rules (each one is a real segfault or hang)

1. **A QObject is deleted on its own thread.** The loop thread must never hold the last reference to a QObject.
   That's why the loop side of a job is a plain `_LoopSide` object, results hop to the GUI thread through the
   runner's `_settled(job_id, future)` signal, and the runner keeps `Job`s in a dict until delivery.
   Every QObject that background code touches (a progress reporter, a delegate) gets a **parent**, usually the screen.
2. **Widgets only from the GUI thread.** Anything from another thread goes through a `Signal` connected with
   `Qt.ConnectionType.QueuedConnection` to a bound method of a QObject that lives in the GUI thread. A lambda slot
   with no receiver object may run in the emitting thread.
3. **Cancel the asyncio task on its loop:** `loop.call_soon_threadsafe(task.cancel)`. Cancelling the
   `concurrent.futures.Future` settles it at once while the coroutine's `finally` (browser close, session close)
   still runs, so the screen resets over live work.
4. **Exactly one outcome per job:** `finished`, `failed` or `cancelled`. A screen connects all three.
5. **Errors:** the user sees one human sentence (`USER_ERROR` or a specific one from the shared texts), the
   traceback goes to the log. Never show `str(exc)`: pydantic and HTTP internals leak into the window.
6. **Break reference cycles:** `self.task = None` in `finally`, so a failed job is freed by refcount on the loop
   thread, not in a GC pass that may collect a QObject on the wrong thread.

## Shutdown order

```python
try:
    return app.exec()
finally:
    runner.shutdown()   # cancel all, wait for their finally (10 s cap), stop the loop, join (10 s cap)
```

- A library with its own threads that report back into the loop (aiosqlite) needs a bounded wait for those
  threads before the loop closes, or CI fills with "Event loop is closed". buy-smarter's `_store_threads_done`.
- `closeEvent` asks before closing over running work (`runner.busy()`), default answer **No**. Without it, closing
  waits silently up to the shutdown timeout and looks like a hang.
- **Not `asyncio.to_thread` for long sync work.** Its pool thread can't be interrupted and the interpreter joins
  it at exit, so closing the window mid-run hangs until the step ends. The template's `in_daemon_thread(fn, stop)`
  runs `fn` on a daemon thread; a cancel sets `stop`, which `fn` checks between steps (cancel is cooperative), and
  a late result after `cancelled` is dropped. If the core has no stop check yet, add one to its loop over items.

## Variant D: QThreadPool / QThread

```python
class WorkerSignals(QObject):            # QRunnable is not a QObject
    finished = Signal(object)
    failed = Signal(str)

class Worker(QRunnable):
    def __init__(self, fn, *args) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self._fn, self._args = fn, args
        self.stop = threading.Event()     # fn checks it between steps: cancel is cooperative

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn(*self._args, stop=self.stop)
        except Exception:
            logger.exception("worker failed")
            self.signals.failed.emit(USER_ERROR)
        else:
            self.signals.finished.emit(result)
```

Rules from linux-coding (a PySide6 overlay with QThreads):
- **Never `QThread.wait()` without a timeout in the GUI thread.** A worker stuck in a network call (proxy, DNS)
  deadlocks the whole app. `quit()` does nothing to a `run()` without an event loop. To cancel, bump a generation
  counter, disconnect the worker's signals and ignore its late result.
- **Keep a reference to a running QThread.** Re-assigning the attribute lets GC destroy it mid-run: "QThread:
  Destroyed while thread is still running", then a crash. Connect `finished` to `deleteLater`.
- **On close, wait in slices with a cap** (`wait(2000)`), then exit anyway. A thread blocked in `recv` for minutes
  must check a stop flag every ~0.2 s instead.
- Shutdown for the pool: set every worker's stop flag, then `QThreadPool.globalInstance().waitForDone(ms)`.

## Progress without changing the core's API

The core logs `logger.info(..., extra={"progress_state": ...})`; a logging handler in the GUI looks up the current
job through a `ContextVar` and re-emits the record as a Qt signal. asyncio copies the context into child tasks, so
two jobs never see each other's stages. Worked code: [`gui/progress.py`](https://github.com/octrow/buy-smarter/blob/main/src/buysmarter/gui/progress.py).
A cancelled stage gets its own state ("пропущен"), not "failed", or the screen shows it as still running.
