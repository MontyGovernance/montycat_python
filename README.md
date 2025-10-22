# 🐍 The official async Python client for Montycat — the Rust-powered NoSQL database built for the Data Mesh era.

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/montycat?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/montycat)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/montycat.svg)](https://pypi.org/project/montycat/)
[![Python Version](https://img.shields.io/pypi/pyversions/montycat)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/maintained-yes-brightgreen.svg)]()

## What is Montycat?

Montycat is a Rust-powered NoSQL engine designed for the future of data — decentralized by nature, ultra-fast, and natively async.
## 🧠 Why Montycat?

- ⚡ Blazing Speed — Powered by the Montycat Engine written in Rust, built for microsecond-level read/write performance.
- 🌀 Async-First Design — Fully asynchronous, built on asyncio. Perfect for APIs, pipelines, and real-time apps.
- 💾 Hybrid Storage — In-memory for raw speed or persistent for durability — or mix both in one engine.
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
    work_order: str

async def migrate_schemas():
    await Production.enforce_schema()
    await Sales.enforce_schema()

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

