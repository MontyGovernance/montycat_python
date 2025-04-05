import orjson, asyncio
from typing import Any

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
    CHUNK_SIZE = 1024 * 256  # 256 KB

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
   return value.isdigit() and len(value) > 16
