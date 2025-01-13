import asyncio
import orjson
from typing import Union

class Engine:
    """
    Represents the configuration and connection details for a communication engine.

    The `Engine` class stores information related to the connection such as the host, port, 
    username, password, and store name required to establish a connection with the service.

    Attributes:
        host (str): The hostname or IP address of the server to connect to.
        port (int): The port number on the server to use for the connection.
        username (str): The username for authentication with the server.
        password (str): The password for authentication with the server.
        store (str): The name of the data store on the server.
    """
    def __init__(self, host: str, port: int, username: str, password: str, store: str):
        """
        Initializes the Engine with the necessary connection parameters.

        Args:
            host (str): The hostname or IP address of the server.
            port (int): The port number on the server to connect to.
            username (str): The username for authentication.
            password (str): The password for authentication.
            store (str): The name of the data store to interact with.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.store = store

    
    def remove_store(self, persistent: bool = False):
        """
        Removes the current store from the engine configuration.

        This method clears the store attribute from the engine, effectively 
        disconnecting the engine from any specific data store.
        """
        query = {
            "raw": ['remove_store', "store", self.store, "persistent", "y" if persistent else "n"],
            "superowner_credentials": [self.username, self.password]
        }

        return asyncio.run(send_data(self.host, self.port, orjson.dumps(query)))
    
    def create_store(self, persistent: bool = False):
        """
        Creates a new store on the server.

        This method sends a request to the server to create a new store with the 
        specified name and persistence settings. The store is created with the 
        provided credentials and returns a success message or an error response.
        """
        
        query = {
            "raw": ['create_store', "store", self.store, "persistent", "y" if persistent else "n"],
            "superowner_credentials": [self.username, self.password]
        }

        return asyncio.run(send_data(self.host, self.port, orjson.dumps(query)))
    
    def grant_to(self, owner: str, permission: str, namespaces: Union[list, str, None] = None):
        """
        Grants a permission to a user on the current store.

        This method sends a request to the server to grant a specific permission 
        to a user on the current store. The permission can be 'read', 'write', or 'admin'.
        """

        valid_permissions = ['read', 'write', 'all']

        if str(permission) not in valid_permissions:
            raise ValueError(f"Invalid permission: {permission}. Valid permissions are: {valid_permissions}")

        query = {
            "raw": ['grant_to', "owner", owner, "permission", str(permission), "store", self.store],
            "superowner_credentials": [self.username, self.password]
        }

        if namespaces:

            query["raw"].extend(["namespaces"])

            if isinstance(namespaces, str):
                query["raw"].extend([namespaces])
            elif isinstance(namespaces, list):

                for each in namespaces:
                    if isinstance(each, type):
                        query["raw"].extend([each.namespace])
                    else:
                        query["raw"].extend([each])

            elif isinstance(namespaces, type):
                query["raw"].extend([namespaces.namespace])

        return asyncio.run(send_data(self.host, self.port, orjson.dumps(query)))
    
    def revoke_from(self, owner: str, permission: str, namespaces: Union[list, str, type, None] = None):
        """
        Revokes a permission from a user on the current store.

        This method sends a request to the server to revoke a specific permission 
        from a user on the current store. The permission can be 'read', 'write', or 'all'.
        """

        valid_permissions = ['read', 'write', 'all']

        if str(permission) not in valid_permissions:
            raise ValueError(f"Invalid permission: {permission}. Valid permissions are: {valid_permissions}")

        query = {
            "raw": ['revoke_from', "owner", owner, "permission", str(permission), "store", self.store],
            "superowner_credentials": [self.username, self.password]
        }

        if namespaces:

            query["raw"].extend(["namespaces"])

            if isinstance(namespaces, str):
                query["raw"].extend([namespaces])
            elif isinstance(namespaces, list):

                for each in namespaces:
                    if isinstance(each, type):
                        query["raw"].extend([each.namespace])
                    else:
                        query["raw"].extend([each])

            elif isinstance(namespaces, type):
                query["raw"].extend([namespaces.namespace])

        return asyncio.run(send_data(self.host, self.port, orjson.dumps(query)))
    
    def create_owner(self, owner: str, password: str):
        """
        Creates a new owner with the specified credentials.

        This method sends a request to the server to create a new owner with the 
        specified username and password. The owner is created with the provided 
        credentials and returns a success message or an error response.
        """

        query = {
            "raw": ['create_owner', "username", owner, "password", password],
            "superowner_credentials": [self.username, self.password]
        }

        return asyncio.run(send_data(self.host, self.port, orjson.dumps(query)))
    
    def remove_owner(self, owner: str):
        """
        Removes an owner from the server.

        This method sends a request to the server to remove an existing owner 
        with the specified username. The owner is removed from the server and 
        returns a success message or an error response.
        """

        query = {
            "raw": ['remove_owner', "username", owner],
            "superowner_credentials": [self.username, self.password]
        }

        return asyncio.run(send_data(self.host, self.port, orjson.dumps(query)))
        

async def send_data(host: str, port: int, string: str):
    """
    Asynchronously sends data to a remote server and receives a response.

    This function connects to the specified server using the given host and port, 
    sends the provided string, and waits for a response. The function handles timeouts, 
    connection errors, and response parsing, ensuring that the data is returned in 
    a usable format.

    Args:
        host (str): The hostname or IP address of the server.
        port (int): The port number of the server.
        string (str): The data to be sent to the server.

    Returns:
        str: The server's response, which is either the parsed response data 
             or an error message if the operation fails.
             
    Raises:
        asyncio.TimeoutError: If the response times out while waiting.
        ConnectionRefusedError: If the connection to the server is refused.
        Exception: If an unexpected error occurs during the connection or data processing.
    """
    resp = None
    writer = None

    try:
        reader, writer = await asyncio.open_connection(host, port)

        # print(f"Sending data: {string}")

        # if raw:
        #     print("Sending raw data", string)
        #     string = "raw " + string
        
        writer.write(string + b"\n")
        await writer.drain()

        try:
            resp = await asyncio.wait_for(reader.readuntil(b"\n"), timeout=120)
            resp = resp.decode().strip()

            try:
                resp = recursive_parse_orjson(resp)
            except Exception as parse_error:
                print(f"Failed to parse response: {parse_error}")

        except asyncio.TimeoutError:
            resp = "Operation timed out"  # Handle timeout errors

    except ConnectionRefusedError:
        resp = "Connection refused"  # Handle connection errors
    except Exception as e:
        resp = f"An unexpected error occurred: {e}"  # Handle general exceptions
    finally:
        # Ensure the writer is closed after the operation
        if writer:
            writer.close()
            await writer.wait_closed()

    return resp

def recursive_parse_orjson(data):
    """
    Recursively parses nested JSON strings in the provided data using orjson for faster parsing.
    
    Args:
        data: A Python object that may contain JSON strings, including nested structures.
        
    Returns:
        A fully parsed Python object with all nested JSON strings converted.
    """
    if isinstance(data, dict):
        return {key: recursive_parse_orjson(value) for key, value in data.items()}
    elif isinstance(data, tuple):
        return tuple(recursive_parse_orjson(element) for element in data)
    elif isinstance(data, list):
        return [recursive_parse_orjson(element) for element in data]
    elif isinstance(data, str):
        try:
            parsed_data = orjson.loads(data)
            return recursive_parse_orjson(parsed_data)
        except orjson.JSONDecodeError:
            return data
    elif isinstance(data, (int, float)):
        return data
    else:
        return data

class MetaclassPermission(type):
    def __str__(cls):
        return cls.permission
    
    def __repr__(cls):
        return cls.permission

class Permission:
    class read(metaclass=MetaclassPermission):
        permission = "read"
    class write(metaclass=MetaclassPermission):
        permission = "write"
    class all(metaclass=MetaclassPermission):
        permission = "all"
    