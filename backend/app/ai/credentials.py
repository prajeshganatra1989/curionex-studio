"""Encrypted AI credential helpers.

API keys are never stored in plaintext. Encryption uses Fernet with
``AI_CREDENTIALS_KEY`` (url-safe base64 32-byte key). When the key is unset,
credential writes are rejected in production-like environments and tests can
use a generated ephemeral key.
"""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class CredentialEncryptionError(RuntimeError):
    """Raised when credentials cannot be encrypted or decrypted safely."""


@lru_cache
def _fernet() -> Fernet | None:
    settings = get_settings()
    raw = settings.AI_CREDENTIALS_KEY.strip()
    if not raw:
        return None
    try:
        return Fernet(raw.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise CredentialEncryptionError(
            "AI_CREDENTIALS_KEY is invalid. Generate with Fernet.generate_key()."
        ) from exc


def require_fernet() -> Fernet:
    fernet = _fernet()
    if fernet is None:
        raise CredentialEncryptionError(
            "AI_CREDENTIALS_KEY is not configured. Set it via environment before "
            "storing provider API keys."
        )
    return fernet


def encrypt_secret(plaintext: str) -> str:
    if not plaintext:
        raise CredentialEncryptionError("Cannot encrypt an empty secret.")
    token = require_fernet().encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        raise CredentialEncryptionError("Cannot decrypt an empty ciphertext.")
    try:
        return require_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise CredentialEncryptionError("Unable to decrypt credential.") from exc


def reset_fernet_cache() -> None:
    _fernet.cache_clear()
