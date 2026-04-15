from fastapi import APIRouter, Depends
from typing import Dict, Any
from .moodle_client import MoodleClient
from .config import get_settings

router = APIRouter(prefix="/api/courses", tags=["course-content"])


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


@router.get("/{course_id}/contents")
async def get_course_content(course_id: int, client: MoodleClient = Depends(get_moodle_client)) -> Dict[str, Any]:
    settings = get_settings()
    contents = await client.get_course_contents(course_id)
    _fix_moodle_urls(contents, settings.MOODLE_URL, settings.MOODLE_PUBLIC_URL)
    return {"course_id": course_id, "contents": contents}
