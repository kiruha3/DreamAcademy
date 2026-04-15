import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode

class MoodleClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _build_url(self, wsfunction: str, params: Optional[Dict[str, Any]] = None) -> str:
        url = f"{self.base_url}/webservice/rest/server.php?wstoken={self.token}&wsfunction={wsfunction}&moodlewsrestformat=json"
        if params:
            url += f"&{urlencode(params)}"
        return url

    def _check_moodle_error(self, data: Dict[str, Any]) -> None:
        if isinstance(data, dict) and "exception" in data:
            msg = data.get('message', 'Unknown error')
            # Moodle enrol may fail notification but still succeed enrolment
            if "Message was not sent" in msg:
                return
            raise RuntimeError(f"Moodle API error: {msg}")

    async def get_users(self, key: str = "id", value: str = "1") -> Dict[str, Any]:
        params = {f"criteria[0][key]": key, f"criteria[0][value]": value}
        url = self._build_url("core_user_get_users", params)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            self._check_moodle_error(data)
            return data

    async def create_user(self, username: str, password: str, firstname: str, lastname: str, email: str) -> Dict[str, Any]:
        params = {
            "users[0][username]": username,
            "users[0][password]": password,
            "users[0][firstname]": firstname,
            "users[0][lastname]": lastname,
            "users[0][email]": email,
        }
        url = self._build_url("core_user_create_users", params)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            self._check_moodle_error(data)
            return data

    async def get_courses(self) -> Dict[str, Any]:
        url = self._build_url("core_course_get_courses")
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            self._check_moodle_error(data)
            return data

    async def enrol_user(self, course_id: int, user_id: int, role_id: int = 5) -> Dict[str, Any]:
        params = {
            "enrolments[0][roleid]": role_id,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id,
        }
        url = self._build_url("enrol_manual_enrol_users", params)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            self._check_moodle_error(data)
            return data

    async def update_user_password(self, user_id: int, password: str) -> Dict[str, Any]:
        params = {
            "users[0][id]": user_id,
            "users[0][password]": password,
        }
        url = self._build_url("core_user_update_users", params)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            self._check_moodle_error(data)
            return data

    async def get_course_contents(self, course_id: int) -> Dict[str, Any]:
        url = self._build_url("core_course_get_contents", {"courseid": course_id})
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            self._check_moodle_error(data)
            return data

    async def get_user_courses(self, user_id: int) -> Dict[str, Any]:
        url = self._build_url("core_enrol_get_users_courses", {"userid": user_id})
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            self._check_moodle_error(data)
            return data

    async def create_course(self, fullname: str, shortname: str, categoryid: int = 1, summary: str = "") -> Dict[str, Any]:
        params = {
            "courses[0][fullname]": fullname,
            "courses[0][shortname]": shortname,
            "courses[0][categoryid]": categoryid,
            "courses[0][summary]": summary,
            "courses[0][visible]": 1,
        }
        url = self._build_url("core_course_create_courses", params)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            self._check_moodle_error(data)
            return data

    async def delete_course(self, course_id: int) -> Dict[str, Any]:
        url = self._build_url("core_course_delete_courses", {"courseids[0]": course_id})
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            text = response.text
            data = response.json() if text else {}
            self._check_moodle_error(data)
            return data
