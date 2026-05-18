"""Auth/security testlari — DB kerak emas."""
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_verify_ok():
    h = hash_password("supersecret")
    assert h != "supersecret"
    assert verify_password("supersecret", h) is True


def test_password_verify_wrong_returns_false():
    h = hash_password("supersecret")
    assert verify_password("WRONG", h) is False


def test_create_and_decode_token():
    token = create_access_token(subject="user-123", extra_claims={"role": "dispatcher"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "dispatcher"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_access_token("invalid.token.here")
