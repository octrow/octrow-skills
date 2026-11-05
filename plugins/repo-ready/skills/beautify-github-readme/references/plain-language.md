# Plain language for READMEs

Who reads: a developer who found the repo five seconds ago. They skim. A wall of text makes them close the tab.

Write so they get it on the first read and know what to type next.

The rules apply to English and Russian READMEs alike. `engine/readme_audit.py` checks most of them.

## Main rule

**No more than 5 lines in a row.**

Split blocks with a blank line. A section can have several blocks.

A line is one short sentence or one list item.

Hard limits:

- paragraph: 5 lines or 60 words;
- sentence: 25 words;
- hero value line: 12 words;
- list: 7 items, no nested lists.

## Block shape

```markdown
## Install

pip install foo

Needs Python 3.11+. On Windows, use WSL.
```

Point first. Then 1-3 short lines: what to do or why.

Details nobody needs on first read go into `<details>` or `docs/`. Same rules inside.

The action you want from the reader goes last, as its own block.

## Words

Short, direct, everyday words. Imperative for steps: "Run", "Set", "Open".

Say what the tool does. Do not tell the story of how it was built.

Comparisons as two lines:

```markdown
Does: X, Y, Z.
Does not: A, B.
```

No contrast framing: "not just a linter, it's a platform", "это не просто бот, а...". Say what it is.

**OK:** short names a reader can search or ask about: `foo run`, `FOO_TOKEN`, `v0.4`.

**Not OK in prose:** internal paths, function names, long slugs. Put them in a code block or `docs/`.

**No bare codes.** `ADR-12`, `§3`, `R2` mean nothing alone. Two or three words first, code in brackets: "the cache decision (ADR-12)".

## Filler: cut it

| Kind | English | Russian |
|---|---|---|
| Hype | powerful, robust, seamless, blazing fast, cutting-edge, next-generation, state-of-the-art, game-changer, revolutionary | мощный, удобный, эффективный, современный, инновационный |
| AI tells | leverage, delve, elevate, unlock, empower, streamline, supercharge, harness, effortless, ever-evolving | позволяет, обеспечивает, является |
| Boosters | very, truly, fully, completely, extremely, highly | очень, максимально, полностью, окончательно |
| Vague | various, several, some, a number of, and more | различные, некоторые, ряд, и многое другое |
| Officialese | in order to, utilize, facilitate, functionality | осуществить, реализация, предоставление, в рамках, на предмет |
| Stock lines | "Whether you're...", "Look no further", "In today's world", "It's worth noting", "Happy coding!" | "надеемся, будет полезно", "обращайтесь" |

## Bans

- Em and en dashes. Use `-`.
- Emoji in headings, prose and list items. Badges are fine.
- Caps for emphasis: "IMPORTANT", "NOTE:". Use a GitHub alert (`> [!NOTE]`) if it really matters.
- Intros before the point: "This project is a tool that...".
- A closing line that repeats what was said.
- Nested lists.
- Bold labels on every list item ("**Fast:** ..."). Bold is for one thing per block.
- Feature lists of 10+ items. Pick the 3-5 that decide whether someone tries the tool.
- Badge walls. Keep 3-5 badges that answer a question (version, CI, license).

## Before and after

**Hero line**

Before:

> FooBar is a powerful, blazing-fast, and fully extensible next-generation CLI tool that seamlessly empowers developers to effortlessly streamline their logging workflows.

After:

> Size-capped, rotated logs for Python apps in one call.

**Feature list**

Before:

> - 🚀 **Blazing Fast:** Leverages cutting-edge async I/O for unmatched performance.
> - 🔒 **Secure by Default:** Comprehensive secret redaction ensures your data is always protected.
> - 🧩 **Highly Extensible:** A robust plugin system lets you customize virtually everything.

After:

> - Writes up to 5k lines/s without blocking the event loop.
> - Hides tokens and passwords in log lines.
> - Plugins add new sinks: see `docs/plugins.md`.

**Why section**

Before:

> In today's fast-paced development world, logging is not just an afterthought, it's a critical part of observability. That's why we built FooBar: to give you a comprehensive solution that truly makes a difference.

After:

> Python apps fill disks with logs.
> FooBar caps the total size and rotates files for you.

## Self-check before handing off

1. Read only the first screen. Do you know what it does and what to type?
2. Any paragraph over 5 lines? Split or cut.
3. Any word from the filler table? Delete it and reread. Usually the sentence gets better.
4. Did the README get shorter? If not, cut again.
