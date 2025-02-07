import asyncio
import orjson
from typing import Union, List, Optional, Any
from tools import Permission

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


def recursive_parse_orjson(data: Any) -> Any:
    """
    Recursively parses nested JSON strings using orjson.

    Args:
        data (Any): The data to be parsed, can be a JSON string, list, tuple, or dictionary.

    Returns:
        Any: Fully parsed data structure.
    """
    if isinstance(data, str):
        try:
            return recursive_parse_orjson(orjson.loads(data))
        except orjson.JSONDecodeError:
            return data
    elif isinstance(data, (list, tuple)):
        return type(data)(recursive_parse_orjson(item) for item in data)
    elif isinstance(data, dict):
        return {key: recursive_parse_orjson(value) for key, value in data.items()}
    return data
