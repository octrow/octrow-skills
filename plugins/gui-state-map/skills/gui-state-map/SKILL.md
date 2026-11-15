---
name: gui-state-map
description: Map a GUI's logic by screens × states × actions, proved by screenshots and before/after diffs. Every screen, window, dialog and tray item; every state it can be in; every clickable thing read from the code (handler file:line, what it writes, which subprocess and steps it starts, what it should change on OTHER screens), then clicked on a safe stand on real data and checked by a data snapshot diff, a Playwright trace or a log. Output is a plan.md, an actions map, a merged map.md with mermaid state and sequence graphs, and findings.md as a by-product: duplicates, contradictions, doc drift, dead ends, wording, visual issues. Nothing gets fixed during the pass. Works for web GUIs (NiceGUI, any browser app through Playwright) and desktop ones (Fyne, Qt, GTK through an offscreen test driver plus a live run with X11 tools). Splits the work between cheap shooter agents and mid-tier analyst agents. Use it whenever the user wants a full GUI walkthrough, a screen-by-screen review, a map of what each button does, screenshots of every state, a check that the GUI matches the code and docs, or a "fresh user" pass, even if they only say "review the GUI" or "пройди весь интерфейс". Russian triggers: «обзор GUI по экранам и состояниям», «карта GUI», «карта логики через GUI», «сними все экраны и состояния», «что делает каждая кнопка», «пройди все кнопки», «собери скриншоты и проведи ревью», «план обзора GUI». Not for fixing a visual defect on one screen (qt-ui, impeccable) and not for mapping the code pipeline without a GUI (logic-map).
---

# GUI state map: screens × states × actions, proved by screenshots and diffs

The goal is **one map** (`map.md`): every screen and window, every state it can be in, every action and where it
leads: what it changes on screen, in the data, and on other screens; which processes it starts and in what order.
Each state is backed by a screenshot, each transition by a diff, a trace or a log. Anything not captured is marked
"not captured" with a reason.

**Nothing gets fixed during the pass**: no code, docs or data. Anything noticed becomes one row in `findings.md`
and the work moves on. Bugs, duplicates and contradictions are a by-product of the map. Fixing comes later, as
separate changes, once the map is done. Fixing mid-pass would stale half the screenshots already taken and mix
two jobs that need different attention.

This method came out of three real runs (a NiceGUI job-hunting dashboard, a NiceGUI content app, a Fyne desktop
overlay app). Each run turned up 17–80 findings, several of them H severity: broken buttons, a header that never
refreshed, an undo that lost data, "applied now" that wasn't. Most were visible only because the click's
**expected effect on other screens** had been written down from the code before anyone clicked.

## Where things go

Make a report folder: `docs/reports/<YYYY-MM-DD>-gui-review/`. If screenshots will show personal data (real
handles, emails, account names, private photos), use a **git-ignored** folder instead (for example `docs/archive/…`),
or a folder outside the repo (`~/.local/share/<app>-gui-review/<date>/`) when the repo must stay untouched or the
user keeps personal files out of repos. Say which one in the plan. Personal data does not go into git.

Files: `plan.md`, `stand.md` (or `states.md`), `inventory.md`, `actions[-a|-b|-c].md`, `map[-a|-b|-c].md`,
`map.md`, `findings.md`, `scripts/`, `shots/`, `snaps/`, plus `traces/`, `ws/`, `logs/` as the stack needs.
Write the documents in the user's language.

## Step 0. Write plan.md first, then stop for approval

Read before writing: `docs/logic-map.md` (if it exists), the GUI docs, `DESIGN.md`, the glossary, the GUI module
list. Count the clickable places with a grep for the stack's handler pattern (`on_click`, `ui.button`,
`widget.NewButton`, `clicked.connect`, `onClick`), then count **controls on screen**: one handler often serves
several buttons, and signals other than clicks (`currentIndexChanged`, `textChanged`) are actions too. The control
count sizes the batches. Split them into about three batches along the GUI's natural seams, of similar size.

Use `references/plan-template.md` as the skeleton. The plan must name concretely, for this project:

