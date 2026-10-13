# Discoverability: GitHub search, Google, AI assistants

What ranks a repo in GitHub search: name, description, topics, README text, then stars/forks/activity.
Google indexes the repo page and pulls snippets from the description and the README's opening. AI assistants
answer from the same indexed pages. So the same few fields do almost all the work.

## Name

Short, readable, contains the main keyword or is easy to search for. Renaming later is fine: GitHub redirects.
Don't rename without asking; it changes clone URLs in docs and installers.

## Description (About)

- 5–15 words, the main keyword first, what it does and for whom; no "awesome", no emoji wall.
- The first ~100 characters show in search results and cards; put the point there.
- Same sentence (or close) as the README's one-line pitch and the package metadata description, so all three agree.
- `gh repo edit OWNER/REPO --description "..."`

## Topics

- Up to 20; 8–15 is typical. Mix: what it is (`cli`, `developer-tools`), domain (`github-search`,
  `semantic-search`), stack (`python`, `nicegui`), and the words people actually type.
- Use existing popular topics (check `https://github.com/topics/<name>`) over invented ones.
- `gh repo edit OWNER/REPO --add-topic a,b,c`

## Homepage and social preview

- Homepage: docs site, Pages site or the latest release page. Empty is a small miss.
- Social preview: 1280×640 PNG (under 1 MB), name + one-line promise + one visual from the project (reuse the
  README hero's look). Shows on every shared link (Slack, X, HN, Telegram). **No API to upload it**: produce the
  file, then the user uploads it in Settings → General → Social preview. Preflight reports
  `usesCustomOpenGraphImage` and points at a ready PNG if the repo has one.
  Making one: a small HTML page at 1280×640 (reuse the hero's colors and fonts), shot with
  `shots.py spec.json out file:///abs/dir` and a spec entry `{"name": "social-preview", "path": "/social.html",
  "width": 1280, "height": 640, "scale": 1}`. Keep the HTML next to the PNG so it can be regenerated.

## README opening (the first screen)

- The first 200 words decide both the search snippet and whether a visitor stays. In them: what it is, who it's
  for, the key terms people search for (said naturally, once), and a proof (real screenshot or real numbers).
- Headings as phrases people search ("Install", "How it works", "Compare with X") rather than clever titles.
- Every image has alt text that says what the image shows; the alt text is indexed and read aloud.
- A short FAQ helps humans and AI answers; it gets no Google rich results (FAQ rich results were retired in 2026), so
  keep it only where the questions are real.
- "Alternatives / how this differs from X" sections catch "X alternative" searches. Be fair to X.

## Activity signals

Regular releases with notes, a green CI badge, answered issues, a recent commit. A release is also a page that gets
indexed and shows up in "Releases" on the repo's front page.

## Optional extras (say what they cost and what they give)

- **GitHub Pages landing page** with a proper `<title>`, meta description and Open Graph tags: a second indexed
  page. Worth it once there's a docs site; not before.
- **llms.txt**: a Markdown index for AI tools. Cheap, but Google ignores it and there's no evidence it drives
  citations; offer it as optional, not as an SEO fix.
- **Awesome lists**: a PR to 1–3 relevant lists, following each list's contributing rules. The user approves each PR.
- **Launch posts** (Show HN, Reddit, dev.to): advice only; the user posts.

## Off limits

Bought stars, star exchanges, fake accounts, keyword stuffing, mass-tagging unrelated topics. They break GitHub's
terms and fake-star detectors flag them. Repos that sell "GitHub ranking" are adverts, not sources.
