# qt-app

**English** | [Русский](README.ru.md)

A skill that builds a PySide6 desktop GUI from scratch for a Python project, or adds a screen to an existing Qt app. The pair of [qt-ui](../qt-ui/README.md).

## Install

```bash
claude plugin install qt-app@octrow-skills
npx skills add octrow/octrow-skills --skill qt-app -g
```

## What it does

1. Checks how the core can be called in-process.
2. Runs the core on an asyncio loop in a worker thread, with results back as Qt signals.
3. Scaffolds from a runnable template: the `gui` extra, a `<app> gui` command, a sidebar window and an own light/dark token theme.
4. Builds screens one at a time, test first, with pytest-qt offscreen. Texts and calls are shared with the CLI.
5. Hands screenshots of both themes to qt-ui for layout polish.

## Ask

- "add a desktop window to this CLI"
- "add a «Журнал» screen to the app"
