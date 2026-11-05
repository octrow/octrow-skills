# qt-ui

**English** | [Русский](README.ru.md)

A skill for visual fixes in a PySide6 / PyQt6 desktop app.

## Install

```bash
claude plugin install qt-ui@octrow-skills
npx skills add octrow/octrow-skills --skill qt-ui -g
```

## What it does

1. Shoots every screen offscreen in light and dark.
2. Lists the defects: clipped text, squeezed table columns, spacing off the grid, font weights that never render.
3. Fixes them through the project's theme tokens, copying the neighbour screen that already gets it right.
4. Pixel-diffs before and after, so a shared QSS change can't quietly break another screen.

A reference lists the Qt quirks that look like design defects:

- labels pinned above their fields;
- columns squeezed to letters;
- bold that renders regular.

A bare run picks up the project's list of open defects.

## Ask

- "the GUI looks broken, find what's wrong on every screen"
- "the report doesn't fit the small window"

Pairs with [qt-app](../qt-app/README.md).
