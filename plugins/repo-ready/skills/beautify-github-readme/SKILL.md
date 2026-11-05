---
name: beautify-github-readme
description: Make a GitHub README short, plain and good-looking, or create project-native SVG, composed PNG/WebP and opt-in GIF assets for it. Use when a user asks to beautify, redesign, shorten, simplify, de-slop or audit a README; to create only a hero, section headers, diagrams, badges or motion graphics; or says a README is too long, too "AI", or scares people off. Asks first whether the scope is the whole README or assets only.
---

# Beautify GitHub README

A README is read by a stranger in under a minute. Most of them leave after the first screen.

The job: make it shorter, plainer and easier to scan. Visuals help only when they show the real project.

Fork of [oil-oil/beautify-github-readme](https://github.com/oil-oil/beautify-github-readme), part of repo-ready. This fork adds a length budget, plain-language rules and a text lint. The word list follows [avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing).

## 1. Pick the mode

One mode per task:

- **README mode** - rewrite the whole README: order, text, visuals.
- **Asset-only mode** - create only the asked-for SVG or image. Do not touch the README.

Mode not clear? Ask once:

> Rewrite the whole README, or only make visual assets? If assets: hero, section headers, diagram, badge, or a set?

"Use this skill", a repo path or "beautify it" is not permission to rewrite the README.

Audit only? Report, do not edit, do not ask the mode question.

Motion is opt-in. If a hero or diagram could move and the user did not say, ask:

> Static SVG, or a GIF with the SVG kept as the source?

No answer means static SVG.

## 2. Read before writing

- Read the README, repo tree, package metadata, screenshots, examples, logo, real outputs.
- For a GitHub URL, read the live page and default branch.
- Write down: who reads it, what the project does in one sentence, the best proof, the first command that works.
- Do not invent users, benchmarks, compatibility, quotes or features.
- Start read-only. No commit, push, rename or publish without a direct ask.

## 3. Text rules

Read [references/plain-language.md](references/plain-language.md) before writing any README text, alt text or SVG copy. It is the hard gate for this fork.

The short version:

- One-sentence value at the top. Max 12 words.
- No paragraph longer than 5 lines or 60 words.
- No sentence longer than 25 words.
- No filler, no hype words, no contrast framing, no recap lines.
- No em dashes, no emoji in headings or prose, no caps for emphasis.

## 4. Length budget

| Part | Budget |
|---|---|
| Whole README | 150 lines outside code blocks |
| First screen (hero to first command) | 25 lines |
| One section | 20 lines of prose |
| One list | 7 items |

Over budget? Move the detail to `docs/` and link it, or fold it into `<details>`. Do not shrink the font or squeeze lines.

A README that grew is a failed redesign, even if it looks better.

## 5. README mode

Pick the depth:

- **Trim** - keep the structure, cut text to budget, fix wording. The default.
- **Refresh** - also replace weak visuals.
- **Redesign** - new order and new visual system. Only when asked or when the order is clearly broken.

Default order:

1. Name + one-sentence value (hero).
2. Proof: screenshot, output, short demo.
3. Install + first command.
4. How it works: 3-6 steps or one diagram.
5. Limits, then links to docs, license.

Read [references/content-architecture.md](references/content-architecture.md) for what to cut and where it goes.

## 6. Asset-only mode

- Confirm the asset type and whether it is one asset or a set.
- Put files under `assets/readme/` or a path the user names.
- Default to pure SVG. Composed PNG/WebP only if the user chose it. GIF only if the user opted in, see [references/motion-production.md](references/motion-production.md).
- Show rendered previews. Offer an embed snippet, insert it only after a yes.
- The README stays byte-for-byte the same.

## 7. Visuals

Read [references/visual-direction.md](references/visual-direction.md), [references/github-readme-canvas.md](references/github-readme-canvas.md) and [references/svg-production.md](references/svg-production.md) before drawing. Read [references/project-native-hero.md](references/project-native-hero.md) before a hero.

Fix the visual system first: palette (3-5 hex), system font stack, one radius, one stroke, one motif taken from the project.

Rules:

- One hero, at most. Section banners only if the README has more than 4 sections.
- Real screenshots and outputs beat drawn ones.
- Body text, commands, tables and links stay in Markdown, never inside images.
- SVG: `viewBox` 1200 wide, `width="100%"`, `<title>`, real `alt`. Essential text at least 20 units.
- No scripts, `foreignObject`, web fonts, remote images in SVG. GitHub does not play SVG animation.
- No glow, no neon gradients, no heavy shadows, no fake code, no generic AI-brain art.
- Test: hide the repo name. If the hero fits any other project, redo it.

Hero where pure SVG and a generated image both work? Ask once:

> Pure SVG (light, sharp, easy to edit, weak at people and textures) or hybrid (SVG layout + generated image, final PNG/WebP, heavier)?

Diagrams, badges and headers are always pure SVG. For hybrid, read [references/hybrid-svg-production.md](references/hybrid-svg-production.md).

## 8. Check

Run the audit. It checks images, SVG basics, length budget and text rules:

```bash
python3 engine/readme_audit.py /path/to/README.md
```

Exit code 1 means issues. Fix them or say why each one stays.

In repo-ready's preflight the same lint runs as `readme_length` (warning) and `readme_plain_language` (info).

Then look at it:

- Render at 900px and 360px wide. Check clipped text, contrast in light and dark theme, missing images.
- Read the first screen only. Can a stranger say what the project does?
- Compare line counts before and after. Report both numbers.

## 9. Hand off

Show the preview and the diff. Report: what changed, lines before and after, what moved to `docs/`, what you left alone.

Commit, push or open a PR only when the user asks.

## Examples

```text
Use $beautify-github-readme to cut this README to budget and fix the wording.
Use $beautify-github-readme to make one SVG hero, do not touch the README.
Use $beautify-github-readme to audit the README and list what to cut.
```
