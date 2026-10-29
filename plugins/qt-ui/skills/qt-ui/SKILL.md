---
name: qt-ui
description: Fast, house-style visual fixes for a PySide6 / PyQt6 desktop GUI. Shoots every screen offscreen in light and dark, finds the defects (clipped text, squeezed table columns, spacing off the grid, unreadable colours in one theme, nested scrolling, font weights that never render), copies the pattern from the neighbour screen that already gets it right, fixes through the project's theme tokens and generated QSS only, then re-shoots, pixel-diffs before/after to catch side effects on other screens, and runs the contrast and GUI tests. Use it for ANY visual or UX change in a Qt widgets app — "the GUI looks broken", "fix the layout", "text is cut off", "doesn't fit", "spacing is off", "dark theme is unreadable", "make it like the other screen", a new card, table, form field or status label, or a review of a screen or screenshot — even when the user doesn't say "design". Prefer it over web design skills (frontend-design, impeccable, ui-ux-pro-max) in a Qt project, since those target HTML/CSS and push a new look; here the goal is a screen indistinguishable from its neighbours. Triggers in Russian too — «кривой GUI», «проблемы с визуалом», «поправь вёрстку», «не влезает», «обрезается текст», «съехало», «отступы», «тёмная тема».
---

# Qt UI: like the neighbours, through tokens, checked on screenshots

A good result is a screen that can't be told apart from the screens next to it, not a "beautiful" one.
Don't pull in someone else's look (Fluent, qt-material, a stock dark theme): the project's own tokens win.

When sources disagree, this order decides:
**the user's remark → the neighbour screen → the design doc → the theme module → this skill → taste.**
If the user's remark contradicts the design doc or the neighbour, name the conflict in one line and ask.

