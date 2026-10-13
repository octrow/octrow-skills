# octrow-skills

[English](README.md) | **Русский**

Скиллы для агентов Claude Code и Claude Tag, оформленные как маркетплейс плагинов.

| Плагин | Что делает |
|---|---|
| [repo-publish](plugins/repo-publish/skills/repo-publish/SKILL.md) | Готовит репозиторий к тому, чтобы чужие люди его нашли, поверили ему и смогли установить. Сначала preflight без изменений проверяет секреты и приватные пути в истории, происхождение кода, имя пакета, битые ссылки и скиллы, метаданные GitHub. Затем ведёт README, документацию EN/RU, SEO на GitHub, скриншоты, файлы для сообщества, CI, релиз и план запуска, передавая части скиллам `github-repo`, `beautify-github-readme`, `humanizer`, `impeccable` и `security-review`, если они установлены. |

## Установка

Claude Code:

```bash
claude plugin marketplace add octrow/octrow-skills
claude plugin install repo-publish@octrow-skills
```

Из локального клона: `claude plugin marketplace add ./octrow-skills`.

Claude Tag: администратор подключает этот репозиторий (приватную копию) в Organization settings → Plugins & skills →
Sync from GitHub и добавляет плагин в bundle.

## Структура

```
.claude-plugin/marketplace.json     список плагинов
plugins/<name>/.claude-plugin/      манифест плагина
plugins/<name>/skills/<name>/       SKILL.md, references/, scripts/
evals/<name>.json                   тестовые запросы и проверки, по которым настраивался скилл
```

Проверка перед коммитом: `claude plugin validate .`

## Лицензия

MIT
