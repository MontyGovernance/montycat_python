"""Connection pooling behaviour.

Covers the required matrix in
``montycat_semantic/CLIENT_CONNECTION_POOLING_CONTRACT.md`` §9. Stub asyncio
servers throughout; no live engine required.
"""

import asyncio
import unittest

from montycat.core.pool import PoolConfig, close_all_pools, get_pool
from montycat.core.utils import send_data

OK = b'{"status":true,"payload":null,"error":null}\n'


class StubServer:
    """Newline-framed echo server that counts accepted connections."""

    def __init__(self, responder=None, close_after=None):
        self.accepts = 0
        self._responder = responder
        self._close_after = close_after
        self._server = None
        self.host = "127.0.0.1"
        self.port = None

    async def __aenter__(self):
        self._server = await asyncio.start_server(self._handle, self.host, 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc):
        # Drain client-side pools first. `wait_closed()` waits for every handler
        # task, and a pooled connection stays open by design — so closing the
        # server while the pool still holds one deadlocks the test, not the
        # client. Shut the clients down before the server, as in production.
        await close_all_pools()
        self._server.close()
        try:
            await asyncio.wait_for(self._server.wait_closed(), timeout=2)
        except asyncio.TimeoutError:
            pass

    async def _handle(self, reader, writer):
        index = self.accepts
        self.accepts += 1
        served = 0
        try:
            while True:
                # Mirrors the engine: read a request, write a response, repeat
                # until the client hangs up.
                line = await reader.readline()
                if not line:
                    return
                if self._responder is None:
                    writer.write(OK)
                else:
                    payload = self._responder(index, served)
                    if payload is None:
                        return  # die without responding
                    writer.write(payload)
                await writer.drain()
                served += 1
                if self._close_after is not None and served >= self._close_after(index):
                    return
        except Exception:
            return
        finally:
            try:
                writer.close()
            except Exception:
                pass


def run(coro):
    return asyncio.run(coro)


