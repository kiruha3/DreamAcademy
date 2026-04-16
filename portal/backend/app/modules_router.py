import os
import shutil
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .security import get_current_user, require_roles, get_db
from .models import User, Submission, QuizAttempt, UserModuleCompletion
from .moodle_client import MoodleClient
from .config import get_settings
from . import moodle_db

router = APIRouter(prefix="/api/courses", tags=["modules"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/submissions")


async def get_moodle_client() -> MoodleClient:
    settings = get_settings()
    client = MoodleClient(base_url=settings.MOODLE_URL, token=settings.MOODLE_TOKEN)
    try:
        yield client
    finally:
        await client.close()


def get_user_moodle_client(user_id: int) -> MoodleClient:
    settings = get_settings()
    user_token = moodle_db.ensure_user_token(user_id)
    return MoodleClient(base_url=settings.MOODLE_URL, token=user_token)


async def require_course_access(
    course_id: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
) -> None:
    if current_user.role in {"admin", "teacher", "course_creator"}:
        return
    if not current_user.moodle_user_id:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    user_courses = await client.get_user_courses(current_user.moodle_user_id)
    enrolled_ids = {c.get("id") for c in user_courses} if isinstance(user_courses, list) else set()
    if course_id not in enrolled_ids:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")


@router.get("/{course_id}/modules/{cmid}")
async def get_module_detail(
    course_id: int,
    cmid: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
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
    elif modname == "book" and instance:
        payload["intro"] = instance.get("intro", "")
        payload["numbering"] = instance.get("numbering", 0)
        payload["navstyle"] = instance.get("navstyle", 1)
    else:
        payload["intro"] = target_module.get("description", "")

    return payload


@router.get("/{course_id}/modules/{cmid}/book/chapters")
async def get_book_chapters(
    course_id: int,
    cmid: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    contents = await client.get_course_contents(course_id)
    target_module = None
    for section in contents:
        for mod in section.get("modules", []):
            if mod.get("id") == cmid:
                target_module = mod
                break
        if target_module:
            break
    if not target_module or target_module.get("modname") != "book":
        raise HTTPException(status_code=404, detail="Book module not found")
    chapters = moodle_db.get_book_chapters(target_module["instance"])
    return {"cmid": cmid, "chapters": chapters}


@router.post("/{course_id}/modules/{cmid}/complete")
async def mark_module_complete(
    course_id: int,
    cmid: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    db: Session = Depends(get_db),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    if not current_user.moodle_user_id:
        raise HTTPException(status_code=400, detail="User not linked to Moodle")
    moodle_ok = False
    try:
        result = await client.update_activity_completion_status(cmid, current_user.moodle_user_id, completed=True)
        moodle_ok = True
    except Exception as e:
        msg = str(e)
        if "cannotmanualctrack" in msg or "completionnotenabled" in msg:
            pass  # fallback to local tracking
        else:
            raise HTTPException(status_code=500, detail=f"Failed to update completion: {msg}")

    # Local tracking fallback / backup
    existing = db.query(UserModuleCompletion).filter(
        UserModuleCompletion.user_id == current_user.id,
        UserModuleCompletion.cmid == cmid,
    ).first()
    if not existing:
        db.add(UserModuleCompletion(user_id=current_user.id, cmid=cmid, course_id=course_id))
        db.commit()

    return {"status": "completed", "cmid": cmid, "moodle_sync": moodle_ok}


@router.get("/{course_id}/progress")
async def get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    db: Session = Depends(get_db),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    if not current_user.moodle_user_id:
        return {"course_id": course_id, "modules": [], "completed_count": 0, "total_count": 0}

    # Get all modules in the course for accurate total count
    try:
        contents = await client.get_course_contents(course_id)
    except Exception:
        contents = []

    all_modules = []
    for section in contents:
        for mod in section.get("modules", []):
            all_modules.append({
                "cmid": mod.get("id"),
                "modname": mod.get("modname"),
                "completed": False,
            })

    # Moodle completion statuses
    moodle_completed = set()
    try:
        data = await client.get_activities_completion_status(course_id, current_user.moodle_user_id)
        statuses = data.get("statuses", []) if isinstance(data, dict) else []
        for s in statuses:
            if bool(s.get("state")):
                moodle_completed.add(s.get("cmid"))
    except Exception:
        pass

    # Local completions
    local_completed = set()
    local_rows = db.query(UserModuleCompletion).filter(
        UserModuleCompletion.user_id == current_user.id,
        UserModuleCompletion.course_id == course_id,
    ).all()
    for row in local_rows:
        local_completed.add(row.cmid)

    completed_cmix = moodle_completed | local_completed

    # Local results for quiz and assign
    quiz_rows = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.course_id == course_id,
    ).all()
    quiz_results = {row.cmid: {"grade": row.grade, "max_grade": row.max_grade} for row in quiz_rows}

    sub_rows = db.query(Submission).filter(
        Submission.user_id == current_user.id,
        Submission.course_id == course_id,
    ).all()
    sub_results = {row.cmid: {"grade": row.grade, "status": "submitted" if row.grade is None else "graded"} for row in sub_rows}

    modules = []
    for mod in all_modules:
        cmid = mod["cmid"]
        modname = mod["modname"]
        result = None
        if modname == "quiz" and cmid in quiz_results:
            result = quiz_results[cmid]
        elif modname == "assign" and cmid in sub_results:
            result = sub_results[cmid]
        modules.append({
            "cmid": cmid,
            "modname": modname,
            "completed": cmid in completed_cmix,
            "result": result,
        })

    total = len(modules)
    completed = sum(1 for m in modules if m["completed"])
    return {
        "course_id": course_id,
        "modules": modules,
        "completed_count": completed,
        "total_count": total,
    }


# ===================== ASSIGNMENT =====================

@router.get("/{course_id}/modules/{cmid}/assign/status")
async def get_assignment_status(
    course_id: int,
    cmid: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    db: Session = Depends(get_db),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    contents = await client.get_course_contents(course_id)
    target = None
    for section in contents:
        for mod in section.get("modules", []):
            if mod.get("id") == cmid:
                target = mod
                break
        if target:
            break
    if not target or target.get("modname") != "assign":
        raise HTTPException(status_code=404, detail="Assignment not found")

    instance = moodle_db.get_module_instance("assign", target.get("instance"))
    local_sub = db.query(Submission).filter(Submission.cmid == cmid, Submission.user_id == current_user.id).first()

    status = "not_submitted"
    if local_sub:
        status = "submitted" if local_sub.grade is None else "graded"

    return {
        "cmid": cmid,
        "intro": instance.get("intro", "") if instance else "",
        "duedate": instance.get("duedate", 0) if instance else 0,
        "grade": instance.get("grade", 0) if instance else 0,
        "status": status,
        "submitted_at": local_sub.submitted_at.isoformat() if local_sub else None,
        "local_grade": local_sub.grade if local_sub else None,
        "feedback": local_sub.feedback if local_sub else None,
        "file_name": os.path.basename(local_sub.file_path) if local_sub and local_sub.file_path else None,
    }


@router.post("/{course_id}/modules/{cmid}/assign/submit")
async def submit_assignment(
    course_id: int,
    cmid: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    course_dir = os.path.join(UPLOAD_DIR, str(course_id), str(cmid))
    os.makedirs(course_dir, exist_ok=True)
    file_path = os.path.join(course_dir, f"user_{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    existing = db.query(Submission).filter(Submission.cmid == cmid, Submission.user_id == current_user.id).first()
    if existing:
        existing.file_path = file_path
        existing.submitted_at = datetime.now(timezone.utc)
        existing.grade = None
        existing.feedback = None
        existing.graded_at = None
    else:
        sub = Submission(
            user_id=current_user.id,
            cmid=cmid,
            course_id=course_id,
            file_path=file_path,
        )
        db.add(sub)
    db.commit()

    # Mark module as completed locally
    existing_comp = db.query(UserModuleCompletion).filter(
        UserModuleCompletion.user_id == current_user.id,
        UserModuleCompletion.cmid == cmid,
    ).first()
    if not existing_comp:
        db.add(UserModuleCompletion(user_id=current_user.id, cmid=cmid, course_id=course_id))
        db.commit()

    return {"status": "submitted", "cmid": cmid, "filename": file.filename}


@router.get("/{course_id}/modules/{cmid}/assign/submissions")
async def list_assignment_submissions(
    course_id: int,
    cmid: int,
    current_user: User = Depends(require_roles(["admin", "teacher", "course_creator"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    subs = db.query(Submission).filter(Submission.cmid == cmid).all()
    return {
        "submissions": [
            {
                "user_id": s.user_id,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                "grade": s.grade,
                "feedback": s.feedback,
                "file_name": os.path.basename(s.file_path) if s.file_path else None,
            }
            for s in subs
        ]
    }


class GradePayload(BaseModel):
    grade: float
    feedback: str = ""


@router.post("/{course_id}/modules/{cmid}/assign/submissions/{user_id}/grade")
async def grade_assignment_submission(
    course_id: int,
    cmid: int,
    user_id: int,
    payload: GradePayload,
    current_user: User = Depends(require_roles(["admin", "teacher", "course_creator"])),
    db: Session = Depends(get_db),
    client: MoodleClient = Depends(get_moodle_client),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    sub = db.query(Submission).filter(Submission.cmid == cmid, Submission.user_id == user_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    sub.grade = payload.grade
    sub.feedback = payload.feedback
    sub.graded_at = datetime.now(timezone.utc)
    db.commit()

    # Sync to Moodle if possible
    contents = await client.get_course_contents(course_id)
    target = None
    for section in contents:
        for mod in section.get("modules", []):
            if mod.get("id") == cmid:
                target = mod
                break
        if target:
            break
    if target and target.get("instance"):
        try:
            await client.save_assignment_grade(target["instance"], user_id, payload.grade, payload.feedback)
        except Exception:
            pass

    return {"status": "graded", "cmid": cmid, "user_id": user_id}


# ===================== QUIZ =====================

@router.post("/{course_id}/modules/{cmid}/quiz/start")
async def start_quiz(
    course_id: int,
    cmid: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    contents = await client.get_course_contents(course_id)
    target = None
    for section in contents:
        for mod in section.get("modules", []):
            if mod.get("id") == cmid:
                target = mod
                break
        if target:
            break
    if not target or target.get("modname") != "quiz":
        raise HTTPException(status_code=404, detail="Quiz not found")
    try:
        async with get_user_moodle_client(current_user.moodle_user_id) as user_client:
            result = await user_client.start_quiz_attempt(target["instance"])
        return result
    except Exception as e:
        msg = str(e)
        if "noquestionsfound" in msg.lower():
            raise HTTPException(status_code=400, detail="В тесте пока нет вопросов")
        if "attemptstillinprogress" in msg.lower():
            # Return existing in-progress attempt if found
            existing = moodle_db.get_inprogress_attempt(current_user.moodle_user_id, target["instance"])
            if existing:
                return {"attempt": existing, "warnings": []}
        raise HTTPException(status_code=500, detail=f"Failed to start quiz: {msg}")


@router.get("/{course_id}/modules/{cmid}/quiz/attempt/{attempt_id}")
async def get_quiz_attempt(
    course_id: int,
    cmid: int,
    attempt_id: int,
    page: int = 0,
    current_user: User = Depends(get_current_user),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    try:
        async with get_user_moodle_client(current_user.moodle_user_id) as user_client:
            data = await user_client.get_attempt_data(attempt_id, page)
        return data
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get attempt: {str(e)}")


class QuizSavePayload(BaseModel):
    data: List[Dict[str, Any]]


@router.post("/{course_id}/modules/{cmid}/quiz/attempt/{attempt_id}/save")
async def save_quiz_attempt_api(
    course_id: int,
    cmid: int,
    attempt_id: int,
    payload: QuizSavePayload,
    current_user: User = Depends(get_current_user),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    try:
        async with get_user_moodle_client(current_user.moodle_user_id) as user_client:
            result = await user_client.save_quiz_attempt(attempt_id, payload.data)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save attempt: {str(e)}")


@router.post("/{course_id}/modules/{cmid}/quiz/attempt/{attempt_id}/finish")
async def finish_quiz_attempt_api(
    course_id: int,
    cmid: int,
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    db: Session = Depends(get_db),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    # Find quiz instance for max_grade lookup
    contents = await client.get_course_contents(course_id)
    target = None
    for section in contents:
        for mod in section.get("modules", []):
            if mod.get("id") == cmid:
                target = mod
                break
        if target:
            break
    if not target or target.get("modname") != "quiz":
        raise HTTPException(status_code=404, detail="Quiz not found")

    instance = moodle_db.get_module_instance("quiz", target["instance"])
    max_grade = instance.get("sumgrades", 0) if instance else 0

    try:
        async with get_user_moodle_client(current_user.moodle_user_id) as user_client:
            result = await user_client.finish_quiz_attempt(attempt_id)
            # Try to fetch review for grade
            grade = None
            try:
                review = await user_client.get_attempt_review(attempt_id)
                grade = review.get("grade")
                if isinstance(grade, dict):
                    grade = grade.get("grade")
                if isinstance(grade, str):
                    try:
                        grade = float(grade)
                    except ValueError:
                        grade = None
                if grade is None:
                    raw_mark = review.get("mark")
                    if isinstance(raw_mark, str):
                        parts = raw_mark.split("/")
                        if parts:
                            try:
                                grade = float(parts[0].strip())
                            except ValueError:
                                grade = None
                    elif isinstance(raw_mark, (int, float)):
                        grade = float(raw_mark)
            except Exception:
                pass

            # Save local quiz attempt result
            existing_qa = db.query(QuizAttempt).filter(
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.cmid == cmid,
            ).first()
            if existing_qa:
                existing_qa.moodle_attempt_id = attempt_id
                existing_qa.grade = grade
                existing_qa.max_grade = max_grade
                existing_qa.state = "finished"
                existing_qa.finished_at = datetime.now(timezone.utc)
            else:
                db.add(QuizAttempt(
                    user_id=current_user.id,
                    cmid=cmid,
                    course_id=course_id,
                    moodle_attempt_id=attempt_id,
                    grade=grade,
                    max_grade=max_grade,
                ))

            # Mark completion
            existing_comp = db.query(UserModuleCompletion).filter(
                UserModuleCompletion.user_id == current_user.id,
                UserModuleCompletion.cmid == cmid,
            ).first()
            if not existing_comp:
                db.add(UserModuleCompletion(user_id=current_user.id, cmid=cmid, course_id=course_id))
            db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finish attempt: {str(e)}")


@router.get("/{course_id}/modules/{cmid}/quiz/attempt/{attempt_id}/review")
async def review_quiz_attempt(
    course_id: int,
    cmid: int,
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    try:
        async with get_user_moodle_client(current_user.moodle_user_id) as user_client:
            result = await user_client.get_attempt_review(attempt_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get review: {str(e)}")


# ===================== FORUM =====================

@router.get("/{course_id}/modules/{cmid}/forum/discussions")
async def list_forum_discussions(
    course_id: int,
    cmid: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    contents = await client.get_course_contents(course_id)
    target = None
    for section in contents:
        for mod in section.get("modules", []):
            if mod.get("id") == cmid:
                target = mod
                break
        if target:
            break
    if not target or target.get("modname") != "forum":
        raise HTTPException(status_code=404, detail="Forum not found")
    try:
        result = await client.get_forum_discussions(target["instance"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get discussions: {str(e)}")


class DiscussionPayload(BaseModel):
    subject: str
    message: str


@router.post("/{course_id}/modules/{cmid}/forum/discussions")
async def create_forum_discussion(
    course_id: int,
    cmid: int,
    payload: DiscussionPayload,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    contents = await client.get_course_contents(course_id)
    target = None
    for section in contents:
        for mod in section.get("modules", []):
            if mod.get("id") == cmid:
                target = mod
                break
        if target:
            break
    if not target or target.get("modname") != "forum":
        raise HTTPException(status_code=404, detail="Forum not found")
    if not current_user.moodle_user_id:
        raise HTTPException(status_code=400, detail="User not linked to Moodle")
    try:
        async with get_user_moodle_client(current_user.moodle_user_id) as user_client:
            result = await user_client.add_forum_discussion(target["instance"], payload.subject, payload.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create discussion: {str(e)}")


@router.get("/{course_id}/modules/{cmid}/forum/discussions/{discussion_id}/posts")
async def get_forum_posts_api(
    course_id: int,
    cmid: int,
    discussion_id: int,
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    try:
        result = await client.get_forum_posts(discussion_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get posts: {str(e)}")


class PostPayload(BaseModel):
    subject: str
    message: str
    parent_post_id: int


@router.post("/{course_id}/modules/{cmid}/forum/discussions/{discussion_id}/posts")
async def create_forum_post_api(
    course_id: int,
    cmid: int,
    discussion_id: int,
    payload: PostPayload,
    current_user: User = Depends(get_current_user),
    _course_access: None = Depends(require_course_access),
) -> Dict[str, Any]:
    try:
        async with get_user_moodle_client(current_user.moodle_user_id) as user_client:
            result = await user_client.add_forum_post(payload.parent_post_id, payload.subject, payload.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")
