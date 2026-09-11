"""Certificate verification: what it accepts, what it refuses, what it leaves alone.

The fixtures are a real self-signed pair generated the way the engine's
``init-self-tls`` generates one — same subject, same ``localhost`` /
``127.0.0.1`` / ``::1`` SANs — so the handshake tests exercise the certificate
shape operators actually deploy, including the part that makes hostname
checking the wrong question to ask.
"""

import asyncio
import hashlib
import pathlib
import ssl
import tempfile
import unittest

from montycat import Engine
from montycat.core.tls import TlsOptions, TlsVerificationError, normalize_fingerprint
from montycat.core.utils import _close, _connect

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
CERTIFICATE = str(FIXTURES / "cert.pem")
PRIVATE_KEY = str(FIXTURES / "key.pem")
OTHER_CERTIFICATE = str(FIXTURES / "other_cert.pem")


def fingerprint_of(path: str) -> str:
    pem = pathlib.Path(path).read_text()
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()


class TheDefaultStaysWhereItWas(unittest.TestCase):
    """Verification is opt-in, and opting out of opting in changes nothing."""

    def test_plain_bool_still_means_what_it_always_meant(self):
        # Every existing caller passes a bool. Turning verification on for them
        # would break every deployment using the engine's self-signed
        # certificate, which is every default deployment.
        options = TlsOptions.coerce(True)

        self.assertTrue(options.enabled)
        self.assertFalse(options.verification)
        self.assertFalse(options.pinned)

        context = options.ssl_context()
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)
        self.assertFalse(context.check_hostname)

    def test_no_tls_means_no_context(self):
        self.assertIsNone(TlsOptions.coerce(False).ssl_context())
        self.assertIsNone(TlsOptions.coerce(None).ssl_context())

    def test_options_pass_through_coerce_untouched(self):
        options = TlsOptions(enabled=True, certificate_path=CERTIFICATE)
        self.assertIs(TlsOptions.coerce(options), options)


class FlippingTlsAfterConstruction(unittest.TestCase):
    """`Engine.from_uri(...)` then `engine.tls = True` is a documented flow.

    The Montycat MCP server does exactly this: a URI carries the endpoint and
    credentials, and TLS stays a separate opt-in from the environment. If the
    flag and the connection could disagree, a deployment would believe it was
    encrypted while sending everything in the clear.
    """

    def test_enabling_tls_afterwards_actually_enables_it(self):
        engine = Engine.from_uri("montycat://user:password@localhost:21210/store")
        self.assertIsNone(engine.tls_options.ssl_context())

        engine.tls = True

        self.assertTrue(engine.tls)
        self.assertTrue(engine.tls_options.enabled)
        self.assertIsNotNone(engine.tls_options.ssl_context())

    def test_disabling_tls_afterwards_actually_disables_it(self):
        engine = Engine(
            host="127.0.0.1",
            port=21210,
            username="user",
            password="password",
            tls=True,
        )
        self.assertIsNotNone(engine.tls_options.ssl_context())

        engine.tls = False

        self.assertFalse(engine.tls)
        self.assertIsNone(engine.tls_options.ssl_context())

    def test_a_pin_survives_a_reassignment(self):
        # Rebuilding the options must not quietly drop the trust material that
        # was configured alongside them.
        engine = Engine.from_uri(
            "montycat://user:password@localhost:21210/store",
            tls=True,
            certificate_path=CERTIFICATE,
        )
        self.assertTrue(engine.tls_options.pinned)

        engine.tls = True

        self.assertTrue(engine.tls_options.pinned)

    def test_turning_tls_off_under_a_pin_is_refused(self):
        # The pin would otherwise be silently discarded, leaving a caller who
        # asked for verification with a plaintext connection.
        engine = Engine(
            host="127.0.0.1",
            port=21210,
            username="user",
            password="password",
            tls=True,
            certificate_path=CERTIFICATE,
        )

        with self.assertRaisesRegex(ValueError, "requires TLS"):
            engine.tls = False


class TurningVerificationOn(unittest.TestCase):
    def test_a_pin_implies_verification(self):
        # Nobody should have to pass two arguments to say one thing.
        options = TlsOptions(enabled=True, certificate_path=CERTIFICATE)

        self.assertTrue(options.verification)
        self.assertTrue(options.pinned)

    def test_verification_without_a_pin_uses_the_system_trust_store(self):
        # The proxy-with-a-real-certificate case: nothing to compare against,
        # so the ordinary rules apply — a chain to a public root, and a
        # hostname that matches.
        options = TlsOptions(enabled=True, verification=True)

        self.assertFalse(options.pinned)
        context = options.ssl_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_a_pin_turns_off_hostname_checking(self):
        # The engine's certificate names localhost, 127.0.0.1 and ::1 only. An
        # operator pointing at a LAN address would fail hostname verification
        # with nothing actually wrong, and the comparison has already answered
        # the question that matters.
        context = TlsOptions(enabled=True, certificate_path=CERTIFICATE).ssl_context()

        self.assertFalse(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)

    def test_a_fingerprint_is_accepted_in_the_shape_openssl_prints_it(self):
        digest = fingerprint_of(CERTIFICATE)
        colon_separated = ":".join(
            digest[index : index + 2] for index in range(0, 64, 2)
        ).upper()

        options = TlsOptions(enabled=True, certificate_fingerprint=colon_separated)

        self.assertTrue(options.pinned)
        # Same certificate, whichever way it was named.
        self.assertEqual(
            options.pool_key(),
            TlsOptions(enabled=True, certificate_path=CERTIFICATE).pool_key(),
        )

    def test_a_fingerprint_that_cannot_be_one_is_refused(self):
        for value in ["", "not-a-fingerprint", "ab99cf", "z" * 64]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_fingerprint(value)