class PoolTests(unittest.TestCase):
    def setUp(self):
        run(close_all_pools())

    def tearDown(self):
        run(close_all_pools())

    def test_pooling_is_off_by_default(self):
        async def scenario():
            async with StubServer() as server:
                for _ in range(5):
                    await send_data(server.host, server.port, b"{}")
                return server.accepts

        self.assertEqual(
            run(scenario()), 5, "unpooled client must not reuse connections"
        )

    def test_sequential_requests_reuse_one_connection(self):
        async def scenario():
            config = PoolConfig()
            async with StubServer() as server:
                for _ in range(10):
                    await send_data(
                        server.host, server.port, b"{}", pool_config=config
                    )
                pool = get_pool(server.host, server.port, False, config)
                return server.accepts, pool.idle_len()

        accepts, idle = run(scenario())
        self.assertEqual(accepts, 1, "10 requests should share one connection")
        self.assertEqual(idle, 1)

    def test_max_idle_is_respected(self):
        async def scenario():
            config = PoolConfig(max_idle=2)
            async with StubServer() as server:
                # Concurrency forces several live connections at once; only
                # max_idle of them may be retained afterwards.
                await asyncio.gather(
                    *(
                        send_data(server.host, server.port, b"{}", pool_config=config)
                        for _ in range(8)
                    )
                )
                pool = get_pool(server.host, server.port, False, config)
                return pool.idle_len()

        self.assertLessEqual(run(scenario()), 2, "pool grew past max_idle")

    def test_idle_timeout_discards_the_connection(self):
        async def scenario():
            config = PoolConfig(idle_timeout=0.05)
            async with StubServer() as server:
                await send_data(server.host, server.port, b"{}", pool_config=config)
                first = server.accepts
                await asyncio.sleep(0.12)
                await send_data(server.host, server.port, b"{}", pool_config=config)
                return first, server.accepts

        first, second = run(scenario())
        self.assertEqual(first, 1)
        self.assertEqual(
            second, 2, "an expired connection was reused instead of discarded"
        )

    def test_server_closed_idle_connection_does_not_break_the_next_request(self):
        # The stale-socket case. The mechanism is not a failing write — writing
        # to a peer-closed socket normally succeeds. The pool detects the dead
        # connection at checkout and opens a fresh one, so the request is sent
        # exactly once and never replayed.
        async def scenario():
            config = PoolConfig()
            # First connection serves one request then hangs up.
            async with StubServer(close_after=lambda i: 1 if i == 0 else 10**9) as server:
                first = await send_data(
                    server.host, server.port, b"{}", pool_config=config
                )
                await asyncio.sleep(0.08)
                second = await send_data(
                    server.host, server.port, b"{}", pool_config=config
                )
                return first, second, server.accepts

        first, second, accepts = run(scenario())
        self.assertIsInstance(first, dict)
        self.assertIsInstance(
            second, dict, f"stale connection was not replaced cleanly: {second!r}"
        )
        self.assertEqual(second.get("status"), True)
        self.assertEqual(accepts, 2, "expected exactly one fresh connection")

    def test_read_failure_is_not_retried(self):
        # The rule whose violation duplicates user data: the engine may have
        # applied the write already and only the response was lost.
        async def scenario():
            config = PoolConfig()
            async with StubServer(responder=lambda i, s: None) as server:
                result = await send_data(
                    server.host, server.port, b"{}", pool_config=config
                )
                return result, server.accepts

        result, accepts = run(scenario())
        self.assertEqual(
            accepts, 1, "a read-phase failure was retried — contract §4 forbids it"
        )
        self.assertIsInstance(
            result, str, "EOF before a response must not look like a successful reply"
        )
        self.assertIn("Error:", result)

    def test_no_bytes_leak_between_two_pooled_requests(self):
        # Distinct payloads, so a leaked byte from response one corrupts two.
        def responder(index, served):
            return b'{"status":true,"payload":"response-%d"}\n' % served

        async def scenario():
            config = PoolConfig()
            async with StubServer(responder=responder) as server:
                first = await send_data(
                    server.host, server.port, b"{}", pool_config=config
                )
                second = await send_data(
                    server.host, server.port, b"{}", pool_config=config
                )
                return first, second, server.accepts

        first, second, accepts = run(scenario())
        self.assertEqual(accepts, 1, "the two requests did not share a connection")
        self.assertEqual(first.get("payload"), "response-0")
        self.assertEqual(second.get("payload"), "response-1")

    def test_two_frames_in_one_write_do_not_merge(self):
        # A reader that stops when its buffer merely *contains* a newline would
        # swallow frame two into frame one — on a pooled connection that is the
        # next caller's response.
        def responder(index, served):
            if served == 0:
                return (
                    b'{"status":true,"payload":"first"}\n'
                    b'{"status":true,"payload":"second"}\n'
                )
            return b'{"status":true,"payload":"third"}\n'

        async def scenario():
            config = PoolConfig()
            async with StubServer(responder=responder) as server:
                first = await send_data(
                    server.host, server.port, b"{}", pool_config=config
                )
                return first

        first = run(scenario())
        self.assertEqual(
            first.get("payload"),
            "first",
            "the following frame leaked into this response",
        )

    def test_subscription_is_never_pooled(self):
        # A real subscription streams frames unprompted, which is what lets the
        # loop observe `stop_event` between reads. Note the loop cannot see the
        # event while blocked inside `readline()` — a pre-existing property of
        # this client, unrelated to pooling — so the stub must keep pushing.
        frames = []

        async def push_frames(reader, writer):
            try:
                await reader.readline()  # the subscribe request
                for _ in range(50):
                    writer.write(b'{"status":true,"payload":"event"}\n')
                    await writer.drain()
                    await asyncio.sleep(0.02)
            except Exception:
                return

        async def scenario():
            config = PoolConfig()
            server = await asyncio.start_server(push_frames, "127.0.0.1", 0)
            port = server.sockets[0].getsockname()[1]
            try:
                stop = asyncio.Event()

                async def stop_soon():
                    await asyncio.sleep(0.1)
                    stop.set()

                stopper = asyncio.create_task(stop_soon())
                await send_data(
                    "127.0.0.1",
                    port,
                    b"{}",
                    callback=frames.append,
                    stop_event=stop,
                    tls=False,
                    pool_config=config,
                )
                await stopper
                pool = get_pool("127.0.0.1", port, False, config)
                return pool.idle_len()
            finally:
                server.close()

        idle = run(scenario())
        self.assertEqual(
            idle, 0, "a subscription connection was returned to the pool (contract §5)"
        )
        self.assertTrue(frames, "subscription delivered no frames")
        self.assertEqual(
            frames[0].get("payload"), "event", "frames were not parsed one at a time"
        )

    def test_stop_event_ends_a_quiet_subscription(self):
        # The server sends one frame and then goes silent. Setting the stop event
        # must end the subscription anyway. Checking the event only between reads
        # left the task blocked in readline() forever: the socket never closed,
        # so the server's watchers stayed alive and later remove_keyspace /
        # remove_store calls on that store deadlocked.
        frames = []

        async def one_frame_then_silence(reader, writer):
            try:
                await reader.readline()
                writer.write(b'{"status":true,"payload":"only-event"}\n')
                await writer.drain()
                await asyncio.sleep(30)  # never sends again
            except Exception:
                return

        async def scenario():
            server = await asyncio.start_server(one_frame_then_silence, "127.0.0.1", 0)
            port = server.sockets[0].getsockname()[1]
            try:
                stop = asyncio.Event()

                async def stop_soon():
                    await asyncio.sleep(0.1)
                    stop.set()

                stopper = asyncio.create_task(stop_soon())
                # If the stop event cannot interrupt a blocked read this never
                # returns, and the wait_for below fails the test rather than
                # hanging the suite.
                await asyncio.wait_for(
                    send_data(
                        "127.0.0.1",
                        port,
                        b"{}",
                        callback=frames.append,
                        stop_event=stop,
                    ),
                    timeout=5,
                )
                await stopper
            finally:
                server.close()

        run(scenario())
        self.assertEqual(len(frames), 1, "expected exactly the one frame sent")
        self.assertEqual(frames[0].get("payload"), "only-event")

    def test_close_all_pools_drains_connections(self):
        async def scenario():
            config = PoolConfig()
            async with StubServer() as server:
                await send_data(server.host, server.port, b"{}", pool_config=config)
                pool = get_pool(server.host, server.port, False, config)
                before = pool.idle_len()
                await close_all_pools()
                return before, pool.idle_len()

        before, after = run(scenario())
        self.assertEqual(before, 1)
        self.assertEqual(after, 0, "close_all_pools left connections behind")

    def test_tls_flag_is_part_of_the_registry_key(self):
        # A plaintext and a TLS connection to one address are not interchangeable.
        config = PoolConfig()
        plain = get_pool("127.0.0.1", 21210, False, config)
        secure = get_pool("127.0.0.1", 21210, True, config)
        self.assertIsNot(plain, secure)

    def test_no_config_means_no_pool(self):
        self.assertIsNone(get_pool("127.0.0.1", 21210, False, None))


if __name__ == "__main__":
    unittest.main()
