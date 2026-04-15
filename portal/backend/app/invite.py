from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
import secrets
from .moodle_client import MoodleClient
from .config import get_settings
from .moodle_roles import get_moodle_role_id

router = APIRouter(prefix="/api/courses", tags=["invites"])

def get_moodle_client() -> MoodleClient:
    settings = get_settings()
    return MoodleClient(base_url=settings.MOODLE_URL, token=settings.MOODLE_TOKEN)

class InviteRequest(BaseModel):
    email: EmailStr
    firstname: str = ""
    lastname: str = ""

@router.post("/{course_id}/invite")
async def invite_to_course(
    course_id: int,
    invite: InviteRequest,
    role: str = "student",
    client: MoodleClient = Depends(get_moodle_client)
):
    users = await client.get_users(key="email", value=invite.email)
    user_list = users.get("users", [])

    if user_list:
        user_id = user_list[0]["id"]
    else:
        temp_password = secrets.token_urlsafe(12)
        created = await client.create_user(
            username=invite.email.split("@")[0],
            password=temp_password,
            firstname=invite.firstname or "Student",
            lastname=invite.lastname or "DreamDocs",
            email=invite.email,
        )
        if isinstance(created, list) and len(created) > 0:
            user_id = created[0].get("id")
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")

    moodle_role_id = get_moodle_role_id(role)
    await client.enrol_user(course_id=course_id, user_id=user_id, role_id=moodle_role_id)

    return {"status": "invited", "course_id": course_id, "user_id": user_id, "email": invite.email, "role": role}
