# Compose: the whole stack on one machine

Worked through on octrow/buy-smarter (`docker-compose.yml`, `docker-compose.browser.yml`).

## Stack layout

1. Anchors: `x-env: &env` (service addresses inside the network, `${VAR:-default}`) and `x-app: &app` (build target,
   `image: ghcr.io/…:${TAG:-latest}`, `env_file: [{path: .env, required: false}]`, `environment: *env`).
2. Services: the database and the queue, a one-shot `migrate` (`command: alembic upgrade head`, `restart: "no"`),
   the app (`depends_on: migrate: condition: service_completed_successfully`), the worker.
3. Variants (a browser build) as an override file (`-f docker-compose.browser.yml`), not a duplicated service.
4. Observability (Prometheus, Grafana, Jaeger) behind a profile, with a Makefile target.

Done when: `docker compose up -d --build --wait` from scratch brings every service to healthy, migrations are
idempotent, and CI smoke-tests the published image with `TAG=ci docker compose up -d --no-build --wait`.

## Infrastructure ports

Bind the database, the queue and the metrics stack to the loopback interface: `"127.0.0.1:5434:5432"`. A bare
`"5432:5432"` publishes them on every interface, and on a VPS that means to the internet; Docker's own iptables
rules bypass ufw. Take host ports from variables when they commonly clash (`${GRAFANA_PORT:-3000}`).

## Pitfalls

- YAML merge (`<<:`) is shallow: a service's own `environment:` replaces the whole anchored map; merge it with
  `<<: *env` inside.
- A shell variable doesn't reach a container until it is listed under `environment` (a timeout test silently ran on
  the default).
- The image `HEALTHCHECK` targets the API port; override it for the worker.
- A bind-mounted single file pins the inode: a file an editor rewrites is invisible to the container until
  `docker compose up -d --force-recreate <svc>`.
- Local checks run under their own `COMPOSE_PROJECT_NAME`, so they don't touch the dev stack; end with `down -v`.
