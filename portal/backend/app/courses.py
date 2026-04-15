from fastapi import APIRouter, Depends
from typing import Dict, Any
from .moodle_client import MoodleClient
from .config import get_settings

router = APIRouter(prefix="/api/courses", tags=["courses"])

async def get_moodle_client() -> MoodleClient:
    settings = get_settings()
    client = MoodleClient(base_url=settings.MOODLE_URL, token=settings.MOODLE_TOKEN)
    try:
        yield client
    finally:
        await client.close()

@router.get("")
async def list_courses(client: MoodleClient = Depends(get_moodle_client)) -> Dict[str, Any]:
    courses = await client.get_courses()
    return {"courses": courses if isinstance(courses, list) else []}
