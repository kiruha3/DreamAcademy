import pytest
from pydantic import ValidationError
from app.auth_router import RegisterRequest


def test_register_request_valid_role():
    req = RegisterRequest(
        email="test@example.com",
        username="testuser",
        firstname="Test",
        lastname="User",
        password="pass",
        role="student",
    )
    assert req.role == "student"


def test_register_request_invalid_role():
    with pytest.raises(ValidationError, match="role must be one of"):
        RegisterRequest(
            email="test@example.com",
            username="testuser",
            firstname="Test",
            lastname="User",
            password="pass",
            role="hacker",
        )
