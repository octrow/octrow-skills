# UX laws and layout rules, translated for a Qt desktop app

Read this when auditing a screen ("find what's wrong") or when a fix needs a reason beyond "the neighbour does it".
General rules from [Laws of UX](https://lawsofux.com/) and common typography and grid advice, each turned into what it
means in a PySide6 / PyQt6 widgets app. The project's design doc still wins over this file.

## Laws → what to check on a screen

| Law | In a Qt desktop app |
|---|---|
| Jakob, Mental model, Similarity | The same element looks and sits the same on every screen (heading, card, table, buttons). Use platform conventions: native `QFileDialog`/`QMessageBox`, Enter submits the form, Esc cancels a dialog, a sane tab order |
| Hick, Choice overload, Von Restorff, Selective attention | One primary button per screen; the accent marks action and current selection only, never decoration; rare actions go into a menu |
| Fitts | Every field one height (often 32-36px); icon-only buttons at least 28px; the main action at the end of the form, where the eye finishes |
| Doherty (<400ms) | Instant feedback on click: the button disables, a busy state shows. Anything over a second gets visible progress that only moves forward and a working Cancel |
| Proximity, Common region, Uniform connectedness, Chunking, Miller | Group with a card or with spacing, not with divider lines; at most ~7 fields per group; related controls on one row |
| Prägnanz, Aesthetic-usability | Alignment and an even spacing rhythm make a screen read "professional"; no ornaments |
| Tesler, Occam | The app absorbs complexity: smart defaults over another toggle |
| Postel | Fields accept variants (spaces, `40 000`, case) and normalise them; show the normalised value back |
| Peak-end, Zeigarnik, Goal-gradient | Polish the result screen and the error and finished states; show stages ("2 of 4"); never move progress backwards |
| Paradox of the active user | Nobody reads docs: the empty state says what to do next, hints sit next to the field |
| Serial position | The most used nav item first; the confirming button last in its row |
| Cognitive load, Working memory | Don't make users carry a value from one screen to another; show it where it's needed |

## Typography

- **Hierarchy by size and weight**, one family is enough. Check that weights actually render: Qt registers a
  variable font as a single Regular style, so 600 draws as 400 and 700 as a synthetic bold. Bundle static weights.
- **Never distort**: no synthetic bold, no synthetic italic. If the app shows italics (rich text, markdown), bundle
  the italic file or drop italics.
- **Body size** is the design doc's: dense desktop UIs often use 13-14px instead of the web's 16px. Don't "fix" it.
- **Line length 40-70 characters** for prose: a hint or status text spanning the whole 1200px card is a defect.
  Cap it with a max width on the label or wrap it (`setWordWrap(True)`).
- **Line height ~1.5** applies to rich text only (`QTextBrowser` HTML/CSS); `QLabel` QSS has no line-height.
- **Left-aligned, ragged right**; no justified text. All caps only for short group labels.
- Widows and orphans can't be controlled in Qt; shorten the text instead.

## Grid and spacing

- **One spacing scale** (4px or 8px based), with 4px only for micro gaps (icon to label). Qt's default layout
  spacing (6px) and margins (9-11px) are off any scale: set them explicitly.
- **Internal ≤ external**: the padding inside a card is not larger than the gap between cards, or the cards stop
  reading as separate units. Check card padding in the QSS against the page layout's `setSpacing`.
- **Keylines**: every element aligns with at least one other along a vertical or horizontal line: field starts,
  card edges, table cell text under its header.
- **Max content width** around 1200px, so a maximised window doesn't stretch rows across an ultrawide screen.
- **Focal point**: every screen has one dominant anchor (the result card, the key number); equal boxes don't
  compete.
- **No false bottom**: in a scrolling page, a card that ends exactly at the window's bottom edge hides that the page
  scrolls. Check at the default and the minimum window size.

## What not to take from web rules, and why

- Responsive 12/8/4-column grids, breakpoints, "stack and simplify": a desktop window has one minimum size; the
  equivalent is "everything fits the minimum size, rows wrap (two rows of buttons) rather than clip".
- Serif + sans pairing, fluid type: one family with a fixed scale is the desktop norm.
- 48-96px whitespace between sections, Z-pattern, hero, rule of odds, asymmetric splits: landing-page devices. A
  desktop tool with a sidebar is an F-pattern: heading top left, content down the left edge.
- `box-sizing`: no such thing in QSS. The Qt equivalent: padding and border add to a widget's size, so a fixed
  height plus padding can clip text; check that controls with fixed heights still show the full text.
