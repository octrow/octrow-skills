# GUI polish and README screenshots

## Before changing anything

0. **Is it already done?** When asked to refresh screenshots, compare the date of the last commit touching the
   screenshots with the last one touching the GUI code, and check uncommitted GUI changes. Screenshots newer than
   the GUI change: re-shoot to confirm, compare pixels (`PIL.ImageChops.difference(...).getbbox()` is `None` when
   identical), and if nothing changed, leave the PNGs untouched and say so. Ask where the changes are if the user
   expected a difference (another branch, stash, machine).
1. Find the screenshots the README already shows (`assets/readme/`, `docs/`). They are the "before", and the user has
   seen and accepted them.
2. Run the app and take the same views at the same sizes (`scripts/shots.py`), so "before" and "after" compare 1:1.
3. Read the user's saved taste in memory (e.g. dense tables, one value per column, one line per row). Taste beats
   a generic best practice.

## Doing the work

- Delegate: `impeccable` for critique/polish/audit of any web UI; `nicegui-kit-gui` for NiceGUI apps on the shared kit
  (fixes that belong to the kit go to the kit, or into a proposal there, not into the vendored copy).
- When the user pastes a review from another model, triage it: fix what's real, push back on what conflicts with the
  saved taste or the data, and say which is which.
- Data-heavy screens: information density first. Count rows per screen before and after; a change that halves it
  needs a strong reason.
- Wide tables: keep all columns on wide screens, hide low-priority columns on narrow ones, offer a column picker;
  avoid merged two-line cells.
- One design system: colors, type scale, weights, spacing, radii as tokens; a test that page CSS uses only tokens
  catches drift.
- Check light and dark theme, and a narrow window (~900px and phone width) if the GUI is meant for them.

## Showing the result

Put before/after side by side (same view, same size) and ask which one stays. If the user prefers "before", revert
that part fully and record why in memory; don't keep half of a rejected change.

## Refreshing README screenshots

- Same file names and pixel sizes as the old ones, so the README needs no edits and the diff is only images.
  Read the old size with `python3 -c "from PIL import Image; print(Image.open('x.png').size)"` or `file x.png`, then
  pick viewport × device scale that reproduces it (e.g. 1560×1134 css at scale 1.25 → 1950×1418 px).
- Use realistic data (a real saved run), not lorem ipsum; light theme unless the README shows both.
- Move the mouse away before the shot (no hover tint); wait for network idle and for remote images.
- Crop dialogs to the element (`"element"` in the spec). A nested dialog cropped to its parent's box: a
  `["remember_box", "<parent selector>"]` step before opening it, and `"clip": "box"` on the shot.
- Start your own server on a free port and pass its URL as the third argument (`shots.py spec.json out
  http://127.0.0.1:<port>`); the user may already run the app on the spec's port, and you'd shoot their instance.
- Keep images small: PNG of UI is fine at ~100–300 KB each; exclude `assets/` from the package.
- The spec is the only record of viewport heights (a dialog's PNG size depends on the window height and can't be
  read back from the image), so save it even when nothing needed re-shooting; offer it as a file to commit.
- Use `scripts/shots.py <spec.json> <out-dir> [base-url]`; write the spec once per repo next to the screenshots
  (e.g. `assets/readme/shots.json`) in a folder the package build excludes. Check the excludes:
  `docs/` often ships in the sdist.
- Changed PNGs only if pixels changed: re-encoding an identical image still shows up as a binary diff.
