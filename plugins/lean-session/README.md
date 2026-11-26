# lean-session

**English** | [Русский](README.ru.md)

Keeps Claude Code chats small. A long chat re-reads its whole context on every request, so the cheapest request is one made in a short chat. The `handoff` skill moves the state of a chat into a file, so the next chat can start empty.

## Install

```bash
claude plugin install lean-session@octrow-skills
```

Or link the skill into one project without installing the plugin:

```bash
ln -s /path/to/octrow-skills/plugins/lean-session/skills/handoff .claude/skills/handoff
echo '.claude/skills/handoff' >> .git/info/exclude
```

## What is inside

| Part | What it does |
|---|---|
| `skills/handoff` | At a step boundary writes `.notes/handoff.md` and prints one line to paste after `/clear`. |
| `skills/handoff/scripts/handoff.sh` | Facts for the skill: branch, last commits, uncommitted and new files. `handoff.sh facts` adds the `.notes/` file list and the "Next step" of the last handoff. |
| `scripts/ci-wait.sh` | One blocking wait for a GitHub Actions run, by run id or commit sha. Prints one status line and the failed jobs. |

## The handoff file

`.notes/handoff.md`, at most 40 lines, five sections:

- **Next step**: one command or action.
- **State**: the block from the script.
- **Decisions**: pointers to files only. A decision that lives only in the chat is written to a file first.
- **Open**: what was promised and not done.
- **Rules**: what the user told this chat to keep.

The headings stay in English, the text is in your language. `.notes/` is kept out of git through `.git/info/exclude`, not `.gitignore`. The script works in a folder without git too.

## ci-wait.sh

Run it in the background instead of polling `gh run view` from the chat: the model is woken once, by the final line.

```bash
scripts/ci-wait.sh owner/repo --sha "$(git rev-parse HEAD)" ci.yml
scripts/ci-wait.sh owner/repo 1234567890
```

Exit code 0 means the run passed.

## Ask

- "hand off to a new chat"
- "the context is large, let's continue in a new chat"

## Needs

bash and git; `gh` for `ci-wait.sh`.
