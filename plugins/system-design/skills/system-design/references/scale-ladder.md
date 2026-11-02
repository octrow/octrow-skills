# The scaling ladder

Seven rungs. Each one exists because of what breaks on the rung below it. Climb only when that failure is
measured or the napkin says it will arrive, and say which failure moved you up.

| Rung | Shape | Climb when (what breaks) |
|---|---|---|
| 1. One VM | nginx + app + Postgres + cron on one box, kept alive by systemd/pm2 | one bad query eats RAM, the OOM killer takes the app down with the DB |
| 2. DB on its own host | DB on a private network, backups + point-in-time restore, never on the public internet | the system runs, but "it's slow" and nobody can say why |
| 3. Observability | structured logs, metrics + alerts on what hurts the business, a few product events | one app box pegs its CPU; every deploy is a planned outage |
| 4. LB + stateless app pool | load balancer with health checks, 2–3 stateless app instances, rolling deploys | every box hits the same hot rows; the DB connection pool is full; static files come from origin |
| 5. Cache + CDN | Redis/Valkey for hot reads, sessions, rate limits; CDN for static assets; TTLs before pub/sub busts | a slow third-party API parks every web worker; the site is "down" with nothing crashed |
| 6. Queue + workers | email, PDFs, uploads, webhooks, third-party calls go to a durable queue; workers retry with a dead-letter queue | OLTP writes, dashboards, BI exports and ad-hoc SQL all fight on one primary |
| 7. Replicas, then shards | replicas take read-heavy traffic; shard by tenant/user id when writes are hot; pgbouncer | (new problems, not a ceiling) replica lag gives stale reads; anything across two shards needs coordination |

## Rules

- **Rung 3 comes early and costs little.** Two boxes you can't see into are worse than one you can.
- **Rung 4 needs a stateless app.** Sessions, uploads and in-process caches move out first (to Redis, object
  storage); otherwise the load balancer breaks logins.
- **Rung 6 is about latency, not scale.** Anything the user is not waiting for leaves the request path, even at
  ten users, if an upstream can take seconds.
- **Before rung 7, exhaust the cheap moves:** indexes, the cache hit rate, a bigger primary, moving analytics to
  a replica or a separate store. Sharding scopes every transaction to one shard and makes cross-shard joins hard,
  so most teams do it as late as they can.
- **Read-your-own-writes on replicas:** after a user writes, route their next reads to the primary for a few
  seconds, or the user sees their change vanish.

## Python/FastAPI translation

| Rung | Usual pieces |
|---|---|
| 1–2 | uvicorn/gunicorn under systemd, nginx, Postgres (pgBackRest or a managed DB) |
| 3 | JSON logs (see the `python-logging` skill), Prometheus + Grafana or Sentry, OpenTelemetry SDK |
| 4 | nginx/Caddy/Traefik or a cloud LB; no module-level state in the app |
| 5 | Redis/Valkey via `redis.asyncio`; Cloudflare in front of static files |
| 6 | arq, Celery, Dramatiq or RQ on Redis; or SQS/Pub/Sub; Temporal for multi-step workflows |
| 7 | Postgres streaming replicas, pgbouncer, Citus for sharding |
