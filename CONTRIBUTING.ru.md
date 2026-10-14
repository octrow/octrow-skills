# Как помочь проекту

[English](CONTRIBUTING.md) | **Русский**

Сообщения о багах, неверных советах и недостающих проверках принимаются как issues. Чтобы изменить скилл:

1. Сделайте fork, ветку от `main`, по одному изменению на pull request.
2. Запустите проверки:
   ```bash
   pre-commit install && pre-commit run --all-files   # gitleaks, zizmor, actionlint
   claude plugin validate .
   ```
3. Изменение того, что делает скилл, требует eval-кейса в `evals/<name>.json`: запроса и проверок, которые
   показывают новое поведение. Утверждение об инструменте или платформе («X перестал работать») требует
   источника или реального запуска.
4. Файлы скиллов только на английском. У README, SECURITY, CONTRIBUTING и CODE_OF_CONDUCT есть RU-зеркала; меняйте оба в одном
   коммите.
5. Сообщения коммитов: `<type>: <description>`, где type — feat, fix, docs, chore, ci или refactor. Добавьте
   строку в CHANGELOG.md под следующей версией.
