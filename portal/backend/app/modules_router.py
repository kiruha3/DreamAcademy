from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from .security import get_current_user, require_roles
from .models import User
from .moodle_client import MoodleClient
from .config import get_settings
from . import moodle_db

router = APIRouter(prefix="/api/courses", tags=["modules"])


def get_moodle_client() -> MoodleClient:
    settings = get_settings()
    return MoodleClient(base_url=settings.MOODLE_URL, token=settings.MOODLE_TOKEN)


@router.get("/{course_id}/modules/{cmid}")
async def get_module_detail(
    course_id: int,
    cmid: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
) -> Dict[str, Any]:
    # Find the module in the course contents to get metadata
    contents = await client.get_course_contents(course_id)
    target_module = None
    for section in contents:
        for mod in section.get("modules", []):
            if mod.get("id") == cmid:
                target_module = mod
                break
        if target_module:
            break

    if not target_module:
        raise HTTPException(status_code=404, detail="Module not found in course")

    modname = target_module.get("modname")
    instance_id = target_module.get("instance")

    # Fetch instance data via SQL for content-rich modules
    instance = moodle_db.get_module_instance(modname, instance_id) if instance_id else None

    payload: Dict[str, Any] = {
        "cmid": cmid,
        "course_id": course_id,
        "modname": modname,
        "name": target_module.get("name"),
        "instance_id": instance_id,
        "visible": target_module.get("visible"),
        "modicon": target_module.get("modicon"),
        "modplural": target_module.get("modplural"),
    }

    if modname == "page" and instance:
        payload["content"] = instance.get("content", "")
        payload["intro"] = instance.get("intro", "")
    elif modname == "label" and instance:
        payload["intro"] = instance.get("intro", "")
    elif modname == "url" and instance:
        payload["externalurl"] = instance.get("externalurl", "")
        payload["display"] = instance.get("display", 0)
        payload["intro"] = instance.get("intro", "")
    elif modname == "quiz" and instance:
        payload["intro"] = instance.get("intro", "")
        payload["grade"] = instance.get("grade", 0)
        payload["sumgrades"] = instance.get("sumgrades", 0)
        payload["timeopen"] = instance.get("timeopen", 0)
        payload["timeclose"] = instance.get("timeclose", 0)
    elif modname == "assign" and instance:
        payload["intro"] = instance.get("intro", "")
        payload["duedate"] = instance.get("duedate", 0)
        payload["grade"] = instance.get("grade", 0)
    elif modname == "forum" and instance:
        payload["intro"] = instance.get("intro", "")
        payload["type"] = instance.get("type", "general")
    else:
        payload["intro"] = target_module.get("description", "")

    return payload


@router.post("/{course_id}/modules/{cmid}/complete")
async def mark_module_complete(
    course_id: int,
    cmid: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
) -> Dict[str, Any]:
    if not current_user.moodle_user_id:
        raise HTTPException(status_code=400, detail="User not linked to Moodle")
    try:
        result = await client.update_activity_completion_status(cmid, current_user.moodle_user_id, completed=True)
        return {"status": "completed", "cmid": cmid, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update completion: {str(e)}")


@router.get("/{course_id}/progress")
async def get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
) -> Dict[str, Any]:
    if not current_user.moodle_user_id:
        return {"course_id": course_id, "modules": [], "completed_count": 0, "total_count": 0}
    try:
        data = await client.get_activities_completion_status(course_id, current_user.moodle_user_id)
        statuses = data.get("statuses", []) if isinstance(data, dict) else []
        modules = []
        for s in statuses:
            modules.append({
                "cmid": s.get("cmid"),
                "completed": bool(s.get("state")),
                "modname": s.get("modname"),
            })
        total = len(modules)
        completed = sum(1 for m in modules if m["completed"])
        return {
            "course_id": course_id,
            "modules": modules,
            "completed_count": completed,
            "total_count": total,
        }
    except Exception as e:
        # Graceful fallback if completion tracking is not enabled
        return {"course_id": course_id, "modules": [], "completed_count": 0, "total_count": 0, "error": str(e)}
