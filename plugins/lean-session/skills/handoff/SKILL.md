---
name: handoff
description: Close the chat at a step boundary - write .notes/handoff.md and print the one line to paste after /clear. Use when the context is large or the user says "hand off", "continue in a new chat", «передай в новый чат».
---

# Handoff between chats

Goal: the next chat starts small and still knows everything it needs. The chat is not the store: the store is files.

## 1. Facts by script, not by reading

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/handoff.sh
```

(`scripts/` sits next to this file.) It prints the "State" block (branch, last 5 commits, uncommitted and new files) and creates `.notes/`, kept out of git via `.git/info/exclude`. Do not re-read the same things by hand.

At the start of a chat, `handoff.sh facts` also lists `.notes/` files with dates and prints "Next step" from the last handoff.

## 2. Write `.notes/handoff.md`

Overwrite the previous one. At most 40 lines, plain words, in the user's language. Keep these five `## ` headings in English and in this order (the script finds `Next step` by its heading):

1. `## Next step` - one command or action.
2. `## State` - the block from the script, as is.
3. `## Decisions` - pointers only: "choice X - `.notes/plan.md`". A decision that lives only in this chat is first written into a file, then pointed to.
4. `## Open` - what was promised in the chat and not done: checks, running processes, open errors.
5. `## Rules` - user rules given in this chat that the next chat must keep.

Nothing else: no history of the conversation, no summary of the code.

## 3. Finish

Print exactly one line for the user to paste after `/clear`, in the user's language:

```
Continue: read .notes/handoff.md and do the "Next step".
```

Do not start the next step in this chat.
