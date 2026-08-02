# 🐍 Montycat for Python — The AI-Native NoSQL Database with Semantic Search for RAG & Agents

### Abolish the two-database stack.

The official async Python client for [Montycat](https://montygovernance.com) — a self-hosted **NoSQL + vector database** with AI **semantic search** forged into the core, built for **RAG and AI-agent memory**. One Rust engine, not a sprawl of services. **Your hardware. Your data. Your meaning.**

[![PyPI Version](https://img.shields.io/pypi/v/montycat.svg)](https://pypi.org/project/montycat/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/montycat?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/montycat)
[![Docker Pulls](https://img.shields.io/docker/pulls/montygovernance/montycat)](https://hub.docker.com/r/montygovernance/montycat)
[![Python Version](https://img.shields.io/pypi/pyversions/montycat)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/MontyGovernance/montycat_python/blob/master/LICENSE)

```python
# Search your data by MEANING — no external APIs, no separate vector database.
# (already ON by default in the montycat-semantic server edition)
hits = await Sales.semantic_search_get_values("Show all Bluetooth devices", limit=5)
# → [{__key__: 123..., __score__: 0.82, __value__: {"name": "Wireless Headphones"}}]
```

> ### 🧩 All-in-one. AI-native. **Zero external dependencies.**
> The vector-embedding engine runs **inside** the database — **no** separate vector DB, **no** embedding API, **no** API keys, **no** sidecar service. One engine, one binary, your hardware.

## What is Montycat?

For a generation we were told the price of intelligence was two systems: a database for your records, and a separate vector store — with its per-query bill — for their meaning. Montycat rejects that tax. It is a **self-hosted NoSQL + vector database**: one Rust-powered engine with semantic search built in, so **RAG, AI-agent memory, and vector search** live where your data already lives. No cloud lock-in. No ops headache. Decentralized by nature, ultra-fast, and natively async.

Think of it as an **open-source, self-hosted alternative to Pinecone, Weaviate, Chroma, Qdrant, and Redis** — a **vector database _and_ a NoSQL store in a single engine**, so your records and their embeddings live together instead of in two systems you have to keep in sync. Montycat is not an incremental improvement on the databases you know. It is a break with them.

## 🧠 Why Montycat?

- ⚡ Blazing Speed — Powered by the Montycat Engine written in Rust, built for microsecond-level read/write performance.
- 🌀 Async-First Design — Fully asynchronous, built on asyncio. Perfect for APIs, pipelines, and real-time apps.
- 💾 Hybrid Storage — In-memory for raw speed or persistent for durability — or mix both in one engine.
- 🔎 AI Semantic & Vector Search — Rank data by *meaning* with on-device embeddings. Built-in kNN vector search for **RAG, AI agents & LLM apps** — no external API, no separate vector database. *(requires the `montycat-semantic` server edition — Docker image, package, or apt; see below.)*
- 🧩 Schema-Aware — Define data schemas in Python, enforce them at runtime — with zero ceremony.
- 🗂️ True Data Mesh Architecture — Each keyspace is a self-owned, domain-oriented data product.
- 📡 Reactive Subscriptions — Subscribe to live updates in real-time — per key or per keyspace.
- 🛡️ Memory-Safe & Secure — Backed by Rust’s zero-cost abstractions and modern TLS communication.
- 🤝 Developer-Centric API — Intuitive, predictable, and ready for production.
- 📚 Beautifully Documented — Every method, every example, crystal clear.

## 💡 Philosophy

Montycat is not a database wrapper. It’s a new way to think about data — composable, fast by design. No legacy baggage. Just clean async functions and pure data. Montycat isn’t inspired by NoSQL. It redefines it — with elegance, concurrency, and memory safety.

## Montycat for Python?

This is the official Python client, built to bring Montycat’s next-generation Data Mesh architecture directly into your Python applications — manage and query your data with the flexibility of NoSQL and true decentralized data ownership. Forget ORM hell, clunky SQL syntax, and blocking I/O. With Montycat, data feels alive — reactive, structured, and fast enough to keep up with your imagination.

## 🔍 Example Use Cases

- **RAG pipelines & semantic retrieval** for LLM-powered apps
- **AI agent / chatbot long-term memory** that survives restarts
- **Semantic product search & recommendations** — match intent, not keywords
- Real-time dashboards and analytics
- Async ETL pipelines with real-time awareness and processing
- Microservice data stores and event-driven systems
- Collaborative data products in a Mesh architecture

## 🚀 Get the Engine (30 seconds)

The client talks to a Montycat server. Fastest way — Docker, with AI semantic search built in:

```bash
docker run -d --name montycat \
  -p 21210:21210 -p 21211:21211 \
  -e MONTYCAT_SUPEROWNER="admin" \
  -e MONTYCAT_PASSWORD="change-me" \
  -v montycat_data:/var/lib/.montycat \
  montygovernance/montycat:semantic
```

Prefer the lean edition without the embedding engine? Use the `latest` tag. Prebuilt packages (apt, macOS, Windows) at **https://montygovernance.com**.

## Installation

Install the Python client with `pip`:

```bash
pip install montycat
```

## Quick Start

```python
import asyncio
from montycat import Engine, Keyspace, Schema

# setup connection

connection = Engine(
    host="127.0.0.1",
    port=21210,
    username="USER",
    password="12345",
    store="Departments",
)

# keyspaces: persistent or in-memory — mix freely in one engine

class Sales(Keyspace.Persistent):
    keyspace = "Sales"

class Production(Keyspace.InMemory):
    keyspace = "Production"

Sales.connect_engine(connection)
Production.connect_engine(connection)

# schemas, enforced on the database side (optional)

class SalesSchema(Schema):
    product: str
    amount: int

class ProductionSchema(Schema):
    items: list
    work_order: str | None

async def main():
    # create store and keyspaces using runtime migration
    await Sales.create_keyspace()
    await Production.create_keyspace()

    await Sales.enforce_schema(SalesSchema)
    await Production.enforce_schema(ProductionSchema)

    # write
    sale = SalesSchema(product="Product1", amount=12).serialize()
    await Sales.insert_value(sale)

    order = ProductionSchema(items=["Product1"], work_order="WO 000012").serialize()
    await Production.insert_value(order)

    # query
    print(await Sales.lookup_values_where(schema=SalesSchema, key_included=True))
    print(await Production.lookup_keys_where(work_order="WO 000012"))

asyncio.run(main())
```

## 🧠 AI-Native Semantic Search — Vector Search Built Into Your Database

**Stop bolting a separate vector database onto your stack.** Montycat ranks your data by
*meaning*, not keywords — an embedded, on-device vector-embedding engine turns every write
into a searchable vector automatically. It's the retrieval layer for **RAG pipelines, AI
agents, semantic search, recommendation engines, and LLM-powered apps** — with **zero
external APIs, zero API keys, and zero extra infrastructure.**

- 🔎 **Semantic / vector search** — kNN similarity over on-device embeddings, not brittle keyword matches.
- 🤖 **Built for AI** — RAG, semantic retrieval, AI agents, recommendations, dedup, clustering.
- 🔒 **Private & free** — embeddings never leave your machine. No OpenAI/Cohere bill, no data egress.
- ⚡ **One system, not two** — your data *and* its vectors live in the same database. No sync jobs, no drift, no second service to run.
- 🚀 **Zero setup** — no index tuning, no pipeline: `enable_semantic_search()` and you're ranking by meaning.

> **⚠️ Requires the semantic edition of the server — nothing to compile.** Semantic
> search runs an embedded ONNX vector-embedding engine that ships only in the
> **`montycat-semantic`** edition; the default lean `montycat` server does not include it.
> Get it the way that suits you — pull the **Docker image**
> (`montygovernance/montycat:semantic`), download the prebuilt **package**, or install
> `montycat-semantic` from the **apt repository**. The Python client API is identical
> either way; just point it at a semantic-edition server (semantic search is enabled by
> default there, using the `bge-small` model).

The switch is DB-wide and already on in the semantic edition. The embedding model is
downloaded on demand, and every keyspace is embedded in the background as data is written.

```python
# Semantic search is ON by default in the montycat-semantic edition — just search.
# Rank stored items by meaning — two flavors:
#   get_values → each hit is {__key__, __score__, __value__}
#   get_keys   → each hit is {__key__, __score__} (lighter; fetch a page later with get_bulk)
hits = await Sales.semantic_search_get_values("Show all Bluetooth devices", limit=5)
keys = await Sales.semantic_search_get_keys("Show all Bluetooth devices", limit=5)

# Optionally drop weak matches by cosine similarity (range [-1, 1]).
strong = await Sales.semantic_search_get_keys("Show all Bluetooth devices", limit=5, min_score=0.35)

# Control the DB-wide switch (optional — it's already on):
# Read back the model and backfill state actually assigned to a keyspace.
status = await connection.get_semantic_status(
    store="catalog", keyspace="products"
)

# Enable an unenrolled keyspace with an explicit model.
await connection.enable_semantic_search(
    model=SemanticModel.BGE_BASE,
    store="catalog",
    keyspace="products",
)

# Changing an enrolled keyspace is destructive and starts a full backfill.
await connection.reembed_semantic_search(
    SemanticModel.BGE_BASE,
    store="catalog",
    keyspace="products",
)

# turn it off (vectors are kept so re-enabling resumes instantly;
# pass drop_vectors=True to also clear stored vectors)
await connection.disable_semantic_search()
```

### Hybrid semantic search

Restrict meaning-based ranking to records matching structured metadata. The
filter is a hard AND pre-filter with the same criteria shape as
`lookup_keys_where`; it does not boost cosine scores.

```python
matching_keys = await Sales.semantic_search_get_keys_where(
    "astronomy and outer space",
    {"category": "space"},
    limit=5,
    min_score=0.35,
)

matching_values = await Sales.semantic_search_get_values_where(
    "astronomy and outer space",
    {"category": "space"},
    limit=5,
)
# key hits:   {"__key__", "__score__"}
# value hits: {"__key__", "__score__", "__value__"}
```

## 📨 Response Shape

Every call returns the same envelope, so there is one thing to check everywhere:

```python
# {"status": True,  "payload": <result>, "error": None}
# {"status": False, "payload": None,     "error": "Governance permission denied: ..."}

res = await Sales.insert_value(sale)
if res["status"]:
    print(res["payload"])
```

`payload` is `None` for commands that only acknowledge, the new key for inserts, and a
list for lookups and semantic searches. **Keys are u128 and always arrive as strings** —
keep them that way; Python `int` will hold one, but round-tripping through JSON or a
float will not. Invalid arguments raise `ValueError` before anything touches the network;
server-side failures come back in `error` with `"status": False`.

## 🔄 Connection Pooling

By default every request opens a TCP connection, sends, reads one response, and closes.
Reuse the connection instead and the handshake disappears from every call after the
first. The win scales with how much of your latency is connection setup: large for a
chatty service issuing many small reads, larger still over a network — where the
handshake costs a full round trip before the query is even sent — and larger again with
TLS.

Pooling is opt-in. One new argument, and no call site changes:

```python
from montycat import Engine, PoolConfig, close_all_pools

connection = Engine(
    host="127.0.0.1", port=21210, username="USER", password="12345",
    store="Departments",
    pool=PoolConfig(),          # ← the only new argument
)

Sales.connect_engine(connection)
await Sales.insert_value(sale)  # unchanged

await close_all_pools()         # before exit
```

Tune it if you need to:

```python
pool = PoolConfig(max_idle=4, idle_timeout=15.0)   # defaults: 8, 30.0
```

**Pools are shared per `(host, port, tls)`.** They live in a module-level registry, not on
the `Engine`, because `connect_engine` copies scalars off the engine and discards it. Two
keyspace classes pointing at the same server therefore share one pool rather than each
opening its own. `tls` is part of the key — a plaintext and a TLS connection to one
address are not interchangeable.

**Keep `max_idle` modest.** An idle pooled connection still holds one of the engine's
connection permits. The defaults are deliberately small; raise them only after measuring
with `queue_depths` under realistic load.

**Call `close_all_pools()` before exit**, otherwise idle sockets linger until the process
dies.

Subscriptions are never pooled — they are long-lived, stream many responses to one
request, and live on their own port. A connection is held exclusively for one
request/response, so concurrent `asyncio.gather` calls each get their own rather than
interleaving writes on one socket.

## 📡 Real-Time Subscriptions

Subscribe to one key or to a whole keyspace and get pushed every change — the reactive
core behind live dashboards, async ETL, and event-driven services.

```python
def on_change(event):
    print("changed:", event)

# Whole keyspace: omit both key and custom_key.
task, stop = await Sales.subscribe(callback=on_change)

# Or watch a single key (custom_key is hashed for you).
# Passing key and custom_key together raises ValueError; omitting callback does too.
one_task, one_stop = await Sales.subscribe(
    key="30442970696809394303186116932586352271",
    callback=on_change,
)

# Stop listening and let the task finish.
stop.set()
await task
```

`subscribe` returns `(task, stop_event)` — an `asyncio.Task` running the stream and an
`asyncio.Event` that ends it. Subscriptions use the **subscription port**, which defaults
to `port + 1` — that is the second port (`21211`) published in the Docker command above.
Override it with `subscription_port=` if your deployment maps it elsewhere.

## 🔐 TLS

Pass `tls=True` to negotiate an encrypted connection. It applies to commands and
subscriptions alike:

```python
connection = Engine(
    host="127.0.0.1",
    port=21210,
    username="USER",
    password="12345",
    store="Departments",
    tls=True,
)
```

> **Note.** The client accepts self-signed certificates, which is convenient for local
> and internal deployments but means the server identity is not verified. Terminate TLS
> at a trusted proxy if you need certificate validation.

## 👥 Owners & Access

Governance policies below are written against *owners*, so create them first. A
superowner provisions an owner, then grants data access — optionally narrowed to
specific keyspaces:

```python
from montycat import Permission

await connection.create_owner("alice", "alice-password")

await connection.grant_to("alice", Permission.READ)                       # whole store
await connection.grant_to("alice", Permission.WRITE, keyspaces=["Sales"])  # scoped

await connection.list_owners()

await connection.revoke_from("alice", Permission.WRITE, keyspaces=["Sales"])
await connection.remove_owner("alice")
```

`Permission` is `READ`, `WRITE`, or `ALL`; plain strings work too and are normalized
(`" ALL "` → `all`), with an unknown token raising `ValueError`. `grant_to` and
`revoke_from` apply to the engine's `store`. This governs **data access**; to delegate
*administrative* capabilities such as provisioning keyspaces or managing schemas, see
[Data-mesh governance](#data-mesh-governance-for-shared-and-multi-tenant-deployments) at
the end of this document.

## 🔗 Links

- 🌐 **Website & Docs** — https://montygovernance.com
- 📦 **PyPI** — https://pypi.org/project/montycat/
- 🐳 **Docker Hub** — https://hub.docker.com/r/montygovernance/montycat
- 💻 **Source** — https://github.com/MontyGovernance/montycat_python
- 📝 **Changelog** — [CHANGELOG.md](CHANGELOG.md)

## ❓ FAQ

- **Is Montycat a vector database or a NoSQL database?** Both — one engine. Store records and query them by *meaning* (vector / semantic search) or by key/schema, without running two systems.
- **Do I need OpenAI or an embedding API?** No. Embeddings run on-device in the `montycat-semantic` server. No API keys, no per-query bill, no data egress.
- **Is it a Pinecone / Weaviate / Chroma / Qdrant alternative?** Yes — self-hosted and open-source, with a NoSQL store built in.
- **Which Python versions?** 3.10+ — fully async (`asyncio`).

## Data-mesh governance for shared and multi-tenant deployments

Delegate administration without handing every team full server control. Policies scope
authority to an owner and store, with optional keyspace, storage-type, and semantic-model
constraints. This lets platform teams govern shared infrastructure while domain teams
operate the data products they own.

- Grant, revoke, or explicitly deny keyspace provisioning/removal, schema, semantic,
  snapshot, and access-management capabilities.
- Inspect effective permissions and policy history, or preview a grant/revoke before
  applying it.
- Validate, plan, apply, and export JSON or YAML policy manifests for repeatable
  infrastructure-as-code workflows.
- Constrain storage types for provisioning, removal, schema, access, and semantic
  management. Snapshot management is always in-memory, so it takes no storage-type
  qualifier.
- Constrain semantic models during keyspace provisioning and semantic management.

For example, a superowner can separately constrain keyspace provisioning and semantic
management within one store:

```python
from montycat import PolicyCapability, PolicyKeyspaceType, SemanticModel

await connection.policy_grant(
    "alice", PolicyCapability.PROVISION_KEYSPACE, "catalog",
    types=[PolicyKeyspaceType.IN_MEMORY, PolicyKeyspaceType.PERSISTENT],
    models=[SemanticModel.BGE_SMALL],
)
await connection.policy_grant(
    "alice", PolicyCapability.MANAGE_SEMANTIC, "catalog",
    keyspace="products", models=[SemanticModel.BGE_SMALL],
)
await connection.policy_view(owner="alice", store="catalog")
```

Use `policy_explain` to inspect an authorization decision and `policy_history` to audit
changes. Superowners can manage policies directly with `policy_grant`, `policy_revoke`,
`policy_deny`, and `policy_remove_denial`, or use `policy_validate`, `policy_plan`,
`policy_apply`, and `policy_export` with JSON or YAML documents.
