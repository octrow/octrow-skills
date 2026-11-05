# repo-ready

[English](README.md) | **Русский**

Плагин для Claude Code и Claude Tag с четырьмя скиллами. Каждый доводит рабочий проект до состояния, которого требует цель.

Все четыре начинают с одного и того же preflight, который ничего не меняет. Он перечисляет пробелы как именованные проверки, у каждой есть уровень серьёзности и ссылка на исправление. Потом скилл исправляет только выбранные вами части.

| Скилл | Когда нужен | Что смотрит |
|---|---|---|
| `repo-publish` | репозиторий скоро станет публичным | история и секреты, установка, README, CI, SEO, релиз |
| `repo-deploy` | сервис должен работать в контейнерах | Dockerfile, health-эндпоинты, Compose, публикация образа, Helm, метрики |
| `repo-code-health` | Python-код менять труднее, чем должно быть | ruff, сложность, мёртвый код, линтер, тесты и типы в CI |
| `repo-secure` | приложение уже работает или вот-вот выйдет | авторизация, доверие к клиенту, rate limit, зависимости, логи, секреты, бэкапы |

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
npx skills add octrow/octrow-skills --skill repo-secure -g
```

На Windows сначала выполните `git config --global core.symlinks true`. Каждый скилл подключает общую папку `engine/` символической ссылкой, а Git for Windows по умолчанию превращает ссылки в обычные текстовые файлы.

Потом в проекте можно попросить:

- «подготовь репо к публикации»
- «добавь README на русском»
- «готов ли сервис к Kubernetes?»
- «заверни в Docker»
- «почисти код»
- «найди мёртвый код»
- «проверь безопасность приложения»

Просьбы на английском тоже работают.

## Что находит preflight

Каждый скилл начинает с `preflight.py --scenario publish`, `deploy`, `code-health` или `secure`. Он ничего не меняет.

Он читает репозиторий, его историю и настройки на GitHub. Инструменты code-health запускаются через `uvx` и ничего не пишут в проект.

Фрагмент запуска для публикации на тестовом репо:

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

Уровни:

- error блокирует любой внешний шаг (смену видимости, релиз, команду установки в README), пока его не исправят.
- warning нужно исправить или освободить до конца части.
- info это совет.

Проверка, которая не подходит репо, пропускается с условием, которого ей не хватает (нет Helm-чарта, нет проверок Helm). Или освобождается с причиной в `.repo-ready.yml`.

Для публикации он ещё проверяет:

- секреты во всей истории (gitleaks);
- приватные пути, названия работодателей и email авторов;
- происхождение кода;
- свободно ли имя пакета на PyPI/npm;
- битые ссылки в README;
- frontmatter в SKILL.md, который агенты не смогут загрузить;
- PR от Dependabot с красными проверками;
- описание репозитория, topics, social preview, защиту ветки, secret scanning и приватные сообщения об уязвимостях.

## Публикация: repo-publish

repo-publish читает репозиторий и его историю, прежде чем что-то станет публичным. Он выполняет работу по публикации в безопасном порядке и передаёт части другим скиллам, если они установлены.

После preflight и нескольких вопросов (аудитория, право на публикацию, видимость, языки) он проходит выбранные вами фазы в таком порядке:

1. Безопасность и история: секреты из истории сначала ротируются, приватные материалы уходят через экспорт со свежей историей, а репо получает проверки в pre-commit и CI, чтобы оставаться чистым.
2. Установка: одна команда на установку и одна на запуск, установщики проверяются в CI на Linux, macOS и Windows, а релизы собираются под все три (wheel и, по желанию, standalone-бинарники). Имя пакета проверяется до того, как README предложит кому-то `pipx install`.
3. README и документация: структура через `github-repo`, длина, простой язык и визуал через `beautify-github-readme`, остальной текст через `humanizer`, зеркала EN/RU синхронизированы.
4. GUI, если он есть: скриншоты до и после, затем обновлённые скриншоты в README.
5. Файлы сообщества и CI: SECURITY, CONTRIBUTING, формы issues и шаблоны workflow из списка ниже.
6. Находимость: описание, topics, social preview, первые 200 слов README.
7. Релиз: версия, changelog, тег и публикация в PyPI через trusted publishing.
8. Запуск, только по запросу: проверка готовности и черновики для каждого канала; публикуете их вы.

Всё, что видят другие (push, тег, релиз, видимость, настройки GitHub, посты), ждёт вашего «да».

Приватный или только локальный репозиторий проходит тот же путь. Всё, что живёт в файлах, делается сразу. Настройки, которые работают только у публичного репо (Scorecard, social preview, приватные сообщения об уязвимостях, push protection), собираются в список команд `gh` на день, когда вы его откроете.

Исправления лежат готовыми файлами в [`assets/`](../../plugins/repo-ready/engine/assets):

- конфиг pre-commit (gitleaks, zizmor, actionlint, проверка больших файлов и маркеров конфликтов);
- workflow безопасности (gitleaks по всей истории);
- OpenSSF Scorecard;
- установщики `install.sh`/`install.ps1` с проверкой в CI на трёх ОС;
- workflow релиза (wheel, бинарники под Linux/macOS/Windows, PyPI через trusted publishing, подпись сборок);
- Dependabot с cooldown.

Экшены закреплены по SHA коммитов, каждый файл проходит zizmor и actionlint. [repo-scout](https://github.com/octrow/repo-scout) использует их все, заполненными под настоящее Python-приложение.

## Готовность к деплою: repo-deploy

`/repo-ready:repo-deploy` готовит сервис к запуску в контейнерах или на одной VPS за Caddy или nginx с TLS.

Его preflight (`--scenario deploy`) проверяет:

- Dockerfile (multi-stage, числовой пользователь не root, базовые образы по digest, `.dockerignore`);
- Compose (порты базы и очереди только на 127.0.0.1);
- workflow образа (provenance, SBOM, аттестация, сканирование, без кэша слоёв);
- Helm-чарт (Pod Security `restricted`, пробы, `helm test`, smoke-тест в kind в CI).

Рецепты взяты из того, как [buy-smarter](https://github.com/octrow/buy-smarter) прошёл путь от CLI до чарта, и этот репо проходит все проверки.

Прежде чем считать часть готовой, скилл по-настоящему собирает образ и поднимает стек. Push образа и деплой ждут вашего «да».

## Здоровье кода: repo-code-health

`/repo-ready:repo-code-health` чистит Python-код и настраивает CI, чтобы он снова не зарос. Нужен [uv](https://docs.astral.sh/uv/).

Его preflight (`--scenario code-health`) запускает через `uvx`, ничего не ставя в проект и не пиша в него:

- ruff (линтер и форматирование);
- radon (цикломатическая сложность);
- complexipy (когнитивная сложность);
- vulture (мёртвый код).

Ещё он проверяет, что CI запускает линтер, тесты и проверку типов. Пороги берутся по умолчанию из самих инструментов, если в `pyproject.toml` не заданы свои.

Исправления идут в таком порядке: форматирование отдельным коммитом, линтер, мёртвый код, потом сложные функции, по одной на коммит и только там, где их покрывают тесты.

## Безопасность приложения: repo-secure

`/repo-ready:repo-secure` проверяет работающее или почти готовое приложение на ошибки, на которых чаще всего горят выпущенные приложения, особенно написанные с ИИ. Порядок такой же, как у реальных утечек:

1. авторизация (IDOR, закрытость по умолчанию, row-level security);
2. доверие к клиенту (цены, роли, id владельца);
3. rate limit на вход, регистрацию, письма и LLM-эндпоинты;
4. цепочка поставок (lock-файл, Dependabot, аудит в CI);
5. логи событий безопасности;
6. секреты, включая ключи в переменных `NEXT_PUBLIC_`/`VITE_`, которые сборщик отдаёт в браузер;
7. бэкапы с отрепетированным восстановлением.

Его preflight (`--scenario secure`) доказывает то, что видно по файлам. Остальное становится вопросами с уликами: каждый маршрут с id записи, найденный rate limiter, инструменты бэкапа.

Каждое исправление идёт с тестом, который до него падал (пользователь A запрашивает запись пользователя B и получает 404). Остальной OWASP передаётся в `security-review`.
