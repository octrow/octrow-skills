# One VPS: from a working app to an HTTPS URL

The smallest production that is still honest: one rented Linux box, the app (or its Compose stack) kept alive by
systemd, a reverse proxy in front with TLS, a domain. An afternoon of work, and enough for most side projects until
the numbers say otherwise. Every step below runs on the user's server: show the commands, run them only after a yes.

## Server

Any small Ubuntu/Debian VM (Hetzner, DigitalOcean, Vultr, Lightsail): 1–2 GB RAM for an app plus Postgres.

```bash
ssh root@<ip>
apt update && apt upgrade -y && apt install -y unattended-upgrades ufw
adduser deploy && usermod -aG sudo deploy
rsync -a ~/.ssh/ /home/deploy/.ssh/ && chown -R deploy: /home/deploy/.ssh   # the key login works for deploy too
# /etc/ssh/sshd_config.d/hardening.conf: PermitRootLogin no, PasswordAuthentication no; then `systemctl reload ssh`
ufw allow OpenSSH && ufw enable
```

Check a second `ssh deploy@<ip>` works before closing the root session.

## Service under systemd

Something must restart the app after a crash and a reboot; systemd is already there. The app listens on
`127.0.0.1` only: the proxy is the one door in.

Plain process (`/etc/systemd/system/myapp.service`):

```ini
[Unit]
Description=myapp
After=network-online.target
Wants=network-online.target

[Service]
User=deploy
WorkingDirectory=/home/deploy/myapp
EnvironmentFile=/home/deploy/myapp/.env
ExecStart=/home/deploy/.local/bin/uv run --frozen uvicorn myapp.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

A Compose stack instead: `ExecStart=/usr/bin/docker compose up --wait` with `Type=oneshot`, `RemainAfterExit=yes`
and `ExecStop=/usr/bin/docker compose down`, and publish ports as `127.0.0.1:8000:8000` (see `compose.md`).

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now myapp
journalctl -u myapp -f        # logs; cap journald size (see the python-logging skill)
```

The `.env` stays on the server, mode 600, never in the repo. Migrations run as their own step before the restart,
not inside the app start.

## Reverse proxy and TLS

Caddy by default: it gets and renews the Let's Encrypt certificate itself. `/etc/caddy/Caddyfile`:

```
example.com, www.example.com {
    reverse_proxy 127.0.0.1:8000
    encode gzip
}
```

nginx is fine if the team knows it: a `server` block with `proxy_pass http://127.0.0.1:8000` and the
`Host` / `X-Forwarded-For` / `X-Forwarded-Proto` headers, then `certbot --nginx -d example.com -d www.example.com`.
Either way the app must trust those headers only from the proxy (`uvicorn --proxy-headers
--forwarded-allow-ips 127.0.0.1`), or client IPs (and IP rate limits) are wrong.

```bash
sudo ufw allow 80,443/tcp      # and nothing else: the app port stays closed
```

## Domain

At the registrar's DNS: `A example.com → <ip>` (plus `AAAA` for IPv6) and `CNAME www → example.com`. Propagation
takes minutes to an hour; `dig +short example.com` shows when it's done. Caddy issues the certificate on the
first request after that.

## Done when

- `curl -I https://example.com` answers 200 (or the app's redirect) with a valid certificate;
- `curl http://<ip>:8000` from outside times out (the app port is closed);
- `sudo reboot`, wait, and the site comes back by itself;
- `ssh root@<ip>` and password logins are refused;
- backups exist and a restore was tried (`appsec.md#7-backups-and-recovery`).

When one box stops being enough, the `system-design` skill's scaling ladder says what to add next, and in what order.
