"""Dependency-free encrypted token vault boundary for local development."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets


class TokenVaultError(ValueError):
    pass


class LocalTokenVault:
    version = 1

    def __init__(self, master_key: str) -> None:
        if len(master_key.encode()) < 32:
            raise TokenVaultError("Vault master key must contain at least 32 bytes")
        self._master_key = master_key.encode()

    def _key(self, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", self._master_key, salt, 120_000, dklen=32)

    @staticmethod
    def _stream(key: bytes, nonce: bytes, size: int) -> bytes:
        blocks = [
            hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
            for counter in range((size + 31) // 32)
        ]
        return b"".join(blocks)[:size]

    def encrypt(self, value: str) -> str:
        if not value:
            raise TokenVaultError("Cannot encrypt an empty token")
        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(16)
        key = self._key(salt)
        plaintext = value.encode()
        stream = self._stream(key, nonce, len(plaintext))
        ciphertext = bytes(left ^ right for left, right in zip(plaintext, stream, strict=True))
        tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        payload = {
            "v": self.version,
            "s": base64.urlsafe_b64encode(salt).decode(),
            "n": base64.urlsafe_b64encode(nonce).decode(),
            "c": base64.urlsafe_b64encode(ciphertext).decode(),
            "t": base64.urlsafe_b64encode(tag).decode(),
        }
        encoded = json.dumps(payload, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(encoded).decode()

    def decrypt(self, envelope: str) -> str:
        try:
            payload = json.loads(base64.urlsafe_b64decode(envelope.encode()))
            salt = base64.urlsafe_b64decode(payload["s"])
            nonce = base64.urlsafe_b64decode(payload["n"])
            ciphertext = base64.urlsafe_b64decode(payload["c"])
            supplied_tag = base64.urlsafe_b64decode(payload["t"])
        except (ValueError, KeyError, TypeError) as error:
            raise TokenVaultError("Invalid token envelope") from error
        if payload.get("v") != self.version:
            raise TokenVaultError("Unsupported token envelope")
        key = self._key(salt)
        expected_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_tag, supplied_tag):
            raise TokenVaultError("Token authentication failed")
        stream = self._stream(key, nonce, len(ciphertext))
        return bytes(left ^ right for left, right in zip(ciphertext, stream, strict=True)).decode()
