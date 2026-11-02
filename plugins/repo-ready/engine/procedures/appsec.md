# Application security: the mistakes that burn shipped apps

Code an agent writes works long before it is safe. The same seven gaps show up again and again, and each can be
checked in an afternoon. Go in this order: the first two are how data leaks, the rest decide how bad a bad day gets.

## 1. Authorization

Logged in is not allowed. The most common real breach is IDOR: `GET /orders/42` returns order 42 to anyone with
a session, so a script walks every id.

Fix:
- Every query that loads one record filters by owner (or tenant) in the query itself:
  `select(Order).where(Order.id == order_id, Order.user_id == user.id)`, and a miss returns 404, not 403 (a 403
  confirms the id exists). Prefer one dependency or repository method that does this over a check in each handler.
- Private by default: put auth on the app or router (FastAPI `APIRouter(dependencies=[Depends(current_user)])`,
  Express middleware before the routes), then list the public routes on purpose. Admin routes need a role check,
  not a hidden URL.
- Supabase / Firebase: the client talks to the database directly, so row-level security (or security rules) on
  every table is the authorization. A table without RLS is public.
- Ids from the request body count too (`{"user_id": 7}` in a PATCH). Take the owner from the session, never from
  the payload.

Done when: a test logs in as user A, requests user B's record on every id route, and gets 404.

## 2. Never trust the client

Anything that runs in the browser or the app can be edited: hidden fields, disabled buttons, prices in the cart,
`role: "admin"` in a signup form, the JS validation itself.

Fix:
- Validate every input on the server with a schema (Pydantic models with `extra="forbid"`, zod): types, lengths,
  ranges, enums. Reject, don't repair.
- Compute or look up on the server: prices and totals (from the product id), discounts, roles, owner ids,
  feature flags, plan limits. A field the client must not set is not in the input schema at all.
- Mass assignment: never `Model(**request.json())` or `user.update(body)`; map the allowed fields explicitly.
- Payments: trust the provider's webhook (signature checked) for "paid", not a redirect to `/success`.
- Uploads: check size and type by content, store under a generated name outside the web root.

Done when: the input schemas forbid unknown fields and a test that sends a forged price/role/owner id sees it
ignored or rejected.

## 3. Rate limiting

Without limits, login is a password-guessing service, a signup form is a spam relay, and an LLM endpoint is a
bill someone else runs up.

Limit per IP and per account (an attacker rotates one or the other), return 429 with `Retry-After`:

| Endpoint | Starting limit |
|---|---|
| login, OTP / magic link check | 5–10 per minute per account and per IP, then backoff or lockout with notice |
| signup, password reset, anything that sends email or SMS | 3–5 per hour per IP and per address |
| LLM / paid API calls | a per-user daily budget, plus a global cap that alerts |
| everything else | a generous global per-IP limit against scraping and runaway clients |

Where: `slowapi` or `fastapi-limiter` (Redis-backed once there is more than one app process), `express-rate-limit`
/ `@upstash/ratelimit`, or nginx `limit_req` / the CDN's WAF for the global layer. In-process counters reset on
restart and split across workers: fine for one process, wrong behind a load balancer.

Done when: a test (or a loop with curl) gets 429 on the login route after the limit.

## 4. Supply chain

Your app runs every dependency's code, and its install scripts. Attacks come as hijacked maintainer accounts,
typosquats (`reqeusts`), and packages an LLM hallucinated that someone then registered.

Fix:
- Commit the lockfile (`uv.lock`, `package-lock.json`, `pnpm-lock.yaml`) and install from it in CI and the image
  (`uv sync --locked`, `npm ci`).
- Dependabot or Renovate with a cooldown (`engine/assets/dependabot.yml`: waits days before proposing a fresh
  release, so a hijacked version is usually yanked first). Turn on Dependabot security updates.
- An audit step in CI that fails on known vulnerabilities: `uvx pip-audit` (or `uv export | pip-audit -r -`),
  `npm audit --audit-level=high`, or `osv-scanner`.
- Before adding a dependency: does it exist on PyPI/npm with real history, is the name exactly right, does it
  have a `postinstall` script? Check names an agent suggested before installing them.
- GitHub Actions pinned by commit SHA (the `actions_pinned_sha` Check).

## 5. Security logging and monitoring

When something goes wrong you need to know it happened, who did it and what they touched, without the logs
becoming a leak of their own.

Fix:
- Log security events as structured lines with user id, IP, request id and outcome: failed and successful
  logins, password and email changes, permission denials (403/404 on owned records), rate-limit hits, admin
  actions, exports. The `python-logging` skill sets up the wide-event format and redaction.
- Never log passwords, tokens, session cookies, full card numbers, or request bodies of auth endpoints. Redact
  by key and by value.
- Errors go to a tracker (Sentry or similar) and a few alerts page someone: error-rate spike, 5xx, a burst of
  failed logins, a spend cap reached. An alert nobody reads is noise; keep few.
- Keep logs long enough to investigate (30–90 days) and off the app server.

## 6. Secrets

Fix:
- `.env` in `.gitignore` before the first commit; commit `.env.example` with empty values. Already committed? Rotate
  the key at the provider first, then clean history (`security.md#1-secrets-in-history-not-just-head`).
- Anything in `NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`, `EXPO_PUBLIC_*` is compiled into the browser bundle. Only
  public-by-design values go there (Supabase anon key, Stripe publishable key, analytics ids). A secret key there
  must move to a server route and be rotated: it is already in every visitor's cache. The Check flags names with
  SECRET, PRIVATE, PASSWORD or SERVICE_ROLE; read `*_TOKEN` and `*_API_KEY` client variables by hand, since most
  are public by design (maps, search) but some are not.
- Production secrets live in the host's secret store or env settings, not in the repo, the image or CI logs.
  Check the required ones at startup and fail fast with the variable's name (never its value).
- Different keys per environment, and scoped: a read-only key where read-only is enough.

## 7. Backups and recovery

A backup you have never restored is a hope. Most data loss is not an attack: a bad migration, a `DELETE` without a
`WHERE`, a provider account suspended.

Fix:
- Automatic backups: managed DB point-in-time recovery, or `pg_dump` nightly / `pgBackRest` / `wal-g` /
  `litestream` (SQLite) on a timer. Encrypted.
- At least one copy off the platform: another provider or another account. A backup inside the account that
  got deleted or compromised is gone with it.
- Rehearse the restore into a scratch database on a schedule (quarterly), time it, write the steps down. The
  restore time is your real recovery time.
- Rollback for code: the previous image or build can go back in minutes (a tag, `docker compose up` with the old
  tag, the platform's rollback button). Migrations that drop or rewrite data need their own way back.

Done when: the date of the last successful restore rehearsal is written in the repo's ops notes.
