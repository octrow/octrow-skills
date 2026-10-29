---
name: qt-app
description: Build a desktop GUI from scratch on Qt (PySide6 Widgets) for a Python project — add a window to a CLI or library project that has none, or add a new screen with its own logic to an existing Qt app. Checks how the core can be called in-process and where asyncio lives, picks the bridge (an asyncio loop in a worker thread with Qt signals, the proven CoreRunner; not QtAsyncio or qasync), scaffolds the `gui` extra (PySide6-Essentials, qtawesome), a `<app> gui` command, a sidebar window and an own light/dark token theme from a runnable template, then builds screens one at a time test-first with pytest-qt offscreen, sharing texts and calls with the CLI so both behave the same, shoots every screen in both themes at 960×640 and hands layout polish to qt-ui. Packaging (PyInstaller, CI self-test) only on request. Use it whenever the user asks to add a GUI, make a desktop app, "окно на Qt / PySide6 / PyQt", a new screen or tab with new behaviour in a Qt app, or to turn a CLI into an app for people who don't use a terminal — «добавь GUI», «сделай десктопное приложение», «нужно окно», «новый экран в приложении», «GUI для CLI», even if they don't name Qt. Not for NiceGUI or browser UIs (that's nicegui-kit-gui), and not for fixing the look of an existing screen — spacing, clipped text, dark theme, "make it like the other screen" go to qt-ui.
---

# Qt app: core in a thread, screens test-first, same behaviour as the CLI

qt-app builds; qt-ui polishes. This skill gets a working, crash-free window with every screen the user needs, in the
house style, and stops when the screens behave right. Pixel-level layout fixes after that are qt-ui's job, and its
rules (tokens, grid, screenshots) are referenced here, not repeated.

Talk to the user in Russian, briefly. All UI text is Russian. Code, comments and identifiers stay English.

The reference app is buy-smarter ([`src/buysmarter/gui/`](https://github.com/octrow/buy-smarter/tree/main/src/buysmarter/gui)):
every rule below fixed a real crash, hang or complaint there. When a detail isn't covered here, read how it does it.

## Step 0. Which job is this?

- **No GUI yet** → steps 1-4.
- **A Qt app exists, the user wants a new screen** → read the existing `gui/` package (bridge, theme, a neighbour
  screen, its test), then step 3 for that screen and step 4. Reuse the app's own bridge and theme even if they
  differ from the template; don't add a second one.
- **The request is about how an existing screen looks** (spacing, clipped text, colors, dark theme) → this is qt-ui.
  Say so in one line and hand over (`/qt-ui`), don't start building.
- **A NiceGUI / browser UI** → nicegui-kit-gui.
- The project already has a NiceGUI UI and the user wants Qt: mention it in one line (the house policy is PySide6 for
  apps handed to non-developers, NiceGUI for internal tools) and go on with what the user asked.

## Step 1. The core and the bridge

Read before writing anything:
1. **Can the core be called in-process?** Find what each CLI command calls. The GUI calls exactly those functions.
   If logic sits inside the CLI command body (prints, prompts, `typer.Exit`), extract it into a Qt-free function
   both entry points call. That's part of this job, not a detour.
2. **Where is asyncio?** `async def` in the core, `asyncio.run` in the CLI, async libraries (httpx, aiosqlite,
   Playwright async). Or a sync core with long blocking calls (subprocess, HTTP, LLM CLI).
3. **What does the core touch at import and at start?** Config, DB engines, env, the user's home. The GUI repeats the
   CLI's start-up by calling the same functions.

Then pick the bridge from [references/bridge.md](references/bridge.md). In almost every case it's the template's
**CoreRunner**: one asyncio loop in a daemon thread, `submit(coro) -> Job` with `finished` / `failed` / `cancelled`
delivered on the GUI thread; a sync core goes through the template's `in_daemon_thread(fn, stop)` (not
`asyncio.to_thread`: its thread is joined at exit, so quitting mid-run hangs). No QtAsyncio (no sockets or
subprocesses), no qasync (one shared loop, an unverified dependency). Tell the user the choice in one line with the reason.

## Step 2. Scaffold from the template

Copy the runnable template and its test, then adapt:

```bash
cp -r <this skill's dir>/scripts/template/gui src/<pkg>/gui
cp <this skill's dir>/scripts/template/test_gui_template.py tests/gui/test_shell.py   # `from gui` -> `from <pkg>.gui`
```

The template is `bridge.py` (CoreRunner), `theme.py` (tokens, light and dark palettes, generated QSS, `icon` /
`bind_icon`, `set_state`, `card_body`, `force_scheme`), `app.py` (sidebar window, every page scrolls with a heading,
minimum 960×640, close-while-busy question, excepthook dialog, Ctrl+C from the terminal, shutdown in `finally`) and
`screens/home.py` (a form card running one core call with status and cancel). Its 13 tests pass offscreen as shipped.

Then, in order ([references/scaffold.md](references/scaffold.md) has the snippets):
- pyproject: extra `gui = ["PySide6-Essentials>=6.8", "qtawesome>=1.4"]`, `pytest-qt` in dev, a `<app>-gui` script.
- The `gui` command in the existing CLI, importing Qt lazily and printing how to install the extra.
- `app.main()` does the CLI's start-up (logging, config); `TITLE`, the palette accent and the screen list for this app.
- `uv sync --extra gui` (plain `uv sync` removes PySide6), then the shell tests: green before any screen.
- Start it once for real (`<app> gui`, Ctrl+C quits) if there's a display; offscreen otherwise.

House style: own tokens and QSS, qtawesome `mdi6.*` icons, no Fluent widgets, no qt-material, no stock dark theme.
GPL is allowed when the user agrees, but ask open vs closed first.

## Step 3. Screens, one at a time, test first

First write the **parity table**: every user-visible CLI command, flag, prompt, default and output → the screen and
control that does it in the GUI. Show it to the user and agree the screen list. CLI-only or GUI-only features found
here are closed in this plan (a missing CLI flag gets added too).

Then for each screen ([references/screens-tdd.md](references/screens-tdd.md)):
1. **Test first, RED**: write the test, run it and see it fail (an ImportError of the missing screen counts)
   before the screen exists. A test written after the code tends to assert what the code does, not what the user
   asked. Cover the happy path through the real runner with the core function faked, each outcome (failed,
   cancelled, cancel while running), the parity check against the CLI's text, and closing over a running job.
2. **The screen**: `screens/<name>.py`, takes the runner, calls the same core function as the CLI with texts from the
   shared Qt-free module. Layout through theme helpers only; copy the neighbour screen's structure.
3. **GREEN**: the screen's tests, then the shell tests. Once or twice, not in a loop.
4. **Screenshot** it (step 4) and look at it before moving on.

Rules that keep it from crashing, in short (details and reasons in bridge.md):
- No `import PySide6` outside `gui/`.
- Anything from a background thread reaches widgets only through a signal; every QObject background code touches has
  a parent.
- Every job connects all three outcomes; the error the user sees is a sentence, the traceback goes to the log.
- Long work has a working cancel; state shared between screens lives in one object `MainWindow` creates.

## Step 4. Screenshots and the hand-over to qt-ui

Write `scripts/screenshots.py` from qt-ui's recipe — the qt-ui skill's `references/screenshot-script.md`
([on GitHub](https://github.com/octrow/octrow-skills/blob/main/plugins/qt-ui/skills/qt-ui/references/screenshot-script.md)) —
with two changes for this template: offscreen ignores `setColorScheme`, so call `theme.force_scheme(scheme)`
instead, and the window gives `screen_names()` and `show_screen(i)`. Every screen, light and dark, at the default
size and at **960×640**, filled with the test fixtures' data, on a temp store, a fresh window per theme.

Run it, read every PNG yourself. Fix what's broken in behaviour (missing data, wrong text, a control that does
nothing). Layout defects (clipped text, uneven spacing, a color off in one theme) go on a list for qt-ui.

Before reporting, go through [references/pitfalls.md](references/pitfalls.md) against the diff: it's the list of
what actually broke in these apps.

## Step 5. Packaging — only when asked

Don't add PyInstaller, installers or release workflows unprompted. When the user asks: `--self-test` first, then a
one-dir spec, then a CI matrix that installs and runs the self-test of every artifact.
[references/packaging.md](references/packaging.md).

## Report (Russian, short)

First line: what the user can do now (`<app> gui`, which screens). Then 2-4 points: the bridge chosen and why, the
parity table status (closed / what's left and why), the checks run (tests with counts, screenshot folder path), the
qt-ui list if any — and offer to run `/qt-ui` on it. A test that fails is reported with its output.
