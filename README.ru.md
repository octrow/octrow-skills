<p align="center">
  <img src=".github/readme-hero.svg" width="100%" alt="repo-publish, скилл для Claude Code: сделать репозиторий публичным, сначала проверив историю. Фазы: секреты, установка, README, CI, SEO, релиз. Рядом настоящие строки из отчёта preflight.">
</p>

<p align="center"><a href="README.md">English</a> | <b>Русский</b></p>

<p align="center"><a href="https://scorecard.dev/viewer/?uri=github.com/octrow/octrow-skills"><img src="https://api.scorecard.dev/projects/github.com/octrow/octrow-skills/badge" alt="OpenSSF Scorecard"></a></p>

repo-publish — скилл для Claude Code и Claude Tag. Он доводит рабочий проект до публичного репозитория на GitHub,
который незнакомый человек найдёт, которому поверит и который сможет установить. Прежде чем что-то станет
публичным, скилл читает репозиторий и его историю, потом выполняет работу по публикации в безопасном порядке и
передаёт части другим скиллам, если они установлены.

## Установка

Claude Code:

```bash
claude plugin marketplace add octrow/octrow-skills
claude plugin install repo-publish@octrow-skills
```

Другие агенты (Codex, Cursor, Gemini CLI и другие) через [skills](https://github.com/vercel-labs/skills):

```bash
npx skills add octrow/octrow-skills --skill repo-publish -g
```

Из локального клона: `claude plugin marketplace add ./octrow-skills`.

В том же маркетплейсе есть [repo-scout](https://github.com/octrow/repo-scout), скилл, который ищет на GitHub
готовые репозитории, прежде чем писать своё: `claude plugin install repo-scout@octrow-skills`. Он работает через
CLI repo-scout, поэтому сначала поставьте его (одна команда, см. его README).

Claude Tag: администратор подключает этот репозиторий в Organization settings → Plugins & skills → Sync from GitHub
и добавляет плагин в bundle.

Потом в проекте можно попросить: «подготовь репо к публикации», «чего не хватает, чтобы открыть исходники?» или
только одну часть: «добавь README на русском», «обнови скриншоты».

## Что находит preflight

Первый шаг ничего не меняет: он читает репозиторий, его историю и настройки на GitHub. Фрагмент запуска на
тестовом репо:

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
агенты не смогут загрузить, PR от Dependabot с красными проверками, а также описание репозитория, topics, social
preview, защиту ветки, secret scanning и приватные сообщения об уязвимостях.

## Как работает

После preflight и нескольких вопросов (аудитория, право на публикацию, видимость, языки) скилл проходит выбранные
вами фазы в таком порядке:

1. Безопасность и история: секреты из истории сначала ротируются, приватные материалы уходят через экспорт со
   свежей историей, а репо получает проверки в pre-commit и CI, чтобы оставаться чистым.
2. Установка: одна команда на установку и одна на запуск, установщики проверяются в CI на Linux, macOS и Windows,
   а релизы собираются под все три (wheel и, по желанию, standalone-бинарники). Имя пакета проверяется до того, как README предложит кому-то `pipx install`.
3. README и документация: структура через `github-repo`, визуал через `beautify-github-readme`, простой язык через
   `humanizer`, зеркала EN/RU синхронизированы.
4. GUI, если он есть: скриншоты до и после, затем обновлённые скриншоты в README.
5. Файлы сообщества и CI: SECURITY, CONTRIBUTING, формы issues и шаблоны workflow из списка ниже.
6. Находимость: описание, topics, social preview, первые 200 слов README.
7. Релиз: версия, changelog, тег и публикация в PyPI через trusted publishing.
8. Запуск, только по запросу: проверка готовности и черновики для каждого канала; публикуете их вы.

Всё, что видят другие (push, тег, релиз, видимость, настройки GitHub, посты), ждёт вашего «да».

Исправления лежат готовыми файлами в [`assets/`](plugins/repo-publish/skills/repo-publish/assets): конфиг
pre-commit (gitleaks, zizmor, actionlint), workflow безопасности (gitleaks по всей истории), OpenSSF Scorecard,
установщики `install.sh`/`install.ps1` с проверкой в CI на трёх ОС, workflow релиза (wheel, бинарники под
Linux/macOS/Windows, PyPI через trusted publishing, подпись сборок) и Dependabot с cooldown. Экшены закреплены по SHA коммитов,
каждый файл проходит zizmor и actionlint. [repo-scout](https://github.com/octrow/repo-scout) использует их все,
заполненными под настоящее Python-приложение.

## Чем отличается от похожих скиллов

- [github-repo](https://github.com/jdevalk/skills) проверяет и пишет README, файлы для сообщества, шаблоны и
  метаданные. repo-publish вызывает его для этой части и добавляет то, что до и после: историю и секреты,
  происхождение кода, установку, защиту CI, релиз и запуск.
- [beautify-github-readme](https://github.com/oil-oil/beautify-github-readme) перерабатывает визуальную часть
  README (hero, картинки-доказательства, SVG). repo-publish использует его на этапе README.
- [github-morestar-skill](https://github.com/everest-an/github-morestar-skill) про рост: позиционирование и день
  запуска сразу в нескольких каналах. repo-publish тоже планирует запуск, но только когда репо безопасно
  публиковать и он ставится на чистой машине.

## Структура репозитория

Этот репозиторий — маркетплейс плагинов. repo-publish лежит здесь, repo-scout — в своём репозитории, на него
ссылается запись маркетплейса.

```
.claude-plugin/marketplace.json     список плагинов
plugins/<name>/.claude-plugin/      манифест плагина
plugins/<name>/skills/<name>/       SKILL.md, references/, scripts/, assets/
evals/<name>.json                   тестовые запросы и проверки, по которым настраивался скилл
```

Проверка перед коммитом: `claude plugin validate .` Изменения по версиям: [CHANGELOG.md](CHANGELOG.md). Как помочь
проекту: [CONTRIBUTING.ru.md](CONTRIBUTING.ru.md). Сообщения об уязвимостях: [SECURITY.ru.md](SECURITY.ru.md).

## Лицензия

MIT
