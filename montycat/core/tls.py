"""Client-side TLS settings: what to encrypt with, and whom to trust.

The CLI that ships with the engine can pin the engine's certificate exactly,
because it reads the very file the listener loaded — same package, same host.
A client library has no such luxury. It runs somewhere else entirely, and the
only trust material it has is whatever the operator copied over.

So verification here is opt-in, and it accepts whichever form of that material
the operator actually has:

- ``certificate_path`` — the engine's certificate, copied to the client host.
- ``certificate_fingerprint`` — its SHA-256 digest, which travels in an
  environment variable and needs no file. Read one with::

      openssl x509 -in server.crt -noout -fingerprint -sha256

- neither, with ``certificate_verification=True`` — the operating system's
  trust store with ordinary hostname checking, for an engine behind a proxy
  holding a certificate from a real CA.

Both pinning forms compare the certificate the engine presents against the one
expected, byte for byte, and skip hostname checking: the engine's self-signed
certificate carries only ``localhost``, ``127.0.0.1`` and ``::1`` as subject
alternative names unless it was regenerated with ``init-self-tls dns/ip``, so
requiring a hostname match would reject a perfectly good certificate for the
wrong reason. Identity is already answered exactly by the comparison.
"""

import hashlib
import ssl
from typing import Optional, Tuple, Union

_BEGIN_CERTIFICATE = "-----BEGIN CERTIFICATE-----"
_END_CERTIFICATE = "-----END CERTIFICATE-----"


class TlsVerificationError(Exception):
    """The engine presented a certificate other than the expected one.

    Raised during connection setup, so it surfaces the same way any other
    connection failure does on this client: the request path turns it into an
    ``"Error: ..."`` string rather than propagating it.
    """


def normalize_fingerprint(value: str, source: str = "certificate_fingerprint") -> str:
    """Accept a SHA-256 fingerprint in any of the shapes tools print it in.

    ``openssl`` emits colon-separated uppercase, some dashboards emit bare
    lowercase, and a value pasted from either should work without the operator
    having to reformat it.
    """
    cleaned: str = (
        value.strip().replace(":", "").replace(" ", "").replace("-", "").lower()
    )

    if len(cleaned) != 64 or any(character not in "0123456789abcdef" for character in cleaned):
        raise ValueError(
            f"{source} must be a SHA-256 fingerprint (64 hex characters, "
            f"optionally colon-separated); got {value!r}"
        )

    return cleaned


def _first_certificate(pem: str, source: str) -> str:
    """The first certificate in a PEM file.

    A file may hold a chain. The engine presents its leaf first, so the leaf is
    what a pin compares against.
    """
    start: int = pem.find(_BEGIN_CERTIFICATE)
    end: int = (
        pem.find(_END_CERTIFICATE, start + len(_BEGIN_CERTIFICATE)) if start != -1 else -1
    )

    if start == -1 or end == -1:
        raise ValueError(f"no PEM certificate found in {source}")

    return pem[start : end + len(_END_CERTIFICATE)] + "\n"