**Invoked with no task**, don't start a fresh audit: work the project's open-defects list top down, then audit only
once it is empty. Keep two lists in the project (its own copy of this skill, or the design doc), updated in the
same commit as the fix: **open defects** (seen, not fixed yet) and **left on purpose**, each with its reason (a Qt
limit, a grouping by meaning, the user's call), so the next audit doesn't report them again. A list that lives
only in the conversation is lost when the context is compacted.

## Step 0. Find the four anchors (once per project)

| Anchor | Typical place | If missing |
|---|---|---|
| Design doc: tokens, type scale, component rules | `DESIGN.md`, `docs/design*.md` | Derive the scale from the theme module; offer to write the doc after the fix |
| Theme module: palettes, spacing and type scale, QSS builder | `gui/theme*.py`, `*/theme/__init__.py`; grep `setStyleSheet(` and `QPalette` | Colours scattered in widgets are the first defect to report |
| Screenshot script: every screen, both themes, offscreen | `scripts/screenshots.py`, a CI step uploading PNGs | Write one from [references/screenshot-script.md](references/screenshot-script.md) before fixing anything |
| GUI tests, contrast test | `tests/gui/`, pytest-qt | Note it in the report; don't build a suite for a visual fix |

Map the sidebar or tab names to screen files in a short table for yourself. Users name screens by what they see,
and "settings" often means a different screen than `settings.py`. When it's ambiguous, say which screen you took.

## Step 1. BEFORE screenshots (always first)

Run the screenshot script into `<scratchpad>/before` with `QT_QPA_PLATFORM=offscreen`. If the GUI is an optional
extra, install it for the run (`uv run --extra gui …`, check how CI does it), otherwise everything fails with
`ModuleNotFoundError: PySide6`, especially in a fresh worktree.

Know the script's blind spots before you trust it. The usual ones are in the screenshot reference: a main screen
shot only in its empty state, only one screen shot at the minimum window size, and state that leaks from the light
pass into the dark one. Shoot the screen you are fixing filled with data and at the minimum size, even if the
script doesn't.
Shoot the maximised window on a large screen (e.g. 2560×1440) too: cards stretched in height and rows wider than
the content cap only show there.

Look at the PNGs yourself (Read), every screen in both themes. If the user named problems, start there. If they
said "find them yourself", go through the defect checklist below and hand over a **list before any edit**: screen ·
theme · what's wrong · which rule it breaks. Then fix.

## Step 2. Before the first line of code

Open the neighbour screen that already does it right and copy how it does it: object name or dynamic property for
QSS, the card helper, the status helper, the icon helper, layout margins and spacing from the spacing scale.

Defaults, unless the neighbour does otherwise (then the neighbour wins):

- **Colour and size come only from tokens.** A `#hex` literal, a `setStyleSheet("color: …")` inside a screen, a
  `QColor(…)` with numbers, pixel values off the scale: each one is a defect. A new style is a rule in the QSS
  builder keyed by object name or dynamic property, not an inline style. A new colour goes into both palettes, and
  a text/background pair goes into the contrast test.
- **Spacing:** one grid (usually 4px). Set `layout.setSpacing(...)` explicitly: Qt's default is 6px, which is off
  any 4px grid and the most common "uneven" look. Proximity is meaning: line < group < cards < screen edge.
- **Type:** the fixed scale from the design doc, one family. One screen heading per screen, at the same place on
  every screen, empty states included.
- **Controls:** one height for every field; field starts on one vertical line. Keep the label placement the screen
  already uses (above vs left in a `QFormLayout`); switching it is the user's decision.
- **Buttons:** one primary action per screen, the rest secondary.
- **Statuses:** a label with a state property styled by QSS, never coloured by hand.
- **Tables:** stretch the main text column, don't let it collapse; cell text aligned with its header; no table
  scrolling inside a scrolling page unless the neighbour does it.
- **Empty states:** the same page as the filled screen (heading, one muted line), not text centred in a void.
- **Live theme switch:** anything that reads a colour once (an icon, a `QPalette`, a pixmap) must refresh on
  `QStyleHints.colorSchemeChanged`.
- **Width:** everything fits the window's minimum size without clipping or a horizontal scrollbar.

### Defect checklist (what to look for on the screenshots)

Clipped or elided text · a label wrapped for no reason · fields of different heights or off one vertical ·
spacing off the grid, uneven rhythm between cards · white on white or grey on grey in one theme · an icon that
kept its colour after the theme switched · two primary buttons · a table column squeezed to letters stacked in a
column · cell text not aligned with its header · scrolling inside scrolling · a card with only its title · a
horizontal scrollbar in a text browser · a missing or misplaced screen heading · an empty state without a heading
· an element that differs from the same element on the neighbour screen.

For an audit, also go through [references/ux-rules.md](references/ux-rules.md): the UX laws and the typography
and grid rules translated for Qt, with the web rules that don't apply. Two that catch real defects: line length
over ~70 characters in hints and status text, and card padding larger than the gap between cards.
When a fix doesn't take, check [references/qt-pitfalls.md](references/qt-pitfalls.md) first: Qt quirks that look like design defects.

Then check that **the tokens actually render**, not just that they are written. Zoom into a crop of a card title
next to body text: if 600 looks like 400, the font weight isn't applied (Qt often sees a variable font as a single
Regular style; register static weights or set the weight through `QFont`). That defect hits every screen at once
and is invisible in the screens' code.

## Step 3. Verify before reporting

1. AFTER screenshots into `<scratchpad>/after` with the same command.
2. Pixel diff, to catch a shared QSS change leaking onto other screens:
   ```bash
   python <this skill's dir>/scripts/shotdiff.py <scratchpad>/before <scratchpad>/after
   ```
   Run it with the project's Qt (`uv run --extra gui python …`) and an absolute path to the script. It prints the
   changed images with the share of changed pixels; exit code 1 means "something differs", which is expected for
   the screens you meant to change. Anything else that changed gets explained before the report.
3. Look at AFTER yourself next to BEFORE and the neighbour: same type size, control height, spacing, both themes,
   minimum window size.
4. Only the affected tests: the contrast test plus the tests of the touched screens, and the linter on the GUI
   package. Don't pipe pytest through `tail`: the pipe hides its exit code.

A failing test gets reported with its output; a screenshot is not a substitute for a check.

Commit only your own paths (`git commit -m … -- <paths>`): other sessions may share the index.

## Report

First line: what changed on screen. Then 2-4 points: what was fixed (screen · theme), what was reused, what was
checked (themes, minimum size, tests), paths to the BEFORE and AFTER screenshots. A conflict with the design doc or
the neighbour goes on its own line for the user to decide. If a screen's look changed, offer to refresh the
README/docs screenshots and the design doc.

When refreshing reference screenshots, keep a table in the project from the script's output names to the
reference names (they rarely match), and never put a screen that shows the user's own data (their photos, saved
reports, keys) into the repo: the script may read real local data.
