# Launch: getting the first people to see it

Organic growth (GitHub search, Google, "used by", word of mouth) starts once a repo has some stars and activity.
The first ones come from people who saw a post. So the launch is a few concentrated posts in places where the
audience already is, each written for that place, with the author around to answer.

Everything here is advice and drafts. Posting, opening PRs to lists or messaging people: a yes per item.

## 1. Readiness gate (check before any post)

- **Install works on a clean machine** with the README's exact commands (CI install job green on all OSes).
  A broken first run in front of HN is the most expensive bug the project will ever have.
- **Package name is ours** on the registry the README tells people to use (preflight).
- **Demo in the first screen**: a 10–20 s GIF of a real run, right under the hero. Reproducible tools:
  `vhs` (a `.tape` script → GIF, re-record after changes) or `asciinema rec` + `agg` for terminal tools; for a GUI,
  a short screen capture converted with `ffmpeg` (keep it under ~5 MB).
- **"Why not just X?"** answered in the README: a short honest comparison with the obvious alternatives.
- **Social preview uploaded**, description and topics set (`references/seo.md`): every link shared below shows them.
- **Release with notes** (not just "Full Changelog"), so "what's new" has an answer.
- **Issues open, templates in place**, and the user has time that week to answer within a day.

## 2. Channels (pick 2–4 that fit the audience from Phase 0)

| Channel | Fits | Norms that matter |
|---|---|---|
| Show HN (news.ycombinator.com) | dev tools people can try now | title `Show HN: <name> – <what it does>`; no landing-page-only or signup walls; never ask for upvotes or coordinate votes (it gets flagged); the author posts a first comment with the backstory and stays to answer |
| Reddit (r/Python, r/commandline, r/selfhosted, r/opensource, niche subs) | by stack and by problem | read each sub's self-promotion rules and flair first; write as a person who built a thing, not an ad; one sub per day, adapt the text |
| Habr / vc.ru (RU), dev.to / Medium / personal blog (EN) | when there's a story: a real problem, a real run, numbers | the article is the product of the launch; link the repo once, near the end and in the intro |
| Awesome lists | lasting backlinks and steady trickle | find 1–3 actively merged lists for the category; follow their CONTRIBUTING (format, alphabetical order, sometimes minimum age/stars); one entry, one PR per list |
| Ecosystem places | users who already have the stack | e.g. `gh` extension list for GitHub CLI tools, framework showcases/discussions, skill or plugin marketplaces for agent tools |
| Product Hunt | end-user apps with a UI | low fit for CLI libraries; skip unless the audience is non-developers |
| Own network | first 10–20 people | the user shares it with people who would actually use it; asking friends to star without trying it is the same thing as buying stars, minus the money |

Timing: common advice is a weekday morning US time for HN and English Reddit, and Habr in the Moscow morning.
It's a nudge, not a rule; being available to answer matters more.

## 3. Drafts to prepare

For each chosen channel, write a draft in its language and tone:
- a title under the channel's length limit, stating what it does (no superlatives);
- 3–6 sentences: the problem, what the tool does differently, one real example or number, what's rough or missing;
- the link, install command, and a question that invites feedback.
Run `humanizer` on the drafts.

## 4. After the posts

- Answer every comment and issue within a day during launch week; fix the first reported install bug the same day
  and say so in the thread.
- Turn repeated questions into README FAQ entries.
- Measure (needs push access): `gh api repos/OWNER/REPO/traffic/views`, `.../traffic/popular/referrers`,
  `.../traffic/clones`, and the star count from `gh api repos/OWNER/REPO --jq .stargazers_count`. GitHub keeps
  traffic for 14 days only: save a snapshot after each launch, or schedule it.
- Since 2026-06-30 the stargazer list (`/stargazers`, API and page) is visible only to the repo's admins and
  collaborators, so third-party star-history charts can't rebuild a repo's history from it any more; for your own
  repo the data still comes with your token. Want a chart in the README or traffic kept past 14 days? A daily
  workflow can record it, e.g. MacRimi/repo-growth (young project: pin it to a SHA; it needs `contents: write` and
  commits every day, and clone traffic needs a token with Administration: read). For a one-off post-launch
  look, the snapshots above are enough.
- A second wave works when there's news: a big release, a write-up of a real result, a talk.
