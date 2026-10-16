#!/bin/sh
# Builds the throwaway repo that demo.tape runs the preflight on. Everything in it is fake.
set -e
D=/tmp/weather-cli
rm -rf "$D" && mkdir -p "$D/.github/workflows" "$D/weather_cli" && cd "$D"
git init -q -b master
c() { git add -A && git -c user.name=alice -c user.email=alice@acme-corp.com commit -qm "$1"; }
printf '[project]\nname = "weather-cli"\nversion = "0.1.0"\n[project.scripts]\nweather = "weather_cli.main:run"\n' > pyproject.toml
printf 'CACHE = "/home/%s/work/acme-internal/cache"\n\ndef run():\n    print("sunny")\n' alice > weather_cli/main.py
printf 'GITHUB_TOKEN=ghp_%s\n' "$(printf 'R8sXq2LmV7tZp4KwN9cYb3HdF6jUa1EoGx5i' )" > config.ini
printf '# weather-cli\n\nWeather in your terminal. Install: `pipx install weather-cli`.\n' > README.md
printf 'name: ci\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: softprops/action-gh-release@v2\n' > .github/workflows/ci.yml
printf 'OPENWEATHER_KEY=demo\n' > .env
# community files exist, so the demo shows the findings that matter
mkdir -p .github/ISSUE_TEMPLATE && touch LICENSE CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md CHANGELOG.md \
  .github/ISSUE_TEMPLATE/bug.yml .github/pull_request_template.md
printf 'version: 2\nupdates:\n  - package-ecosystem: pip\n    directory: /\n    schedule: {interval: weekly}\n' > .github/dependabot.yml
c init
git rm -q config.ini && c "remove config"
