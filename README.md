# 🐍 The official async Python client for Montycat — the self-hosted NoSQL + vector database with built-in AI semantic search for RAG & AI agents, powered by Rust.

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/montycat?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/montycat)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/montycat.svg)](https://pypi.org/project/montycat/)
[![Python Version](https://img.shields.io/pypi/pyversions/montycat)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/maintained-yes-brightgreen.svg)]()

## What is Montycat?

Montycat is a **self-hosted NoSQL + vector database** — one Rust-powered engine with semantic search built in, so you get **RAG, AI-agent memory, and vector search** without bolting a separate vector DB (and its per-query bill) onto your stack. No cloud lock-in, no ops headache — decentralized by nature, ultra-fast, and natively async.
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

## 👉 Install the Engine: https://montygovernance.com

## Montycat for Python?

This is the official Python client, built to bring Montycat’s next-generation Data Mesh architecture directly into your Python applications. This client empowers developers to seamlessly manage and query their data while leveraging the unparalleled flexibility and scalability offered by NoSQL databases within a decentralized data ownership paradigm
Forget ORM hell, clunky SQL syntax, or blocking I/O.
With Montycat, data feels alive — reactive, structured, and fast enough to keep up with your imagination.

## 🔍 Example Use Cases

- Real-time dashboards and analytics
- Async ETL pipelines with real-time awareness and processing
- Microservice data stores
- Event-driven data systems
- Collaborative data products in a Mesh architecture

## Installation

You can install Python client for Montycat using `pip`:

```bash
pip install montycat
```

## Quick Start

```python
from montycat import Engine, Keyspace, Schema
import asyncio

# setup connection

connection = Engine(
    host="127.0.0.1",
    port=21210,
    username="USER",
    password="12345",
    store="Departments",
)

class Sales(Keyspace.Persistent):
    keyspace = "Sales"

class Production(Keyspace.InMemory):
    keyspace = "Production"

Sales.connect_engine(connection)
Production.connect_engine(connection)

# create store and keyspaces using runtime migration

async def setup_keyspaces():
    await Production.create_keyspace()
    await Sales.create_keyspace()

asyncio.run(setup_keyspaces())

# create schemas and enforce them on the database side (optional)

class SalesSchema(Schema):
    product: str
    amount: int

class ProductionSchema(Schema):
    items: list
    work_order: str | None

async def migrate_schemas():
    await Production.enforce_schema(ProductionSchema)
    await Sales.enforce_schema(SalesSchema)

asyncio.run(migrate_schemas())

# run first queries

sales = SalesSchema(
    product = "Product1",
    amount = 12
).serialize()

asyncio.run(Sales.insert_value(sales))

items_ordered = ProductionSchema(
    items = ["Product1"],
    work_order = "WO 000012"
).serialize()

asyncio.run(Production.insert_value(items_ordered))

# verify

asyncio.run(Sales.lookup_values_where(schema=SalesSchema, key_included=True))
asyncio.run(Production.lookup_keys_where(work_order="WO 000012"))

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
> Get it the way that suits you — pull the `montycat-semantic` **Docker image**, download
> the prebuilt **package**, or install from the **apt repository**. The Python client API
> is identical either way; just point it at a `montycat-semantic` server (semantic search
> is enabled by default there, using the `bge-small` model).

Enable it once, DB-wide, on the engine. The chosen embedding model is downloaded on demand
on first enable, and every keyspace is embedded in the background as data is written.

```python
# Turn semantic search on for the whole database (model downloaded on first use).
# model: 'minilm' | 'bge-small' (default) | 'bge-base' | 'e5-small'
asyncio.run(connection.enable_semantic_search())

# Rank stored items by meaning — two flavors:
#   get_values → each hit is {key, score, value}
#   get_keys   → each hit is {key, score} (lighter; fetch a page later with get_bulk)
asyncio.run(Sales.semantic_search_get_values("wireless headphones", limit=5))
asyncio.run(Sales.semantic_search_get_keys("wireless headphones", limit=5))

# Optionally drop weak matches by cosine similarity (range [-1, 1]).
asyncio.run(Sales.semantic_search_get_keys("wireless headphones", limit=5, min_score=0.35))

# Turn it off (vectors are kept so re-enabling resumes instantly;
# pass drop_vectors=True to also clear stored vectors).
asyncio.run(connection.disable_semantic_search())
```

