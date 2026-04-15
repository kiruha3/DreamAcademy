from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from .security import get_db, require_roles, get_current_user
from .models import User
from .moodle_client import MoodleClient
from .config import get_settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def get_moodle_client() -> MoodleClient:
    settings = get_settings()
    client = MoodleClient(base_url=settings.MOODLE_URL, token=settings.MOODLE_TOKEN)
    try:
        yield client
    finally:
        await client.close()


class CourseCreateRequest(BaseModel):
    fullname: str
    shortname: str
    categoryid: int = 1
    summary: str = ""


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
) -> Dict[str, Any]:
    users = db.query(User).all()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "firstname": u.firstname,
                "lastname": u.lastname,
                "role": u.role,
                "moodle_user_id": u.moodle_user_id,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@router.post("/courses")
async def create_course(
    req: CourseCreateRequest,
    client: MoodleClient = Depends(get_moodle_client),
    current_user: User = Depends(require_roles(["admin", "course_creator"])),
) -> Dict[str, Any]:
    result = await client.create_course(
        fullname=req.fullname,
        shortname=req.shortname,
        categoryid=req.categoryid,
        summary=req.summary,
    )
    return {"created": result}


@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    client: MoodleClient = Depends(get_moodle_client),
    current_user: User = Depends(require_roles(["admin"])),
) -> Dict[str, Any]:
    await client.delete_course(course_id)
    return {"status": "deleted", "course_id": course_id}
