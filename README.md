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
hits = await Sales.semantic_search_get_values("something to listen to music without wires", limit=5)
# → [{key, score, value: {"name": "Wireless Headphones"}}, ...]  (matched by meaning, not keywords)
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
  -v montycat_data:/app/.montycat \
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
#   get_values → each hit is {key, score, value}
#   get_keys   → each hit is {key, score} (lighter; fetch a page later with get_bulk)
hits = await Sales.semantic_search_get_values("something to listen to music without wires", limit=5)
keys = await Sales.semantic_search_get_keys("something to listen to music without wires", limit=5)

# Optionally drop weak matches by cosine similarity (range [-1, 1]).
strong = await Sales.semantic_search_get_keys("something to listen to music without wires", limit=5, min_score=0.35)

# Control the DB-wide switch (optional — it's already on):
# switch the embedding model: 'minilm' | 'bge-small' (default) | 'bge-base' | 'e5-small'
await connection.enable_semantic_search(model="bge-base")

# turn it off (vectors are kept so re-enabling resumes instantly;
# pass drop_vectors=True to also clear stored vectors)
await connection.disable_semantic_search()
```

## 🔗 Links

- 🌐 **Website & Docs** — https://montygovernance.com
- 📦 **PyPI** — https://pypi.org/project/montycat/
- 🐳 **Docker Hub** — https://hub.docker.com/r/montygovernance/montycat
- 💻 **Source** — https://github.com/MontyGovernance/montycat_python

## ❓ FAQ

- **Is Montycat a vector database or a NoSQL database?** Both — one engine. Store records and query them by *meaning* (vector / semantic search) or by key/schema, without running two systems.
- **Do I need OpenAI or an embedding API?** No. Embeddings run on-device in the `montycat-semantic` server. No API keys, no per-query bill, no data egress.
- **Is it a Pinecone / Weaviate / Chroma / Qdrant alternative?** Yes — self-hosted and open-source, with a NoSQL store built in.
- **Which Python versions?** 3.9+ — fully async (`asyncio`).


