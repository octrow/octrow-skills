# Scaffold: extra, command, window, theme

Step 2 in detail. The template in `scripts/template/` is the starting point; this file says where each piece goes
and what to change.

## Layout

```
src/<pkg>/
  core..., services..., cli...  # no `import PySide6` anywhere here
  <texts module>                # Qt-free: labels, messages, number formats, shared by the CLI and the GUI
  gui/
    __init__.py
    __main__.py   # python -m <pkg>.gui, and the frozen app's entry
    app.py        # QApplication, theme, CoreRunner, MainWindow, excepthook, Ctrl+C, shutdown
    bridge.py     # CoreRunner / Job
    theme.py      # tokens, LIGHT/DARK, build_qss, apply_theme, icon/bind_icon, set_state, card_body
    screens/      # one file per screen: <name>.py with <Name>Screen(QWidget)
tests/gui/
  conftest.py     # QT_QPA_PLATFORM=offscreen, the runner fixture, fakes for slow or external checks
  test_shell.py   # from the template: bridge, theme contrast, window, close-while-busy
scripts/screenshots.py
```

Grows into a package (`theme/` with fonts and SVGs) when it needs assets; start with one file.
Reference layout: [buy-smarter `src/buysmarter/gui/`](https://github.com/octrow/buy-smarter/tree/main/src/buysmarter/gui).

## pyproject

```toml
[project.optional-dependencies]
# The desktop app: Widgets/Gui/Core only, without WebEngine and the addons (hundreds of MB).
gui = ["PySide6-Essentials>=6.8", "qtawesome>=1.4"]

[project.scripts]
<app>-gui = "<pkg>.gui.__main__:main"

[dependency-groups]
dev = [..., "pytest-qt>=4.5"]
```

- **PySide6-Essentials**, not `PySide6` (that adds the addons). LGPL, so fine for MIT and closed code. PyQt6 only
  if the user asks: it's GPL or commercial.
- `uv sync` without the extra removes PySide6, and pytest-qt then fails to load at all. Everywhere (CI, fresh
  worktrees, docs) use `uv sync --extra gui` or `--all-extras`; a fresh worktree hits this first.
- Don't remove the `pyside6` metapackage from an env that has Essentials: the uninstall deletes shared files.
- No Fluent widgets (PyQt-Fluent-Widgets / PySide6-Fluent-Widgets): GPLv3, full PySide6 instead of Essentials, a
  Windows 11 look with a custom title bar that's foreign on GNOME, English strings. Our own tokens plus qtawesome.

## The `gui` command in the existing CLI

The command imports Qt lazily, so the CLI works without the extra and says how to get it:

```python
@app.command()
def gui() -> None:
    """Открыть окно приложения (нужен extra gui)."""
    try:
        from <pkg>.gui.app import run as run_gui
    except ModuleNotFoundError as exc:
        if not (exc.name or "").startswith("PySide6"):
            raise
        print("Для окна нужен extra gui: pip install '<pkg>[gui]'", file=sys.stderr)
        raise SystemExit(1) from exc
    raise SystemExit(run_gui())
```

argparse CLI: the same, as a `gui` subcommand. The GUI's `main()` does the CLI's own start-up (logging setup, config
load, local store prepare): call the same functions, don't copy them.

## The window

The template's `MainWindow` already has: a fixed-width sidebar (`QListWidget#sidebar`, icons through `bind_icon`,
no horizontal scrollbar, elided items), a `QStackedWidget`, every screen wrapped in `_page()` (heading, width cap
1200, centered, scrolls), `setMinimumSize(960, 640)`, `closeEvent` that asks over running work, and
`screen_names()` / `show_screen(i)` for the screenshot script.

Add a screen: its file in `screens/`, one row in `MainWindow._screens()` (sidebar title = screen heading, an
`mdi6.*` icon). Group the sidebar with headers once there are more than ~5 screens (buy-smarter `_nav_groups`).

## The theme

The template's `theme.py` is the house style: tokens (`TYPE`, `SPACE` on a 4px grid, `PAGE_GAP`, `CARD_GAP`,
`RADIUS`, `CONTENT_MAX_WIDTH`, `MIN_WINDOW`), `LIGHT` and `DARK` palettes with semantic names, `TEXT_PAIRS` held
to WCAG AA by a test, a generated QSS, the scheme following the OS live, `force_scheme()` for offscreen.
Change the palette (accent first) for the project; keep the shape. The rules for using it — tokens only, no
`setStyleSheet` in screens, states through `set_state` — are qt-ui's; see its SKILL.md step 2.

- **A bundled font** gives the same look on every OS. Ship **static** faces (Regular, SemiBold, Bold) in
  `gui/fonts/` (`theme.py` loads every `*.ttf` there): Qt registers a variable font as one Regular style, so 600
  renders as 400 and 700 as a fake bold. No italic face means markdown italics render wrong: avoid italics or ship it.
  Keep the font's licence file (OFL) next to it.
- **Icons:** qtawesome `mdi6.*`, drawn in a palette color through `icon()`. An icon set once keeps the old theme's
  colors after a live switch: every icon goes through `bind_icon(owner, setter, name)`.
- **Offscreen has no OS scheme.** `styleHints().setColorScheme()` does nothing under `QT_QPA_PLATFORM=offscreen`, so
  tests and screenshots call `theme.force_scheme(Qt.ColorScheme.Dark)`.

## Start-up details that bit real apps

- **Excepthook**: `install_excepthook(window)` turns an unexpected error into a dialog with one sentence; a second
  error while the dialog is open is only logged. Without it, exceptions in slots vanish.
- **Ctrl+C / Ctrl+D**: Qt's C++ loop never lets Python run its SIGINT handler, so `<app> gui` ignores Ctrl+C.
  `quit_from_terminal(app)` (a SIGINT handler plus a 200 ms timer that wakes the interpreter) is in the template.
- **Terminal output**: an expected failure (HTTP 503, missing key) is one WARNING line; the traceback goes only to the
  log file. A terminal full of tracebacks reads as "it crashed".
- **PATH from a desktop-menu launch** lacks what shell rc files add (nvm, `~/.local/bin`), so tools the core shells
  out to "aren't installed". If the core runs external CLIs, take PATH from the login shell once when stdin isn't a
  TTY: buy-smarter `inherit_login_path` in [`gui/app.py`](https://github.com/octrow/buy-smarter/blob/main/src/buysmarter/gui/app.py).
- **Nothing heavy at import.** A DB engine or a config read at import crashed the packaged app on a stale `.env`.
  A missing optional backend degrades one feature with a visible note; it never kills start-up.
- **Start-up checks are not modal.** A blocking "system check" dialog at start freezes everything behind it; show
  the result on a status screen or a banner.
- **One instance** if the app holds a heavy resource (GPU model, a port, a DB lock): a second copy's failure gets
  misreported as something else ("check your internet").
