---
name: tlf
description: Answer questions from the TikTok creators the user follows, through the tlf (tiktok-lazy-follower) CLI — search every transcript, read the weekly digests and their action lists, check the setup. Use when the user asks what creators said about a topic ("что говорили про MCP", "найди видео где объясняют X", "what did my TikTok creators say about Claude Code"), wants this week's digest or the collected action items, asks where a video or transcript is, or asks whether tlf is set up. Read-only by default; sync, transcribe, digest, run and capture only after the user confirms.
---

# tlf: ask your TikTok follows

tlf downloads videos from tracked TikTok creators, transcribes them and writes a weekly digest
per topic. This skill reads what tlf already has. Needs the `tlf` CLI on PATH (`tlf --version`).

## Before running

Run `tlf doctor --quick --json` once per session. From its JSON take:

- `ok`: false means a required check failed; name the failing `checks[]` row and its `detail`.
- `paths.digests`, `paths.transcripts`, `paths.db`: where the data lives. Never guess these.
- `tracked_creators`: 0 means nothing is tracked yet, so there is nothing to search.

`--quick` skips a live `claude` call; plain `tlf doctor` costs one.

## Intent → command

| The user wants | Run | Safe without asking |
|---|---|---|
| what creators said about X | `tlf search "<q>" --json` | yes |
| the full transcript of a hit | read `hits[].transcript_path` | yes |
| this week's / a week's digest | read `<paths.digests>/<topic>/YYYY-Www.md` (newest name = newest week) | yes |
| all action items of a topic | read `<paths.digests>/<topic>-actions.md`; stale → `tlf collect` | yes |
| a month or all-time report | read `<topic>/monthly-YYYY-MM.md`, `<topic>/all-time.md` | yes |
| which authors are useful | `tlf authors` (text table) | yes |
| fetch new videos / transcribe / build a digest | `tlf sync` / `tlf transcribe` / `tlf digest` / `tlf run` | **no** |
| import follows from TikTok | `tlf capture` (opens the user's browser) | **no** |
| move or disable authors | `tlf authors --set-topic T @x`, `tlf authors --prune` | **no** |

**Pause and confirm** before every "no" row: say what it will do and roughly how long. `run`
downloads, runs Whisper on the GPU and spends `claude` calls; a run can take an hour. Never
start two pipeline commands at once: tlf exits 75 when a stage is already running; report
that, don't retry in a loop.

## Search queries

The index is SQLite FTS5 over titles and transcript text; it catches up by itself on each search.

- No stemming: `нейросет*` finds нейросеть / нейросети / нейросетью; plain `нейросети` finds only that form.
- `a OR b`, `"exact phrase"`, `a NOT b`. A query that is not valid FTS5 (`c++`) is searched as one phrase.
- Transcripts keep the spoken language. For a Russian question about an English topic, search both:
  `агент* OR agent*`.
- `--limit N` (default 20). Exit 1 with `"hits": []` means no match: widen the query once
  (prefix, OR synonyms), then say nothing was found.

## Reading the result

`hits[]`: `tiktok_id`, `author`, `url`, `title`, `snippet` (matches in `**bold**`), `transcript_path`.

- Quote or summarize only what the snippet or transcript says, and link each claim to its `url`.
  Never fill gaps from the title or from what the video "probably" says.
- Several hits from one author on one point: cite one, mention the rest by count.
- Digests are already summaries: answer from them first, go to transcripts for detail or proof.

## Failure modes

| Symptom | Meaning | Do |
|---|---|---|
| `tlf: command not found` | CLI not installed | tell the user; don't install it unasked |
| exit 2 + "config.yaml is invalid" (stderr) | broken config | show the error, don't edit config.yaml unasked |
| exit 2 on search | empty query | pass the query as one quoted argument |
| `database is locked` | a pipeline stage is writing | wait a minute, retry once |
| doctor `ok: false` | a required tool is missing | name the row and its `detail`; fixes are the user's call |
