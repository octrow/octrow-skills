# A screenshot script for a Qt app

What the skill needs from it: every screen, light and dark, as PNG files with stable names, rendered offscreen on
temporary data so the user's own files are never touched. CI can upload the same output for review.

Worked example: [buy-smarter `scripts/screenshots.py`](https://github.com/octrow/buy-smarter/blob/main/scripts/screenshots.py)
(PySide6, a sidebar app, about 240 lines with seeding).

## Skeleton

```python
"""Every screen in light and dark:  python scripts/screenshots.py OUT_DIR -> OUT_DIR/{light,dark}/NN-name.png"""
import os, sys, time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

SIZES = {"": (1280, 800), "-min": (960, 640)}  # the default window and the window's minimum size


def settle(app, seconds=0.3):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()


def main(out: Path) -> None:
    app = QApplication(sys.argv[:1])
    # point the app's store/config at a temp dir HERE, before the window builds anything
    from myapp.gui.app import MainWindow  # import after the environment is set
    for scheme in (Qt.ColorScheme.Light, Qt.ColorScheme.Dark):
        app.styleHints().setColorScheme(scheme)  # Qt 6.8+; older: apply the palette by hand
        window = MainWindow()                   # a fresh window per theme: no scroll or input state leaks across
        window.show()
        for index, name in enumerate(window.screen_names()):
            window.show_screen(index)
            fill_with_data(window, name)        # the screen as users see it, not only empty
            for suffix, size in SIZES.items():
                window.resize(*size)
                settle(app)
                path = out / scheme.name.lower() / f"{index:02d}-{name}{suffix}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                window.grab().save(str(path))
        window.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
```

`screen_names`, `show_screen` and `fill_with_data` stand for whatever the app has; reuse the GUI tests' fixtures
for the data (a filled report, a table with long names) instead of writing new ones.

## Blind spots seen in real runs

- **Main screen shot only empty.** The screen users look at most had no data in the script, so the audit missed
  its worst defects. Fill every screen that shows data.
- **Only one screen at the minimum size.** Squeezed table columns and clipped status text appear only at the
  minimum window size, on the screens that weren't shot there. Shoot every screen at both sizes.
- **State leaking between themes.** One window reused for both passes kept the scroll position and the typed
  query, so light and dark couldn't be compared side by side. Build a fresh window per theme.
- **Names that don't match the docs.** `light/02-Report.png` from the script and `light-report.png` in the README
  folder make comparison awkward. Pick one naming scheme.
- **Fonts.** Load the bundled font in the script exactly as the app does, or every screenshot renders in a
  fallback font and the type scale can't be judged.
