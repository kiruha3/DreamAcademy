import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.auth_router import login, LoginRequest
from app.security import get_password_hash


def test_login_syncs_moodle_user_on_first_attempt():
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = None  # No local user
    mock_query.filter.return_value = mock_filter
    mock_db.query.return_value = mock_query
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()

    def refresh_side_effect(obj):
        obj.id = 1
    mock_db.refresh = MagicMock(side_effect=refresh_side_effect)

    mock_client = AsyncMock()
    mock_client.get_users = AsyncMock(return_value={
        "users": [{
            "id": 99,
            "email": "sync@test.com",
            "username": "syncuser",
            "firstname": "Sync",
            "lastname": "User",
        }]
    })
    mock_client.update_user_password = AsyncMock(return_value=None)

    req = LoginRequest(email="sync@test.com", password="Secret123!")
    result = asyncio.run(login(req, db=mock_db, client=mock_client))

    assert result["user"].email == "sync@test.com"
    assert result["user"].moodle_user_id == 99
    assert "access_token" in result
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called()
    mock_client.update_user_password.assert_called_once_with(99, "Secret123!")


def test_login_rejects_wrong_password_for_existing_local_user():
    local_user = MagicMock()
    local_user.hashed_password = get_password_hash("CorrectPass123!")
    local_user.moodle_user_id = 1

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = local_user
    mock_query.filter.return_value = mock_filter
    mock_db.query.return_value = mock_query

    mock_client = AsyncMock()

    req = LoginRequest(email="local@test.com", password="WrongPass123!")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(login(req, db=mock_db, client=mock_client))
    assert exc_info.value.status_code == 401


def test_login_accepts_correct_password_for_existing_local_user():
    local_user = MagicMock()
    local_user.id = 1
    local_user.email = "local@test.com"
    local_user.username = "localuser"
    local_user.firstname = "Local"
    local_user.lastname = "User"
    local_user.role = "student"
    local_user.moodle_user_id = 1
    local_user.hashed_password = get_password_hash("CorrectPass123!")

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = local_user
    mock_query.filter.return_value = mock_filter
    mock_db.query.return_value = mock_db.query

    # Chain query().filter().first()
    def query_side_effect(model):
        return mock_query
    mock_db.query.side_effect = query_side_effect

    mock_client = AsyncMock()
    mock_client.update_user_password = AsyncMock(return_value=None)

    req = LoginRequest(email="local@test.com", password="CorrectPass123!")
    result = asyncio.run(login(req, db=mock_db, client=mock_client))

    assert result["user"].email == "local@test.com"
    assert "access_token" in result
    mock_client.update_user_password.assert_called_once_with(1, "CorrectPass123!")
