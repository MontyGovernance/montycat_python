import asyncio, orjson
from typing import Union, List, Optional, Any
from .tools import Permission

class Engine:
    """
    Represents the configuration and connection details for a communication engine.

    Attributes:
        host (str): The hostname or IP address of the server to connect to.
        port (int): The port number on the server to use for the connection.
        username (str): The username for authentication with the server.
        password (str): The password for authentication with the server.
        store (str): The name of the data store on the server.
    """
    VALID_PERMISSIONS = {'read', 'write', 'all'}

    def __init__(self, host: str, port: int, username: str, password: str, store: str) -> None:
        """
        Initializes the Engine with the given connection parameters.

        Args:
            host (str): Hostname or IP address of the server.
            port (int): Port number to connect to.
            username (str): Username for server authentication.
            password (str): Password for server authentication.
            store (str): Name of the data store to interact with.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.store = store

    async def _execute_query(self, command: List[Any]) -> Any:
        """
        Executes a command query asynchronously.

        Args:
            command (List[Any]): The command to be executed on the server.

        Returns:
            Any: The server's response after executing the command.
        """
        query = orjson.dumps({
            "raw": command,
            "superowner_credentials": [self.username, self.password]
        })
        return await send_data(self.host, self.port, query)

    async def create_store(self, persistent: bool = False) -> Any:
        """
        Creates a new data store on the server.

        Args:
            persistent (bool): Flag indicating if the store should be persistent.

        Returns:
            bool
        """
        return await self._execute_query([
            'create_store', "store", self.store, "persistent", "y" if persistent else "n"
        ])

    async def remove_store(self, persistent: bool = False) -> Any:
        """
        Removes an existing data store from the server.

        Args:
            persistent (bool): Flag indicating if the removal should be persistent.

        Returns:
            bool
        """
        return await self._execute_query([
            'remove_store', "store", self.store, "persistent", "y" if persistent else "n"
        ])

    async def grant_to(self, owner: str, permission: Union[str, Permission], namespaces: Optional[Union[List[str], str]] = None) -> Any:
        """
        Grants specific permissions to a user for the current store.

        Args:
            owner (str): The user to grant permissions to.
            permission (str): The type of permission ('read', 'write', 'all').
            namespaces (Optional[Union[List[str], str]]): Optional namespaces for permission scoping.

        Returns:
            bool

        Raises:
            ValueError: If an invalid permission is provided.
        """
        if permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}. Valid permissions are: {self.VALID_PERMISSIONS}")

        command = ['grant_to', "owner", owner, "permission", permission, "store", self.store]
        if namespaces:
            command.append("namespaces")
            if isinstance(namespaces, str):
                command.append(namespaces)
            else:
                command.extend(namespaces)

        return await self._execute_query(command)

    async def revoke_from(self, owner: str, permission: Union[str, Permission], namespaces: Optional[Union[List[str], str]] = None) -> Any:
        """
        Revokes specific permissions from a user for the current store.

        Args:
            owner (str): The user to revoke permissions from.
            permission (str): The type of permission ('read', 'write', 'all').
            namespaces (Optional[Union[List[str], str]]): Optional namespaces for permission scoping.

        Returns:
            bool

        Raises:
            ValueError: If an invalid permission is provided.
        """
        if permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}. Valid permissions are: {self.VALID_PERMISSIONS}")

        command = ['revoke_from', "owner", owner, "permission", permission, "store", self.store]
        if namespaces:
            command.append("namespaces")
            if isinstance(namespaces, str):
                command.append(namespaces)
            else:
                command.extend(namespaces)

        return await self._execute_query(command)

    async def create_owner(self, owner: str, password: str) -> Any:
        """
        Creates a new owner on the server with specified credentials.

        Args:
            owner (str): The username for the new owner.
            password (str): The password for the new owner.

        Returns:
            bool.
        """
        return await self._execute_query([
            'create_owner', "username", owner, "password", password
        ])

    async def remove_owner(self, owner: str) -> Any:
        """
        Removes an owner from the server.

        Args:
            owner (str): The username of the owner to be removed.

        Returns:
            bool
        """
        return await self._execute_query([
            'remove_owner', "username", owner
        ])

    async def list_owners(self) -> Any:
        """
        Lists all owners registered on the server.

        Returns:
            Any: The server's response containing the list of owners.
        """
        return await self._execute_query(['list_owners'])


async def send_data(host: str, port: int, query: bytes) -> Any:
    """
    Sends data asynchronously to a remote server and handles the response.

    Args:
        host (str): The server's hostname or IP address.
        port (int): The server's port.
        query (bytes): The serialized data to be sent.

    Returns:
        Any: The server's parsed response. Suppose to be dict {}.

    Raises:
        asyncio.TimeoutError: If the operation exceeds the time limit.
        ConnectionRefusedError: If the server refuses the connection.
    """
    CHUNK_SIZE = 1024 * 1024  # 1MB

    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(query + b"\n")
        await writer.drain()

        data = bytearray()
        while True:
            chunk = await asyncio.wait_for(reader.read(CHUNK_SIZE), timeout=120)
            if not chunk or b"\n" in chunk:
                data.extend(chunk)
                break
            data.extend(chunk)

        writer.close()
        await writer.wait_closed()

        response = data.decode().strip()
        return recursive_parse_orjson(response)

    except (asyncio.TimeoutError, ConnectionRefusedError) as e:
        return str(e)
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def recursive_parse_orjson(data):
   """
   Recursively parses nested JSON strings in the provided data using orjson for faster parsing.
   Keeps u128 values as strings.
   Args:
       data: A Python object that may contain JSON strings, including nested structures.
   Returns:
       A fully parsed Python object with all nested JSON strings converted, except for u128 values.
   """
   if isinstance(data, dict):
       return {key: recursive_parse_orjson(value) for key, value in data.items()}
   elif isinstance(data, tuple):
       return tuple(recursive_parse_orjson(element) for element in data)
   elif isinstance(data, list):
       return [recursive_parse_orjson(element) for element in data]
   elif isinstance(data, str):
       # Check if the string is a u128 value (you can define your own condition)
       if is_u128(data):
           return data  # Keep u128 as a string
       try:
           parsed_data = orjson.loads(data)
           return recursive_parse_orjson(parsed_data)
       except orjson.JSONDecodeError:
           return data
   elif isinstance(data, (int, float)):
       return data
   else:
       return data
   
def is_u128(value):
   """
   Check if the given string is a u128 value.
   Args:
       value: A string to check.
   Returns:
       True if the string is a u128 value, False otherwise.
   """
   # Example condition: u128 values are 128-bit unsigned integers, so they are long numeric strings
   # You can define your own condition based on your specific requirements
   return value.isdigit() and len(value) > 16  # Example condition for u128

# def preprocess_large_ints(json_str: str) -> str:
#     """Wraps large integers in quotes to preserve them as strings in the final parse."""
#     # Match integers larger than u64 (i.e., more than 19 digits)
#     LARGE_INT_PATTERN = re.compile(r'(?<![\d"])(\d{15,})(?![\d"])')
#     return LARGE_INT_PATTERN.sub(r'"\1"', json_str)

# def recursive_parse_orjson(data: Any) -> Any:
#     """
#     Recursively parses nested JSON strings using orjson.

