from ..core.engine import Engine, send_data
from ..core.limit import Limit
from ..core.schema import Timestamp
import asyncio
import orjson
import xxhash
from typing import Union

def connect_engine_(cls: type, engine: Engine) -> None:
    """
    Establishes a connection to the specified engine, setting the necessary connection details.
    
    Args:
        cls (type): The class that will hold the connection information.
        engine (Engine): An instance of the Engine class containing connection details.
    
    This function updates the class with connection attributes such as username, 
    password, host, port, and store name.
    """
    cls.username = engine.username
    cls.password = engine.password
    cls.host = engine.host
    cls.port = engine.port
    cls.store = engine.store

def convert_custom_key(key: Union[int, str]) -> int:
    """
    Converts a custom key (either an integer or string) into a hash value using xxHash.
    
    Args:
        key (int | str): The custom key to be hashed.
    
    Returns:
        int: The xxHash digest of the provided key as an integer.
    
    This function ensures that any input key, whether integer or string, is consistently 
    hashed into a unique integer for use as a custom key in further queries.
    """
    return str(xxhash.xxh32(str(key)).intdigest())

def convert_custom_keys(keys: list) -> list:
    """
    Converts a list of custom keys into their hashed equivalents.
    
    Args:
        keys (list): A list of custom keys to be hashed.
    
    Returns:
        list: A list of hashed keys as integers.
    
    This function maps over the provided list of keys and applies `convert_custom_key` 
    to each one to ensure they are converted to hashed integers.
    """
    return [convert_custom_key(key) for key in keys]

def convert_custom_keys_values(keys_values: dict) -> dict:
    """
    Converts a dictionary of custom keys and their corresponding values into a new 
    dictionary with hashed keys.
    
    Args:
        keys_values (dict): A dictionary where the keys are custom keys (either 
                             integers or strings) and the values are associated values.
    
    Returns:
        dict: A dictionary where the custom keys have been hashed into integers.
    
    This function maps over the dictionary and applies `convert_custom_key` to each 
    key while leaving the corresponding value unchanged.
    """
    return {convert_custom_key(key): value for key, value in keys_values.items()}

