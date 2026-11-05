# README content architecture

## First-screen test

Without scrolling, a new visitor should know:

1. What is this?
2. What does it do for me?
3. What do I type first?

The hero answers 1 and 2. Proof and the install command answer 3.

## Order

```text
Value -> Proof -> First use -> How it works -> Limits and links
```

Do not open with architecture, a contributor guide, a long table of contents or a badge wall.

## What stays in the README

- One-sentence value.
- One proof: screenshot, output or short demo.
- The shortest install and the first working command.
- How it works: 3-6 steps or one diagram.
- Limits that change whether someone tries it.
- Links: docs, changelog, license, contributing.

## What moves out

| Content | Where it goes |
|---|---|
| Full config reference, all CLI flags | `docs/configuration.md` |
| Architecture, design decisions | `docs/architecture.md` |
| Long FAQ, troubleshooting | `docs/faq.md` |
| Contributor setup, release steps | `CONTRIBUTING.md` |
| Version history | `CHANGELOG.md` |
| Second and third examples | `examples/` or `docs/` |
| Translations | `README.<lang>.md` with a link at the top |

Leave one line and a link where the content was.

Folding into `<details>` is fine for one or two blocks. A README made of ten `<details>` is still too long.

## Editing rules

- Cut first, rewrite second. Most READMEs get better by deleting.
- Replace jargon with a concrete result.
- Say each promise once.
- One example that works end to end beats five fragments.
- Keep limits visible when they change the reader's choice.
- Do not fake community size or adoption.

## Text vs visuals

Visuals: identity, sequence, comparison, proof.

Markdown: explanation, commands, API, links, compatibility.

Anything people copy, search, translate or update often stays out of images.
