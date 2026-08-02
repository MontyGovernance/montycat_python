import orjson, asyncio
from typing import Union
import asyncio
import ssl

from .pool import PoolConfig, get_pool

CHUNK_SIZE = 1024 * 256


def _ssl_context(tls: bool):
    if not tls:
        return None
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


async def _connect(host: str, port: int, tls: bool):
    return await asyncio.wait_for(
        asyncio.open_connection(host, port, ssl=_ssl_context(tls)),
        timeout=10.0,
    )


async def _close(writer):
    if writer is None:
        return
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


class _WriteFailed(Exception):
    """The request could not be written, so nothing reached the server.

    Distinguished from a read failure because only this case is safe to replay:
    after a read failure the engine may have applied the write already, and the
    commands are not idempotent (contract §4).
    """


async def send_data(
    host: str,
    port: int,
    query: bytes,
    callback=None,
    stop_event: Union[asyncio.Event, None] = None,
    tls=False,
    pool_config: Union[PoolConfig, None] = None,
):
    """
    Sends data asynchronously to a remote server and handles the response.

    Args:
        host (str): The server's hostname or IP address.
        port (int): The server's port.
        query (bytes): The serialized data to be sent.
        callback: Supplying one makes this a subscription. Subscription mode is
            never inferred from the payload.
        stop_event (asyncio.Event, optional): Terminates a subscription.
        tls (bool): Use TLS for the connection.
        pool_config (PoolConfig, optional): Enables connection pooling for the
            request/response path. None (the default) connects per request.

    Returns:
        Any: The server's parsed response. Suppose to be dict {}.

    Raises:
        asyncio.TimeoutError: If the operation exceeds the time limit.
        ConnectionRefusedError: If the server refuses the connection.
    """
    # A subscription is the call that supplies a callback — never inferred
    # from the payload. Searching the request for b"subscribe" misread any
    # record whose value merely contained that word, routing it into the
    # streaming branch, which never returns.
    if callback is not None:
        return await _subscription(host, port, query, callback, stop_event, tls)
    return await _request(host, port, query, tls, pool_config)


async def _subscription(host, port, query, callback, stop_event, tls):
    """Streaming path. Never pooled (contract §5)."""
    writer = None
    try:
        reader, writer = await _connect(host, port, tls)

        writer.write(query + b"\n")
        await writer.drain()

        stop_waiter = (
            asyncio.ensure_future(stop_event.wait()) if stop_event is not None else None
        )
        try:
            while True:
                if stop_event is not None and stop_event.is_set():
                    break

                # One frame per callback. The previous loop appended raw chunks
                # and handed the callback whatever had accumulated, so two frames
                # arriving together were delivered as a single event and a
                # partial third was discarded by the following clear().
                read = asyncio.ensure_future(reader.readline())

                if stop_waiter is None:
                    line = await read
                else:
                    # Race the read against the stop event. Checking the event
                    # only *between* reads meant `stop_event.set()` could not
                    # interrupt a blocked read, so a quiet subscription never
                    # ended: the task leaked, the socket stayed open, and the
                    # server's watchers stayed alive — which is precisely the
                    # deadlock the unconditional close below exists to prevent.
                    done, _ = await asyncio.wait(
                        {read, stop_waiter}, return_when=asyncio.FIRST_COMPLETED
                    )
                    if read not in done:
                        read.cancel()
                        break
                    line = read.result()

                if not line:
                    break

                callback(recursive_parse_orjson(line.decode().strip()))
        finally:
            if stop_waiter is not None and not stop_waiter.done():
                stop_waiter.cancel()

        return None  # subscription ended
    except Exception as e:
        return f"Error: {e}"
    finally:
        # Always close the connection — including on asyncio.CancelledError
        # (which doesn't inherit from Exception), so the server-side
        # subscription handler sees EOF and tears down its watchers. Without
        # this, the cancelled subscription leaves the TCP socket open until
        # GC, and the server's sled subscribers stay alive — which then
        # deadlocks any subsequent remove_keyspace/remove_store on the same
        # store.
        await _close(writer)


async def _request(host, port, query, tls, pool_config):
    """Request/response path — the only one that may use a pool."""
    pool = get_pool(host, port, tls, pool_config)

    if pool is not None:
        leased = await pool.checkout()
        if leased is not None:
            reader, writer = leased
            try:
                response = await _exchange(reader, writer, query)
            except asyncio.CancelledError:
                # A cancelled task may leave an unread response in the socket,
                # which would corrupt the next borrower. Close, never re-pool.
                await _close(writer)
                raise
            except _WriteFailed:
                # Nothing was transmitted, so replaying on a fresh connection
                # below is safe (contract §4).
                await _close(writer)
            except Exception as e:
                await _close(writer)
                return f"Error: {e}"
            else:
                await pool.checkin(reader, writer)
                return response

    writer = None
    try:
        reader, writer = await _connect(host, port, tls)
        response = await _exchange(reader, writer, query)
    except asyncio.CancelledError:
        await _close(writer)
        raise
    except Exception as e:
        await _close(writer)
        return f"Error: {e}"

    if pool is not None:
        await pool.checkin(reader, writer)
    else:
        await _close(writer)
    return response


async def _exchange(reader, writer, query):
    """Write one request and read exactly one newline-framed response."""
    try:
        writer.write(query + b"\n")
        await writer.drain()
    except Exception as e:
        raise _WriteFailed(str(e)) from e

    # Exactly one frame. `readline` leaves anything past the newline in the
    # StreamReader's own buffer, so the leftover travels with the connection
    # rather than being parsed as part of this response (contract §7). The
    # previous loop appended whole chunks and kept those trailing bytes.
    line = await asyncio.wait_for(reader.readline(), timeout=120)

    if not line:
        # EOF before any response byte. Returning an empty success would hand
        # callers something they would then try to parse.
        raise ConnectionError("connection closed before a response was received")

    return recursive_parse_orjson(line.decode().strip())


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
       if is_u128(data):
           return data
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
