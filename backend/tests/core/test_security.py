"""Tests for app.core.security — password hashing and JWT tokens.

Note: bcrypt>=5.0 is incompatible with passlib's internal bug-detection
routine (detect_wrap_bug tries to hash a >72 byte secret). We mock
_pwd_context with a thin bcrypt wrapper for the password hashing tests.
JWT tests are unaffected.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import bcrypt
import pytest
from jose import JWTError, jwt

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# Helper: bcrypt-based mock that bypasses passlib's bug detection
# ---------------------------------------------------------------------------


class _BcryptHasher:
    """Minimal bcrypt hasher compatible with passlib's CryptContext interface."""

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


_mock_ctx = _BcryptHasher()


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_hash_password_returns_string():
    """hash_password returns a non-empty bcrypt hash string."""
    with patch("app.core.security._pwd_context", _mock_ctx):
        h = hash_password("mypassword")
    assert isinstance(h, str)
    assert h.startswith("$2")  # bcrypt prefix


def test_verify_password_correct():
    """verify_password returns True for the correct password."""
    with patch("app.core.security._pwd_context", _mock_ctx):
        plain = "correct-horse-battery-staple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True


def test_verify_password_wrong():
    """verify_password returns False for an incorrect password."""
    with patch("app.core.security._pwd_context", _mock_ctx):
        hashed = hash_password("real-password")
        assert verify_password("wrong-password", hashed) is False


def test_hash_password_different_hashes():
    """Hashing the same password twice produces different salts/hashes."""
    with patch("app.core.security._pwd_context", _mock_ctx):
        h1 = hash_password("same")
        h2 = hash_password("same")
    assert h1 != h2
    # But both verify correctly
    with patch("app.core.security._pwd_context", _mock_ctx):
        assert verify_password("same", h1)
        assert verify_password("same", h2)


# ---------------------------------------------------------------------------
# JWT access tokens
# ---------------------------------------------------------------------------


def test_create_access_token_returns_string():
    """create_access_token returns a non-empty JWT string."""
    token = create_access_token(subject="user-42")
    assert isinstance(token, str)
    assert len(token) > 20


def test_decode_token_valid():
    """decode_token returns correct claims for a valid token."""
    token = create_access_token(subject="user-42")
    claims = decode_token(token)
    assert claims["sub"] == "user-42"
    assert claims["type"] == "access"


def test_decode_token_extra_claims():
    """Extra claims are embedded in the token and decoded correctly."""
    token = create_access_token(
        subject="admin",
        extra_claims={"role": "admin", "org_id": 7},
    )
    claims = decode_token(token)
    assert claims["sub"] == "admin"
    assert claims["role"] == "admin"
    assert claims["org_id"] == 7


def test_decode_token_expired():
    """decode_token raises JWTError for an expired token."""
    token = create_access_token(
        subject="user",
        expires_delta=timedelta(seconds=-10),  # already expired
    )
    with pytest.raises(JWTError, match="Signature has expired"):
        decode_token(token)


def test_decode_token_wrong_secret():
    """decode_token raises JWTError when signed with a different secret."""
    token = jwt.encode(
        {"sub": "user", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "wrong-secret-key",
        algorithm="HS256",
    )
    with pytest.raises(JWTError, match="Signature"):
        decode_token(token)


# ---------------------------------------------------------------------------
# JWT refresh tokens
# ---------------------------------------------------------------------------


def test_create_refresh_token():
    """create_refresh_token returns a valid token with type=refresh."""
    token = create_refresh_token(subject="user-10")
    claims = decode_token(token)
    assert claims["sub"] == "user-10"
    assert claims["type"] == "refresh"


def test_create_access_token_custom_expiry():
    """Custom expires_delta is reflected in the token's exp claim."""
    delta = timedelta(hours=2)
    token = create_access_token(subject="user", expires_delta=delta)
    claims = decode_token(token)
    assert "exp" in claims
    # The exp should be roughly 2 hours from now (within a generous margin)
    exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    diff = (exp - now).total_seconds()
    assert 7000 < diff < 7300  # ~2 hours in seconds, with margin


# ---------------------------------------------------------------------------
# Token type validation
# ---------------------------------------------------------------------------


def test_decode_token_type_validation_access():
    """decode_token with expected_type='access' accepts access tokens."""
    token = create_access_token(subject="user")
    claims = decode_token(token, expected_type="access")
    assert claims["type"] == "access"


def test_decode_token_type_validation_refresh_rejected():
    """decode_token with expected_type='access' rejects refresh tokens."""
    token = create_refresh_token(subject="user")
    with pytest.raises(ValueError, match="Expected token type 'access'"):
        decode_token(token, expected_type="access")


def test_decode_token_type_validation_refresh_accepted():
    """decode_token with expected_type='refresh' accepts refresh tokens."""
    token = create_refresh_token(subject="user")
    claims = decode_token(token, expected_type="refresh")
    assert claims["type"] == "refresh"


def test_decode_token_no_type_validation():
    """decode_token without expected_type accepts any token type."""
    access = create_access_token(subject="user")
    refresh = create_refresh_token(subject="user")
    assert decode_token(access)["type"] == "access"
    assert decode_token(refresh)["type"] == "refresh"
