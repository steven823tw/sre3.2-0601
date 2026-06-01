"""Tests for app.middleware.audit — redaction helpers and action extraction."""
from __future__ import annotations

import json

import pytest

from app.middleware.audit import (
    _extract_action_and_resource,
    _redact_recursive,
    _redact_sensitive,
)


# ---------------------------------------------------------------------------
# _redact_sensitive
# ---------------------------------------------------------------------------


def test_redact_sensitive_password():
    """Sensitive fields like 'password' are replaced with [REDACTED]."""
    body = json.dumps({"username": "admin", "password": "s3cret"})
    result = json.loads(_redact_sensitive(body))
    assert result["username"] == "admin"
    assert result["password"] == "[REDACTED]"


def test_redact_sensitive_token():
    """Token fields are redacted."""
    body = json.dumps({"access_token": "eyJ...", "data": "keep"})
    result = json.loads(_redact_sensitive(body))
    assert result["access_token"] == "[REDACTED]"
    assert result["data"] == "keep"


def test_redact_sensitive_api_key():
    """api_key field is redacted (case-insensitive)."""
    body = json.dumps({"API_KEY": "sk-123", "name": "test"})
    result = json.loads(_redact_sensitive(body))
    assert result["API_KEY"] == "[REDACTED]"
    assert result["name"] == "test"


def test_redact_sensitive_nested_dict():
    """Sensitive fields inside nested dicts are redacted."""
    body = json.dumps({
        "name": "server",
        "credentials": {
            "username": "root",
            "password": "hunter2",
            "secret": "top-secret",
        },
    })
    result = json.loads(_redact_sensitive(body))
    assert result["credentials"]["username"] == "root"
    assert result["credentials"]["password"] == "[REDACTED]"
    assert result["credentials"]["secret"] == "[REDACTED]"


def test_redact_sensitive_list_of_dicts():
    """Sensitive fields inside list items are redacted."""
    body = json.dumps([
        {"name": "host1", "password": "pw1"},
        {"name": "host2", "api_key": "key2"},
    ])
    result = json.loads(_redact_sensitive(body))
    assert result[0]["name"] == "host1"
    assert result[0]["password"] == "[REDACTED]"
    assert result[1]["api_key"] == "[REDACTED]"


def test_redact_sensitive_empty_body():
    """Empty/None body is returned as-is."""
    assert _redact_sensitive("") == ""
    assert _redact_sensitive(None) is None


def test_redact_sensitive_invalid_json():
    """Non-JSON body is returned unchanged."""
    body = "not json at all"
    assert _redact_sensitive(body) == body


def test_redact_sensitive_connection_string():
    """connection_string field is redacted."""
    body = json.dumps({"connection_string": "postgresql://user:pass@host/db"})
    result = json.loads(_redact_sensitive(body))
    assert result["connection_string"] == "[REDACTED]"


# ---------------------------------------------------------------------------
# _redact_recursive
# ---------------------------------------------------------------------------


def test_redact_recursive_no_sensitive_fields():
    """Dicts without sensitive fields are left unchanged."""
    data = {"name": "web-01", "status": "running"}
    _redact_recursive(data)
    assert data["name"] == "web-01"
    assert data["status"] == "running"


def test_redact_recursive_deeply_nested():
    """Redaction works at any nesting depth."""
    data = {"level1": {"level2": {"level3": {"private_key": "rsa-key-here"}}}}
    _redact_recursive(data)
    assert data["level1"]["level2"]["level3"]["private_key"] == "[REDACTED]"


def test_redact_recursive_mixed_list_and_dict():
    """Redaction handles mixed lists and dicts."""
    data = {
        "servers": [
            {"name": "s1", "dsn": "postgres://..."},
            {"name": "s2", "encrypted_password": "enc-pw"},
        ],
        "metadata": {"credential": "mycred"},
    }
    _redact_recursive(data)
    assert data["servers"][0]["dsn"] == "[REDACTED]"
    assert data["servers"][1]["encrypted_password"] == "[REDACTED]"
    assert data["metadata"]["credential"] == "[REDACTED]"


# ---------------------------------------------------------------------------
# _extract_action_and_resource
# ---------------------------------------------------------------------------


def test_extract_action_create_asset():
    """POST /api/v1/assets maps to (create_asset, asset, None)."""
    action, rtype, rid = _extract_action_and_resource("/api/v1/assets", "POST")
    assert action == "create_asset"
    assert rtype == "asset"
    assert rid is None


def test_extract_action_read_assets():
    """GET /api/v1/assets maps to (read_asset, asset, None)."""
    action, rtype, rid = _extract_action_and_resource("/api/v1/assets", "GET")
    assert action == "read_asset"
    assert rtype == "asset"


def test_extract_action_update_with_id():
    """PUT /api/v1/assets/42 maps to (update_asset, asset, 42)."""
    action, rtype, rid = _extract_action_and_resource("/api/v1/assets/42", "PUT")
    assert action == "update_asset"
    assert rtype == "asset"
    assert rid == "42"


def test_extract_action_delete_operation():
    """DELETE /api/v1/operations/7 maps to (delete_operation, operation, 7)."""
    action, rtype, rid = _extract_action_and_resource("/api/v1/operations/7", "DELETE")
    assert action == "delete_operation"
    assert rtype == "operation"
    assert rid == "7"


def test_extract_action_unknown_path():
    """Unknown paths use the raw HTTP method (lowercased) as the action."""
    action, rtype, rid = _extract_action_and_resource("/unknown/path", "GET")
    assert action == "get"
    assert rtype is None
    assert rid is None


def test_extract_action_alerts():
    """POST /api/v1/alerts maps to (create_alert, alert, None)."""
    action, rtype, rid = _extract_action_and_resource("/api/v1/alerts", "POST")
    assert action == "create_alert"
    assert rtype == "alert"


def test_extract_action_patch_with_id():
    """PATCH /api/v1/alerts/99 maps to (update_alert, alert, 99)."""
    action, rtype, rid = _extract_action_and_resource("/api/v1/alerts/99", "PATCH")
    assert action == "update_alert"
    assert rtype == "alert"
    assert rid == "99"