1. **The stand** (§0): which instance, which port, which data. Rules:
   - **Never shoot the owner's running instance.** Start a second one on the current working-tree code, on a
     separate port (web) or with a separate home (desktop: `HOME`/`XDG_*` pointed at a copy). The owner's instance
     runs the code of its own start and would show already-fixed bugs.
   - Use **real data as it is today**. Find one real example per state with a read-only query. If a state has no
     example in the data, mark it "not in data". Never fake rows without the owner's explicit decision.
   - Where the app writes, prefer a **sandbox copy** of the data (hard links for big media, `cp -al`). Typical
     stands: **L** live (read-only clicks), **S** sandbox copy (write clicks), **F** fake "run in progress"
     (swap the run pool or submit a dummy subprocess that prints progress), **E** empty home (no config / no
     data states).
   - Back up every file a click can overwrite before the first click, with `sha256sum` in `stand.md`. Use a
     **new backup name per batch**: reusing a name overwrites the earlier copy.
   - Check what **starting** the app does on its own (polls mail, migrates a store, runs health checks,
     **auto-updates its own code**). A start can write before any click. If it always writes, drop the read-only
     L stand and work on copies only. Secrets that live outside files (the system keyring) can't be backed up:
     swap the backend in the stand. See "Desktop stands" in `references/stack-recipes.md`.
2. **Action classes**. The class decides how to roll a click back, not whether to click:
   - **R** read-only: click freely.
   - **W** the GUI writes (status, note, setting, file): click on the sandbox, or back up first. Undo with the
     GUI's own undo button first, which gets shot as its own transition. Where there is no undo, restore row by row
     (other processes may write to the same store), and log each restore in `snaps/RESTORES.md`.
     **Hidden W**: actions that write without a "save" (a search that rebuilds an index, a page that runs checks
     on open). The diff has to prove them.
   - **Q** quota, network, a live account, GPU: don't press it just for a screenshot. Shoot the button, the
     confirm dialog with "Cancel", and "running" on the F stand. Take the step order from the code and from
     **past real runs** (logs, run history pages). If the owner wants live Q shots, press it, shoot start and
     "running", stop within about 5 s, shoot the stop and the toast, then diff. A stop mid-step is itself a state
     worth mapping.
   - **X** system level (systemd, restart or shut down the server, reinstall timers, self-update of the code,
     anything outside the app's own data): a separate last batch,
     and **ask the owner first**, because it can kill their instance. Permission classifiers often block it for
     agents. Then hand the owner a ready `! …` command.
3. **The state matrix** (§2): one table per screen, `ID | what to shoot`. IDs are short and stable (`S1`, `T3`,
   `C12a`). Add 390×844 phone width once for the main screens next to the main size (for example 1440×900). For
   desktop apps, add both themes and a window at its minimum size (or below it, if the app allows it). A
   collapsible section takes two shots (`-a` collapsed, `-b` expanded). A row can also be a **check** rather than
   a state ("no way back from X"). Mark those rows `check`, so they aren't counted as states.
4. **The tools** (§0a), the split between agents (§5) and the done criteria (§6), as in the template.

A value the plan can't know without running anything (a path the app computes, which health checks fail on this
machine, whether the data has an example) is written as `determine in step 1: <the read-only query or command>`,
never as a guess. Put the open decisions for the owner at the end of the plan, each with a recommendation.

Show the plan to the user and **wait for approval** before step 1. The owner decides the W/Q/X rules for their
data, and those decisions get written into §0 with the date.

## Step 1. Stand and inventory (cheap agent, one)

Bring up the stand, check that it answers, and run the project's GUI tests (green at the start, green at the
end). Then list every clickable element from the **code**: one row per element with surface, label, `file:line`
and handler, written to `inventory.md`. For a web app, cross-check against `getByRole` on the live page.
Find the real example for each state from §2 and write `states.md` as `ID → key → why it fits`.

## Step 1a. The actions map, from code before any click (mid-tier agents, one per batch)

One record per action, **read from the code, not guessed from the screen**:

