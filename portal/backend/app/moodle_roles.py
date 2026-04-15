PORTAL_TO_MOODLE_ROLE = {
    "admin": 1,
    "course_creator": 3,
    "teacher": 3,
    "student": 5,
}

def get_moodle_role_id(portal_role: str) -> int:
    return PORTAL_TO_MOODLE_ROLE.get(portal_role, 5)
