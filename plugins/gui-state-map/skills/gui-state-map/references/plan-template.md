# plan.md skeleton

Copy, fill in for the project, delete what doesn't apply. Write it in the user's language. Every `<…>` becomes a
concrete port, path, command or file:line, or `determine in step 1: <read-only query>` when only a run can tell.
A plan with bare placeholders left in is not ready for approval.

```markdown
# GUI review by screens and states: plan

**Main result: the full logic map through the GUI** (`map.md`). <one paragraph: every screen/window, state,
action; what it changes on screen, in data, on other screens; which steps of docs/logic-map.md it starts.>
Each state is backed by a screenshot, each transition by a diff/trace/log, or marked "not captured" with a reason.

**Nothing gets fixed during the pass.** Findings: one row in `findings.md`, then move on.

Report folder: `docs/archive/<date>-gui-review/` (git-ignored: screenshots carry personal data).

## Status on <date>

| Step | Status | Where |
|---|---|---|
| 0, 1 stand, inventory | | |
| 1a actions map | | |
| 1b, 1c scripts | | |
| 2 shooting | | |
| 3 batch maps | | |
| 4 merge | | |

Left to do: <numbered, with exact commands>. Refuted: <ids>. Learned about the tools: <…>.

## 0. Stand: real data on <date>

| Stand | Port / home | Data | What we do there |
|---|---|---|---|
| L live | <port> | <path> | R only |
| S sandbox | <port> | copy in <scratch path> | W |
| F fake run | <port> | as S | "running" without a real pipeline: <how> |
| E empty | <port> | empty home | no config / no data states |

- Owner's instance: <port>. Not shot.
- Start command (the real CLI path, so logging, migrations and .env behave as for the owner): `<cmd>`.
  Stop it with a separate command (`pkill -f "[p]ort=<port>"`), not in the same call as the start.
- What a start does on its own: <polls mail / runs checks / migrates>.
- Backups before the first click: <files> → <dir>, sha256 in stand.md. New backup name per batch.
- Action classes, with the owner's decisions and their dates:
  - R: <…>
  - W: <…>; undo first through <GUI undo>, else <restore>; log in snaps/RESTORES.md
  - hidden W: <…>
  - Q: <…>; not pressed / press-and-stop within 5 s, as the owner decided
  - X: <…>; last batch, ask the owner first
- Sizes: <main> and 390×844 once for <screens>. Themes: <…>.
- Keys for each state: one read-only query (step 1), not picked by hand.

## 0a. Tools

| Task | Tool | Why |
|---|---|---|
| Shooting the matrix and the click protocol | <Playwright script / offscreen test driver / import -window> | deterministic, a cheap agent only runs it |
| What a click changed in the UI | <trace / widget tree dump diff> | |
| What the server sent | <websocket frames> | which elements redrew and when |
| Front-end errors | <console / pageerror> | |
| Waiting | <expect(...).toHaveText(timeout)> instead of sleep | |
| Data before/after | snap script (1b) | |
| Reviewing screenshots | <design-critique skill, DESIGN.md wins> | |

Traps that break the scripts: <from references/stack-recipes.md and the project's GUI docs>.

## 1. Preparation (cheap model, one agent)
## 1a. Actions map (mid-tier, <N> agents by batch, code only)  ← record format from the skill
## 1b. Snapshot script (main session)
## 1c. Subprocesses (class Q): order from code + past runs, not run for screenshots
## 1d. Shooting scripts (mid-tier, one agent) + trial on one page

## 2. Matrix of screens × states

Click protocol: <copy the 6 steps from the skill, adapted>.

### 2.1 Shell (on any page)
| ID | What to shoot |
|---|---|

### 2.2 <screen> (`<module>`)
| ID | State |
|---|---|

## 3. Analyst's checklist  ← the 8 items, with this project's concrete examples
## 4. Map and findings  ← map.md structure and findings row format, with this project's graphs named
## 5. Agent split
| Step | Who | Input → output |
|---|---|---|
## 6. Done when
## Open decisions for the owner  ← each with a recommendation
```