```
### A<NN> «<label>» — <screen>, state <ID from §2>
Handler:        file:line (and through what: registry action / direct call)
GUI writes:     table.column / file / config key — or "nothing"
Starts:         exact argv of a subprocess, or the in-process coroutine / thread / worker — or "nothing"
Order:          its steps in order, with §§ of docs/logic-map.md; where it can stop and with what result
Quota:          does it spend LLM / API quota, which model by default
Disabled when:  when the control is disabled or ignored
UI reaction:    what redraws at once / on a timer tick / on a periodic resync; toast; where it navigates
Expected after: the new state (ID from §2) AND what appears or disappears on OTHER screens
```

**The last line matters most**: cross-screen mismatches only show up this way. Reject records without
`Handler: file:line`. The records add up to a graph "state → action → state". Holes in it (a state with no way
out, an action with no expected result, two actions with one result under different words) are findings already.
Batches follow the GUI's natural split (shell + home, the main entity card, the rest), the same three batches
through steps 1a, 2 and 3.

## Step 1b. The snapshot script (main session)

One script, `snap <ID>` (or `snap <key>` for an entity page), that **reads only** and dumps everything a click can
change: the entity's DB row and related rows, new lines of append-only logs since the last snapshot, file listings
of output dirs, the config hash and copy, the run pool, the page title and header counters. Then
`diff before after` shows what the action actually changed. Compare the diff with "GUI writes" and "Expected after"
from the actions map. A mismatch is a finding. Use a new ID each time, because a reused ID overwrites its log slice.

## Step 1c. The shooting scripts (mid-tier agent, one), then a trial run

Deterministic scripts, one per batch: go to the state, shoot it, dump the page text, click, shoot again. The page
text next to every screenshot lets the analysts check wording without OCR. Put **a blacklist of Q and X selectors**
in the script so that it fails loudly if it tries to press one, and test the blacklist. Add a `--dry` mode that
writes to `dry-*` files.

**Run it on one page first and look at the output** before shooting the whole matrix. Stack recipes and the
pitfalls that broke scripts in real runs are in `references/stack-recipes.md`. Read the section for this
project's stack before writing the scripts.

## Step 2. Shooting (cheap agents, one per batch, **one after another**)

The shooters run the scripts and check that the files appeared. They don't judge anything. They run **one after
another**, not in parallel: they share live data and append-only logs, and in parallel the diffs would mix.
They still check each diff for foreign lines (the owner's instance, nightly timers).

**Protocol for one click** (each A<NN>, in its starting state):

0. snapshot `before` + `shots/A<NN>-0-before.png` (+ `.txt`);
1. click; shoot at once `A<NN>-1-click.png` (dialog, "running" button);
2. with a subprocess: shoot on the first tick `A<NN>-2-running.png` and at the end `A<NN>-3-done.png`;
3. shoot after the periodic resync, if the app has one `A<NN>-4-settled.png`;
4. shoot the **other** screens that the actions map says should change `A<NN>-5-<screen>.png`;
5. snapshot `after`, `diff` → `A<NN>.diff`.

Clicks that timed out or were skipped go into `skipped-<batch>.md` with the reason. They don't block the batch.

Desktop apps with a live run that needs a human (tray menus drawn by the shell, system portal dialogs, a real
voice question): the **owner clicks from a numbered script** (`live-scenario.md`), and the main session calls
`snap` after each step. Don't hand a live, quota-spending run to a cheap agent, because it needs decisions on the
way.

## Step 3. A map per batch (mid-tier agents, the same batches)

Input: screenshots + page text + diffs, traces or logs + the batch's actions map. Output: `map-<batch>.md` with
screens and their states, a transitions table, and for each transition **"confirmed: shot / diff / trace / log"**
or **"code only" with the reason**. Along the way, add rows to `findings-<batch>.md` using the checklist below,
without fixing anything. The analysts don't shoot. They may re-check a doubtful claim in the code and mark it
"not sure" when the evidence is thin.

### The analyst's checklist, for every screenshot

1. **Duplicates**: the same number or action in two places. Do the value, the word and the redraw moment match?
2. **Contradicting states**: the progress strip says one thing, the button another, the status a third.
3. **Doc drift**: screen vs `docs/gui*.md`, `docs/logic-map.md`, spec, module docstring.
4. **Words**: a term missing from the glossary, jargon, two words for one concept, raw exceptions, technical keys.
5. **Dead ends**: an action with no next step, a link to nowhere, an empty state with no explanation, a hidden
   window with no way back.
6. **CLI or config ⇒ GUI**: a command or a config key the code reads has no control in the GUI, or a control
   changes nothing.
7. **Transition**: the diff ≠ "GUI writes" / "Expected after"; another screen didn't update (or only after a
   resync or F5); a half-written row after a failed subprocess; the toast or journal says something other than
   what happened.
