"""
Автоматизация создания тестового курса в DreamDocs Academy (Moodle).
Запускать ПОСЛЕ поднятия Docker-окружения и настройки Moodle Web Services.

Пример запуска:
    python scripts/setup_moodle_course.py http://localhost:8080 YOUR_MOODLE_TOKEN
"""
import sys
import requests


def build_url(base_url, token, wsfunction, params=None):
    url = (
        f"{base_url.rstrip('/')}/webservice/rest/server.php"
        f"?wstoken={token}"
        f"&wsfunction={wsfunction}"
        f"&moodlewsrestformat=json"
    )
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url += f"&{query}"
    return url


def create_course(base_url, token, fullname, shortname, category_id=1):
    params = {
        "courses[0][fullname]": fullname,
        "courses[0][shortname]": shortname,
        "courses[0][categoryid]": category_id,
        "courses[0][summary]": "Автоматически созданный курс для Академии DreamDocs",
        "courses[0][visible]": 1,
    }
    url = build_url(base_url, token, "core_course_create_courses", params)
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
        return data[0]["id"]
    raise RuntimeError(f"Failed to create course: {data}")


def enrol_user(base_url, token, course_id, user_id, role_id=5):
    params = {
        "enrolments[0][roleid]": role_id,
        "enrolments[0][userid]": user_id,
        "enrolments[0][courseid]": course_id,
    }
    url = build_url(base_url, token, "enrol_manual_enrol_users", params)
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def get_or_create_test_user(base_url, token, email, username, firstname, lastname):
    # 1. Try to find existing user
    params = {
        "criteria[0][key]": "email",
        "criteria[0][value]": email,
    }
    url = build_url(base_url, token, "core_user_get_users", params)
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    users = data.get("users", [])
    if users:
        return users[0]["id"]

    # 2. Create new user
    params = {
        "users[0][username]": username,
        "users[0][password]": "TestPass123!",
        "users[0][firstname]": firstname,
        "users[0][lastname]": lastname,
        "users[0][email]": email,
    }
    url = build_url(base_url, token, "core_user_create_users", params)
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
        return data[0]["id"]
    raise RuntimeError(f"Failed to create user: {data}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python setup_moodle_course.py <base_url> <token>")
        print("Example: python setup_moodle_course.py http://localhost:8080 abc123xyz")
        sys.exit(1)

    base_url = sys.argv[1]
    token = sys.argv[2]

    print("Creating course...")
    course_id = create_course(base_url, token, "DreamDocs: Базовое обучение", "DD_Basic")
    print(f"Course created: ID={course_id}")

    print("Creating/enrolling test student...")
    student_id = get_or_create_test_user(
        base_url, token,
        email="test.student@example.com",
        username="teststudent",
        firstname="Тест",
        lastname="Студент",
    )
    enrol_user(base_url, token, course_id, student_id, role_id=5)
    print(f"Student enrolled: ID={student_id}")

    print("Creating/enrolling test teacher...")
    teacher_id = get_or_create_test_user(
        base_url, token,
        email="teacher@dreamdocs.local",
        username="teacher1",
        firstname="Учитель",
        lastname="DreamDocs",
    )
    enrol_user(base_url, token, course_id, teacher_id, role_id=3)
    print(f"Teacher enrolled: ID={teacher_id}")

    print("\nDone! Next steps:")
    print(f"1. Open Moodle: {base_url}/course/view.php?id={course_id}")
    print("2. Login as admin and add course sections + quiz manually")
    print("3. Or extend this script to call core_course_update_courses for sections")


if __name__ == "__main__":
    main()
