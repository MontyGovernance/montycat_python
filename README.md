Example

from montycat import Engine, Store, Schema, Pointer

connection = Engine(
    host="localhost",
    port=8080,
    username="admin",
    password="password",
    store="main"
)

class Departments(Store.InMemory):
    namespace = "departments"

class Managers(Store.InMemory):
    namespace = "managers"

Departments.connect_engine(connection)
Managers.connect_engine(connection)

class Department(Schema):
    name: str
    employees: int
    manager_pointer: Pointer
    another_manager_pointer: Pointer

class Manager(Schema):
    name: str

department = Department(
    name="Engineering", 
    employees=10, 
    manager_pointer=Pointer(
        Managers, "1820983982083707070768"
    ),
    another_manager_pointer=Pointer(
        Managers, "1820983982083707070768"
    )
).serialize()

Departments.insert_value(department)