8. **Visual**: off the design tokens (font, spacing, colour, contrast), clipped text at phone width, jumping
   numbers.

`findings.md` row, one per finding:

```
| # | Shot/ID | Type (duplicate/logic/doc/word/dead end/visual) | What is wrong | Where in code (file:line) | Severity (H/M/L) |
```

Type and file:line are required. A finding without a file gets rejected. H = broken, M = logic or wording that
misleads, L = polish.

## Step 4. Merge (main session, strongest model)

Glue the batch maps into one `map.md`:

1. **Screens / surfaces**: routes or windows with their states (IDs), each with a screenshot and the condition
   under which it shows up.
2. **Transitions**: `from state → action A<NN> (R/W/Q) → to state`, plus writes, starts (steps in order), changes
   on other screens, confirmed / code only.
3. **Graphs**: mermaid `stateDiagram` for the main entity's lifecycle with buttons on the edges, and one for the
   shell or process (idle → running → error / stopped). On desktop, add one for window visibility.
4. **Processes**: a mermaid `sequenceDiagram` for each Q action: click → argv → steps → what each step writes →
   what the screen shows, with real timings from logs when they exist.
5. **Cross-screen links and duplicates**, which no batch agent can see, being stuck in one batch. This is the
   main value of the merge.

Then clean up `findings.md`: remove repeats, add a summary grouped by severity at the top, and list refuted
findings separately, so they don't get carried forward. Re-check every H finding in the code before reporting it.

## Done when

- every row of §2 has a screenshot, or a mark "not in data / not reproducible / Q, not pressed" with a reason;
- every action in the actions map has a transition in `map.md`, marked confirmed or code only, with a reason;
- `map.md` has no unexplained state without a way in and a way out;
- live data, config and tokens match their backups (`sha256sum`, or a live snapshot at the start and end matches
  except for the owner's cron jobs); `git status` is as before except the report folder; temporary test files
  are removed from the source tree; stands S/F/E are stopped;
- `findings.md` has no repeats. **The owner decides what to fix**, separately.

## Keep plan.md resumable

A run like this spans sessions and context compactions. Keep a **status section at the top of `plan.md`**: a
table step → done / partial → which files hold it, what is left (with exact commands to bring the stand back),
what was refuted, and what the run itself taught about the tools ("ydotool doesn't move the pointer, use XTEST").
Update it at the end of every session. A status that lives only in the conversation is lost.

## Optional: a fresh-user pass

After the map, or alongside it, one agent plays a first-time user with only the browser. It may not read the code
or docs, works through 3–5 real tasks, and writes down every "what is this for?" and every silent no-op. It finds
what the code-first map can't: the screen is correct but unclear. The prompt template is in
`references/persona-pass.md`.

## After the pass

Fixes go as separate commits, each pointing at finding numbers. After fixing, **the map is stale on the changed
screens**. Note in the plan status which screens changed and reshoot them into `reshoot-<date>/`. A small
`fixcheck` script that reshoots just the fixed states is cheaper than a full rerun. Before a full rerun, try one
batch first.

## Model split, and why

| Step | Who |
|---|---|
| 0 plan, 1b snapshot script, 4 merge | main session |
| 1 stand, inventory, states; 2 shooting | cheap model (haiku), the shooting one batch at a time |
| 1a actions map, 1c scripts, 3 batch maps | mid-tier model (sonnet), one agent per batch |

If the project or the user already sets which models subagents use, follow that instead of this table.
The shooters don't judge and the analysts don't shoot, so the cheap model never writes conclusions and the
expensive one doesn't spend tokens on clicks. Driving a real browser through a browser extension costs over 10k
tokens a page. Use it only when the owner wants to watch a write click happen in their own browser.
