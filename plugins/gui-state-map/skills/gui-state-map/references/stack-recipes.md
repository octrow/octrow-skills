# Stack recipes and pitfalls

What worked, and what broke, in real runs. Read the section for the project's stack before writing the shooting
scripts, and copy the relevant pitfalls into the plan's §0a.

## Contents
- Web (any browser GUI) with Playwright
- NiceGUI specifics
- Desktop: two methods, offscreen and live
- Fyne / X11 on GNOME Wayland
- Qt (PySide6 / PyQt6)
- Desktop stands: no port, shared files
- Process pitfalls (any stack)

## Web with Playwright

Use whichever Playwright is already installed: Python in the project venv, or global Node
(`NODE_PATH=$(npm root -g)`). Don't install the other one. Run headless chromium at a fixed viewport.

| Need | Recipe |
|---|---|
| Shoot + text | `goto → screenshot → innerText → click → …`, text into `shots/<ID>.txt` |
| What a click changed | `context.tracing.start({screenshots: true, snapshots: true})` → `traces/<batch>.zip`, view with `playwright show-trace` |
| What the server pushed | `page.on('websocket')` → frames into `ws/<A-NN>.jsonl`; shows which elements redrew and when (at once / timer tick / resync) |
| Silent JS errors | `page.on('console')`, `page.on('pageerror')` → `console-<batch>.txt` |
| Waiting | `expect(locator).toHaveText(…, {timeout})` sized to the app's slowest refresh, never `sleep` |
| Selectors | `getByRole` + visible text; stable CSS classes of the shell |
| Click log | one JSON line per click in `clicks.jsonl`: id, selector, ok/timeout, ms |

Pitfalls:
- Don't use `fullPage` on a page whose height equals the window and scrolls inside a container. It shoots one
  screen. Scroll the container and take frames.
- A closed dialog may not exist in the DOM until it opens. Open it through its trigger first.
- Tables that cut to 5 rows by default (Quasar without `rowsPerPage: 0`) are a finding when they show up.

## NiceGUI specifics

- `.mark()` is a server-side marker. There is no DOM attribute, so `[marker=…]` selectors don't work.
- `ui.refreshable` rebuilds on the next tick: wait for the text between two clicks.
- The shell often has a 1–2 s timer and a slower resync (for example 30 s). Shoot "settled" after the resync.
- Each process has its own run pool. A run started in the owner's instance doesn't show in the stand. Check this
  on purpose: it's a state.
- **Fake "running"**: a tiny launcher on a spare port that calls `app.on_startup(lambda: run_pool.submit([python,
  "-u", "-c", "<print [i/60] with sleeps>"]))`, or swaps `run_pool.RUNS`. Data is untouched.
- Starting through `gui.run(load_config())` skips what the real CLI entry does (logging, log pruning, store
  migrations, `.env`). Start through the CLI, and remember the difference when reading shots from a launcher.
- Toasts followed by a page reload disappear in milliseconds. That's a finding, and it's why a screenshot right
  after the click matters.

## Desktop: two methods, both needed

| Method | Gives | Doesn't give |
|---|---|---|
| **A. Offscreen test driver** (a test that renders each state with taps and typing, then captures the canvas) | every state of every widget, both themes, deterministic, plus a widget-tree dump as "page text" | the real coordinator or backend, always-on-top windows, tray, system dialogs |
| **B. Live run** on the machine | real pipeline behaviour, timing, transparency, tray, portals | determinism |

A shoots the **form**, B shoots the **behaviour**. Keep the review test **outside** the source tree
(`review_test.go.txt` in the report folder). A runner copies it in, runs it and deletes it, so the tree stays clean
and the done criteria can check it. For W clicks in A, point `HOME` at a temp copy of the real config and diff the
YAML afterwards.

## Fyne / X11 on GNOME Wayland

Fyne windows live in XWayland (`DISPLAY=:0`), so X tools see them. GNOME Shell (tray, portals) is not visible to
them.

- Find windows: `xwininfo -root -tree | grep '<title>'`. Shoot one: `import -window <id> shots/<ID>.png`.
- **A covered window returns a stale frame.** Raise it before the shot.
- Window state as fact, not as a picture: `xprop -id <id> _NET_WM_STATE _NET_WM_WINDOW_OPACITY WM_STATE`.
- Clicks: **XTEST** through python-xlib (small `xclick.py`, `xraise.py`, `xclose.py`, `xdrag.py` helpers) works.
  `ydotool` did **not** move the pointer. Don't use it.