class TlsOptions:
    """How this client connects, and what it requires of the far end.

    Constructed for you by :class:`montycat.Engine`; build one directly only
    when calling :func:`montycat.core.utils.send_data` yourself.

    Args:
        enabled: Use TLS at all. Everything else is meaningless without it.
        verification: Verify the engine's certificate. ``None`` (the default)
            means "whatever the other arguments imply": on when a pin is given,
            off otherwise — which keeps existing TLS callers working unchanged.
            Passing ``False`` alongside a pin is a contradiction and raises.
        certificate_path: Path to the engine's certificate in PEM form.
        certificate_fingerprint: Its SHA-256 digest, as an alternative to the
            file.

    Raises:
        ValueError: If the combination cannot mean anything coherent, or if the
            certificate file cannot be read or parsed. Both are raised at
            construction rather than at first request, so a misconfiguration
            fails where it was written.
    """

    __slots__ = (
        "enabled",
        "verification",
        "certificate_path",
        "certificate_fingerprint",
        "_expected_der",
        "_expected_fingerprint",
    )

    def __init__(
        self,
        enabled: bool = False,
        verification: Optional[bool] = None,
        certificate_path: Optional[str] = None,
        certificate_fingerprint: Optional[str] = None,
    ) -> None:
        pinned: bool = certificate_path is not None or certificate_fingerprint is not None

        if verification is None:
            verification = pinned
        elif not verification and pinned:
            raise ValueError(
                "certificate_verification=False contradicts certificate_path / "
                "certificate_fingerprint. Drop the pin to connect without "
                "verification, or drop the argument to verify against the pin."
            )

        if (verification or pinned) and not enabled:
            raise ValueError(
                "certificate verification requires TLS; pass tls=True as well "
                "(there is nothing to verify on a plaintext connection)"
            )

        self.enabled = enabled
        self.verification = verification
        self.certificate_path = certificate_path
        self.certificate_fingerprint = certificate_fingerprint
        self._expected_der: Optional[bytes] = None
        self._expected_fingerprint: Optional[str] = None

        if certificate_fingerprint is not None:
            self._expected_fingerprint = normalize_fingerprint(certificate_fingerprint)

        if certificate_path is not None:
            self._expected_der = self._load_certificate(certificate_path)
            loaded: str = hashlib.sha256(self._expected_der).hexdigest()

            # Both forms given: they must agree, or the operator believes
            # something about this connection that is not true.
            if self._expected_fingerprint is not None and self._expected_fingerprint != loaded:
                raise ValueError(
                    f"certificate_fingerprint does not match the certificate at "
                    f"{certificate_path} (that file is {loaded})"
                )

            self._expected_fingerprint = loaded

    @staticmethod
    def _load_certificate(path: str) -> bytes:
        try:
            with open(path, "r", encoding="ascii", errors="strict") as handle:
                pem: str = handle.read()
        except OSError as error:
            raise ValueError(f"could not read certificate_path {path}: {error}") from error

        try:
            return ssl.PEM_cert_to_DER_cert(_first_certificate(pem, path))
        except ValueError as error:
            raise ValueError(f"could not parse the certificate at {path}: {error}") from error

    @property
    def pinned(self) -> bool:
        """Is identity decided by comparison rather than by a trust store?"""
        return self._expected_fingerprint is not None

    @classmethod
    def coerce(cls, value: Union[bool, "TlsOptions", None]) -> "TlsOptions":
        """Accept the historical ``tls=True`` / ``tls=False`` as well as options.

        ``send_data`` has always taken a bool here, and callers outside this
        package pass one. They keep working, and get exactly what they got
        before: encryption without verification.
        """
        if isinstance(value, cls):
            return value
        return cls(enabled=bool(value))

    def pool_key(self) -> Tuple:
        """The part of a pool's identity that this configuration decides.

        Connections with different trust requirements are not interchangeable,
        so two engines pointing at one address with different pins must not
        share pooled connections.
        """
        return (self.enabled, self.verification, self._expected_fingerprint)

    def ssl_context(self) -> Optional[ssl.SSLContext]:
        """The context to hand :func:`asyncio.open_connection`, or ``None``."""
        if not self.enabled:
            return None

        if self.pinned:
            # Identity is settled after the handshake by comparing the
            # certificate itself, so the library's own checks are turned off
            # rather than duplicated — see this module's docstring for why
            # hostname checking in particular would reject valid certificates.
            context: ssl.SSLContext = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context

        if self.verification:
            return ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    def verify_peer(self, ssl_object) -> None:
        """Check the certificate the engine presented against the pin.

        A no-op unless pinning: the other modes were already decided by
        OpenSSL during the handshake.

        Raises:
            TlsVerificationError: If the engine presented anything else.
        """
        if not self.pinned:
            return

        if ssl_object is None:
            raise TlsVerificationError(
                "a certificate pin was configured but the connection is not TLS"
            )

        presented: Optional[bytes] = ssl_object.getpeercert(binary_form=True)
        if not presented:
            raise TlsVerificationError(
                "the engine presented no certificate to compare against the pin"
            )

        if self._expected_der is not None:
            if presented == self._expected_der:
                return
        elif hashlib.sha256(presented).hexdigest() == self._expected_fingerprint:
            return

        # Naming what actually arrived is what makes this fixable: the usual
        # cause is a regenerated certificate, not an attack, and the operator
        # needs the new value to update the pin.
        raise TlsVerificationError(
            "the engine presented a certificate that is not the expected one "
            f"(expected {self._expected_fingerprint}, got "
            f"{hashlib.sha256(presented).hexdigest()}). Update the pin if the "
            "engine's certificate was regenerated, or check what is listening "
            "on this port."
        )

    def __repr__(self) -> str:
        if not self.enabled:
            return "TlsOptions(enabled=False)"
        if self.pinned:
            return f"TlsOptions(enabled=True, pinned={self._expected_fingerprint})"
        return f"TlsOptions(enabled=True, verification={self.verification})"
