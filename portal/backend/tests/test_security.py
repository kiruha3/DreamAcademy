import pytest
from app.security import get_password_hash, verify_password, MAX_PASSWORD_BYTES


def test_password_hash_roundtrip():
    plain = "SecurePass123!"
    hashed = get_password_hash(plain)
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_password_too_long_raises():
    too_long = "a" * 100
    with pytest.raises(ValueError, match=f"exceeds {MAX_PASSWORD_BYTES} bytes"):
        get_password_hash(too_long)


def test_password_exactly_max_bytes_ok():
    # 72 ASCII chars = 72 bytes
    exact = "a" * MAX_PASSWORD_BYTES
    hashed = get_password_hash(exact)
    assert verify_password(exact, hashed) is True
