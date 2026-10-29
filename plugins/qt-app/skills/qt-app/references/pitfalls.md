# Pitfalls: what went wrong in real Qt apps, and the fix

From the buy-smarter desktop app (15 sessions, Oct 2026) and the linux-coding overlay. Each line: symptom → cause →
fix. Read the section for what you're about to build; at the end, check the whole list against the diff.

## Crashes and hangs

- Segfault in GUI test teardown, ~1 run in 11 → a `Job`/`Progress` QObject released on the asyncio thread → the loop
  side is a plain object, results hop through a runner signal, every such QObject has a parent (bridge.md rules 1, 6).
- "Event loop is closed" in CI → a cancelled task's aiosqlite thread wrote into the closed loop → shutdown cancels all,
  then waits (bounded) for library threads before closing the loop.
- App froze on "cancel" → `QThread.wait()` in the GUI thread on a worker stuck in a network call → never wait
  unbounded; generation counter, disconnect, ignore the late result.
- "QThread: Destroyed while thread is still running" → the attribute holding the thread got re-assigned → keep the
  reference until `finished`, then `deleteLater`.
- Quit took 8-120 s → a worker thread blocked in one long `recv`/`join` → wait in 0.2 s slices on a stop flag, join
  with a timeout.
- Closing the window mid-job silently waited 10 s → no `closeEvent` → ask (default No) when `runner.busy()`, test it.
- Sync Playwright crashed in parallel threads / froze the loop → serialize it and run it off the loop on its own thread.
- Packaged app died at launch → a DB engine built at import from a stale `.env` with a driver not in the build →
  nothing heavy at import; a missing backend turns one feature off with a visible note.
- Second instance failed with "check your internet" → really GPU out of memory → single-instance guard, honest text.

## Terminal (`<app> gui` from a shell)

- Ctrl+C ignored for 20+ s → Qt's loop never runs Python's signal handler → SIGINT handler + 200 ms wake-up timer.
- A routine 503 printed a full traceback → logging `exc_info` on expected errors → one WARNING line; the traceback
  only for unexpected errors, and only in the log file.
- AI features silently off when launched from the menu → short session PATH → read PATH from the login shell once.
  Parse the last line only: rc files print banners, and a trailing newline once dropped the whole PATH.

## Text, layout, theme (build them right; polishing is qt-ui's job)

- Bold rendered as regular on every screen → a variable font, which Qt sees as one Regular style → ship static faces.
- Text clipped, columns squeezed to letters, horizontal scrollbars → nobody looked at 960×640 → every page scrolls,
  stretch columns have a minimum width, every screen is shot at the minimum size.
- A wrapped table cell lost its second line → row height measured at full width, text drawn inside padding → measure
  height at the padded width (buy-smarter `gui/tables.py`).
- Uneven gaps everywhere → `setSpacing` never called (Qt's 6px) and `QGroupBox` default margins added to the QSS
  padding → `card_body()` and explicit spacing on every layout.
- A hint in a QSpinBox looked like a typed value → the color never reached the inner QLineEdit; a placeholder is
  the text color at ~50% alpha → QSS on `QSpinBox[state="hint"] QLineEdit` with the alpha as a token.
- A QSS rule `QGroupBox QWidget { font-weight: 400 }` also un-bolded the buttons → check specificity of broad rules.
- The logo kept its light color in dark mode → color read once → `bind_icon` for every icon.
- Links blue-on-dark in a QTextBrowser → default document style → render rich text with the theme's colors.
- Dark mode never checked in CI → offscreen ignores `setColorScheme` → `force_scheme()` in tests and screenshots.
- The home screen looked like a settings dialog (form pinned top-left, 70% empty, bare text sidebar) → a hero heading,
  one form card, the sidebar with icons and the app name: the template's shell.
- Russian and English mixed in one row → strings from the core shown raw → one texts module, one language.

## CLI ↔ GUI parity (the most frequent source of bugs)

- The same message differed (English in the CLI, Russian in the GUI; internals in one, a human sentence in the other)
  → texts in one Qt-free module both import; a test compares them.
- Different defaults (the core's `None` meant one source; the CLI searched three) → defaults resolved in one shared
  function, not in each entry point.
- A saved city pre-filled into the field overrode the city typed in the query → saved values are placeholders,
  precedence as in the CLI.
- Features only in one entry point (toggles only in the GUI, create-category only in the CLI) → the parity table at
  the start; gaps closed in the same plan, the CLI gets flags for GUI-only switches.
- A background task in the CLI died on a prompt → the whole flow in one `asyncio` loop, not two `asyncio.run`.
- Verify parity with a live run of both (same input, same output), not only unit tests: the live run found bugs the
  tests didn't.

## State and flow

- A job finished before the report showed and the report reset it, offering to start a second paid run → state shared
  across screens lives in one object, and a reset clears only what the screen owns.
- A cancelled job left a "running" mark in the DB forever → clear marks in `finally` under `asyncio.shield`.
- A status said "ждёт" for every source and looked hung → named stages, elapsed seconds, an indeterminate bar, the
  button says "Выполняется…", "в очереди" for what hasn't started.
- A UI step that does nothing on this platform ("click the window" on Linux) → gate the UI by platform, not only the
  backend.
- Results lost on restart → save what the CLI saves (same file, same folder) and list it on a screen.
- Store down → screens did nothing silently → a warning banner above the content, cleared by "проверить снова".

## Process

- Look at every screenshot yourself, both themes, after every UI change; "the rule applied" isn't proof.
- Count fixed items from the list, not from memory, when reporting "N of M fixed".
- Commit only your own paths (`git commit -- <paths>`): parallel sessions share the index.
