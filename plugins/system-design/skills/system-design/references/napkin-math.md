# Napkin math

Run `scripts/napkin.py` for the arithmetic; this page is what the numbers mean and where they lie.
The goal is the order of magnitude: 11.6 servers is "about a dozen". Round to a power of ten and keep going.

## Constants worth knowing

| Time | |
|---|---|
| seconds in a day | 86,400 ≈ 10⁵ |
| seconds in a month / year | ≈ 2.6M / ≈ 31.5M |
| 1M requests a day | ≈ 12 req/s (drop five zeros) |
| 1B requests a day | ≈ 12k req/s |

| Sizes (powers of ten, not 1024) | |
|---|---|
| UUID | 16 B |
| short text post | ~300 B |
| typical DB row | ~1 KB |
| JSON API response | 1–10 KB |
| compressed photo | ~200 KB |
| 1 min of 1080p video | ~50 MB |

| Latency (each row ~10× the one above) | |
|---|---|
| RAM read | 100 ns |
| SSD random read | 100 µs |
| round trip inside one DC | 0.5 ms |
| 1 MB sequential from SSD | 1 ms |
| HDD seek | 10 ms |
| round trip across an ocean | 150 ms |

| Throughput per node (±10× with hardware and query shape) | |
|---|---|
| app server, simple JSON CRUD | ~1k req/s (cached JSON ~5k, image resize ~50) |
| Postgres, indexed reads | ~5k/s |
| Postgres, writes | ~2k/s |
| Redis GET | ~100k/s |
| Kafka ingest | ~1M msg/s |

## The chain

| Step | Formula | Rule of thumb |
|---|---|---|
| average load | `DAU × req/user ÷ 86,400` | requests per user: utility ~5, feed 20–50, chat hundreds; one tap is 1–3 API calls |
| peak | `average × peak factor` | 2–3× for a daily cycle, 5–10× for launches and viral spikes |
| app servers | `peak ÷ (capacity × 0.7) + 1 spare` | 70% leaves room for spikes, retries and rolling deploys |
| DB reads | `reads × (1 − cache hit rate)` | the DB sees only misses plus writes |
| cache memory | `daily reads × 20% × object size` | 80/20: a fifth of the data takes most reads |
| read replicas | `DB reads ÷ 5k` | an afternoon of work |
| shards | `writes ÷ 2k` | a commitment for life, so last |
| storage | `writes/day × size × 3 × days` | 3 copies in production; storage piles up, traffic resets every second |
| egress | `peak reads × response size` | past ~1 Gbit/s a CDN is not optional |

## How the estimate goes wrong

- **DAU alone says nothing.** Ask how many requests one user fires a day before anything else.
- **Per-server capacity is a guess.** Say the number, mark it an assumption, and plan a load test. Being 2× off
  turns 10 servers into 20, which is the same architecture. The estimate is there to catch 12 vs 4,000.
- **The cache hit rate swings the DB tier more than anything.** At 95% hits one Postgres carries a large product;
  at 0% the same traffic needs a replica fleet. Run the script both ways and show both.
- **Media flips the storage story.** Text-only storage is a rounding error, so stop optimising it. With media,
  tier it: hot data on SSD, the rest in object storage, a CDN in front so egress leaves the origin.
- **Real systems are measured, not estimated.** When the system exists, take RPS, p95, DB time and cache hit
  rate from its metrics and logs, and use the napkin only for the growth you expect.
