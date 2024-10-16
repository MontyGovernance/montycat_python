import asyncio
import orjson

class Engine:
    def __init__(self, host: str, port: int, username: str, password: str, store_name: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.store_name = store_name

async def send_data(host: str, port: int, string: str):
    resp = None
    writer = None

    try:
        reader, writer = await asyncio.open_connection(host, port)
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
            resp = "Operation timed out"

    except ConnectionRefusedError:
        resp = "Connection refused"
    except Exception as e:
        resp = f"An unexpected error occurred: {e}"
    finally:
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

# def recursive_parse_orjson(data):
#     """
#     Recursively parses nested JSON strings in the provided data using orjson for faster parsing.
    
#     Args:
#         data: A Python object that may contain JSON strings, including nested structures.
    
#     Returns:
#         A fully parsed Python object with all nested JSON strings converted.
#     """
#     if isinstance(data, dict):
#         return {key: recursive_parse_orjson(value) for key, value in data.items()}
#     elif isinstance(data, tuple):
#         return tuple(recursive_parse_orjson(element) for element in data)
#     elif isinstance(data, list):
#         return [recursive_parse_orjson(element) for element in data]
#     elif isinstance(data, str):
#         try:
#             # Attempt to parse the string as JSON
#             parsed_data = orjson.loads(data)
#             return recursive_parse_orjson(parsed_data)
#         except orjson.JSONDecodeError:
#             # Return the original string if it can't be parsed
#             return data
#     else:
#         return data
