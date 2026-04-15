from portal.backend.app.auth import has_permission, Permission

def test_admin_has_all_permissions():
    role_permissions = {"admin": [Permission.COURSE_CREATE, Permission.COURSE_EDIT_ANY]}
    assert has_permission("admin", Permission.COURSE_CREATE, role_permissions) is True

def test_student_cannot_create_course():
    role_permissions = {"student": [Permission.COURSE_VIEW]}
    assert has_permission("student", Permission.COURSE_CREATE, role_permissions) is False
