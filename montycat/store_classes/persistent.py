from ..core.engine import send_data
from ..store_functions.store_generic_functions import convert_to_binary_query, convert_custom_key, handle_limit
from typing import Union
import orjson

class persistent_kv:

    persistent: bool = True
    cache: Union[int, None] = None
    compression: bool = False

    @classmethod
    async def _run_query(cls, query: str):
        return await send_data(cls.host, cls.port, query)

    @classmethod
    async def insert_custom_key(cls, custom_key: str):
        """
        Args:
            custom_key: A custom key to insert into the store. This key can be used to retrieve the value later.
        Returns:
            True if the insert operation was successful. Class 'str' if the insert operation failed.
        """
        if not custom_key:
            raise ValueError("No custom key provided for insertion.")
        
        custom_key_converted = convert_custom_key(custom_key)
        cls.command = "insert_custom_key"

        query = convert_to_binary_query(cls, key=custom_key_converted)
        return await cls._run_query(query)
    
    @classmethod
    async def insert_custom_key_value(cls, custom_key: str, value: dict):
        """
        Args:
            custom_key: A custom key to insert into the store. This key can be used to retrieve the value later.
            value: A Python class / dict to insert into the store.
        Returns:
            True if the insert operation was successful. Class 'str' if the insert operation failed.
            
        """
        if not value:
            raise ValueError("No value provided for insertion.")
        if not custom_key:
            raise ValueError("No custom key provided for insertion.")

        custom_key_converted = convert_custom_key(custom_key)
        cls.command = "insert_custom_key_value"

        query = convert_to_binary_query(cls, key=custom_key_converted, value=value)
        return await cls._run_query(query)
    
    @classmethod
    async def insert_value(cls, value: dict):
        """
        Args:
            value: A Python class / dict to insert into the store.
        Returns:
            Key number if the insert operation was successful. Class 'str' if the insert operation failed.
        """
        if not value:
            raise ValueError("No value provided for insertion.")
        
        cls.command = "insert_value"

        query = convert_to_binary_query(cls, value=value)
        return await cls._run_query(query)
    
    @classmethod
    async def update_value(cls, key: Union[str, None] = None, custom_key: Union[str, None] = None, **filters):
        """
        Update the value associated with a given key in the store. If a custom key is provided,
        it will be converted to the appropriate format before updating.

        Args:
            key (int | str, optional): The key whose associated value needs to be updated. 
                                       This can either be an integer or a string. Default is an empty string,
                                       which will be ignored if custom_key is provided.
            custom_key (str, optional): The custom key whose associated value needs to be updated. 
                                        Default is an empty string.
            filters (dict): A dictionary of field-value pairs that need to be updated in the store.

        Returns:
            bool | str: Returns a boolean indicating success (True) or failure (False),
                        or a string message if the update was unsuccessful.
        """

        if custom_key and len(custom_key) > 0:
            key = convert_custom_key(custom_key)

        if not filters:
            raise ValueError("No filters provided")
        if not key:
            raise ValueError("No key provided")
        
        cls.command = "update_value"

        query = convert_to_binary_query(cls, key=key, value=filters)  # Convert the key and filters into a binary query format
        return await cls._run_query(query)  # Run the query and return the result

    @classmethod
    async def insert_bulk(cls, bulk_values: list):
        """       
        Args:
            bulk_values: A list of Python objects to insert into the store.            
        Returns:
            True if the bulk insert operation was successful.
            List of values that were not inserted.
        """

        if not bulk_values:
            raise ValueError("No values provided for bulk insertion.")
        
        cls.command = "insert_bulk"
        query = convert_to_binary_query(cls, bulk_values=bulk_values)
        return await cls._run_query(query)
    
    @classmethod
    async def get_keys(cls, limit: Union[list, int] = []):
        """
        Args:
            Limit: A list of two integers that determine the range of keys to retrieve.
            Example: limit = [10, 20] will retrieve keys 10 to 20.
        Returns:
            A list of keys in the store. Class 'str' if the get operation failed.
        """
        cls.limit_output = handle_limit(limit)
        cls.command = "get_keys"

        query = convert_to_binary_query(cls)
        return await cls._run_query(query)
    
    @classmethod  
    async def create_keyspace(cls):

        query = orjson.dumps({
            "raw": ["create-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "y", "cache", cls.cache if cls.cache else "0", "compression", "y" if cls.compression else "n"],
            "credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)
    
    @classmethod
    async def update_cache_and_compression(cls):
        """
        Updates the cache size and compression settings for the current store.

        Returns:
            bool
        """

        query = orjson.dumps({
            "raw": ['update-cache-compression', "store", cls.store, "keyspace", cls.keyspace, "persistent", "y", "cache", cls.cache if cls.cache else "0", "compression", "y" if cls.compression else "n"],
            "credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)