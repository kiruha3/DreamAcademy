from fastapi.testclient import TestClient
from portal.backend.app.main import app
from portal.backend.app.courses import get_moodle_client
from portal.backend.app.moodle_client import MoodleClient

client = TestClient(app)

async def fake_get_courses():
    return [{"id": 2, "fullname": "DreamDocs: Базовое обучение"}]

def fake_get_moodle_client():
    mc = MoodleClient(base_url="http://test", token="test")
    mc.get_courses = fake_get_courses
    return mc

app.dependency_overrides[get_moodle_client] = fake_get_moodle_client

def test_courses_list_structure():
    response = client.get("/api/courses")
    assert response.status_code == 200
    data = response.json()
    assert "courses" in data
    assert isinstance(data["courses"], list)
    assert data["courses"][0]["fullname"] == "DreamDocs: Базовое обучение"
