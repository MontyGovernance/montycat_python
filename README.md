# MontyCat

MontyCat is a Python client for **Montycat**, a high-performance, distributed NoSQL store designed with a cutting-edge Data Mesh architecture. This client empowers developers to seamlessly manage and query their data while leveraging the unparalleled flexibility and scalability offered by NoSQL databases within a decentralized data ownership paradigm.

## Key Features

- ⚡ **High Performance:** Harnesses MontyCat's advanced architecture for lightning-fast read and write operations.
- 🌐 **Distributed Architecture:** Effortlessly connects to a distributed NoSQL database, enabling dynamic horizontal scalability across diverse data domains.
- 🗂️ **Data Mesh Design:** Empowers cross-functional teams to own, manage, and serve their own data, enhancing collaboration and eliminating bottlenecks.
- 🔄 **Asynchronous Support:** Built on `asyncio` for ultra-responsive, non-blocking operations, enabling high concurrency and real-time data processing.
- 🧩 **Meshing and Sharding:** Efficiently orchestrates data across multiple nodes with robust support for data meshing and sharding, optimizing resource utilization.
- 🛡️ **Memory Safety:** Implements state-of-the-art memory management practices, minimizing the risk of memory-related issues and enhancing stability.
- 📊 **Smart Data Governance:** Integrates intelligent governance features to ensure data quality and compliance across the distributed architecture.
- 🤝 **Seamless Integration:** Offers a simple and intuitive API for effortless integration with Python applications, reducing time-to-value.
- 📚 **Robust Documentation:** Comprehensive and user-friendly documentation to accelerate onboarding and maximize productivity.

## Installation

You can install Python client for Montycat using `pip`:

```bash
pip install montycat

```python
#models.py
from montycat import Engine, Store, Schema

connection = Engine(
    host="127.0.0.1",
    port=21210,
    username="admin",
    password="password",
    store="main"
)

class Departments(Store.Persistent):
    keyspace = "departments"

class Managers(Store.InMemory):
    keyspace = "managers"

Departments.connect_engine(connection)
Managers.connect_engine(connection)

#migrations.py -- execute separately 
from models.py import Departments, Managers

Departments.create_keyspace()
Managers.create_keyspace()

class Department(Schema):
    name: str
    employees: int

class Manager(Schema):
    name: str
    age: int

#***.py
from models.py import Departments, Managers, Department, Manager

department = Department(
    name="Sales",
    employees=10
).serialize()

manager = Manager(
    name="John Doe",
    age=46
).serialize()

#put into async function
res1 = await Departments.insert_custom_key_value(custom_key="Sales", value=department) 
#{'success': True, 'payload': 192893812831283134324}
res2 = await Managers.insert_value(value=manager)
#{'success': True, 'payload': 192893812831283134324}
res3 = await Departments.get_value(custom_key="Sales")
#{'success': True, 'payload': {'name': 'Sales', 'employees': 10}}
res4 = await Managers.lookup_values_where(age=46)
#{'success': True, 'payload': [{'name': 'John Doe', 'age': 46}]}
