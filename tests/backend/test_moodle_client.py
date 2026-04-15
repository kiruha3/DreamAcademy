from portal.backend.app.moodle_client import MoodleClient

def test_moodle_client_init():
    client = MoodleClient(base_url="http://localhost:8080", token="test_token")
    assert client.base_url == "http://localhost:8080"
    assert client.token == "test_token"

def test_moodle_client_get_users_format():
    client = MoodleClient(base_url="http://test", token="test")
    url = client._build_url("core_user_get_users", {"criteria[0][key]": "id", "criteria[0][value]": "1"})
    assert "wsfunction=core_user_get_users" in url
    assert "wstoken=test" in url