class CombinationsThatCannotMeanAnything(unittest.TestCase):
    def test_a_pin_with_verification_switched_off_is_a_contradiction(self):
        with self.assertRaisesRegex(ValueError, "contradicts"):
            TlsOptions(enabled=True, verification=False, certificate_path=CERTIFICATE)

    def test_verifying_a_plaintext_connection_is_refused(self):
        # Ignoring this quietly would leave someone believing a connection is
        # checked when it is not even encrypted.
        with self.assertRaisesRegex(ValueError, "requires TLS"):
            TlsOptions(enabled=False, verification=True)

        with self.assertRaisesRegex(ValueError, "requires TLS"):
            TlsOptions(enabled=False, certificate_path=CERTIFICATE)

    def test_a_fingerprint_that_disagrees_with_the_file_is_refused(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            TlsOptions(
                enabled=True,
                certificate_path=CERTIFICATE,
                certificate_fingerprint=fingerprint_of(OTHER_CERTIFICATE),
            )

    def test_an_unreadable_certificate_fails_where_it_was_configured(self):
        with self.assertRaisesRegex(ValueError, "could not read"):
            TlsOptions(enabled=True, certificate_path="/nonexistent/montycat/cert.pem")

    def test_a_file_that_is_not_a_certificate_is_named_as_such(self):
        with tempfile.NamedTemporaryFile("w", suffix=".pem") as junk:
            junk.write("just some text\n")
            junk.flush()

            with self.assertRaisesRegex(ValueError, "no PEM certificate"):
                TlsOptions(enabled=True, certificate_path=junk.name)


class PoolsKeepTrustBoundariesApart(unittest.TestCase):
    def test_different_trust_means_a_different_pool(self):
        # A connection pinned to one certificate must never be handed to a
        # caller expecting a different one, or expecting no checking at all.
        keys = [
            TlsOptions.coerce(True).pool_key(),
            TlsOptions(enabled=True, verification=True).pool_key(),
            TlsOptions(enabled=True, certificate_path=CERTIFICATE).pool_key(),
            TlsOptions(enabled=True, certificate_path=OTHER_CERTIFICATE).pool_key(),
        ]

        self.assertEqual(len(set(keys)), len(keys))


class AgainstARealListener(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(CERTIFICATE, PRIVATE_KEY)

        async def handle(reader, writer):
            try:
                await reader.readline()
                writer.write(b'{"status":true,"payload":"ok","error":null}\n')
                await writer.drain()
            finally:
                writer.close()

        self.server = await asyncio.start_server(handle, "127.0.0.1", 0, ssl=context)
        self.port = self.server.sockets[0].getsockname()[1]

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()

    async def test_the_expected_certificate_completes_a_handshake(self):
        options = TlsOptions(enabled=True, certificate_path=CERTIFICATE)
        reader, writer = await _connect("127.0.0.1", self.port, options)

        writer.write(b'{"raw":["version"],"credentials":[]}\n')
        await writer.drain()
        self.assertIn(b'"status":true', await reader.readline())

        await _close(writer)

    async def test_a_different_certificate_is_refused_before_anything_is_sent(self):
        options = TlsOptions(enabled=True, certificate_path=OTHER_CERTIFICATE)

        with self.assertRaises(TlsVerificationError) as failure:
            await _connect("127.0.0.1", self.port, options)

        # The message has to name what actually arrived: a regenerated
        # certificate is the common cause, and the operator needs the new value
        # in order to update the pin.
        self.assertIn(fingerprint_of(CERTIFICATE), str(failure.exception))

    async def test_a_fingerprint_pin_reaches_the_same_verdict_as_a_file_pin(self):
        good = TlsOptions(
            enabled=True, certificate_fingerprint=fingerprint_of(CERTIFICATE)
        )
        _, writer = await _connect("127.0.0.1", self.port, good)
        await _close(writer)

        bad = TlsOptions(
            enabled=True, certificate_fingerprint=fingerprint_of(OTHER_CERTIFICATE)
        )
        with self.assertRaises(TlsVerificationError):
            await _connect("127.0.0.1", self.port, bad)

    async def test_an_unverified_connection_still_reaches_a_self_signed_engine(self):
        # The default path, and the reason it is still the default.
        reader, writer = await _connect("127.0.0.1", self.port, TlsOptions.coerce(True))

        writer.write(b'{"raw":["version"],"credentials":[]}\n')
        await writer.drain()
        self.assertIn(b'"status":true', await reader.readline())

        await _close(writer)


if __name__ == "__main__":
    unittest.main()