def modify_pointers(value: dict):
    """
    Processes and modifies the dictionary by converting all 'pointers' (Pointer type) entries into 
    a consolidated 'pointers' dictionary and all 'timestamps' (TImestamp type) entries into a 
    'timestamps' dictionary. The function validates that each pointer is in the 
    correct format, and ensures that timestamps are valid strings.
    
    Args:
        value (dict): The dictionary that may contain multiple fields
    
    Returns:
        dict: The modified dictionary containing two additional fields:
            - 'pointers': A dictionary of all the '_pointer' fields converted to a structured format.
            - 'timestamps': A dictionary of all the '_timestamp' fields stored as strings.
    
    Raises:
        ValueError: If a '_pointer' entry is not a list of two elements (namespace, key), 
                    or if a '_timestamp' value is not a string.
    
    This function ensures that all pointer values are correctly processed and stored in the 
    'pointers' field, and all timestamp values are correctly stored in the 'timestamps' field.
    """
    try:
        for key in list(value.keys()):
            if key == "pointers":
                for k, v in value[key].items():
                    namespace, raw_key = v
                    if isinstance(raw_key, str) and raw_key.isdigit() or isinstance(raw_key, int):
                        processed_key = str(raw_key)
                    else:
                        processed_key = convert_custom_key(raw_key)
                    value[key][k] = [namespace, processed_key]

    except Exception as e:
        raise ValueError(f"Error processing pointers: {e}")
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
        ) -> bytes:
    """
    Converts the given parameters into a binary query format suitable for transmission.
    
    Args:
        cls (type): The class for which the query is being generated. This includes 
                    connection details and command settings.
        key (str): A single key to be included in the query (default is empty string).
        search_criteria (dict): A dictionary of search filters to be included (default is empty dict).
        value (dict): The value associated with the key for the query (default is empty dict).
        expire_sec (int): The expiration time for the value in seconds (default is 0).
        bulk_values (list): A list of values for bulk operations (default is empty list).
        bulk_keys (list): A list of keys for bulk operations (default is empty list).
        bulk_keys_values (dict): A dictionary of keys and values for bulk operations (default is empty dict).
        with_pointers (bool): Flag to include pointers in the query (default is False).
    
    Returns:
        bytes: A binary-encoded query in the appropriate format.
    
    This function prepares all input parameters and structures them into a query, 
    ensuring that any pointers or custom key conversions are handled. The query is 
    then serialized into a binary format using `orjson`.
    """
    
    if len(value) > 0:
        value = modify_pointers(value)

    if len(bulk_values) > 0:
        bulk_values = [str(modify_pointers(value)) for value in bulk_values]

    if len(bulk_keys_values) > 0:
        bulk_keys_values = {key: str(modify_pointers(value)) for key, value in bulk_keys_values.items()}

    if 'schema' in value:
        cls.schema = value['schema']
        del value['schema']
    else:
        cls.schema = None
            
    return orjson.dumps({
        "schema": cls.schema,
        "request": cls.request,
        "username": cls.username,
        "password": cls.password,
        "namespace": cls.namespace,
        "store": cls.store,
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

def run_query(cls: type) -> None:
    """
    Executes the query built using the provided class and parameters.
    
    Args:
        cls (type): The class containing connection details and settings for the query.
    
    This function generates a binary query based on the class settings and sends 
    it using the `send_data` function asynchronously.
    """
    query = convert_to_binary_query(cls)
    return asyncio.run(send_data(cls.host, cls.port, query))

def handle_timestamps_schema(search_criteria: dict) -> dict:
    for key, value in search_criteria.items():
        if isinstance(value, Timestamp.before) or isinstance(value, Timestamp.after) or isinstance(value, Timestamp.range) or isinstance(value, Timestamp):
            search_criteria[key] = value.serialize()
        if key == "schema":
            search_criteria[key] = str(value) #by default schema is a class name
    return search_criteria

def handle_limit(limit: Union[list, int]) -> dict:
    """
    Processes and returns pagination limits for queries based on the provided input.
    
    Args:
        limit (list | int): The pagination limit, either a list with two values (start, stop) 
                             or an integer representing the stop limit.
    
    Returns:
        dict: A dictionary containing the pagination limits (`start` and `stop`).
    
    Raises:
        ValueError: If the provided limit is neither a valid list nor a valid integer.
    
    This function ensures the pagination limits are properly structured and returns
    them in a dictionary format suitable for query processing.
    """
    # Initialize the Limit object with default values
    limit_instance = Limit()

    if isinstance(limit, list):
        if len(limit) == 2:
            # Set both start and stop from the list
            limit_instance.start, limit_instance.stop = limit
        elif len(limit) == 0:
            # No limits provided, set both to 0
            limit_instance.start, limit_instance.stop = 0, 0
        else:
            # Invalid list length
            raise ValueError("Limit should be a list with exactly two values (start, stop).")
    
    elif isinstance(limit, int):
        if limit >= 0:
            # If the limit is a positive integer, set it as the stop value
            limit_instance.start, limit_instance.stop = 0, limit
        else:
            # Invalid integer value
            raise ValueError("Limit should be an integer greater than 0.")
    
    else:
        # Invalid type
        raise ValueError("Limit should be either a list (with two values) or a positive integer.")

    # Return the pagination limit as a dictionary
    return limit_instance.return_limit()

def create_namespace_(cls: type) -> None:
    """
    Creates a new namespace using the provided class settings.
    
    Args:
        cls (type): The class containing the configuration details for the namespace creation.
    
    This function sets the class to perform a "create_namespace" command and sends 
    a query to execute it.
    """
    cls.command = "create_namespace"
    cls.request = "utils"
    return run_query(cls)

def drop_namespace_(cls: type) -> None:
    """
    Drops the namespace associated with the provided class settings.
    
    Args:
        cls (type): The class containing the configuration details for the namespace drop.
    
    This function sets the class to perform a "drop_namespace" command and sends 
    a query to execute it.
    """
    cls.command = "drop_namespace"
    cls.request = "utils"
    return run_query(cls)

def drop_store_(cls: type) -> None:
    """
    Drops the store associated with the provided class settings.
    
    Args:
        cls (type): The class containing the configuration details for the store drop.
    
    This function sets the class to perform a "drop_store" command and prints 
    a message that the store is being dropped.
    """
    cls.command = "drop_store"
    cls.request = "utils"
    return print('DROP', cls.store)

def show_store_properties_(cls: type) -> None:
    """
    Displays the properties of the store associated with the provided class settings.
    
    Args:
        cls (type): The class containing the configuration details for the store.
    
    This function sets the class to perform a "show_properties" command and sends 
    a query to retrieve the store's properties.
    """
    return print(
        f"Store Name: {cls.store}\n"
        f"Store Namespace: {cls.storespace}\n"
        f"Persistent: {cls.persistent}\n"
        f"Distributed: {cls.distributed}\n"
        f"Host: {cls.host}\n"
        f"Port: {cls.port}\n"
        f"Username: {cls.username}\n"
        f"Password: {cls.password}\n"
    )
