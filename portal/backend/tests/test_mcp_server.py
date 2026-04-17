import pytest
import subprocess
import json
import base64


@pytest.fixture
def mcp_proc():
    """Start MCP server in Docker and yield the subprocess."""
    proc = subprocess.Popen(
        ["docker", "exec", "-i", "dd_academy_mcp", "python", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # Initialize
    _send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "1.0"},
    }})
    yield proc
    proc.stdin.close()
    proc.wait()


def _send(proc, req):
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    return json.loads(line)


def _call_tool(proc, name, arguments, req_id=100):
    return _send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
        "name": name,
        "arguments": arguments,
    }})


class TestMCPTools:
    def test_list_tools_returns_expected_tools(self, mcp_proc):
        resp = _send(mcp_proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = resp["result"]["tools"]
        names = {t["name"] for t in tools}
        expected = {
            "list_courses", "list_categories", "create_course", "update_course",
            "delete_course", "create_category", "create_section", "get_course_contents",
            "add_page_module", "add_url_module", "add_label_module", "add_forum_module",
            "add_quiz_module", "add_assignment_module", "enrol_user", "upload_file",
            "list_available_api_functions",
        }
        assert expected <= names, f"Missing tools: {expected - names}"

    def test_list_courses(self, mcp_proc):
        resp = _call_tool(mcp_proc, "list_courses", {}, req_id=3)
        assert "result" in resp
        courses = json.loads(resp["result"]["content"][0]["text"])
        assert isinstance(courses, list)
        assert len(courses) >= 1

    def test_list_categories(self, mcp_proc):
        resp = _call_tool(mcp_proc, "list_categories", {}, req_id=4)
        assert "result" in resp
        cats = json.loads(resp["result"]["content"][0]["text"])
        assert isinstance(cats, list)

    def test_create_and_delete_course(self, mcp_proc):
        shortname = "mcp-pytest-course"
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Pytest Course",
            "shortname": shortname,
            "categoryid": 1,
            "summary": "Auto-created by pytest",
        }, req_id=5)
        assert "result" in resp
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]
        assert isinstance(course_id, int)

        # Delete
        del_resp = _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=6)
        assert "result" in del_resp

    def test_create_section_and_add_modules(self, mcp_proc):
        # Create a temp course first
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Section Test",
            "shortname": "mcp-section-test",
            "categoryid": 1,
        }, req_id=7)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        # Create section
        sec_resp = _call_tool(mcp_proc, "create_section", {
            "course_id": course_id,
            "name": "Test Section",
            "summary": "Section for pytest",
        }, req_id=8)
        sec_data = json.loads(sec_resp["result"]["content"][0]["text"])
        assert "section_id" in sec_data

        # Add page
        page_resp = _call_tool(mcp_proc, "add_page_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test Page",
            "content": "<p>Hello pytest</p>",
            "intro": "Intro",
        }, req_id=9)
        assert "cmid=" in page_resp["result"]["content"][0]["text"]

        # Add URL
        url_resp = _call_tool(mcp_proc, "add_url_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test URL",
            "url": "https://example.com",
            "intro": "Example",
        }, req_id=10)
        assert "cmid=" in url_resp["result"]["content"][0]["text"]

        # Add label
        label_resp = _call_tool(mcp_proc, "add_label_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test Label",
            "content": "<p>Label content</p>",
        }, req_id=11)
        assert "cmid=" in label_resp["result"]["content"][0]["text"]

        # Add quiz
        quiz_resp = _call_tool(mcp_proc, "add_quiz_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test Quiz",
            "intro": "Quiz intro",
        }, req_id=12)
        assert "cmid=" in quiz_resp["result"]["content"][0]["text"]

        # Add forum
        forum_resp = _call_tool(mcp_proc, "add_forum_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test Forum",
            "intro": "Forum intro",
        }, req_id=13)
        assert "cmid=" in forum_resp["result"]["content"][0]["text"]

        # Add assignment
        assign_resp = _call_tool(mcp_proc, "add_assignment_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test Assignment",
            "intro": "Assignment intro",
            "duedate": 0,
            "grade": 100,
        }, req_id=14)
        assert "cmid=" in assign_resp["result"]["content"][0]["text"]

        # Cleanup
        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=99)

    def test_upload_file(self, mcp_proc):
        file_bytes = b"pytest uploaded content"
        b64 = base64.b64encode(file_bytes).decode()
        resp = _call_tool(mcp_proc, "upload_file", {
            "filename": "pytest_test.txt",
            "file_bytes_b64": b64,
            "filearea": "draft",
            "itemid": 0,
        }, req_id=15)
        assert "result" in resp
        data = json.loads(resp["result"]["content"][0]["text"])
        assert isinstance(data, list)
        assert data[0]["filename"] == "pytest_test.txt"
        assert data[0]["filesize"] == len(file_bytes)

    def test_enrol_user(self, mcp_proc):
        # Create a temp course so manual enrol is guaranteed and user not already enrolled
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Enrol Test",
            "shortname": "mcp-enrol-test",
            "categoryid": 1,
        }, req_id=16)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        # Enrol admin (user 2) as editingteacher (role 3)
        enrol_resp = _call_tool(mcp_proc, "enrol_user", {
            "course_id": course_id,
            "user_id": 2,
            "role_id": 3,
        }, req_id=17)
        assert "result" in enrol_resp
        text = enrol_resp["result"]["content"][0]["text"]
        assert "null" in text or "enrolled" in text or "status" in text

        # Cleanup
        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=199)

    def test_add_forum_module(self, mcp_proc):
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Forum Test",
            "shortname": "mcp-forum-test",
            "categoryid": 1,
        }, req_id=17)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        _call_tool(mcp_proc, "create_section", {"course_id": course_id, "name": "Forum Section"}, req_id=18)

        forum_resp = _call_tool(mcp_proc, "add_forum_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Discussion Forum",
            "intro": "Forum for testing",
            "forum_type": "general",
        }, req_id=19)
        assert "cmid=" in forum_resp["result"]["content"][0]["text"]

        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=299)

    def test_add_assignment_module(self, mcp_proc):
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Assignment Test",
            "shortname": "mcp-assign-test",
            "categoryid": 1,
        }, req_id=20)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        _call_tool(mcp_proc, "create_section", {"course_id": course_id, "name": "Assignment Section"}, req_id=21)

        assign_resp = _call_tool(mcp_proc, "add_assignment_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test Assignment",
            "intro": "Complete the tasks",
            "duedate": 1893456000,
            "grade": 100,
        }, req_id=22)
        assert "cmid=" in assign_resp["result"]["content"][0]["text"]

        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=399)

    def test_add_book_module_and_chapters(self, mcp_proc):
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Book Test",
            "shortname": "mcp-book-test",
            "categoryid": 1,
        }, req_id=40)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        _call_tool(mcp_proc, "create_section", {"course_id": course_id, "name": "Book Section"}, req_id=41)

        book_resp = _call_tool(mcp_proc, "add_book_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test Book",
            "intro": "Book intro",
        }, req_id=42)
        book_data = json.loads(book_resp["result"]["content"][0]["text"])
        assert "book_id" in book_data

        chap_resp = _call_tool(mcp_proc, "add_book_chapter", {
            "book_id": book_data["book_id"],
            "title": "Chapter 1",
            "content": "<p>First chapter</p>",
        }, req_id=43)
        assert "id=" in chap_resp["result"]["content"][0]["text"]

        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=499)

    def test_add_quiz_question(self, mcp_proc):
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Quiz Question Test",
            "shortname": "mcp-quiz-q-test",
            "categoryid": 1,
        }, req_id=50)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        _call_tool(mcp_proc, "create_section", {"course_id": course_id, "name": "Quiz Section"}, req_id=51)

        quiz_resp = _call_tool(mcp_proc, "add_quiz_module", {
            "course_id": course_id,
            "section_num": 1,
            "name": "Test Quiz",
            "intro": "Quiz with questions",
        }, req_id=52)
        quiz_cmid = int(quiz_resp["result"]["content"][0]["text"].replace("Created quiz module with cmid=", ""))

        # Get quiz instance via get_course_contents instead of DB (runs on Windows)
        contents_resp = _call_tool(mcp_proc, "get_course_contents", {"course_id": course_id}, req_id=520)
        contents = json.loads(contents_resp["result"]["content"][0]["text"])
        quiz_mod = None
        for sec in contents:
            for mod in sec.get("modules", []):
                if mod.get("id") == quiz_cmid:
                    quiz_mod = mod
                    break
            if quiz_mod:
                break
        assert quiz_mod is not None
        quiz_id = quiz_mod["instance"]

        q_resp = _call_tool(mcp_proc, "add_quiz_question", {
            "quiz_id": quiz_id,
            "qtype": "multichoice",
            "name": "Test Question",
            "questiontext": "<p>What is DreamDocs?</p>",
            "answers": [
                {"text": "A. Just storage", "fraction": 0},
                {"text": "B. IDP system", "fraction": 1},
            ],
        }, req_id=53)
        q_data = json.loads(q_resp["result"]["content"][0]["text"])
        assert q_data["success"] is True
        assert "question_id" in q_data

        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=599)

    def test_create_course_with_full_content(self, mcp_proc):
        # 1. Create course
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Full Course Test",
            "shortname": "mcp-full-test",
            "categoryid": 1,
        }, req_id=60)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        # 2. Create section
        _call_tool(mcp_proc, "create_section", {"course_id": course_id, "name": "Full Test Section"}, req_id=61)

        # 3. Add book with chapters
        book_resp = _call_tool(mcp_proc, "add_book_module", {
            "course_id": course_id, "section_num": 1, "name": "Theory Book", "intro": "Theory"
        }, req_id=62)
        book_data = json.loads(book_resp["result"]["content"][0]["text"])
        book_id = book_data["book_id"]
        for i in range(3):
            call_tool_resp = _call_tool(mcp_proc, "add_book_chapter", {
                "book_id": book_id, "title": f"Chapter {i+1}", "content": f"<p>Content {i+1}</p>"
            }, req_id=63 + i)
            assert "id=" in call_tool_resp["result"]["content"][0]["text"]

        # 4. Add quiz with questions
        quiz_resp = _call_tool(mcp_proc, "add_quiz_module", {
            "course_id": course_id, "section_num": 1, "name": "Knowledge Quiz", "intro": "Quiz"
        }, req_id=66)
        quiz_cmid = int(quiz_resp["result"]["content"][0]["text"].replace("Created quiz module with cmid=", ""))

        contents_resp = _call_tool(mcp_proc, "get_course_contents", {"course_id": course_id}, req_id=670)
        contents = json.loads(contents_resp["result"]["content"][0]["text"])
        quiz_mod = None
        for sec in contents:
            for mod in sec.get("modules", []):
                if mod.get("id") == quiz_cmid:
                    quiz_mod = mod
                    break
            if quiz_mod:
                break
        assert quiz_mod is not None
        quiz_id = quiz_mod["instance"]

        q_resp = _call_tool(mcp_proc, "add_quiz_question", {
            "quiz_id": quiz_id,
            "qtype": "multichoice",
            "name": "Q1",
            "questiontext": "<p>Pick correct</p>",
            "answers": [
                {"text": "Wrong", "fraction": 0},
                {"text": "Correct", "fraction": 1},
            ],
        }, req_id=67)
        q_data = json.loads(q_resp["result"]["content"][0]["text"])
        assert q_data["success"] is True

        # 5. Add assignment and forum
        assign_resp = _call_tool(mcp_proc, "add_assignment_module", {
            "course_id": course_id, "section_num": 1, "name": "Lab Work", "intro": "Lab"
        }, req_id=68)
        assert "cmid=" in assign_resp["result"]["content"][0]["text"]

        forum_resp = _call_tool(mcp_proc, "add_forum_module", {
            "course_id": course_id, "section_num": 1, "name": "Discussion", "intro": "Forum"
        }, req_id=69)
        assert "cmid=" in forum_resp["result"]["content"][0]["text"]

        # 6. Verify structure (purge Moodle caches first because REST API caches aggressively)
        subprocess.run(["docker", "exec", "dd_academy_moodle", "php", "admin/cli/purge_caches.php"], capture_output=True)
        verify_resp = _call_tool(mcp_proc, "get_course_contents", {"course_id": course_id}, req_id=70)
        verify_data = json.loads(verify_resp["result"]["content"][0]["text"])
        sections = [s for s in verify_data if s.get("section", 0) > 0]
        assert len(sections) >= 1
        mods = sections[0].get("modules", [])
        modnames = {m["modname"] for m in mods}
        assert {"book", "quiz", "assign", "forum"} <= modnames

        # Also verify DB-level presence as fallback
        db_check = subprocess.run(
            ["docker", "exec", "-i", "dd_academy_db", "mysql", "-umoodle", "-pmoodlesecret", "moodle",
             "-e", f"SELECT COUNT(*) as cnt FROM mdl_course_modules WHERE course = {course_id} AND module IN (SELECT id FROM mdl_modules WHERE name IN ('book','quiz','assign','forum'));"],
            capture_output=True, text=True,
        )
        db_count = int([l for l in db_check.stdout.splitlines() if l.strip() and not l.startswith("cnt")][0])
        assert db_count >= 4

        # Cleanup
        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=799)

    def test_quiz_questions_are_playable(self, mcp_proc):
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Quiz Playable Test",
            "shortname": "mcp-quiz-play-test",
            "categoryid": 1,
        }, req_id=80)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        _call_tool(mcp_proc, "create_section", {"course_id": course_id, "name": "Quiz Section"}, req_id=81)
        quiz_resp = _call_tool(mcp_proc, "add_quiz_module", {
            "course_id": course_id, "section_num": 1, "name": "Playable Quiz", "intro": "Quiz"
        }, req_id=82)
        quiz_cmid = int(quiz_resp["result"]["content"][0]["text"].replace("Created quiz module with cmid=", ""))

        contents_resp = _call_tool(mcp_proc, "get_course_contents", {"course_id": course_id}, req_id=820)
        contents = json.loads(contents_resp["result"]["content"][0]["text"])
        quiz_mod = next((m for sec in contents for m in sec.get("modules", []) if m.get("id") == quiz_cmid), None)
        assert quiz_mod is not None
        quiz_id = quiz_mod["instance"]

        for i in range(3):
            q_resp = _call_tool(mcp_proc, "add_quiz_question", {
                "quiz_id": quiz_id,
                "qtype": "multichoice",
                "name": f"Q{i+1}",
                "questiontext": f"<p>Question {i+1}</p>",
                "answers": [
                    {"text": "A", "fraction": 0},
                    {"text": "B", "fraction": 1},
                ],
            }, req_id=83 + i)
            q_data = json.loads(q_resp["result"]["content"][0]["text"])
            assert q_data["success"] is True
            assert q_data["slot"] == i + 1

        # Verify DB linkage via DB query from inside MCP container (docker exec mysql)
        check_cmd = [
            "docker", "exec", "-i", "dd_academy_db", "mysql", "-umoodle", "-pmoodlesecret", "moodle",
            "-e", f"SELECT COUNT(*) as cnt FROM mdl_quiz_slots WHERE quizid = {quiz_id};"
        ]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        count_line = [l for l in result.stdout.splitlines() if l.strip() and not l.startswith("cnt")][0]
        assert int(count_line) == 3

        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=899)

    def test_book_chapters_persist_after_cache_purge(self, mcp_proc):
        resp = _call_tool(mcp_proc, "create_course", {
            "fullname": "MCP Book Cache Test",
            "shortname": "mcp-book-cache-test",
            "categoryid": 1,
        }, req_id=90)
        data = json.loads(resp["result"]["content"][0]["text"])
        course_id = data["id"] if isinstance(data, dict) else data[0]["id"]

        _call_tool(mcp_proc, "create_section", {"course_id": course_id, "name": "Book Section"}, req_id=91)
        book_resp = _call_tool(mcp_proc, "add_book_module", {
            "course_id": course_id, "section_num": 1, "name": "Cache Book", "intro": "Book"
        }, req_id=92)
        book_data = json.loads(book_resp["result"]["content"][0]["text"])
        book_id = book_data["book_id"]
        book_cmid = book_data["cmid"]

        for i in range(2):
            _call_tool(mcp_proc, "add_book_chapter", {
                "book_id": book_id, "title": f"Ch {i+1}", "content": f"<p>Body {i+1}</p>"
            }, req_id=93 + i)

        # Purge caches
        subprocess.run(["docker", "exec", "dd_academy_moodle", "php", "admin/cli/purge_caches.php"], capture_output=True)

        # Verify via backend API (we'll need to mock auth, but we can at least query DB)
        check_cmd = [
            "docker", "exec", "-i", "dd_academy_db", "mysql", "-umoodle", "-pmoodlesecret", "moodle",
            "-e", f"SELECT COUNT(*) as cnt FROM mdl_book_chapters WHERE bookid = {book_id};"
        ]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        count_line = [l for l in result.stdout.splitlines() if l.strip() and not l.startswith("cnt")][0]
        assert int(count_line) == 2

        # Verify revision incremented
        rev_cmd = [
            "docker", "exec", "-i", "dd_academy_db", "mysql", "-umoodle", "-pmoodlesecret", "moodle",
            "-e", f"SELECT revision FROM mdl_book WHERE id = {book_id};"
        ]
        rev_result = subprocess.run(rev_cmd, capture_output=True, text=True)
        rev_line = [l for l in rev_result.stdout.splitlines() if l.strip() and not l.startswith("revision")][0]
        assert int(rev_line) >= 2

        _call_tool(mcp_proc, "delete_course", {"course_id": course_id}, req_id=999)

    def test_list_available_api_functions(self, mcp_proc):
        resp = _call_tool(mcp_proc, "list_available_api_functions", {}, req_id=30)
        assert "result" in resp
        funcs = json.loads(resp["result"]["content"][0]["text"])
        assert isinstance(funcs, list)
        assert len(funcs) > 0
