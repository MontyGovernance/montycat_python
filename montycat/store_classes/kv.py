from ..core.engine import Engine, send_data
from ..store_functions.store_generic_functions import \
    handle_limit, convert_to_binary_query, convert_custom_key, \
    convert_custom_keys, convert_custom_keys_values
from typing import Union
import orjson

class inmemory_kv:
    persistent: bool = False

    @classmethod
    async def _run_query(cls, query: str):
        return await send_data(cls.host, cls.port, query)
    
    @classmethod
    async def do_snaphots_for_keyspace(cls):
        """
        Returns:
            True if the snapshot operation was successful. Class 'str' if the snapshot operation failed.
        """
        
        # if cls.persistent:
        #     raise ValueError("Cannot take snapshots on a persistent store.")

        query = orjson.dumps({
            "raw": ["do-snapshots-for-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "n"],
            "superowner_credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)
    
    @classmethod
    async def clean_snapshots_for_keyspace(cls):
        """
        Returns:
            True if the snapshot operation was successful. Class 'str' if the snapshot operation failed.
        """
        
        # if cls.persistent:
        #     raise ValueError("Cannot clean snapshots on a persistent store.")

        query = orjson.dumps({
            "raw": ["clean-snapshots-for-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "n"],
            "superowner_credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)
    
    async def stop_snapshots_for_keyspace(cls):
        """
        Returns:
            True if the snapshot operation was successful. Class 'str' if the snapshot operation failed.
        """
        
        # if cls.persistent:
        #     raise ValueError("Cannot stop snapshots on a persistent store.")

        query = orjson.dumps({
            "raw": ["stop-snapshots-for-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "n"],
            "superowner_credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)

class generic_kv:
    store: str = ""
    command: str = ""
    # persistent: bool = False
    limit_output: dict = {}
    schema = None

    @classmethod
    async def _run_query(cls, query: str):
        return await send_data(cls.host, cls.port, query)
    
    # @classmethod
    # async def do_snaphots_for_keyspace(cls):
    #     """
    #     Returns:
    #         True if the snapshot operation was successful. Class 'str' if the snapshot operation failed.
    #     """
        
    #     if cls.persistent:
    #         raise ValueError("Cannot take snapshots on a persistent store.")

    #     query = orjson.dumps({
    #         "raw": ["do-snapshots-for-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "n"],
    #         "superowner_credentials": [cls.username, cls.password]
    #     })

    #     return await cls._run_query(query)
    
    # @classmethod
    # async def clean_snapshots_for_keyspace(cls):
    #     """
    #     Returns:
    #         True if the snapshot operation was successful. Class 'str' if the snapshot operation failed.
    #     """
        
    #     if cls.persistent:
    #         raise ValueError("Cannot clean snapshots on a persistent store.")

    #     query = orjson.dumps({
    #         "raw": ["clean-snapshots-for-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "n"],
    #         "superowner_credentials": [cls.username, cls.password]
    #     })

    #     return await cls._run_query(query)
    
    # async def stop_snapshots_for_keyspace(cls):
    #     """
    #     Returns:
    #         True if the snapshot operation was successful. Class 'str' if the snapshot operation failed.
    #     """
        
    #     if cls.persistent:
    #         raise ValueError("Cannot stop snapshots on a persistent store.")

    #     query = orjson.dumps({
    #         "raw": ["stop-snapshots-for-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "n"],
    #         "superowner_credentials": [cls.username, cls.password]
    #     })

    #     return await cls._run_query(query)
    
    @classmethod
    async def insert_custom_key(cls, custom_key: str, expire_sec: int = 0):
        """
        Args:
            custom_key: A custom key to insert into the store. This key can be used to retrieve the value later.
            expire_sec: The number of seconds before the inserted value expires.
        Returns:
            True if the insert operation was successful. Class 'str' if the insert operation failed.
        """
        if not custom_key:
            raise ValueError("No custom key provided for insertion.")
        
        custom_key_converted = convert_custom_key(custom_key)
        cls.command = "insert_custom_key"

        query = convert_to_binary_query(cls, key=custom_key_converted, expire_sec=expire_sec)
        return await cls._run_query(query)
    
    @classmethod
    async def insert_custom_key_value(cls, custom_key: str, value: dict, expire_sec: int = 0):
        """       
        Args:
            custom_key: A custom key to insert into the store. This key can be used to retrieve the value later.
            value: A Python class / dict to insert into the store.
            expire_sec: The number of seconds before the inserted value expires.
        Returns:
            True if the insert operation was successful. Class 'str' if the insert operation failed.
            
        """
        if not value:
            raise ValueError("No value provided for insertion.")
        if not custom_key:
            raise ValueError("No custom key provided for insertion.")

        custom_key_converted = convert_custom_key(custom_key)
        cls.command = "insert_custom_key_value"

        query = convert_to_binary_query(cls, key=custom_key_converted, value=value, expire_sec=expire_sec)
        return await cls._run_query(query)
    
    @classmethod
    async def insert_value(cls, value: dict, expire_sec: int = 0):
        """       
        Args:
            value: A Python class / dict to insert into the store.
            expire_sec: The number of seconds before the inserted value expires.
        Returns:
            Key number if the insert operation was successful. Class 'str' if the insert operation failed.
        """
        if not value:
            raise ValueError("No value provided for insertion.")
        
        cls.command = "insert_value"

        query = convert_to_binary_query(cls, value=value, expire_sec=expire_sec)
        return await cls._run_query(query)
    
    @classmethod
    async def get_value(cls, key: Union[str, None] = None, custom_key: Union[str, None] = None, with_pointers: bool = False):

        """
        Args:
            key: The key number of the value to retrieve.
            custom_key: The custom key of the value to retrieve.
            with_pointers: A boolean value that determines whether to include pointers (foreign values) in the output.
        Returns:
            The value associated with the key or custom key. Class 'str' if the get operation failed.
        """
        if custom_key and len(custom_key) > 0:
            key = convert_custom_key(custom_key)

        if not key:
            raise ValueError("No key provided for retrieval.")
        
        cls.command = "get_value"

        query = convert_to_binary_query(cls, key=key, with_pointers=with_pointers)
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
    async def delete_key(cls, key: Union[str, None] = None, custom_key: Union[str, None] = None):
        """
        Delete a key from the store. If a custom key is provided, it will be converted
        to the appropriate format before deletion.

        Args:
            key (int | str, optional): The key to delete. This can either be an integer or a string.
                                       Default is an empty string, which will be ignored if custom_key is provided.
            custom_key (str, optional): The custom key to delete. This is used if the key provided is a custom key string.
                                       Default is an empty string.

        Returns:
            bool | str: Returns a boolean indicating success (True) or failure (False),
                        or a string message if the deletion was unsuccessful.
        """
        if custom_key and len(custom_key) > 0:
            key = convert_custom_key(custom_key)
        #custom key should be string

        if not key:
            raise ValueError("No key provided for deletion.")
        
        cls.command = "delete_key"  # Set the command type for the query

        query = convert_to_binary_query(cls, key=key)  # Convert the key into a binary query format
        return await cls._run_query(query)  # Run the query and return the result

    @classmethod
    async def update_value(cls, key: Union[str, None] = None, custom_key: Union[str, None] = None, expire_sec: int = 0, **filters):
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
            raise ValueError("No filters provided for update.")
        if not key:
            raise ValueError("No key provided for update.")
        
        # combine together two methods
        # value = handle_timestamps(filters)  # Normalize the value to update
        # value = handle_pointers_for_update(value)  # Normalize the pointers in the value
        
        cls.command = "update_value"

        query = convert_to_binary_query(cls, key=key, value=filters, expire_sec=expire_sec)  # Convert the key and filters into a binary query format
        return await cls._run_query(query)  # Run the query and return the result

    @classmethod
    async def insert_bulk(cls, bulk_values: list, expire_sec: int = 0):
        """       
        Args:
            bulk_values: A list of Python objects to insert into the store.
            expire_sec: The number of seconds before the inserted values expire.
            
        Returns:
            True if the bulk insert operation was successful.
            List of values that were not inserted.
        """

        if not bulk_values:
            raise ValueError("No values provided for bulk insertion.")
        
        cls.command = "insert_bulk"
        query = convert_to_binary_query(cls, bulk_values=bulk_values, expire_sec=expire_sec)
        return await cls._run_query(query)
    
    @classmethod
    async def delete_bulk(cls, bulk_keys: list = [], bulk_custom_keys: list = []):
        """
        Delete multiple keys in bulk. If custom keys are provided, they are first converted
        to the appropriate format and then appended to the list of keys to be deleted.

        Args:
            bulk_keys (list, optional): A list of keys to delete. Each key can be either an integer or a string. 
                                        Default is an empty list.
            bulk_custom_keys (list, optional): A list of custom keys to delete. These keys will be converted to 
                                                the appropriate format before being included in the deletion query. 
                                                Default is an empty list.

        Returns:
            bool | str: Returns a boolean indicating whether the bulk deletion was successful (True) or not (False).
                        It may also return a string message in case of an error or failure.
        
        Raises:
            ValueError: If both `bulk_keys` and `bulk_custom_keys` are empty.
        """
        if len(bulk_custom_keys) > 0:
            bulk_custom_keys = convert_custom_keys(bulk_custom_keys)
            bulk_keys += bulk_custom_keys

        if not bulk_keys:  # Ensure at least one key exists for the operation
            raise ValueError("No keys provided for deletion.")
        
        cls.command = "delete_bulk"  # Set the command for bulk deletion
        query = convert_to_binary_query(cls, bulk_keys=bulk_keys)  # Construct the query in binary format
        return await cls._run_query(query)  # Execute the query and return the result
    
    @classmethod
    async def get_bulk(cls, bulk_keys: list = [], bulk_custom_keys: list = [], limit: list = [], with_pointers: bool = False):
        """
        Retrieve multiple keys in bulk. Custom keys can be converted and added to the bulk retrieval list.
        Additionally, a limit on the number of records to retrieve can be applied, and whether to include pointers 
        in the results can be specified.

        Args:
            bulk_keys (list, optional): A list of keys to retrieve. Each key can be either an integer or a string.
                                        Default is an empty list.
            bulk_custom_keys (list, optional): A list of custom keys to retrieve. These keys will be converted 
                                                before being included in the bulk retrieval. Default is an empty list.
            limit (list, optional): A list defining the limit on the number of records to return. If empty, 
                                     no limit is applied.
            with_pointers (bool, optional): If True, the query will include pointer information with the results.
                                            Default is False.

        Returns:
            dict | str: Returns a dictionary of keys and their associated values if successful, or a string 
                        message if the retrieval fails or there is an error.
        
        Raises:
            ValueError: If both `bulk_keys` and `bulk_custom_keys` are empty.
        """
        if len(bulk_custom_keys) > 0:
            bulk_custom_keys = convert_custom_keys(bulk_custom_keys)  # Convert custom keys if provided
            bulk_keys += bulk_custom_keys
        
        if not bulk_keys:
            raise ValueError("No keys provided for retrieval.")
        
        cls.command = "get_bulk"
        cls.limit_output = handle_limit(limit)
        query = convert_to_binary_query(cls, bulk_keys=bulk_keys, with_pointers=with_pointers)
        return await cls._run_query(query)
    
    @classmethod
    async def update_bulk(cls, bulk_keys_values: dict = {}, bulk_custom_keys_values: dict = {}):
        """
        Update multiple keys in bulk with the provided new values. If custom keys are provided, 
        they will be converted before being applied to the bulk update.

        Args:
            bulk_keys_values (dict, optional): A dictionary where the keys are the keys to be updated, 
                                                and the values are the new values to assign. Default is an empty dictionary.
            bulk_custom_keys_values (dict, optional): A dictionary of custom keys and their new values to be updated. 
                                                      These custom keys will be converted before being included in the update. 
                                                      Default is an empty dictionary.

        Returns:
            bool | str: Returns a boolean indicating success (True) or failure (False), or a string error message 
                        if the update operation fails.
        
        Raises:
            ValueError: If neither `bulk_keys_values` nor `bulk_custom_keys_values` is provided.
        """
        
        if not bulk_keys_values:
            raise ValueError("No key-value pairs provided for update.")
        
        if len(bulk_custom_keys_values) > 0:
            bulk_custom_keys_values = convert_custom_keys_values(bulk_custom_keys_values)  # Convert custom keys and values
            bulk_keys_values = {**bulk_keys_values, **bulk_custom_keys_values}  # Merge the dictionaries

        #handle timestamps and pointers in bulk_keys_values together COMBINE!
        # for k, v in bulk_keys_values.items():
        #     bulk_custom_keys_values[k] = handle_timestamps(v)
        

        
        cls.command = "update_bulk"  # Set the command for bulk update
        query = convert_to_binary_query(cls, bulk_keys_values=bulk_keys_values)  # Build the query in binary format
        return await cls._run_query(query)  # Execute the query and return the result
    
    @classmethod
    async def lookup_keys_where(cls, limit: int = 0, schema: Union[str, None] = None, **filters):
        """
        Perform a lookup for keys matching the given filters with an optional limit on the number of records returned.

        Args:
            limit (int, optional): The maximum number of results to return. If 0, no limit is applied. Default is 0.
            filters (dict): The filtering criteria for the lookup. These are field-value pairs that the keys should match.

        Returns:
            dict | str: A dictionary of matching keys and their associated values, or a string error message if the query fails.
        
        Raises:
            ValueError: If no filters are provided.
        """
        if not filters:  # Ensure filters are provided for the lookup
            raise ValueError("No criteria provided for the lookup.")
        
        # search_criteria = handle_timestamps(filters)  # Normalize the search criteria

        if schema:
            cls.schema = str(schema)
        else: 
            cls.schema = None
        
        cls.command = "lookup_keys"
        cls.limit_output = handle_limit(limit)
        query = convert_to_binary_query(cls, search_criteria=filters)
        return await cls._run_query(query)
    
    @classmethod
    async def lookup_values_where(cls, limit=0, with_pointers: bool = False, schema: Union[str, None] = None, **filters):
        """
        Perform a lookup for values matching the given filters, with options to apply a limit and include pointer information.

        Args:
            limit (int, optional): The maximum number of results to return. If 0, no limit is applied. Default is 0.
            with_pointers (bool, optional): If True, the query will include pointers in the result. Default is False.
            filters (dict): The filtering criteria for the lookup. These are field-value pairs that the values should match.

        Returns:
            dict | str: A dictionary of matching values and their associated keys, or a string error message if the query fails.
        
        Raises:
            ValueError: If no filters are provided.
        """
        if not filters: # Ensure filters are provided for the lookup
            raise ValueError("No criteria provided for the lookup.")
        
        # search_criteria = handle_timestamps(filters) # Normalize the search criteria

        if schema:
            cls.schema = str(schema)
        else: 
            cls.schema = None

        cls.command = "lookup_values"
        # if class Limit then do not handle limit JUST use prebuild function -> return_limit()
        cls.limit_output = handle_limit(limit) 
        query = convert_to_binary_query(cls, search_criteria=filters, with_pointers=with_pointers)
        return await cls._run_query(query)

    @classmethod
    async def list_all_depending_keys(cls, key: Union[str, None] = None, custom_key: Union[str, None] = None):
        """
        List all keys that depend on a specified key or custom key.

        This class method generates a query to retrieve all keys that are dependent
        on a given `key` or a `custom_key` if provided. It converts the key into 
        the appropriate format and executes the query.

        Parameters:
            key (str | int, optional): The primary key whose dependencies are to be listed. 
                Defaults to an empty string.
            custom_key (str, optional): A custom key that can be converted into the 
                appropriate format. If provided, it overrides the `key` parameter.

        Returns:
            Any: The result of executing the query, typically representing the 
                dependent keys.

        Raises:
            ValueError: If both `key` and `custom_key` are empty, as one of them 
                is required to form a valid query.
        """
        if custom_key and len(custom_key) > 0:
            key = convert_custom_key(custom_key)

        if not key:
            raise ValueError("No key provided for retrieval.")

        cls.command = "list_all_depending_keys"

        query = convert_to_binary_query(cls, key=key)
        return await cls._run_query(query)
    
    @classmethod
    async def get_len(cls):
        cls.command = "get_len"
        query = convert_to_binary_query(cls)
        return await cls._run_query(query)
    
    @classmethod
    def connect_engine(cls, engine: Engine) -> None:
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

    @classmethod  
    async def create_keyspace(cls):

        query = orjson.dumps({
            "raw": ["create-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "y" if cls.persistent else "n"],
            "superowner_credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)
    
    @classmethod  
    async def remove_keyspace(cls):

        query = orjson.dumps({
            "raw": ["remove-keyspace", "store", cls.store, "keyspace", cls.keyspace, "persistent", "y" if cls.persistent else "n"],
            "superowner_credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)
    
    @classmethod
    async def list_all_schemas_in_keyspace(cls):
        cls.command = "list_all_schemas_in_keyspace"
        query = convert_to_binary_query(cls)
        return await cls._run_query(query)

    @classmethod
    def show_store_properties(cls):
        """
        Displays the properties of the store associated with the provided class settings.
        
        Args:
            cls (type): The class containing the configuration details for the store.
        
        This function sets the class to perform a "show_properties" command and sends 
        a query to retrieve the store's properties.
        """
        return cls.__dict__
