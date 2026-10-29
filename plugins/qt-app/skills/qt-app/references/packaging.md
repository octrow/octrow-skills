# Packaging (only when the user asks)

Worked pipeline: buy-smarter [`packaging/`](https://github.com/octrow/buy-smarter/tree/main/packaging) and
[`.github/workflows/desktop.yml`](https://github.com/octrow/buy-smarter/blob/main/.github/workflows/desktop.yml);
the reasons are in its ADR 0003.

## The order

1. **`--self-test` first**, before any spec file: `python -m <pkg>.gui --self-test` builds the main window
   offscreen on a temp store and exits 0, or prints a traceback to a temp log and exits 1. It isolates HOME/data
   dirs and uses an in-memory keyring, so it never reads the user's files. Worked code:
   [`gui/selftest.py`](https://github.com/octrow/buy-smarter/blob/main/src/buysmarter/gui/selftest.py). Dispatch on
   the flag in `__main__.py` before anything reads the environment.
2. **PyInstaller one-dir**, one `.spec`: `collect_data_files` for package data (migrations, theme fonts and SVGs),
   hidden imports for what's loaded dynamically (keyring backends, Alembic, aiosqlite: the self-test found these),
   `excludes` for unused Qt modules. One-file starts slower and trips antivirus.
3. **CI matrix**: ubuntu-22.04 (the oldest glibc you support) → `.deb`; windows → Inno Setup; macos (arm64) → `.dmg`.
   **Every artifact is installed and started with `--self-test` in CI.** That's the only check for Windows and macOS
   when nobody can test there by hand; record those manual checks as deferred.
4. Release: one workflow that builds everything and publishes only when all builds and checks pass (a release that
   went out without its wheel broke `install.sh`).

## What broke in real builds

- Missing hidden imports (aiosqlite, Alembic) → caught by the self-test of the built app, not by unit tests.
- SVG icons need the `qsvg` image plugin in the build; the self-test asserts the window icon isn't null.
- Linux: `.deb` `Depends` from `ldd` of the frozen build (libEGL, libGL, libxcb-cursor0 for Qt ≥ 6.5's xcb plugin).
  X11 `WM_CLASS` must equal `StartupWMClass` in the `.desktop` file (`app.setDesktopFileName(...)`).
- Bundled native libraries need loader paths (PortAudio in an AppImage); test on a clean machine or container.
- Windows: the exe is windowed, so CI reads the exit code with `Start-Process -Wait -PassThru`. Inno Setup's lzma2
  on ~400 MB is slow, not hung.
- macOS: `hdiutil detach` fails with "Resource busy" on runners: retry with `-force`. Unsigned apps open only via
  System Settings → Privacy & Security → Open Anyway; `uv tool install` + `<app> gui` avoids Gatekeeper.
- An old unpacked version in `~/.local/opt` with a symlink in `~/.local/bin` shadows the new install.
- Size: PySide6-Essentials is ~100 MB unpacked; Playwright's driver another ~120 MB.

Alternatives when PyInstaller stops being enough: `pyside6-deploy` (Nuitka, faster start, long builds, breaks on
dynamic imports), Briefcase (native installers), tufup (signed auto-update).
