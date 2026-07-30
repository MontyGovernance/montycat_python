"""A request is a subscription because the caller supplied a callback, never
because its payload happens to contain the word "subscribe".

Regression: subscription mode used to be detected with ``b"subscribe" in query``,
so inserting a record whose value contained that word routed the call into the
streaming branch, which never returns.
"""

import asyncio
import unittest

from montycat.core.utils import send_data

RESPONSE = b'{"status":true,"payload":"1","error":null}\n'


async def stub_engine():
    """Read a newline-framed request, answer it, keep the connection open --
    the same loop the server's main_server/connection.rs runs."""

    async def handle(reader, writer):
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                writer.write(RESPONSE)
                await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


class SubscriptionDetectionTests(unittest.IsolatedAsyncioTestCase):
    async def _round_trip(self, note):
        server, port = await stub_engine()
        try:
            query = b'{"command":"insert_value","value":"{\\"note\\":\\"%s\\"}"}' % note.encode()
            return await asyncio.wait_for(
                send_data("127.0.0.1", port, query), timeout=5
            )
        finally:
            server.close()
            await server.wait_closed()

    async def test_value_containing_subscribe_is_not_a_subscription(self):
        # control
        self.assertEqual((await self._round_trip("hello"))["status"], True)

        for note in ("please subscribe", "subscribe", "unsubscribe from this"):
            with self.subTest(note=note):
                response = await self._round_trip(note)
                self.assertEqual(
                    response["status"],
                    True,
                    f"a value containing {note!r} must not be routed into the "
                    "streaming branch",
                )


if __name__ == "__main__":
    unittest.main()
