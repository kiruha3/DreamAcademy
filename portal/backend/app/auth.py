from enum import Enum
from typing import Dict, List

class Permission(str, Enum):
    COURSE_CREATE = "course.create"
    COURSE_EDIT_OWN = "course.edit.own"
    COURSE_EDIT_ANY = "course.edit.any"
    COURSE_DELETE_OWN = "course.delete.own"
    COURSE_DELETE_ANY = "course.delete.any"
    COURSE_ENROLL_MANAGE = "course.enroll.manage"
    COURSE_TEACHER_ASSIGN = "course.teacher.assign"
    CONTENT_REVIEW = "content.review"
    CONTENT_VIEW_PROGRESS = "content.view.progress"
    USER_MANAGE = "user.manage"
    SYSTEM_CONFIG = "system.config"
    ANALYTICS_VIEW = "analytics.view"
    COURSE_VIEW = "course.view"

DEFAULT_ROLE_PERMISSIONS: Dict[str, List[Permission]] = {
    "admin": list(Permission),
    "course_creator": [
        Permission.COURSE_CREATE,
        Permission.COURSE_EDIT_OWN,
        Permission.COURSE_DELETE_OWN,
        Permission.COURSE_ENROLL_MANAGE,
        Permission.COURSE_TEACHER_ASSIGN,
        Permission.CONTENT_VIEW_PROGRESS,
    ],
    "teacher": [
        Permission.CONTENT_REVIEW,
        Permission.CONTENT_VIEW_PROGRESS,
        Permission.COURSE_VIEW,
    ],
    "student": [
        Permission.COURSE_VIEW,
    ],
}

def has_permission(role: str, permission: Permission, role_permissions: Dict[str, List[Permission]] = None) -> bool:
    if role_permissions is None:
        role_permissions = DEFAULT_ROLE_PERMISSIONS
    perms = role_permissions.get(role, [])
    return permission in perms
