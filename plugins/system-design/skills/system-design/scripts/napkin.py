#!/usr/bin/env python3
"""Napkin math for a backend: DAU in, servers / cache / DB nodes / storage / egress out.

Stdlib only. Every default is a starting assumption to say out loud, not a fact:
override any of them with a flag, then re-run.

    python3 napkin.py --dau 1e6 --req-per-user 20
    python3 napkin.py --dau 5e7 --req-per-user 50 --peak 5 --hit-rate 0.95 --object-kb 200
"""
import argparse
import math
from dataclasses import dataclass, fields

SECONDS_PER_DAY = 86_400
DAYS_PER_YEAR = 365
HOT_SHARE = 0.2            # 80/20: a fifth of the daily reads is the hot set worth caching
PG_READS_PER_NODE = 5_000  # indexed reads/s one Postgres node carries
PG_WRITES_PER_NODE = 2_000 # writes/s one Postgres primary carries
CDN_EGRESS_BPS = 1e9       # past ~1 Gbit/s of egress a CDN stops being optional
BITS_PER_BYTE = 8
KB = 1_000


@dataclass(frozen=True)
class Assumptions:
    """What the napkin starts from; the defaults are the usual opening guesses."""
    dau: float
    req_per_user: float
    peak: float = 3.0
    server_rps: float = 1_000
    util: float = 0.7
    read_share: float = 0.9
    hit_rate: float = 0.8
    object_kb: float = 2.0
    write_kb: float = 2.0
    response_kb: float = 2.0
    replication: int = 3
    retention_years: float = 5


def napkin(a: Assumptions) -> dict[str, float]:
    """Return the whole chain as a dict. Pure function; the CLI only formats it."""
    req_day = a.dau * a.req_per_user
    avg = req_day / SECONDS_PER_DAY
    peak_rps = avg * a.peak
    # ponytail: one spare box flat; at 50+ servers use N+10% instead
    servers = math.ceil(peak_rps / (a.server_rps * a.util)) + 1
    reads_peak = peak_rps * a.read_share
    writes_peak = peak_rps - reads_peak
    db_reads = reads_peak * (1 - a.hit_rate)
    cache_bytes = req_day * a.read_share * HOT_SHARE * a.object_kb * KB
    shards = max(1, math.ceil(writes_peak / PG_WRITES_PER_NODE))
    # each shard's primary also serves reads; replicas cover the rest
    replicas = max(0, math.ceil(db_reads / PG_READS_PER_NODE) - shards)
    store_day = req_day * (1 - a.read_share) * a.write_kb * KB * a.replication
    return {
        "req_day": req_day, "avg_rps": avg, "peak_rps": peak_rps, "servers": servers,
        "reads_peak": reads_peak, "writes_peak": writes_peak, "db_reads": db_reads,
        "db_reads_no_cache": reads_peak, "cache_bytes": cache_bytes, "shards": shards,
        "replicas": replicas, "store_day": store_day, "store_year": store_day * DAYS_PER_YEAR,
        "store_total": store_day * DAYS_PER_YEAR * a.retention_years,
        "egress_bps": reads_peak * a.response_kb * KB * BITS_PER_BYTE,
        "ingress_bps": writes_peak * a.write_kb * KB * BITS_PER_BYTE,
    }


def verdict(r: dict[str, float]) -> list[str]:
    """Smallest rung of the scaling ladder (references/scale-ladder.md) that holds."""
    notes = []
    if r["servers"] > 2:
        notes.append(f"rung 4: load balancer + {r['servers']} stateless app servers")
    if r["db_reads_no_cache"] > PG_READS_PER_NODE and r["replicas"] == 0 and r["shards"] == 1:
        notes.append("rung 5: the cache is what keeps this on one database; size it and plan for its failure")
    if r["egress_bps"] > CDN_EGRESS_BPS:
        notes.append("rung 5: egress past 1 Gbit/s, put a CDN in front")
    if r["shards"] > 1:
        notes.append(f"rung 7: writes need {r['shards']} shards; first try batching, a queue, or a bigger primary")
    elif r["replicas"] > 0:
        notes.append(f"rung 7: {r['replicas']} read replica(s); first raise the cache hit rate")
    if not notes:
        notes.append("rungs 1-2: one good VPS (DB on its own host once data matters). Ship it.")
    return notes


