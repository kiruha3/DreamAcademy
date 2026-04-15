import httpx
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

    async def delete_course(self, course_id: int) -> Dict[str, Any]:
        url = self._build_url("core_course_delete_courses", {"courseids[0]": course_id})
        response = await self.client.get(url)
        response.raise_for_status()
        text = response.text
        data = response.json() if text else {}
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

    async def save_quiz_attempt(self, attempt_id: int, data_seq: list) -> Dict[str, Any]:
        params = {"attemptid": attempt_id}
        for idx, slot_data in enumerate(data_seq):
            params[f"data[{idx}][name]"] = slot_data["name"]
            params[f"data[{idx}][value]"] = slot_data["value"]
            if slot_data.get("slot") is not None:
                params[f"data[{idx}][slot]"] = slot_data["slot"]
        url = self._build_url("mod_quiz_save_attempt", params)
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

    async def finish_quiz_attempt(self, attempt_id: int) -> Dict[str, Any]:
        url = self._build_url("mod_quiz_finish_attempt", {"attemptid": attempt_id, "timeup": 0})
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        self._check_moodle_error(data)
        return data

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
