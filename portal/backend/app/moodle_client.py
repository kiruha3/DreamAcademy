import httpx
from typing import Dict, Any, Optional

class MoodleClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _build_url(self, wsfunction: str, params: Optional[Dict[str, Any]] = None) -> str:
        url = f"{self.base_url}/webservice/rest/server.php?wstoken={self.token}&wsfunction={wsfunction}&moodlewsrestformat=json"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url += f"&{query}"
        return url

    async def get_users(self, key: str = "id", value: str = "1") -> Dict[str, Any]:
        params = {f"criteria[0][key]": key, f"criteria[0][value]": value}
        url = self._build_url("core_user_get_users", params)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def create_user(self, username: str, password: str, firstname: str, lastname: str, email: str) -> Dict[str, Any]:
        params = {
            "users[0][username]": username,
            "users[0][password]": password,
            "users[0][firstname]": firstname,
            "users[0][lastname]": lastname,
            "users[0][email]": email,
        }
        url = self._build_url("core_user_create_users", params)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_courses(self) -> Dict[str, Any]:
        url = self._build_url("core_course_get_courses")
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def enrol_user(self, course_id: int, user_id: int, role_id: int = 5) -> Dict[str, Any]:
        params = {
            "enrolments[0][roleid]": role_id,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id,
        }
        url = self._build_url("enrol_manual_enrol_users", params)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
