# Logic map

How the configured sources become the weekly digest.
The map describes the code as it is today, step by step.

Rule: if you change a step or a branch, update this file in the same commit.

## The flow at a glance

```
sources.yaml
  │
  ├─ 1  collect ........... Telegram, sites and Instagram → raw_posts
  ├─ 2  transcribe ........ video posts → text
  ├─ 3  extract ........... raw post → scored Event
  ├─ 4  dedup ............. same event under two titles → one row
  └─ 5  digest ............ events → digests/YYYY-Www.md
  │
weekly Markdown digest
```

## Entry points

| Entry | Model by default | Notes |
|---|---|---|
| `gce run` | sonnet | collect → transcribe → extract → digest |
| `gce <stage>` | sonnet | one stage |

`--source <name>` limits collect to the source with exactly that name.

Module: `cli`

## Steps

### 1. Collect

Decides: which new posts enter `raw_posts`.
Branches:
- every source in `sources.yaml` gets an adapter: Telegram, sites, Instagram;
- `--force --source X` resets X's offset and re-collects from the start.
Fails: one failing source stops the collect run.
Module: `adapters/base`, `adapters/telegram`, `adapters/sites`

### 2. Transcribe

Decides: the text of video posts.
faster-whisper runs on the GPU for reels and stories; the transcript is appended to the post text.
Module: `transcribe`

### 3. Extract

Decides: whether a post is an event, its fields and a relevance score 0–10.
Posts are batched; a bad batch reply falls back to one call per post.
A non-event is marked and skipped next time.
Module: `extract`

### 4. Dedup

Decides: which rows are the same event.
Titles on the same date with high similarity merge; the higher relevance survives.
Module: `ranking`

### 5. Digest

Decides: which events go into this week's file.
Events with relevance ≥ 6 that are not yet digested are rendered; `--force` re-renders all of them.
Read-only on the database.
Module: `render`

## Known gaps

- none
