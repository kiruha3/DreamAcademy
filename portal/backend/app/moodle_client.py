import asyncio
import base64
import httpx
import json
import os
import subprocess
from typing import Dict, Any, Optional
from urllib.parse import urlencode

class MoodleClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

        self.client = httpx.AsyncClient(follow_redirects=True)
    def _build_url(self, wsfunction: str, params: Optional[Dict[str, Any]] = None) -> str:
        url = f"{self.base_url}/webservice/rest/server.php?wstoken={self.token}&wsfunction={wsfunction}&moodlewsrestformat=json"
        if params:
            url += f"&{urlencode(params)}"
        return url

    def _check_moodle_error(self, data: Dict[str, Any]) -> None:
        if isinstance(data, dict) and "exception" in data:
            msg = data.get('message', 'Unknown error')
            code = data.get('errorcode', '')
            # Moodle enrol may fail notification but still succeed enrolment
            if "Message was not sent" in msg:
                return
            raise RuntimeError(f"Moodle API error [{code}]: {msg}")

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def get_users(self, key: str = "id", value: str = "1") -> Dict[str, Any]:
        params = {f"criteria[0][key]": key, f"criteria[0][value]": value}
        url = self._build_url("core_user_get_users", params)
        response = await self.client.get(url)
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
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def get_courses(self) -> Dict[str, Any]:
        url = self._build_url("core_course_get_courses")
        response = await self.client.get(url)
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
        response = await self.client.get(url)
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
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def get_course_contents(self, course_id: int) -> Dict[str, Any]:
        url = self._build_url("core_course_get_contents", {"courseid": course_id})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def get_user_courses(self, user_id: int) -> Dict[str, Any]:
        url = self._build_url("core_enrol_get_users_courses", {"userid": user_id})
        response = await self.client.get(url)
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
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def update_course(self, course_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        params = {"courses[0][id]": course_id}
        for key, value in fields.items():
            params[f"courses[0][{key}]"] = value
        url = self._build_url("core_course_update_courses", params)
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def delete_course(self, course_id: int) -> Dict[str, Any]:
        url = self._build_url("core_course_delete_courses", {"courseids[0]": course_id})
        response = await self.client.get(url)
        response.raise_for_status()
        text = response.text
        data = response.json() if text else {}
        self._check_moodle_error(data)
        return data

    async def create_category(self, name: str, parent: int = 0, idnumber: str = "") -> Dict[str, Any]:
        params = {
            "categories[0][name]": name,
            "categories[0][parent]": parent,
            "categories[0][idnumber]": idnumber,
        }
        url = self._build_url("core_course_create_categories", params)
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def list_categories(self, criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = {}
        if criteria:
            for idx, (key, value) in enumerate(criteria.items()):
                params[f"criteria[{idx}][key]"] = key
                params[f"criteria[{idx}][value]"] = value
        url = self._build_url("core_course_get_categories", params)
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def upload_file(self, file_bytes: bytes, filename: str, filearea: str = "draft", itemid: int = 0) -> Dict[str, Any]:
        url = f"{self.base_url}/webservice/upload.php?token={self.token}&filearea={filearea}&itemid={itemid}"
        files = {"file_1": (filename, file_bytes)}
        response = await self.client.post(url, files=files)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and len(data) > 0 and "error" in data[0]:
            raise RuntimeError(f"Moodle upload error: {data[0].get('error', 'Unknown')}")
        self._check_moodle_error(data)
        return data

    async def list_external_functions(self) -> Dict[str, Any]:
        url = self._build_url("core_webservice_get_site_info")
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def get_activities_completion_status(self, course_id: int, user_id: int) -> Dict[str, Any]:
        url = self._build_url("core_completion_get_activities_completion_status", {"courseid": course_id, "userid": user_id})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def update_activity_completion_status(self, cmid: int, user_id: int, completed: bool = True) -> Dict[str, Any]:
        # core_completion_update_activity_completion_status_manually does not accept userid;
        # it uses the token's current user.
        url = self._build_url("core_completion_update_activity_completion_status_manually", {
            "cmid": cmid,
            "completed": int(completed),
        })
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    # Assignment WS methods
    async def get_assignment_submission_status(self, assign_id: int, user_id: int) -> Dict[str, Any]:
        url = self._build_url("mod_assign_get_submission_status", {"assignid": assign_id, "userid": user_id})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def save_assignment_grade(self, assign_id: int, user_id: int, grade: float, feedback: str = "") -> Dict[str, Any]:
        url = self._build_url("mod_assign_save_grade", {
            "assignmentid": assign_id,
            "userid": user_id,
            "grade": grade,
            "attemptnumber": -1,
            "addattempt": 0,
            "workflowstate": "",
            "applytoall": 0,
            "plugindata[assignfeedbackcomments_editor][text]": feedback,
            "plugindata[assignfeedbackcomments_editor][format]": 1,
        })
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    # Quiz WS methods
    async def get_quiz_data(self, quiz_id: int) -> Dict[str, Any]:
        url = self._build_url("mod_quiz_get_quizzes_by_courses", {})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        quizzes = data.get("quizzes", []) if isinstance(data, dict) else []
        for q in quizzes:
            if q.get("id") == quiz_id:
                return q
        return {}

    async def start_quiz_attempt(self, quiz_id: int) -> Dict[str, Any]:
        url = self._build_url("mod_quiz_start_attempt", {"quizid": quiz_id, "forcenew": 1})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def get_attempt_data(self, attempt_id: int, page: int = 0) -> Dict[str, Any]:
        url = self._build_url("mod_quiz_get_attempt_data", {"attemptid": attempt_id, "page": page})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def _call_process_attempt_php(self, attempt_id: int, data_seq: list, finishattempt: bool = False) -> Dict[str, Any]:
        # Moodle process_attempt only expects name/value pairs; strip extra keys like slot
        cleaned = [{"name": d["name"], "value": d["value"]} for d in data_seq]
        data_json = json.dumps(cleaned)
        data_b64 = base64.b64encode(data_json.encode("utf-8")).decode("utf-8")
        cmd = [
            "docker", "exec", os.getenv("MOODLE_CONTAINER_NAME", "dd_academy_moodle"),
            "php", "/var/www/html/moodle_process_attempt.php",
            str(attempt_id), data_b64, "1" if finishattempt else "0",
        ]
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"PHP script failed: {result.stderr or result.stdout}")
        output = result.stdout.strip().split("\n")[-1]
        parsed = json.loads(output)
        if not parsed.get("success"):
            raise RuntimeError(f"Moodle process attempt error: {parsed.get('error')}")
        return parsed["result"]

    async def save_quiz_attempt(self, attempt_id: int, data_seq: list) -> Dict[str, Any]:
        return await self._call_process_attempt_php(attempt_id, data_seq, finishattempt=False)

    async def finish_quiz_attempt(self, attempt_id: int) -> Dict[str, Any]:
        return await self._call_process_attempt_php(attempt_id, [], finishattempt=True)

    async def get_attempt_review(self, attempt_id: int) -> Dict[str, Any]:
        url = self._build_url("mod_quiz_get_attempt_review", {"attemptid": attempt_id})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    # Forum WS methods
    async def get_forum_discussions(self, forum_id: int) -> Dict[str, Any]:
        url = self._build_url("mod_forum_get_forum_discussions", {"forumid": forum_id})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def get_forum_posts(self, discussion_id: int) -> Dict[str, Any]:
        url = self._build_url("mod_forum_get_discussion_posts", {"discussionid": discussion_id})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def add_forum_discussion(self, forum_id: int, subject: str, message: str) -> Dict[str, Any]:
        url = self._build_url("mod_forum_add_discussion", {
            "forumid": forum_id,
            "subject": subject,
            "message": message,
        })
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def add_forum_post(self, post_id: int, subject: str, message: str) -> Dict[str, Any]:
        url = self._build_url("mod_forum_add_discussion_post", {
            "postid": post_id,
            "subject": subject,
            "message": message,
        })
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data
