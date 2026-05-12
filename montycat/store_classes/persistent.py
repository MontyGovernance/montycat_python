from ..store_functions.store_generic_functions import convert_to_binary_query, convert_custom_key, handle_limit
from typing import Union
import orjson

class persistent_kv:

    persistent: bool = True

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
        query = convert_to_binary_query(cls, command="insert_custom_key", key=custom_key_converted)
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
        query = convert_to_binary_query(cls, command="insert_custom_key_value", key=custom_key_converted, value=value)
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

        query = convert_to_binary_query(cls, command="insert_value", value=value)
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

        if key and custom_key:
            raise ValueError("Provide either key or custom_key, not both.")

        if custom_key and len(custom_key) > 0:
            key = convert_custom_key(custom_key)

        if not filters:
            raise ValueError("No filters provided")
        if not key:
            raise ValueError("No key provided")

        query = convert_to_binary_query(cls, command="update_value", key=key, value=filters)
        return await cls._run_query(query)

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

        query = convert_to_binary_query(cls, command="insert_bulk", bulk_values=bulk_values)
        return await cls._run_query(query)

    @classmethod
    async def get_keys(cls, limit: list[int] = [], volumes: list[str] = [], latest_volume: bool = False):
        """
        Args:
            limit: A list of two integers [start, stop] to retrieve keys in range.
            volumes (list[str], optional): A list of volumes to retrieve. Default is an empty list.
            latest_volume (bool, optional): Whether to retrieve keys from the latest volume. Default is False.
        Returns:
            A list of keys in the store. Class 'str' if the get operation failed.
        """

        if not volumes and not latest_volume:
            if not limit or limit == [0, 0]:
                raise ValueError("Please provide volumes/latest volume or limit.")

        query = convert_to_binary_query(cls, command="get_keys", limit_output=handle_limit(limit), volumes=volumes, latest_volume=latest_volume)
        return await cls._run_query(query)

    @classmethod
    async def create_keyspace(cls, cache: Union[int, None] = None, compression: bool = False):
        """
        Creates a new keyspace in the store with the specified settings for persistence, distribution, caching, and
        compression.

        Args:
            cache: Optional cache size in bytes. If None, no cache is used.
            compression: Whether to enable compression. Default is False.

        Returns:
            bool: True if the keyspace was created successfully, False otherwise.
        """
        query = orjson.dumps({
            "raw": [
                "create-keyspace",
                "store", cls.store,
                "keyspace", cls.keyspace,
                "persistent", "y",
                "distributed", "y" if cls.distributed else "n",
                "cache", cache if cache else "0",
                "compression", "y" if compression else "n"
                ],
            "credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)

    @classmethod
    async def update_cache_and_compression(cls, cache: Union[int, None] = None, compression: bool = False):
        """
        Updates the cache size and compression settings for the current store.

        Args:
            cache: Optional cache size in bytes. If None, no cache is used.
            compression: Whether to enable compression. Default is False.

        Returns:
            bool
        """
        query = orjson.dumps({
            "raw": [
                'update-cache-compression',
                "store", cls.store,
                "keyspace", cls.keyspace,
                "cache", cache if cache else "0",
                "compression", "y" if compression else "n"
            ],
            "credentials": [cls.username, cls.password]
        })

        return await cls._run_query(query)