- Tray: dbusmenu through `busctl` (`tray.sh layout`, `tray.sh click <id>`). GNOME Shell is not needed.
- Portal dialogs and anything the shell draws: the owner presses PrtSc, and `snap --take-latest` picks up the
  newest file from `~/Pictures/Screenshots`.
- Video of a streaming transition: `ffmpeg -f x11grab -window_id <id>`. If it gives black frames, use GNOME's
  Ctrl+Alt+Shift+R (the owner presses it).
- Run the app with a JSON log to a file through env vars, so the config file isn't touched. Cut the log by
  `snap` timestamps into `logs/<A-NN>.jsonl`. That log is the answer to "which processes, in what order".
- A cached screen-share token can make the portal skip its dialog. To shoot the dialog, move the token aside and
  restore it afterwards.
- Process lookup: `pgrep -x <name>`. A `-f <path>` pattern also matches the agent's own shell.
- Metrics redraw on their own clock. Shoot "running" after the first slow redraw.
- If the app's own window is in its capture area, its redraws trigger extra work. That's behaviour, not noise.
  Log it.

## Qt (PySide6 / PyQt6)

Method A runs on `QT_QPA_PLATFORM=offscreen`. If the project already has a screenshot script (often
`scripts/screenshots.py`), build on it. The skeleton is in the `qt-ui` plugin of the octrow-skills marketplace,
`plugins/qt-ui/skills/qt-ui/references/screenshot-script.md`, and may not be installed next to this skill. Add
these four pieces to it:

- **Clicks**: `button.click()` or `QTest.mouseClick(w, Qt.LeftButton)`, then pump events (`processEvents` in a short
  loop) before the shot. Find controls by `objectName` or `findChildren(QAbstractButton)` + text.
- **"Page text"**: walk `window.findChildren(QWidget)` and dump class, `objectName`, text/title/placeholder,
  `isEnabled()`, `isVisible()`, the current value of inputs, one line each, into `<ID>.txt`. Diffing two dumps
  replaces the Playwright trace.
- **Modal dialogs** (`QMessageBox.exec`, `QFileDialog`) block the script. Monkeypatch the static calls to return a
  chosen answer and record that they were asked, or fire `QTimer.singleShot(0, grab_active_modal_then_close)`
  before the click.
- **Async work** (asyncio loop on a thread, `QThreadPool`): replace the slow or quota-spending call with a stub that
  emits the same signals with a fixed delay. That's the desktop F stand.

Method B (live) goes through XWayland like the Fyne section: `import -window`, `xprop`, XTEST.

## Desktop stands: no port, shared files

A desktop app has no port and reads fixed paths, so a "second instance on its own port" means a **second home**:
point `HOME` / `XDG_CONFIG_HOME` / `XDG_DATA_HOME` (or the app's own env var) at a copy. Things that don't follow
`HOME`:

- **The system keyring** (keys in Secret Service / KWallet). There's no file to back up. Swap the backend for an
  in-memory one in the driver (`keyring.set_keyring(...)`), and don't press key buttons in the live run.
- **Self-update**: an app that auto-updates (git fast-forward, `uv sync`, downloads) can change **the repo itself**
  a few seconds after start. Turn it off in the stand's copy of the update config and start the driver without
  the auto-start hook. Class X.
- If even starting the app writes to its data (migrations, health checks, "last opened"), there is no read-only L
  stand. Shoot on S only and say so in the plan.

## Process pitfalls (any stack)

- Start and stop a stand in **separate** tool calls, and match with a bracket pattern (`pkill -f "[p]ort=8142"`)
  so the kill doesn't match itself.
- Shoot the stand on the current working-tree code. Restart it after fixes, and keep a note of the commit each
  shot was taken on.
- A snapshot or backup **ID reused overwrites** the earlier one. Generate new IDs.
- Append-only logs shared with the owner's instance or cron jobs: check every diff for foreign lines.
- A restore can bypass the app's own ledger (a status log keeps the click line with no undo line). Note it in
  `RESTORES.md` so the next reader doesn't take it for a bug.
- Some data a Q action deletes isn't in the backup (exports regenerated from the DB). List what wasn't restored.
- Permission classifiers may refuse X-class or live-account actions for agents. Don't fight it. Write the exact
  `! …` command for the owner.
- Big backups (about 80 MB each) go in the plan status with "delete after reshoot".