def human(n: float, unit: str = "") -> str:
    for div, suffix in ((1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "k")):
        if abs(n) >= div:
            return f"{n / div:.1f}{suffix}{unit}"
    return f"{n:.0f}{unit}" if n >= 10 else f"{n:.1f}{unit}"


def report(r: dict[str, float], a: Assumptions) -> str:
    rows = [
        ("traffic", ""), ("requests/day", human(r["req_day"])),
        ("average", human(r["avg_rps"], " req/s")), (f"peak (x{a.peak:g})", human(r["peak_rps"], " req/s")),
        ("app tier", ""), (f"servers @ {a.server_rps:g} req/s, {a.util:.0%} util, +1 spare", str(r["servers"])),
        ("read path", ""), (f"reads at peak ({a.read_share:.0%})", human(r["reads_peak"], " req/s")),
        (f"reach the DB ({a.hit_rate:.0%} hit)", human(r["db_reads"], " req/s")),
        ("cache memory (80/20)", human(r["cache_bytes"], "B")),
        ("database", ""), ("writes at peak", human(r["writes_peak"], " req/s")),
        (f"shards @ {PG_WRITES_PER_NODE} w/s", str(r["shards"])),
        (f"replicas @ {PG_READS_PER_NODE} r/s", str(r["replicas"])),
        ("storage", ""), (f"per day (x{a.replication} repl)", human(r["store_day"], "B")),
        ("per year", human(r["store_year"], "B")), (f"after {a.retention_years:g} years", human(r["store_total"], "B")),
        ("network", ""), ("egress at peak", human(r["egress_bps"], "bit/s")),
        ("ingress at peak", human(r["ingress_bps"], "bit/s")),
    ]
    lines = [f"DAU {human(a.dau)} x {a.req_per_user:g} req/user/day"]
    for label, value in rows:
        lines.append(label if not value else f"  {label} ".ljust(46, ".") + f" {value}")
    lines += ["verdict:"] + [f"  - {n}" for n in verdict(r)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dau", type=float, required=True, help="daily active users")
    p.add_argument("--req-per-user", type=float, required=True, help="API calls per user per day (utility 5, feed 20-50, chat 100s)")
    p.add_argument("--peak", type=float, default=3.0, help="peak / average (2-3 daily cycle, 5-10 spiky)")
    p.add_argument("--server-rps", type=float, default=1_000, help="req/s one app server carries (CRUD ~1k, media/ML ~50)")
    p.add_argument("--util", type=float, default=0.7, help="target utilisation per server")
    p.add_argument("--read-share", type=float, default=0.9, help="share of requests that are reads")
    p.add_argument("--hit-rate", type=float, default=0.8, help="cache hit rate (0 = no cache)")
    p.add_argument("--object-kb", type=float, default=2.0, help="size of one cached object, KB")
    p.add_argument("--write-kb", type=float, default=2.0, help="bytes stored per write, KB")
    p.add_argument("--response-kb", type=float, default=2.0, help="response size, KB")
    p.add_argument("--replication", type=int, default=3, help="copies of every byte")
    p.add_argument("--retention-years", type=float, default=5)
    a = p.parse_args(argv)
    for name in ("util", "read_share", "hit_rate"):
        if not 0 <= getattr(a, name) <= 1:
            p.error(f"--{name.replace('_', '-')} is a share between 0 and 1")
    if a.util == 0 or a.server_rps <= 0:
        p.error("--util and --server-rps must be positive")
    assumptions = Assumptions(**{f.name: getattr(a, f.name) for f in fields(Assumptions)})
    print(report(napkin(assumptions), assumptions))


if __name__ == "__main__":
    main()
