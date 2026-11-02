# Picking storage and a cache pattern

Pick by access pattern: how the data is read and written, not what it is. Postgres is the default; leave it
only for a reason from the "avoid" column, and say that reason.

## Storage engines

| Kind | Pick when | Avoid when | Examples |
|---|---|---|---|
| **Relational** | real relationships (users, orders, line items); ACID across rows; queries you can't list up front; correctness over last-mile throughput; working set fits one big node | sub-ms key lookups at huge QPS; writes beyond one node; many writers updating the same rows (lock contention); sparse rows with different columns each | Postgres (default), MySQL, SQLite (embedded, very capable), CockroachDB/Spanner |
| **Key-value** | data is addressed by a key (session, user id, sku); sub-ms latency at huge QPS; TTL data (caches, rate counters); hot config and feature flags | query by anything but the key; relations; ACID across keys; data larger than RAM; it is the only copy | Redis/Valkey, Memcached, DynamoDB (durable), etcd |
| **Wide-column** | write volume one node can't take; reads always by a known partition key; time series, event logs, append-heavy; eventual consistency is fine | ad-hoc queries; joins; strong consistency across partitions; data fits one machine; access patterns not known yet | Cassandra, ScyllaDB, Bigtable, DynamoDB |
| **Object storage** | blobs (media, backups, datasets, model weights); write once, read many; static assets behind a CDN | transactions; querying by content; partial updates; sub-ms latency; relational data | S3, R2, GCS, MinIO |
| **Vector** | semantic search, RAG, similarity recommendations, dedup, anomaly detection | exact key lookup; transactional data; joins; "similar" is ill-defined; small sets where brute force is fine | pgvector (default: stays in Postgres), Qdrant, Weaviate, Milvus, Chroma |
| **Graph** | multi-hop questions (friends of friends, paths, shared neighbours): fraud rings, knowledge graphs, dependency analysis | tabular data; simple key lookups; you rarely traverse; flat SQL analytics | Neo4j, Neptune, Memgraph |

Access-pattern red flags in a relational design: `LIKE '%x%'` or filters on unindexed columns (full scan, O(N));
one hot row many writers update (serialised by its row lock); a connection pool smaller than the app's
concurrency. In key-value: needing to find entries by value (a scan over every key); one hot key.

## Cache patterns

| Pattern | How | Good for | Watch out for |
|---|---|---|---|
| **Cache-aside** (default) | the app reads the cache, on a miss reads the DB and fills the cache; on write, writes the DB and deletes the key | retrofitting; a cache outage only slows things down; per-call-site policy | a miss costs a full DB round trip; a forgotten invalidation on a new write path means stale data; a stampede when a hot key expires |
| **Read-through** | the cache loads from the DB itself; the app talks only to the cache | one place owns loading; simple call sites | the first miss still pays; the cache must know the data model |
| **Write-through** | each write goes to the cache and the DB before returning | reads never stale; no invalidation code | slower writes; a DB outage blocks writes; memory spent on keys nobody reads |
| **Write-behind** | write to the cache, return, flush to the DB in batches from a queue | very fast writes; spike absorption; fewer, larger DB transactions | a cache crash loses data; other readers of the DB see stale values; ordering is hard. Never for money or orders |
| **Refresh-ahead** | refresh hot keys in the background before their TTL ends | hot keys never miss (leaderboards, home page, top-N) | wasted DB load on cold keys; hard to tune; useless for unpredictable access |

Cache rules: start with TTLs and cache-aside; add jitter to TTLs and a single-flight lock on hot keys against
stampedes; decide what the system does when the cache is down (fall through to the DB at what load?). Rate
limits and sessions in Redis are fine; Redis as the only copy of data that matters is not.
