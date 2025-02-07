from ..core.engine import Engine
from ..core.tools import Timestamp, Pointer, Limit
import orjson
import xxhash
from typing import Type, Dict, List, Union, Any

def connect_engine_inner(cls: type, engine: Engine) -> None:
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

def handle_pointers_for_update(value: dict) -> dict:
    for k, v in value.items():
        print(v)
        if isinstance(v, Pointer):
            value[k] = v.serialize()
    return value

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

def normalize_bools(s: str) -> str:
    return s.replace("True", "true").replace("False", "false")

def convert_to_binary_query(
    cls: Type,
    key: str = "",
    search_criteria: Dict[str, Any] = None,
    value: Dict[str, Any] = None,
    expire_sec: int = 0,
    bulk_values: List[Dict[str, Any]] = None,
    bulk_keys: List[str] = None,
    bulk_keys_values: Dict[str, Any] = None,
    with_pointers: bool = False
) -> bytes:
    """
    Converts parameters into a binary query format suitable for transmission.
    
    Args:
        cls: Query class containing connection details and command settings
        key: Single key for the query
        search_criteria: Search filters dictionary
        value: Key-associated value dictionary
        expire_sec: Value expiration time in seconds
        bulk_values: List of values for bulk operations
        bulk_keys: List of keys for bulk operations
        bulk_keys_values: Dictionary of keys and values for bulk operations
        with_pointers: Flag to include pointers
    
    Returns:
        bytes: Binary-encoded query in appropriate format
        
    Raises:
        ValueError: If bulk values contain multiple schemas
    """
    # Initialize with empty defaults
    search_criteria = search_criteria or {}
    value = value or {}
    bulk_values = bulk_values or []
    bulk_keys = bulk_keys or []
    bulk_keys_values = bulk_keys_values or {}
    
    # Process single value
    if value:
        value = modify_pointers(value)
    
    # Process bulk values and handle schema validation
    if bulk_values:
        # Extract schemas in single pass
        schemas = []
        for item in bulk_values:
            if 'schema' in item:
                schemas.extend([item['schema']])
            else:
                schemas.extend([None])
        
        # Validate schemas
        unique_schemas = set(schemas)
        if len(unique_schemas) > 1:
            raise ValueError("Bulk values should fit only one schema")
        
        # Set schema and clean bulk values
        cls.schema = schemas[0] if schemas else None
        bulk_values = [
            str(modify_pointers({k: v for k, v in item.items() if k != 'schema'}))
            for item in bulk_values
        ]
    
    # Process bulk key-values if present
    if bulk_keys_values:
        bulk_keys_values = {
            k: str(modify_pointers(v)) 
            for k, v in bulk_keys_values.items()
        }

    if bulk_keys:
        bulk_keys = [str(k) for k in bulk_keys]
    
    # Handle schema from single value after bulk processing
    if 'schema' in value:
        cls.schema = value.pop('schema')
    
    # Construct query dictionary with normalized values
    query_dict = {
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
        "value": normalize_bools(str(value)),
        "command": cls.command,
        "expire": expire_sec,
        "bulk_values": [normalize_bools(v) for v in bulk_values],
        "bulk_keys": bulk_keys,
        "bulk_keys_values": {k: normalize_bools(str(v)) for k, v in bulk_keys_values.items()},
        "blockchain": cls.blockchain,
        "search_criteria": normalize_bools(str(search_criteria)),
        "with_pointers": with_pointers,
    }
        
    return orjson.dumps(query_dict)

def handle_timestamps(search_criteria: dict) -> dict:
    for key, value in search_criteria.items():
        if isinstance(value, Timestamp.before) or isinstance(value, Timestamp.after) or isinstance(value, Timestamp.range) or isinstance(value, Timestamp):
            search_criteria[key] = value.serialize()
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
