---
name: repo-secure
description: >
  Security audit and hardening of a shipped or about-to-ship app, in the order breaches actually happen:
  authorization (IDOR, default-deny, row-level security), trusting client input (prices, roles, owner ids, mass
  assignment), rate limits on login, signup, email and LLM endpoints, supply chain (lockfile, Dependabot, an audit in
  CI), security logging, secrets (including keys in NEXT_PUBLIC_/VITE_ variables), and backups with a rehearsed
  restore. Use whenever the user asks "проверь безопасность", "аудит безопасности", "насколько безопасно моё
  приложение", "можно ли выкатывать", "захардень", "security checklist", "is my app secure", "vibe-coded app
  security", or worries about leaking data, a scraped API, an LLM bill run up by strangers, or losing the database.
  Runs a read-only preflight first and fixes only the parts the user picks.
---

# Repo secure

Find the handful of gaps that burn shipped apps and close them, worst first. Read-only first: the preflight lists
what a file search can prove, plus judgement questions with evidence (routes that take a record id, limiter and
backup tooling it found). You answer those by reading the code, the user picks the parts, then each part closes
its gaps with the procedure the preflight points to.

## Phase 0: preflight and scope

```bash
python3 <skill-dir>/engine/preflight.py [project-path] --scenario secure
```

The report groups failed and broken Checks by severity, each with a `fix:` path from this skill's folder
(`engine/procedures/<topic>.md#<section>` or `engine/assets/...`). **error** blocks a deploy or release until fixed;
**warning** must be fixed or exempted before the part is done; **info** is advice. Judgement questions are Checks:
answer each by reading the code, and count it as passed or failed at its severity. In the answer, list every one by
id: passed or failed, with one line of evidence and the file it comes from ("authz_per_object: failed,
`GET /contacts/{contact_id}` loads by id only, app/api/contacts_routes/crud.py:129"). "Looks fine" is not an
answer: for `authz_per_object`, open each listed route and follow the query down to the database call.

A Check that doesn't fit gets an exemption in `.repo-ready.yml` (`exempt:` then `  check_id: reason`), after the
user agrees. Skipped Checks name the fact they need: without `web_app`, no authorization part.

Then ask only what the code can't tell, with a recommendation each: where it runs and who hosts the database
(backups), which endpoints cost money per call, whether real users' data is already in it (urgency). Default: every
part with findings, in the order below.

## Parts, in this order

The first two are how data leaks; the rest decide how bad a bad day gets.

1. **Authorization** (`appsec.md#1-authorization`): owner filter in every record query, private by default,
   role checks on admin routes, RLS on every table the client reaches.
2. **Never trust the client** (`appsec.md#2-never-trust-the-client`): input schemas that forbid unknown fields;
   prices, roles and owner ids from the server; payment state from a signed webhook.
3. **Secrets** (`appsec.md#6-secrets`, `security.md#1-secrets-in-history-not-just-head`): nothing secret in client
   env vars or history; a leaked key is rotated first, then cleaned.
4. **Rate limits** (`appsec.md#3-rate-limiting`): auth, email/SMS and paid endpoints, per IP and per account.
5. **Supply chain** (`appsec.md#4-supply-chain`): lockfile, Dependabot with cooldown, an audit step in CI,
   pinned actions.
6. **Logging and monitoring** (`appsec.md#5-security-logging-and-monitoring`): security events logged without
   secrets, errors to a tracker, a few alerts. The `python-logging` skill does the Python side.
7. **Backups and recovery** (`appsec.md#7-backups-and-recovery`): automatic, off-platform, a rehearsed restore,
   a fast rollback.

Then, for web apps, hand the code to `security-review` (or the `code-reviewer` agent) for the rest of OWASP:
injection, SSRF, path traversal, headers, CSRF, session settings (`security.md#6-code-level-review`).

Each part ends with its "Done when" from the procedure, run for real: the cross-user test returns 404, the forged
price is rejected, curl gets a 429, the restore lands in a scratch database.

## Working rules

- **Read-only until scoped.** The preflight changes nothing; edits start after the user picks the parts.
- **Tests prove the fix.** Every authorization and trust fix gets a test that fails before it (user A reads user
  B's record, a forged field is accepted) and passes after.
- **Rotate before you clean.** A leaked key is live until rotated at the provider; ask before any history rewrite.
- **Outward-facing needs a yes.** Changing GitHub settings, rotating production keys, running a restore against
  anything but a scratch database, each waits for the user's explicit yes.
- **Don't break login.** Rate limits and auth changes ship with the limits written down and a test for the happy
  path too.
- **Commit by part**, `<type>: <description>`, staging only that part's files.

## Report format

At the start, after the preflight, give a scorecard: one row per part, status (ok / gaps / not applicable), and
the top finding for each. End each part with:

```
## <Part>
Before → after: <one line per change, with file paths>
Verified: <the test or command run, and its result>
Not done: <skipped items and why>
Next step: <recommendation>
```

## Sources

The seven parts follow the security checklist for AI-written apps by arjaythedev, rewritten and extended with
checks and procedures for this kit.
