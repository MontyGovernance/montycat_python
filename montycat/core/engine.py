import orjson
from typing import Union, List, Optional, Any
from .tools import Permission
from .utils import send_data

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

    def __init__(self, host: str, port: int, username: str, password: str, store: Union[str, None] = None) -> None:
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

    @classmethod
    def from_uri(cls, uri: str) -> 'Engine':
        """
        Creates an Engine instance from a URI string in the format:
        montycat://host/port/username/password[/store]

        The store is optional. If not provided, it will be set to None.

        Args:
            uri (str): The URI string to parse.

        Returns:
            Engine: An instance of Engine with the parsed parameters.

        Raises:
            ValueError: If the URI is invalid, has incorrect format, or cannot be parsed.
        """
        if not uri.startswith("montycat://"):
            raise ValueError("URI must use 'montycat://' protocol")
        parts = uri[len("montycat://"):].split("/")
        if len(parts) == 4:
            host, port_str, username, password = parts
            store = None
        elif len(parts) == 5:
            host, port_str, username, password, store = parts
        else:
            raise ValueError("Missing or extra parts in URI")
        if any(part == "" for part in [host, port_str, username, password]):
            raise ValueError("Host, port, username, and password must be non-empty")
        try:
            port = int(port_str)
        except ValueError:
            raise ValueError("Port must be an integer")
        return cls(host, port, username, password, store)

    async def _execute_query_with_credentials(self, command: List[Any]) -> Any:
        """
        Executes a command query asynchronously.

        Args:
            command (List[Any]): The command to be executed on the server.

        Returns:
            Any: The server's response after executing the command.
        """
        query = orjson.dumps({
            "raw": command,
            "credentials": [self.username, self.password]
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
        return await self._execute_query_with_credentials([
            'create-store', "store", self.store, "persistent", "y" if persistent else "n"
        ])

    async def remove_store(self, persistent: bool = False) -> Any:
        """
        Removes an existing data store from the server.

        Args:
            persistent (bool): Flag indicating if the removal should be persistent.

        Returns:
            bool
        """
        return await self._execute_query_with_credentials([
            'remove-store', "store", self.store, "persistent", "y" if persistent else "n"
        ])

    async def grant_to(self, owner: str, permission: Union[str, Permission], keyspaces: Optional[Union[List[str], str, None]] = None) -> Any:
        """
        Grants specific permissions to a user for the current store.

        Args:
            owner (str): The user to grant permissions to.
            permission (str): The type of permission ('read', 'write', 'all').
            keyspaces (Optional[Union[List[str], str]]): Optional keyspaces for permission scoping.

        Returns:
            bool

        Raises:
            ValueError: If an invalid permission is provided.
        """
        if permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}. Valid permissions are: {self.VALID_PERMISSIONS}")

        command = ['grant-to', "owner", owner, "permission", permission, "store", self.store]
        if keyspaces:
            command.append("keyspaces")
            if isinstance(keyspaces, str):
                command.append(keyspaces)
            else:
                command.extend(keyspaces)

        return await self._execute_query_with_credentials(command)

    async def revoke_from(self, owner: str, permission: Union[str, Permission], keyspaces: Optional[Union[List[str], str]] = None) -> Any:
        """
        Revokes specific permissions from a user for the current store.

        Args:
            owner (str): The user to revoke permissions from.
            permission (str): The type of permission ('read', 'write', 'all').
            keyspaces (Optional[Union[List[str], str]]): Optional keyspaces for permission scoping.

        Returns:
            bool

        Raises:
            ValueError: If an invalid permission is provided.
        """
        if permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}. Valid permissions are: {self.VALID_PERMISSIONS}")

        command = ['revoke-from', "owner", owner, "permission", permission, "store", self.store]
        if keyspaces:
            command.append("keyspaces")
            if isinstance(keyspaces, str):
                command.append(keyspaces)
            else:
                command.extend(keyspaces)

        return await self._execute_query_with_credentials(command)

    async def create_owner(self, owner: str, password: str) -> Any:
        """
        Creates a new owner on the server with specified credentials.

        Args:
            owner (str): The username for the new owner.
            password (str): The password for the new owner.

        Returns:
            bool
        """
        return await self._execute_query_with_credentials([
            'create-owner', "username", owner, "password", password
        ])

    async def remove_owner(self, owner: str) -> Any:
        """
        Removes an owner from the server.

        Args:
            owner (str): The username of the owner to be removed.

        Returns:
            bool
        """
        return await self._execute_query_with_credentials([
            'remove-owner', "username", owner
        ])

    async def list_owners(self) -> Any:
        """
        Lists all owners registered on the server.

        Returns:
            Any: The server's response containing the list of owners.
        """
        return await self._execute_query_with_credentials(['list-owners'])
    
    async def get_structure_available(self) -> Any:
        """
        Retrieves the structure of the current store.

        Returns:
            Any: The server's response containing the store structure.
        """
        return await self._execute_query_with_credentials(['get-structure-available'])
