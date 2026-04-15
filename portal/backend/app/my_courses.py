from fastapi import APIRouter, Depends
from typing import Dict, Any
from .moodle_client import MoodleClient
from .config import get_settings
from .security import get_current_user
from .models import User

router = APIRouter(prefix="/api/my-courses", tags=["my-courses"])


async def get_moodle_client() -> MoodleClient:
    settings = get_settings()
    client = MoodleClient(base_url=settings.MOODLE_URL, token=settings.MOODLE_TOKEN)
    try:
        yield client
    finally:
        await client.close()


@router.get("")
async def list_my_courses(
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
) -> Dict[str, Any]:
    if not current_user.moodle_user_id:
        return {"courses": []}
    courses = await client.get_user_courses(current_user.moodle_user_id)
    return {"courses": courses if isinstance(courses, list) else []}
