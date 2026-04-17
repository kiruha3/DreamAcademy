import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("MOODLE_DATABASE_HOST", "localhost")
os.environ.setdefault("MOODLE_URL", "http://185.112.226.84:62080")
os.environ.setdefault("MOODLE_PUBLIC_URL", "http://185.112.226.84:62080")
os.environ.setdefault("MOODLE_TOKEN", "acb6c0eeb8d4cc046fe4bb2f86a79c32")

# Force re-import with local DB configs
import sys
for key in list(sys.modules.keys()):
    if key.startswith("app."):
        del sys.modules[key]

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import get_current_user
from app.modules_router import require_course_access
from app.models import User
from app.moodle_client import MoodleClient
from app.modules_router import get_moodle_client

# Force moodle_db to use localhost when running tests on Windows
# Patch both the standalone module and the one referenced by modules_router
import app.moodle_db as _mdb
_mdb.DB_HOST = "localhost"
import app.modules_router as _mr
_mr.moodle_db.DB_HOST = "localhost"

client = TestClient(app)


def make_fake_user(role="student", moodle_user_id=1):
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        firstname="Test",
        lastname="User",
        role=role,
        hashed_password="hashed",
        moodle_user_id=moodle_user_id,
    )


def test_get_book_chapters_via_api():
    fake_user = make_fake_user("admin")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[require_course_access] = lambda: None

    try:
        # Use course 72 (car repair) which has books
        import app.moodle_db as db
        with db._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, course FROM mdl_book WHERE course = 72 LIMIT 1")
                row = cur.fetchone()
        if not row:
            pytest.skip("No book found in course 72")
        book_id = row["id"]

        with db._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM mdl_course_modules WHERE instance = %s AND module = (SELECT id FROM mdl_modules WHERE name = 'book')",
                    (book_id,),
                )
                cm_row = cur.fetchone()
        if not cm_row:
            pytest.skip("No course_module for book")
        cmid = cm_row["id"]

        response = client.get(f"/api/courses/72/modules/{cmid}/book/chapters")
        assert response.status_code == 200
        data = response.json()
        assert "chapters" in data
        assert len(data["chapters"]) > 0
        for ch in data["chapters"]:
            assert "id" in ch
            assert "title" in ch
            assert "content" in ch
    finally:
        app.dependency_overrides.clear()


def test_get_module_detail():
    fake_user = make_fake_user("admin")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[require_course_access] = lambda: None

    try:
        import app.moodle_db as db
        with db._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, instance, module FROM mdl_course_modules WHERE course = 72 AND module = (SELECT id FROM mdl_modules WHERE name = 'page') LIMIT 1")
                row = cur.fetchone()
        if not row:
            pytest.skip("No page module in course 72")
        cmid = row["id"]

        response = client.get(f"/api/courses/72/modules/{cmid}")
        assert response.status_code == 200
        data = response.json()
        assert data["modname"] == "page"
        assert "content" in data
    finally:
        app.dependency_overrides.clear()


def test_start_quiz_with_questions():
    fake_user = make_fake_user("student", moodle_user_id=2)
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[require_course_access] = lambda: None

    # Mock the shared MoodleClient.get_course_contents to include a fake quiz
    class FakeClient:
        async def get_course_contents(self, course_id):
            return [{"modules": [{"id": 9999, "modname": "quiz", "instance": 8888}]}]
        async def close(self):
            pass

    # Mock user-specific client (supports async context manager)
    class FakeUserClient:
        async def start_quiz_attempt(self, quiz_id):
            return {"attempt": {"id": 12345}, "messages": []}
        async def close(self):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    import app.modules_router as mr
    original_get_user_moodle_client = mr.get_user_moodle_client

    # Use app.dependency_overrides for FastAPI-injected dependencies
    from app.modules_router import get_moodle_client
    app.dependency_overrides[get_moodle_client] = lambda: FakeClient()
    mr.get_user_moodle_client = lambda user_id: FakeUserClient()

    try:
        response = client.post("/api/courses/72/modules/9999/quiz/start")
        assert response.status_code == 200
        data = response.json()
        assert data["attempt"]["id"] == 12345
    finally:
        mr.get_user_moodle_client = original_get_user_moodle_client
        app.dependency_overrides.clear()


def test_start_quiz_without_questions_returns_400():
    fake_user = make_fake_user("student", moodle_user_id=2)
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[require_course_access] = lambda: None

    class FakeClient:
        async def get_course_contents(self, course_id):
            return [{"modules": [{"id": 9998, "modname": "quiz", "instance": 8887}]}]
        async def close(self):
            pass

    class FakeUserClientNoQuestions:
        async def start_quiz_attempt(self, quiz_id):
            raise Exception("noquestionsfound")
        async def close(self):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    import app.modules_router as mr
    original_get_user_moodle_client = mr.get_user_moodle_client

    from app.modules_router import get_moodle_client
    app.dependency_overrides[get_moodle_client] = lambda: FakeClient()
    mr.get_user_moodle_client = lambda user_id: FakeUserClientNoQuestions()

    try:
        response = client.post("/api/courses/72/modules/9998/quiz/start")
        assert response.status_code == 400
        assert "нет вопросов" in response.json()["detail"]
    finally:
        mr.get_user_moodle_client = original_get_user_moodle_client
        app.dependency_overrides.clear()
