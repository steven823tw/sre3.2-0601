"""Application-level symmetric encryption for sensitive fields.

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the cryptography library.
"""
from __future__ import annotations

import logging

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger(__name__)
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet
    settings = get_settings()
    key = getattr(settings, "ENCRYPTION_KEY", "")
    if not key:
        if settings.is_production:
            raise RuntimeError("ENCRYPTION_KEY must be set in production")
        key = Fernet.generate_key().decode()
        logger.warning("ENCRYPTION_KEY not set - generated ephemeral key")
    _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string with Fernet.

    Returns empty string for empty input (no-op) — callers should
    validate required fields *before* calling encrypt.
    """
    if not plaintext:
        logger.warning("encrypt_empty_input: caller should validate required fields")
        return ""
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken:
        logger.error("Decryption failed - key mismatch or corrupted data")
        raise


def reset_fernet() -> None:
    global _fernet
    _fernet = None
