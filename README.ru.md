<p align="center">
  <img src=".github/readme-hero.svg" width="100%" alt="repo-publish, скилл для Claude Code: сделать репозиторий публичным, сначала проверив историю. Фазы: секреты, установка, README, CI, SEO, релиз. Рядом настоящие строки из отчёта preflight.">
</p>

<p align="center"><a href="README.md">English</a> | <b>Русский</b></p>

<p align="center"><a href="https://scorecard.dev/viewer/?uri=github.com/octrow/octrow-skills"><img src="https://api.scorecard.dev/projects/github.com/octrow/octrow-skills/badge" alt="OpenSSF Scorecard"></a></p>

repo-ready это плагин для Claude Code и Claude Tag с тремя скиллами. Каждый доводит рабочий проект до состояния,
которого требует цель, и начинает с одного и того же preflight, который ничего не меняет. Он перечисляет пробелы как
именованные проверки, у каждой есть уровень серьёзности и ссылка на исправление, а потом скилл исправляет только
выбранные вами части.

| Скилл | Когда нужен | Что смотрит |
|---|---|---|
| `repo-publish` | репозиторий скоро станет публичным | история и секреты, установка, README, CI, SEO, релиз |
| `repo-deploy` | сервис должен работать в контейнерах | Dockerfile, health-эндпоинты, Compose, публикация образа, Helm, метрики |
| `repo-code-health` | Python-код менять труднее, чем должно быть | ruff, сложность, мёртвый код, линтер, тесты и типы в CI |

repo-publish читает репозиторий и его историю, прежде чем что-то станет публичным, выполняет работу по публикации в
безопасном порядке и передаёт части другим скиллам, если они установлены. Ниже его preflight на тестовом репо:

<img src=".github/demo.gif" width="100%" alt="Прогон preflight на тестовом репо: GitHub-токен в истории, отслеживаемый .env, домашний путь и имя работодателя в коде, рабочая почта в коммитах, незакреплённые actions на Node 20, нет установщиков.">

## Установка

Claude Code:

```bash
claude plugin marketplace add octrow/octrow-skills
claude plugin install repo-ready@octrow-skills
```

