from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from .moodle_client import MoodleClient
from .config import get_settings
from . import moodle_db

router = APIRouter(prefix="/api/courses", tags=["courses"])

async def get_moodle_client() -> MoodleClient:
    settings = get_settings()
    client = MoodleClient(base_url=settings.MOODLE_URL, token=settings.MOODLE_TOKEN)
    try:
        yield client
    finally:
        await client.close()


def _fix_moodle_urls(data, internal_url: str, public_url: str):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value.startswith(internal_url):
                data[key] = value.replace(internal_url, public_url, 1)
            else:
                _fix_moodle_urls(value, internal_url, public_url)
    elif isinstance(data, list):
        for item in data:
            _fix_moodle_urls(item, internal_url, public_url)


def _extract_course_image(course: Dict[str, Any]) -> str:
    # Moodle 4.x sometimes returns a direct courseimage field
    if course.get("courseimage"):
        return course["courseimage"]
    files = course.get("overviewfiles") or []
    for f in files:
        if isinstance(f, dict) and f.get("fileurl"):
            return f["fileurl"]
    return ""


@router.get("")
async def list_courses(client: MoodleClient = Depends(get_moodle_client)) -> Dict[str, Any]:
    settings = get_settings()
    courses = await client.get_courses()
    courses = courses if isinstance(courses, list) else []
    _fix_moodle_urls(courses, settings.MOODLE_URL, settings.MOODLE_PUBLIC_URL)

    course_ids = [c["id"] for c in courses if isinstance(c, dict)]
    db_images = moodle_db.get_course_images(course_ids, settings.MOODLE_PUBLIC_URL, settings.MOODLE_TOKEN)

    for course in courses:
        cid = course.get("id")
        image = db_images.get(cid) or _extract_course_image(course)
        course["imageUrl"] = image
    return {"courses": courses}
