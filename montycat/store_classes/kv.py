from ..core.engine import Engine, send_data
from ..core.schema import Pointer
from ..store_functions.store_generic_functions import handle_limit, connect_engine_, create_namespace_, drop_namespace_, drop_store_, show_store_properties_, convert_to_binary_query, convert_custom_key, convert_custom_keys, convert_custom_keys_values
import asyncio

class generic_kv:
    store_name: str = ""
    command: str = ""
    persistent: bool = False
    request: str = "store"
    blockchain: bool = False
    limit_output: dict = {}

    @classmethod
    def _run_query(cls, query: str):
        return asyncio.run(send_data(cls.host, cls.port, query))
    
    @classmethod
    def insert_custom_key(cls, custom_key: str, expire_sec: int = 0):
        """       
        Args:
            custom_key: A custom key to insert into the store. This key can be used to retrieve the value later.
            expire_sec: The number of seconds before the inserted value expires.
        Returns:
            True if the insert operation was successful. Class 'str' if the insert operation failed.
        """
        custom_key_converted = convert_custom_key(custom_key)
        cls.command = "insert_custom_key"
        query = convert_to_binary_query(cls, key=custom_key_converted, expire_sec=expire_sec)
        return cls._run_query(query)
    
    @classmethod
    def insert_custom_key_value(cls, custom_key: str, value: dict, expire_sec: int = 0):
        """       
        Args:
            custom_key: A custom key to insert into the store. This key can be used to retrieve the value later.
            value: A Python class / dict to insert into the store.
            expire_sec: The number of seconds before the inserted value expires.
        Returns:
            True if the insert operation was successful. Class 'str' if the insert operation failed.

            custom_key = "some_value"
            value = {
                "operation": 1,
                "amount": 4500.0
            }
            
        """
        custom_key_converted = convert_custom_key(custom_key)
        cls.command = "insert_custom_key_value"
        query = convert_to_binary_query(cls, key=custom_key_converted, value=value, expire_sec=expire_sec)
        return cls._run_query(query)
    
    @classmethod
    def insert_value(cls, value: dict, expire_sec: int = 0):
        """       
        Args:
            value: A Python class / dict to insert into the store.
            expire_sec: The number of seconds before the inserted value expires.
        Returns:
            Key number if the insert operation was successful. Class 'str' if the insert operation failed.
        """
        cls.command = "insert_value"
        query = convert_to_binary_query(cls, value=value, expire_sec=expire_sec)
        return cls._run_query(query)
    
    @classmethod
    def get_value(cls, key: int | str = "", custom_key: str = "", with_pointers: bool = False):

        """
        Args:
            key: The key number of the value to retrieve.
            custom_key: The custom key of the value to retrieve.
            with_pointers: A boolean value that determines whether to include pointers (foreign values) in the output.
        Returns:
            The value associated with the key or custom key. Class 'str' if the get operation failed.
        """
        if len(custom_key) > 0:
            key = convert_custom_key(custom_key)
        cls.command = "get_value"
        query = convert_to_binary_query(cls, key=key, with_pointers=with_pointers)
        return cls._run_query(query)
        
    @classmethod
    def get_keys(cls, limit: list = []):
        """
        Args:
            Limit: A list of two integers that determine the range of keys to retrieve.
            Example: limit = [10, 20] will retrieve keys 10 to 20.
        Returns:
            A list of keys in the store. Class 'str' if the get operation failed.
        """
        lim = handle_limit(limit)
        cls.command = "get_keys"
        cls.limit_output = lim
        query = convert_to_binary_query(cls)
        return cls._run_query(query)
    
    @classmethod
    def delete_key(cls, key: int | str = "", custom_key: str = ""):

        if len(custom_key) > 0:
            key = convert_custom_key(custom_key)

        cls.command = "delete_key"
        query = convert_to_binary_query(cls, key=key)
        return cls._run_query(query)

    @classmethod
    def update_value(cls, key: int | str = "", custom_key: str = "", **filters):

        if len(custom_key) > 0:
            key = convert_custom_key(custom_key)

        cls.command = "update_value"
        query = convert_to_binary_query(cls, key=key, value=filters)
        print(query)
        return cls._run_query(query)
    
    @classmethod
    def insert_bulk(cls, bulk_values: list, expire_sec: int = 0):
        # bulk_values = [str(item) for item in bulk if len(bulk) > 0]
        """       
        Args:
            bulk_values: A list of Python objects to insert into the store.
            expire_sec: The number of seconds before the inserted values expire.
            
        Returns:
            True if the bulk insert operation was successful.
            List of values that were not inserted.
        """
        cls.command = "insert_bulk"
        query = convert_to_binary_query(cls, bulk_values=bulk_values, expire_sec=expire_sec)
        return cls._run_query(query)
    
    @classmethod
    def delete_bulk(cls, bulk_keys: list = [], bulk_custom_keys: list = []):

        if len(bulk_custom_keys) > 0:
            bulk_custom_keys = convert_custom_keys(bulk_custom_keys)
            bulk_keys += bulk_custom_keys

        cls.command = "delete_bulk"
        query = convert_to_binary_query(cls, bulk_keys=bulk_keys)
        return cls._run_query(query)
    
    @classmethod
    def get_bulk(cls, bulk_keys: list = [], bulk_custom_keys: list = [], limit: list = [], with_pointers: bool = False):

        lim = handle_limit(limit)

        if len(bulk_custom_keys) > 0:
            bulk_custom_keys = convert_custom_keys(bulk_custom_keys)
            bulk_keys += bulk_custom_keys
        
        cls.command = "get_bulk"
        cls.limit_output = lim
        query = convert_to_binary_query(cls, bulk_keys=bulk_keys, with_pointers=with_pointers)
        return cls._run_query(query)
    
    @classmethod
    def update_bulk(cls, bulk_keys_values: dict = {}, bulk_custom_keys_values: dict = {}):

        if len(bulk_custom_keys_values) > 0:
            bulk_custom_keys_values = convert_custom_keys_values(bulk_custom_keys_values)
            bulk_keys_values = bulk_keys_values | bulk_custom_keys_values

            # print(bulk_keys_values)

        cls.command = "update_bulk"
        query = convert_to_binary_query(cls, bulk_keys_values=bulk_keys_values)
        return cls._run_query(query)
    
    @classmethod
    def lookup_keys_where(cls, limit: int = 0, **filters):

        lim = handle_limit(limit)

        cls.command = "lookup_keys"
        cls.limit_output = lim
        query = convert_to_binary_query(cls, search_criteria=filters)
        return cls._run_query(query)
    
    @classmethod
    def lookup_values_where(cls, limit = 0, with_pointers: bool = False, **filters):

        lim = handle_limit(limit)

        cls.command = "lookup_values"
        cls.limit_output = lim
        query = convert_to_binary_query(cls, search_criteria=filters, with_pointers=with_pointers)
        return cls._run_query(query)
    
    @classmethod
    def to_blockchain(cls, key: int):
        cls.command = "blockchain"
        cls.persistent = True
        cls.blockchain = True
        query = convert_to_binary_query(cls, key=key)
        return cls._run_query(query)
    
    @classmethod
    def connect_engine(cls, engine: Engine) -> None:
        connect_engine_(cls, engine)

    @classmethod  
    def create_namespace(cls):
        return create_namespace_(cls)
    
    @classmethod  
    def drop_namespace(cls):
        return drop_namespace_(cls)
    
    @classmethod
    def drop_store(cls):
        drop_store_(cls)

    @classmethod
    def show_store_properties(cls):
        show_store_properties_(cls)

