"""Connection pooling for request/response traffic.

Implements the client half of
``montycat_semantic/CLIENT_CONNECTION_POOLING_CONTRACT.md``. The rules that
shape this module:

- **§3** — pooling by ``(host, port, tls)`` is safe: credentials travel in every
  request payload and the engine re-authenticates per request, so a pooled
  connection carries no identity and may serve different users.
- **§4** — never replay a request after a read failure; the engine may have
  applied it already. Stale connections are caught by a health check at
  checkout, not by waiting for a write to fail.
- **§5** — subscriptions are never pooled.
- **§6** — pooling is opt-in and bounded; an idle pooled connection still holds
  a server permit.
- **§7** — the reader doing the line splitting travels with the connection, so
  bytes past the newline are not lost between requests.

The pool lives in a module-level registry rather than on the ``Engine``, because
``connect_engine`` copies six scalars onto the keyspace class and discards the
engine object — nothing downstream holds a reference to it.
"""

import asyncio
import select
import time
from typing import Dict, Optional, Tuple


class PoolConfig:
    """How many idle connections to keep, and how long to keep them.

    Defaults are deliberately conservative. An idle pooled connection still
    holds one of the engine's connection permits (``num_workers * 200``, of
    which the main listener receives 35%), so a large pool spread across many
    client processes can starve the server while mostly idle. Raise these only
    after measuring with the ``queue_depths`` command under realistic load.

    Args:
        max_idle: Maximum idle connections retained per ``(host, port, tls)``.
            Never unbounded.
        idle_timeout: Discard an idle connection older than this, in seconds.
            Keep it shorter than any server or firewall idle reaper so the
            client drops a connection before the peer does.
    """

    __slots__ = ("max_idle", "idle_timeout")

    def __init__(self, max_idle: int = 8, idle_timeout: float = 30.0):
        if max_idle < 1:
            raise ValueError("max_idle must be at least 1")
        if idle_timeout <= 0:
            raise ValueError("idle_timeout must be positive")
        self.max_idle = max_idle
        self.idle_timeout = idle_timeout

    def __repr__(self) -> str:
        return (
            f"PoolConfig(max_idle={self.max_idle}, "
            f"idle_timeout={self.idle_timeout})"
        )


def _is_healthy(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> bool:
    """Is this connection still usable for a fresh request/response exchange?

    Checked at checkout rather than by waiting for the write to fail, because
    writing to a peer-closed socket normally *succeeds* — the bytes land in the
    send buffer and the reset arrives later. The request would then read EOF,
    which is indistinguishable from "the engine applied the write and the
    response was lost", the one case contract §4 forbids retrying.

    A quiet socket is healthy. Readable before we have sent anything means
    either EOF (the peer hung up) or unsolicited bytes left over from a previous
    response; both would corrupt the next exchange.

    Deliberately uses a zero-timeout ``select`` rather than an awaited timeout:
    the Rust client first used a zero-duration timer here, and timer granularity
    made every checkout cost a millisecond, which was slower than not pooling.
    """
    if writer.is_closing():
        return False

    if reader.at_eof():
        return False

    # Anything already buffered means a previous response was not fully
    # consumed, which would desynchronise the next caller's read.
    buffered = getattr(reader, "_buffer", None)
    if buffered:
        return False

    sock = writer.get_extra_info("socket")
    if sock is None:
        return False

    try:
        readable, _, errored = select.select([sock], [], [sock], 0)
    except (OSError, ValueError):
        return False

    return not readable and not errored


class ConnectionPool:
    """A bounded set of idle connections for one ``(host, port, tls)`` target."""

    def __init__(self, config: PoolConfig):
        self._config = config
        self._idle: list = []  # (reader, writer, idle_since), most recent last
        self._lock = asyncio.Lock()

    @property
    def config(self) -> PoolConfig:
        return self._config

    def idle_len(self) -> int:
        """Idle connections currently held. Test and diagnostic use."""
        return len(self._idle)

    async def checkout(self) -> Optional[Tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
        """Take a healthy idle connection, discarding any that aged out or died.

        Returns ``None`` when nothing usable is left; the caller then opens a
        fresh connection. The connection is removed from the pool, so it is held
        exclusively for the duration of one request/response — two coroutines
        interleaving writes on one socket would deliver a response to the wrong
        caller.
        """
        async with self._lock:
            while self._idle:
                reader, writer, idle_since = self._idle.pop()
                aged_out = (time.monotonic() - idle_since) >= self._config.idle_timeout
                if aged_out or not _is_healthy(reader, writer):
                    await _close(writer)
                    continue
                return reader, writer
        return None

    async def checkin(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Return a healthy connection.

        Callers must not return a connection that errored, was cancelled
        mid-exchange, or carried a subscription.
        """
        async with self._lock:
            if len(self._idle) >= self._config.max_idle:
                await _close(writer)
                return
            self._idle.append((reader, writer, time.monotonic()))

    async def close(self) -> None:
        """Drain and close every idle connection."""
        async with self._lock:
            entries, self._idle = self._idle, []
        for _reader, writer, _idle_since in entries:
            await _close(writer)


async def _close(writer: asyncio.StreamWriter) -> None:
    """Close a writer, swallowing the errors a dead peer produces."""
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


# One pool per target. Keyed on tls as well as host/port: a plaintext and a TLS
# connection to the same address are not interchangeable.
_POOLS: Dict[Tuple[str, int, bool], ConnectionPool] = {}


def get_pool(
    host: str, port: int, tls: bool, config: Optional[PoolConfig]
) -> Optional[ConnectionPool]:
    """The pool for this target, creating it on first use.

    Returns ``None`` when ``config`` is ``None``, which is how pooling stays
    opt-in: the caller then connects per request exactly as before.
    """
    if config is None:
        return None
    key = (host, port, tls)
    pool = _POOLS.get(key)
    if pool is None:
        pool = ConnectionPool(config)
        _POOLS[key] = pool
    return pool


async def close_all_pools() -> None:
    """Drain every pool. Call before process exit, and between test cases."""
    pools, _POOLS_snapshot = list(_POOLS.values()), None
    _POOLS.clear()
    for pool in pools:
        await pool.close()
