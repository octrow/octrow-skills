# Trade-offs to say out loud

Every choice gives something up. A design is only as good as its stated trade-offs. For each one below: name
the side you picked, why, and what you lose.

## Consistency vs availability

During a network partition you choose one: refuse to answer (consistent) or answer with possibly stale data
(available). Partitions happen, so this choice is not optional.
- **Consistent:** balances and payments, permissions and security settings (a password change must take effect
  everywhere before "done"), inventory you must not oversell.
- **Available:** feeds, likes, view counts, caches, logs and analytics, profile pictures.
- **Mixed is normal:** the product page can be available and stale while checkout is strongly consistent.
  Draw the line per data type, not per system.

## Latency vs durability

Fast writes acknowledge before the data is safe (write-behind, buffered flushes, memory only). Durable writes
wait for the disk, replicas or consensus, which adds 50–200 ms.
- Pick latency for low-risk or reversible writes (likes, views, telemetry) or when a reliable queue with retries
  stands behind the write.
- Pick durability when a lost write is unacceptable: payments, orders, password changes.

## Cost vs performance

Count engineering time, not only the cloud bill: self-hosting to save money means someone maintains it. Cheap
moves: smaller instances, fewer replicas, batching, rate limits, shorter retention (logs are always more
expensive than expected). Pay for performance where it clearly earns money or where a requirement demands it.

## Monolith vs services

Start with a modular monolith: one codebase, one deploy, easy to debug. Split a service out only when a part
scales differently (needs 10× the resources), fails differently, or another team owns it. If most requests
touch most components, they belong in one process; a network hop between them adds latency and new failure
modes for nothing.

## Read- vs write-optimised

Most systems are read-heavy: denormalise, cache, avoid joins and scans on hot paths, accept costlier writes
(fan-out on write for feeds). Write-heavy systems (ingest, telemetry, ledgers): append-only, batches, few
indexes, normalised and auditable. When reads and writes differ in volume, latency, consistency or shape, split
the paths (CQRS): a normalised transactional write model and a denormalised read model fed from it.

## Strong vs eventual consistency

Strong consistency in a distributed system needs locks, consensus or synchronous replication: slower writes,
harder scaling, painful under load. Eventual consistency is the practical default; agree with the product side
how stale is acceptable ("a profile picture may take 10 s to show everywhere") and write that number down.
