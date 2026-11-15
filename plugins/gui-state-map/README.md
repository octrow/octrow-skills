# gui-state-map

**English** | [Русский](README.ru.md)

A skill that maps a GUI by screens × states × actions and proves each step with a screenshot and a diff.

## Install

```bash
claude plugin install gui-state-map@octrow-skills
npx skills add octrow/octrow-skills --skill gui-state-map -g
```

## What it does

1. Writes a plan: a safe stand on real data, the click classes (read, write, quota, system), the state matrix.
2. Reads every button from the code: handler, what it writes, what it starts, what it should change on other screens.
3. Clicks through the matrix with scripts, with a screenshot, the page text and a data diff before and after each click.
4. Merges `map.md` with state and sequence graphs. Findings go to `findings.md`, and nothing gets fixed during the pass.

Web GUIs go through Playwright. Desktop GUIs go through an offscreen test driver plus a live run with X11 tools.

## Ask

- "review the GUI screen by screen: what every button does, with screenshots"
