from fastapi.testclient import TestClient
from portal.backend.app.main import app
from portal.backend.app.invite import get_moodle_client
from portal.backend.app.moodle_client import MoodleClient
from portal.backend.app.security import get_current_user
from portal.backend.app.models import User

client = TestClient(app)

async def fake_get_users(*, key, value):
    return {"users": [{"id": 99, "email": value}]}

async def fake_create_user(*args, **kwargs):
    return [{"id": 99}]

async def fake_enrol_user(*args, **kwargs):
    return {}

def fake_get_moodle_client():
    mc = MoodleClient(base_url="http://test", token="test")
    mc.get_users = fake_get_users
    mc.create_user = fake_create_user
    mc.enrol_user = fake_enrol_user
    return mc

app.dependency_overrides[get_moodle_client] = fake_get_moodle_client

def test_invite_endpoint_requires_auth():
    response = client.post("/api/courses/1/invite", json={"email": "test@example.com"})
    assert response.status_code == 401


def test_invite_endpoint_with_auth():
    fake_user = User(
        id=1,
        email="admin@example.com",
        username="admin",
        firstname="Admin",
        lastname="User",
        role="admin",
        hashed_password="hashed",
        moodle_user_id=1,
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        response = client.post("/api/courses/1/invite", json={"email": "test@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "invited"
        assert data["course_id"] == 1
        assert data["email"] == "test@example.com"
    finally:
        del app.dependency_overrides[get_current_user]