#     Args:
#         data (Any): The data to be parsed, can be a JSON string, list, tuple, or dictionary.

#     Returns:
#         Any: Fully parsed data structure.
#     """
#     if isinstance(data, str):
#         try:
#             return recursive_parse_orjson(orjson.loads(data))
#         except orjson.JSONDecodeError:
#             return data
#     elif isinstance(data, (list, tuple)):
#         return type(data)(recursive_parse_orjson(item) for item in data)
#     elif isinstance(data, dict):
#         return {key: recursive_parse_orjson(value) for key, value in data.items()}
#     return data

# class CustomJSONDecoder(json.JSONDecoder):
#     def decode(self, s: str, **kwargs):
#         # Preprocess large integers
#         processed_s = self._preprocess_large_ints(s)
#         return super().decode(processed_s, **kwargs)

#     def _preprocess_large_ints(self, json_str: str) -> str:
#         """
#         Replace large integers in JSON string with string representations to avoid precision loss.
#         Matches numbers with more than 19 digits (i.e., larger than u64 max).
#         """
#         return re.sub(r'(?<![\d"])(\d{20,})(?![\d"])', r'"\1"', json_str)

# def recursive_parse_json(data: Any) -> Any:
#     """
#     Recursively parses nested JSON data using a custom decoder to handle large integers as strings.

#     Args:
#         data (Any): JSON string, list, dict, etc.
    
#     Returns:
#         Any: Parsed data with large integers as strings.
#     """
#     U64_MAX = 2**64 - 1

#     if isinstance(data, str):
#         try:
#             return json.loads(data, cls=CustomJSONDecoder)
#         except json.JSONDecodeError:
#             return data

#     elif isinstance(data, list):
#         return [recursive_parse_json(item) for item in data]
    
#     elif isinstance(data, dict):
#         return {key: recursive_parse_json(value) for key, value in data.items()}
    
#     elif isinstance(data, int) and data > U64_MAX:
#         return str(data)
#     return data
