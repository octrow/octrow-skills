# Qt pitfalls that look like design defects

Each of these cost a full fix-and-reshoot round in a real PySide6 app. Check this table before inventing a
workaround: the symptom on the screenshot rarely points at the cause.

| Symptom on the screenshot | Cause → fix |
|---|---|
| A `QPushButton` rule doesn't apply to buttons inside a card | `QGroupBox QWidget` (or any `Parent QWidget`) is more specific than a bare type → write `QGroupBox QPushButton` |
| Spinbox text glued to the frame | QSS padding doesn't reach the inner editor → `box.lineEdit().setTextMargins(...)` |
| A table column squeezed to letters stacked in a column | `Stretch` next to `ResizeToContents` columns gets only the leftovers → make it `Fixed` and give it the spare width yourself, with a floor (~160px), and let the table scroll sideways below that |
| A `resizeSection` call doesn't stick | the header overwrites it in its own layout pass → defer with `QTimer.singleShot(0, ...)` |
| A wrapped `QLabel` with a max width cuts its last line | the height is measured at the full offered width → subclass and override `heightForWidth(min(width, maximumWidth()))` |
| Gaps "almost" on the grid | Qt's default spacing is 6px and margins 9-11px → set `setSpacing` / `setContentsMargins` on every layout |
| Bold renders as regular | a variable font registers as one Regular style → bundle static weight files |
| `_text_` in markdown shows underlined | Qt's markdown maps emphasis this way → restyle the blocks after `setMarkdown`, or drop the markup |
| A text browser scrolls sideways by 1px | rounding overflow → `ScrollBarAlwaysOff` horizontally plus word wrap |
| A widget grows more or less than its siblings in a layout | its alignment flag changes how the layout gives it space → drop the flag, align with stretch instead |
| Line height in `QLabel` QSS does nothing | QSS has no `line-height` → only rich text (`QTextDocument` block format, proportional height) |

Process traps:
- `pytest … | tail` hides pytest's exit code: a failure looks like success. Run it unpiped or check `$?` first.
- A change to a shared model (a dataclass the CLI also prints) breaks the CLI tests, not the GUI ones: run both.
- Several agent sessions on one repo share the git index: commit only your paths (`git commit -m … -- <paths>`)
  and check `git show --stat HEAD` before pushing.
