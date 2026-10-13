# EN/RU (or any two languages): docs and UI

## Docs layout

- Primary language in the plain file (`README.md`), mirror next to it with a suffix (`README.ru.md`).
  Same for every prose file people read: CONTRIBUTING, SECURITY, CONTEXT, PLAN, docs/*.md, skill files
  (`SKILL.md` / `SKILL.ru.md`). Code, templates and workflow YAML stay single-language (English).
- The first line under the badges switches languages, current one bold:
  ```html
  <p align="center"><b>English</b> | <a href="README.ru.md">Русский</a></p>
  ```
  For non-README files a plain line works: `**English** | [Русский](SECURITY.ru.md)`.
- Links inside a mirror point to the mirror's siblings (`CONTRIBUTING.ru.md`), images are shared, alt text is translated.
- GitHub shows only `README.md` on the front page, so the primary language is the one with the larger audience
  (usually English); the description, topics and social preview use it too.

## Writing the mirror

- Translate meaning, not words. Each language reads as if written in it: Russian with natural word order, without
  English calques, and with terms the audience actually uses (keep `CLI`, `README`, `pull request` if that's how
  people say it).
- Keep numbers, commands, flags, file names and code blocks identical.
- Then run `humanizer` on both versions.
- Check sync: same headings in the same order, same links and images. A quick diff of headings:
  ```bash
  diff <(grep -E '^#{1,3} ' README.md | wc -l) <(grep -E '^#{1,3} ' README.ru.md | wc -l)
  ```

## UI strings

- All user-facing strings in one place per language (a dict or catalog), looked up at call time so a header
  switch changes the language without a restart.
- Strings that come from a vendored or shared library get their own table, synced by the app on switch;
  don't edit the vendored copy.
- A test checks that every language has the same keys, and one that switching actually changes a rendered string.
- Plurals: Russian needs three forms (1 строка, 2 строки, 5 строк); use a plural helper, not `n + " lines"`.
