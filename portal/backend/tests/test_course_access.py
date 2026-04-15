import pytest
from fastapi import HTTPException

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.modules_router import require_course_access
from app.models import User


class FakeMoodleClient:
    def __init__(self, enrolled_course_ids):
        self._enrolled = enrolled_course_ids

    async def get_user_courses(self, moodle_user_id):
        return [{"id": cid} for cid in self._enrolled]


@pytest.mark.anyio
async def test_admin_allowed_without_enrolment(db):
    user = User(
        email="admin@test.com",
        username="adminuser",
        firstname="Admin",
        lastname="User",
        role="admin",
        hashed_password="hp",
        moodle_user_id=None,
    )
    db.add(user)
    db.commit()
    client = FakeMoodleClient(enrolled_course_ids=[])
    await require_course_access(course_id=99, current_user=user, client=client)


@pytest.mark.anyio
async def test_teacher_allowed_without_enrolment(db):
    user = User(
        email="teacher@test.com",
        username="teacheruser",
        firstname="Teach",
        lastname="User",
        role="teacher",
        hashed_password="hp",
        moodle_user_id=None,
    )
    db.add(user)
    db.commit()
    client = FakeMoodleClient(enrolled_course_ids=[])
    await require_course_access(course_id=99, current_user=user, client=client)


@pytest.mark.anyio
async def test_student_enrolled_allowed(db):
    user = User(
        email="student@test.com",
        username="studentuser",
        firstname="Student",
        lastname="User",
        role="student",
        hashed_password="hp",
        moodle_user_id=5,
    )
    db.add(user)
    db.commit()
    client = FakeMoodleClient(enrolled_course_ids=[1, 2, 3])
    await require_course_access(course_id=2, current_user=user, client=client)


@pytest.mark.anyio
async def test_student_not_enrolled_forbidden(db):
    user = User(
        email="student2@test.com",
        username="studentuser2",
        firstname="Student",
        lastname="Two",
        role="student",
        hashed_password="hp",
        moodle_user_id=6,
    )
    db.add(user)
    db.commit()
    client = FakeMoodleClient(enrolled_course_ids=[1, 2])
    with pytest.raises(HTTPException) as exc_info:
        await require_course_access(course_id=99, current_user=user, client=client)
    assert exc_info.value.status_code == 403


@pytest.mark.anyio
async def test_student_no_moodle_id_forbidden(db):
    user = User(
        email="student3@test.com",
        username="studentuser3",
        firstname="Student",
        lastname="Three",
        role="student",
        hashed_password="hp",
        moodle_user_id=None,
    )
    db.add(user)
    db.commit()
    client = FakeMoodleClient(enrolled_course_ids=[1, 2])
    with pytest.raises(HTTPException) as exc_info:
        await require_course_access(course_id=1, current_user=user, client=client)
    assert exc_info.value.status_code == 403
