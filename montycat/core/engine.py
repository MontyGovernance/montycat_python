import asyncio
import orjson

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
        store_name (str): The name of the data store on the server.
    """
    def __init__(self, host: str, port: int, username: str, password: str, store_name: str):
        """
        Initializes the Engine with the necessary connection parameters.

        Args:
            host (str): The hostname or IP address of the server.
            port (int): The port number on the server to connect to.
            username (str): The username for authentication.
            password (str): The password for authentication.
            store_name (str): The name of the data store to interact with.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.store_name = store_name


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
        # Establish a connection to the server
        reader, writer = await asyncio.open_connection(host, port)
        
        # Write the data string to the server
        writer.write(string.encode() + b"\n")
        await writer.drain()

        try:
            # Wait for the response from the server with a timeout
            resp = await asyncio.wait_for(reader.readuntil(b"\n"), timeout=120)
            resp = resp.decode().strip()

            try:
                # Parse the response using a custom function (e.g., orjson parsing)
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
        return {
            key: recursive_parse_orjson(value)
            for key, value in data.items()
        }
    elif isinstance(data, tuple):
        return tuple(recursive_parse_orjson(element) if not element.isdigit() else element for element in data)
    elif isinstance(data, list):
        return [recursive_parse_orjson(element) if not element.isdigit() else element for element in data]
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