Другие агенты (Codex, Cursor, Gemini CLI и другие) через [skills](https://github.com/vercel-labs/skills):

```bash
npx skills add octrow/octrow-skills --skill repo-publish -g
npx skills add octrow/octrow-skills --skill repo-deploy -g
npx skills add octrow/octrow-skills --skill repo-code-health -g
```

На Windows сначала выполните `git config --global core.symlinks true`: каждый скилл подключает общую папку `engine/`
символической ссылкой, а Git for Windows по умолчанию превращает ссылки в обычные текстовые файлы.

Из локального клона: `claude plugin marketplace add ./octrow-skills`.

В том же маркетплейсе есть [repo-scout](https://github.com/octrow/repo-scout), скилл, который ищет на GitHub
готовые репозитории, прежде чем писать своё: `claude plugin install repo-scout@octrow-skills`. Он работает через
CLI repo-scout, поэтому сначала поставьте его (одна команда, см. его README).

Там же есть python-logging, скилл, который настраивает, чинит или улучшает логирование в Python-проекте: общий
бюджет на все логи с ротацией по размеру, широкие события (одна JSON-строка на запрос, сообщение или задачу),
маскировку секретов, записи, которые остаются одной строкой в journald, и тесты, доказывающие потолок. Установка:
`claude plugin install python-logging@octrow-skills` или `npx skills add octrow/octrow-skills --skill python-logging -g`.
Потом попросите: «логи забили диск, ограничь их 1 ГБ» или «по логам непонятно, что случилось с задачей 42».

Claude Tag: администратор подключает этот репозиторий в Organization settings → Plugins & skills → Sync from GitHub
и добавляет плагин в bundle.

Потом в проекте можно попросить: «подготовь репо к публикации», «добавь README на русском», «готов ли сервис к
Kubernetes?», «заверни в Docker», «почисти код», «найди мёртвый код». Просьбы на английском тоже работают.

## Что находит preflight

Каждый скилл начинает с `preflight.py --scenario publish`, `deploy` или `code-health`. Он ничего не меняет: читает
репозиторий, его историю и настройки на GitHub, а инструменты code-health запускает через `uvx` и ничего не пишет в
проект. Фрагмент запуска для публикации на тестовом репо:

```text
## Error (blocks outward-facing steps)
- secrets_in_history: once public, history is copied and indexed; a leaked key is only safe after rotation
  - gitleaks: github-pat in config.ini at 94d0ab7f (rotate the key, then ask about a rewrite)
  fix: engine/procedures/security.md#1-secrets-in-history-not-just-head

## Warning (fix or exempt before done)
- actions_node_runtime: runners force Node 20 actions onto Node 24 with a warning; bump the major
  - actions/checkout@v4: targets node20, deprecated; bump the major
  fix: engine/procedures/security.md#8-workflow-hardening
- dependabot_cooldown: a release-day dependency update is how a hijacked package reaches you
  - dependabot.yml: no `cooldown` (wait ~7 days before proposing a release)
  fix: engine/assets/dependabot.yml

## Skipped (condition not met)
- scorecard_workflow: needs public
```

error блокирует любой внешний шаг (смену видимости, релиз, команду установки в README), пока его не исправят.
warning нужно исправить или освободить до конца части, info это совет. Проверка, которая не подходит репо,
пропускается с условием, которого ей не хватает (нет Helm-чарта, нет проверок Helm), или освобождается с причиной в
`.repo-ready.yml`.

Для публикации он ещё проверяет: секреты во всей истории (gitleaks), приватные пути, названия работодателей и email авторов,
происхождение кода, свободно ли имя пакета на PyPI/npm, битые ссылки в README, frontmatter в SKILL.md, который
агенты не смогут загрузить, PR от Dependabot с красными проверками, а также описание репозитория, topics, social
preview, защиту ветки, secret scanning и приватные сообщения об уязвимостях.

## Публикация: repo-publish

После preflight и нескольких вопросов (аудитория, право на публикацию, видимость, языки) repo-publish проходит выбранные
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

Приватный или только локальный репозиторий проходит тот же путь: всё, что живёт в файлах, делается сразу, а
настройки, которые работают только у публичного репо (Scorecard, social preview, приватные сообщения об уязвимостях,
push protection), собираются в список команд `gh` на день, когда вы его откроете.

Исправления лежат готовыми файлами в [`assets/`](plugins/repo-ready/engine/assets): конфиг
pre-commit (gitleaks, zizmor, actionlint, проверка больших файлов и маркеров конфликтов), workflow безопасности (gitleaks по всей истории), OpenSSF Scorecard,
установщики `install.sh`/`install.ps1` с проверкой в CI на трёх ОС, workflow релиза (wheel, бинарники под
Linux/macOS/Windows, PyPI через trusted publishing, подпись сборок) и Dependabot с cooldown. Экшены закреплены по SHA коммитов,
каждый файл проходит zizmor и actionlint. [repo-scout](https://github.com/octrow/repo-scout) использует их все,
заполненными под настоящее Python-приложение.

## Готовность к деплою: repo-deploy

`/repo-ready:repo-deploy` готовит сервис к запуску в контейнерах. Его preflight (`--scenario deploy`) проверяет Dockerfile (multi-stage, числовой пользователь не root, базовые образы
по digest, `.dockerignore`), Compose (порты базы и очереди только на 127.0.0.1), workflow образа (provenance, SBOM,
аттестация, сканирование, без кэша слоёв) и Helm-чарт (Pod Security `restricted`, пробы, `helm test`, smoke-тест в
kind в CI). Рецепты взяты из того, как [buy-smarter](https://github.com/octrow/buy-smarter) прошёл путь от CLI до
чарта, и этот репо проходит все проверки. Прежде чем считать часть готовой, скилл по-настоящему собирает образ и
поднимает стек; push образа и деплой ждут вашего «да».

## Здоровье кода: repo-code-health

`/repo-ready:repo-code-health` чистит Python-код и настраивает CI, чтобы он снова не зарос. Его preflight
(`--scenario code-health`) запускает через `uvx` ruff (линтер и форматирование), radon (цикломатическая сложность),
complexipy (когнитивная сложность) и vulture (мёртвый код). В проект он ничего не ставит и ничего в нём не пишет.
Ещё он проверяет, что CI запускает линтер, тесты и проверку типов. Пороги берутся по умолчанию из самих
инструментов, если в `pyproject.toml` не заданы свои. Исправления идут в таком порядке: форматирование отдельным
коммитом, линтер, мёртвый код, потом сложные функции, по одной на коммит и только там, где их покрывают тесты.
Нужен [uv](https://docs.astral.sh/uv/).

## Чем repo-publish отличается от похожих скиллов

- [github-repo](https://github.com/jdevalk/skills) проверяет и пишет README, файлы для сообщества, шаблоны и
  метаданные. repo-publish вызывает его для этой части и добавляет то, что до и после: историю и секреты,
  происхождение кода, установку, защиту CI, релиз и запуск.
- [beautify-github-readme](https://github.com/oil-oil/beautify-github-readme) перерабатывает визуальную часть
  README (hero, картинки-доказательства, SVG). repo-publish использует его на этапе README.
- [github-morestar-skill](https://github.com/everest-an/github-morestar-skill) про рост: позиционирование и день
  запуска сразу в нескольких каналах. repo-publish тоже планирует запуск, но только когда репо безопасно
  публиковать и он ставится на чистой машине.

## Структура репозитория

Этот репозиторий является маркетплейсом плагинов. repo-ready с тремя скиллами и python-logging лежат здесь, а repo-scout живёт в
своём репозитории, и на него ссылается запись маркетплейса.

```
.claude-plugin/marketplace.json     список плагинов
plugins/<name>/.claude-plugin/      манифест плагина
plugins/<name>/skills/<skill>/      SKILL.md одного сценария и ссылка `engine/`
plugins/repo-ready/engine/          preflight, каталог проверок, procedures/ и assets/, общие для сценариев
tests/                              тесты preflight (stdlib unittest)
evals/<skill>.json                  тестовые запросы и проверки, по которым настраивался скилл
```

Проверка перед коммитом: `claude plugin validate .` и `python3 -m unittest discover tests`. Изменения по версиям: [CHANGELOG.md](CHANGELOG.md). Как помочь
проекту: [CONTRIBUTING.ru.md](CONTRIBUTING.ru.md). Сообщения об уязвимостях: [SECURITY.ru.md](SECURITY.ru.md).

## Лицензия

MIT
