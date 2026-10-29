# Screens, test first, in parity with the CLI

Step 3 in detail. One screen per cycle: the test, RED, the screen, GREEN, a screenshot, the next screen.

## Before the first screen: the parity table

List every user-visible CLI capability (commands, flags, prompts, outputs, defaults, errors) and map each to a screen
and a control. Show the table to the user once. Rows without a GUI home are gaps you close in this plan, not later:
in real apps, users found "where is create-category in the GUI?" and "where are past searches?" themselves.

What must be shared, not copied (put it in a Qt-free module both entry points import):
- **Texts**: labels, status lines, error sentences, hints. One language in the whole window (Russian here); a
  core that speaks English gets a translation table in the shared module, and an unknown key shows the
  original, never an empty string.
- **Calls**: the GUI calls the same service function the CLI command calls, with the same arguments.
- **Defaults and precedence**: what "no value" means, saved settings vs typed input vs values parsed from the query.
  A saved value pre-filled *into* a field gets sent as if typed, and overrides a value from the query; show it as
  placeholder text and resolve it the CLI's way (field/flag > query > saved > none).
- **Formats**: one money/number/date formatter (`35 000 ₸`, not `35,000 ₸`), one row count, one sort order.
- **Hints in the GUI name a GUI action** ("нажмите «Пройти проверку»"), never a CLI command or env var. The
  terminal `doctor` keeps its CLI hints: the wording differs, the check is the same.
- **Side effects**: if the CLI saves a report, the GUI saves the same file to the same folder.

When the CLI lacks something the GUI does (a toggle, a flag), add it to the CLI in the same plan.

## The test (pytest-qt, offscreen)

`tests/gui/conftest.py`:

```python
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

@pytest.fixture
def runner(qapp):
    r = CoreRunner()
    yield r
    r.shutdown()
```

plus autouse fakes for anything slow or external the window touches at start (doctor checks that launch a
browser, keyring, network probes). A test never reaches the network or the user's files.

Per screen, the minimum:
1. **The happy path through the real runner** with the core function replaced by a fake coroutine (monkeypatch
   the name the screen imports, or pass it in the constructor like the template's `HomeScreen(core=...)`).
2. **Each outcome**: `failed` shows the human sentence and re-enables the form; `cancelled` shows "Остановлено."
   and the cancel button works *while* the job runs.
3. **Parity**: the screen and the CLI produce the same text for the same input. Call the shared formatter from the
   test and compare, or render the CLI command with `CliRunner` and check the same lines appear.
4. **Lifecycle** (once per screen that runs work): close the window or delete the screen while the job runs.
   These are the places of the real segfaults.

Waiting:

```python
with qtbot.waitSignal(job.finished, timeout=3000) as blocker:
    blocker.connect(job.failed)          # a failure ends the wait now, not as a timeout
qtbot.waitUntil(lambda: not screen.is_running(), timeout=3000)   # no signal to wait on
```

Gotchas seen in real suites:
- `qtbot.keyClicks` on a widget that was never shown crashes offscreen: `show()` it first or `setText()`.
- Running `run()` (the whole app) twice in one session poisons later tests through the shared QApplication: the
  ticker, notifier and excepthook stay attached. Test `MainWindow` with the runner fixture instead, or undo
  everything `run()` installs.
- "Passes alone, fails in the full run" means shared QApplication state, not test order luck.
- A window's start-up checks still running when the fixture shuts the runner down crash the test: wait for them.
- Rare segfaults in offscreen runs: run with `python -X faulthandler -m pytest` from the start so a crash prints
  the stack and the test name.
- Run the affected GUI tests once or twice before a commit; don't loop the suite dozens of times.

## The screen

- A `QWidget` subclass in `screens/<name>.py` taking the `CoreRunner` (and shared state objects) in the
  constructor. It never starts its own threads or loops.
- Layout through the theme: cards are `QGroupBox` with `card_body(layout)`; spacing from `SPACE`/`PAGE_GAP`/
  `CARD_GAP`, always set explicitly (Qt's default 6px is off the grid); one primary button
  (`set_state(button, "primary", "true")`); statuses through `set_state(label, "state", "ok"|"warning"|"error")`.
- Copy the neighbour screen's structure when there is one. The detailed layout rules (tables, empty states, field
  heights, label placement) live in qt-ui; for a new screen, the template and the neighbour are enough.
- **Tables:** `QAbstractTableModel` + `QTableView` for data that grows, `QSortFilterProxyModel` for sort and filter;
  the main text column stretches with a minimum width (~160px), or at 960px names break into letters. Key rows by a
  full identity (`(source, id)`), not an id two sources can share. A table on a scrolling page doesn't scroll
  itself: buy-smarter [`gui/tables.py`](https://github.com/octrow/buy-smarter/blob/main/src/buysmarter/gui/tables.py).
- **State that outlives a screen** (a long job started on one screen and shown on another) lives in one object
  created by `MainWindow` and passed to both screens, not in either screen.
- **Late results**: a background reload that lands after the user typed must not overwrite input; a reload asked
  while one runs sets a "pending" flag instead of being dropped.
- **Discoverability**: a new control goes where the user is looking, not at the bottom of a long page.
- `setAccessibleName` on icon-only buttons.

## After each screen

Screenshot it in both themes at 960×640 (step 4) and look at the PNGs. Text clipped at the minimum size and colors
that only fail in dark mode don't show up in any test.
