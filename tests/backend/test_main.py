from fastapi.testclient import TestClient
from portal.backend.app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "DreamDocs Academy" in response.json()["message"]
