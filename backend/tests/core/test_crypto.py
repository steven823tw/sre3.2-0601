"""Tests for app.core.crypto — Fernet encrypt/decrypt and key management."""
from __future__ import annotations

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.core.crypto import decrypt, encrypt, reset_fernet


@pytest.fixture(autouse=True)
def _clean_fernet():
    """Reset the global Fernet instance before each test."""
    reset_fernet()
    yield
    reset_fernet()


def test_encrypt_decrypt_roundtrip():
    """Encrypting then decrypting returns the original plaintext."""
    plaintext = "super-secret-password-123"
    ciphertext = encrypt(plaintext)
    assert ciphertext != plaintext
    assert decrypt(ciphertext) == plaintext


def test_encrypt_empty_string():
    """Encrypting an empty string returns an empty string."""
    assert encrypt("") == ""


def test_decrypt_empty_string():
    """Decrypting an empty string returns an empty string."""
    assert decrypt("") == ""


def test_decrypt_invalid_token_raises():
    """Decrypting garbage data raises InvalidToken."""
    with pytest.raises(InvalidToken):
        decrypt("not-a-valid-fernet-token!!!")


def test_reset_fernet_clears_cache():
    """reset_fernet clears the cached Fernet instance so a new key is used."""
    # Encrypt with the first key
    ciphertext = encrypt("hello")

    # Reset — a new ephemeral key will be generated on next use
    reset_fernet()

    # Decrypting with the new key must fail
    with pytest.raises(InvalidToken):
        decrypt(ciphertext)


def test_encrypt_produces_different_ciphertext():
    """Fernet uses a random IV, so the same plaintext encrypts differently."""
    plaintext = "same-value"
    c1 = encrypt(plaintext)
    c2 = encrypt(plaintext)
    assert c1 != c2
    # Both must still decrypt to the same value
    assert decrypt(c1) == plaintext
    assert decrypt(c2) == plaintext


def test_encrypt_unicode_text():
    """Encrypting and decrypting Unicode text works correctly."""
    plaintext = "数据库密码-secret-パスワード"
    assert decrypt(encrypt(plaintext)) == plaintext
