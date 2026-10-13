# octrow-skills

[English](README.md) | **Русский**

Скиллы для агентов Claude Code и Claude Tag, оформленные как маркетплейс плагинов. Главный из них, repo-publish,
доводит рабочий проект до публичного репозитория на GitHub, который незнакомый человек найдёт, которому поверит и
который сможет установить. Сначала скилл проверяет историю на секреты и приватные данные, пока ничего не стало
публичным, а потом настраивает защиту CI, README, документацию, SEO на GitHub и релиз.

| Плагин | Что делает |
|---|---|
| [repo-publish](plugins/repo-publish/skills/repo-publish/SKILL.md) | Preflight без изменений, затем работа по публикации в безопасном порядке: безопасность и история, установка, README и документация EN/RU, скриншоты, файлы для сообщества и CI, находимость, релиз, план запуска. Части передаёт скиллам `github-repo`, `beautify-github-readme`, `humanizer`, `impeccable` и `security-review`, если они установлены. |

## Что находит preflight

Он ничего не меняет: читает репозиторий, его историю и настройки на GitHub. Фрагмент запуска на тестовом репо:

```text
## .gitignore
- not ignored: .env, .env.local, .venv/x, dist/x.whl, x.egg-info/PKG-INFO
- append the template: gh api gitignore/templates/Python --jq .source >> .gitignore

## CI workflows
- ci.yml: no top-level `permissions:` (default token may be read-write)
- third-party actions pinned by tag, not SHA: softprops/action-gh-release@v2 (zizmor flags these)
- actions/checkout@v4: targets node20, deprecated (forced onto Node 24 with a warning); bump the major
- dependabot.yml: no `cooldown` (wait ~7 days before proposing a release; assets/dependabot.yml)
```

Ещё он проверяет: секреты во всей истории (gitleaks), приватные пути, названия работодателей и email авторов,
происхождение кода, свободно ли имя пакета на PyPI/npm, битые ссылки в README, frontmatter в SKILL.md, который
агенты не смогут загрузить, PR от Dependabot с красными проверками, а также описание репозитория, topics,
social preview, защиту ветки, secret scanning и приватные сообщения об уязвимостях.

Исправления лежат готовыми файлами в [`assets/`](plugins/repo-publish/skills/repo-publish/assets): конфиг
pre-commit (gitleaks, zizmor, actionlint), workflow безопасности (gitleaks по всей истории), OpenSSF Scorecard,
релиз в PyPI через trusted publishing с подписью сборок и Dependabot с cooldown. Экшены закреплены по SHA
коммитов, каждый файл проходит zizmor и actionlint.

## Установка

Claude Code:

```bash
claude plugin marketplace add octrow/octrow-skills
claude plugin install repo-publish@octrow-skills
```

Из локального клона: `claude plugin marketplace add ./octrow-skills`.

Claude Tag: администратор подключает этот репозиторий в Organization settings → Plugins & skills → Sync from
GitHub и добавляет плагин в bundle.

Потом в проекте можно попросить: «подготовь репо к публикации», «чего не хватает, чтобы открыть исходники?» или
только одну часть: «добавь README на русском», «обнови скриншоты».

## Чем отличается от похожих скиллов

- [github-repo](https://github.com/jdevalk/skills) проверяет и пишет README, файлы для сообщества, шаблоны и
  метаданные. repo-publish вызывает его для этой части и добавляет то, что до и после: историю и секреты,
  происхождение кода, установку, защиту CI, релиз и запуск.
- [beautify-github-readme](https://github.com/oil-oil/beautify-github-readme) перерабатывает визуальную часть
  README (hero, картинки-доказательства, SVG). repo-publish использует его на этапе README.
- [github-morestar-skill](https://github.com/everest-an/github-morestar-skill) про рост: позиционирование и день
  запуска сразу в нескольких каналах. repo-publish тоже планирует запуск, но только когда репо безопасно
  публиковать и он ставится на чистой машине.

## Структура

```
.claude-plugin/marketplace.json     список плагинов
plugins/<name>/.claude-plugin/      манифест плагина
plugins/<name>/skills/<name>/       SKILL.md, references/, scripts/, assets/
evals/<name>.json                   тестовые запросы и проверки, по которым настраивался скилл
```

Проверка перед коммитом: `claude plugin validate .` Изменения по версиям: [CHANGELOG.md](CHANGELOG.md).

## Лицензия

MIT
