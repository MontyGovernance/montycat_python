from ..core.engine import Engine, send_data
from ..core.limit import Limit
from ..core.schema import Pointer
import asyncio
import orjson
import xxhash

def connect_engine_(cls: type, engine: Engine) -> None:
    cls.username = engine.username
    cls.password = engine.password
    cls.host = engine.host
    cls.port = engine.port
    cls.store_name = engine.store_name

def convert_custom_key(key: int | str) -> int:
    return str(xxhash.xxh32(str(key)).intdigest())

def convert_custom_keys(keys: list) -> list:
    return [convert_custom_key(key) for key in keys]

def convert_custom_keys_values(keys_values: dict) -> dict:
    return {convert_custom_key(key): value for key, value in keys_values.items()}

def modify_pointers(value: dict):
    if "pointers" in value:
        try:
            for k, v in value['pointers'].items():
                if v[1].isdigit():
                    value['pointers'][k] = [v[0], str(v[1])]
                else:
                    value['pointers'][k] = [v[0], convert_custom_key(v[1])]
            return value
        except:
            raise ValueError("Pointer should be a valid hash key or custom key")
    return value
    
        

def convert_to_binary_query(
        cls: type, 
        key: str = "", 
        search_criteria: dict = {}, 
        value: dict = {}, 
        expire_sec: int = 0, 
        bulk_values: list = [], 
        bulk_keys: list = [],
        bulk_keys_values: dict = {},
        with_pointers: bool = False
        ):
    
    if len(value) > 0:
        value = modify_pointers(value)

    if len(bulk_values) > 0:
        bulk_values = [str(modify_pointers(value)) for value in bulk_values]

    if len(bulk_keys_values) > 0:
        bulk_keys_values = {key: str(modify_pointers(value)) for key, value in bulk_keys_values.items()}
            
    return orjson.dumps({
        "request": cls.request,
        "username": cls.username,
        "password": cls.password,
        "store_namespace": cls.store_namespace,
        "store_name": cls.store_name,
        "persistent": cls.persistent,
        "distributed": cls.distributed,
        "limit_output": cls.limit_output,
        "key": str(key),
        "value": str(value).replace("True", "true").replace("False", "false"),
        "command": cls.command, 
        "expire": expire_sec,
        "bulk_values": [str(value).replace("True", "true").replace("False", "false") for value in bulk_values],
        "bulk_keys": bulk_keys,
        "bulk_keys_values": {key: str(value).replace("True", "true").replace("False", "false") for key, value in bulk_keys_values.items()},
        "blockchain": cls.blockchain,
        "search_criteria": str(search_criteria).replace("True", "true").replace("False", "false"),
        'with_pointers': with_pointers,
    })

def run_query(cls: type):
    query = convert_to_binary_query(cls)
    return asyncio.run(send_data(cls.host, cls.port, query))

def handle_limit(limit: list) -> dict:

    limit_class = Limit()

    if type(limit) == list:
        if len(limit) > 1:
            limit_class.start = limit[0]
            limit_class.stop = limit[1]
        elif len(limit) == 1:
            limit_class.stop = limit[0]

    return limit_class.return_limit()

def create_namespace_(cls: type) -> None:
    cls.command = "create_namespace"
    cls.request = "utils"
    return run_query(cls)

def drop_namespace_(cls: type) -> None:
    cls.command = "drop_namespace"
    cls.request = "utils"
    return run_query(cls)

def drop_store_(cls: type) -> None:
    cls.command = "drop_store"
    cls.request = "utils"
    return print('DROP', cls.store_name)

def show_store_properties_(cls: type) -> None:
    return print(
        f"Store Name: {cls.store_name}\n"
        f"Store Namespace: {cls.store_namespace}\n"
        f"Persistent: {cls.persistent}\n"
        f"Distributed: {cls.distributed}\n"
        f"Host: {cls.host}\n"
        f"Port: {cls.port}\n"
        f"Username: {cls.username}\n"
        f"Password: {cls.password}\n"
    )
