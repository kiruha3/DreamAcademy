from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from .security import require_roles, get_current_user
from .models import User
from . import moodle_db
import subprocess
router = APIRouter(prefix="/api/admin/courses", tags=["course-builder"])


def _clear_moodle_cache(course_id: int) -> None:
    try:
        subprocess.run(
            [
                "docker", "exec", "dd_academy_moodle", "php", "-r",
                f"define('CLI_SCRIPT', true); require('/var/www/html/config.php'); rebuild_course_cache({course_id}, true);"
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        pass


class SectionCreateRequest(BaseModel):
    name: str
    summary: str = ""


class ModuleCreateRequest(BaseModel):
    section_num: int
    modname: str  # page, url, forum, quiz, assign, label
    name: str
    content: str = ""
    url: str = ""
    intro: str = ""
    duedate: int = 0
    grade: int = 100


@router.get("/{course_id}/contents")
async def get_course_contents(
    course_id: int,
    current_user: User = Depends(require_roles(["admin", "course_creator", "teacher"])),
) -> Dict[str, Any]:
    contents = moodle_db.get_course_contents(course_id)
    return {"course_id": course_id, "sections": contents}


@router.post("/{course_id}/seed")
async def seed_course(
    course_id: int,
    current_user: User = Depends(require_roles(["admin", "course_creator"])),
) -> Dict[str, Any]:
    try:
        moodle_db.clear_course_contents(course_id)
        # Ensure sections
        for secnum, name in [(0, "Общие сведения"), (1, "Теория"), (2, "Практика")]:
            sec = moodle_db._get_section_by_num(course_id, secnum)
            if not sec:
                moodle_db.add_section(course_id, name)
            else:
                # Update name if empty
                if not sec.get("name"):
                    with moodle_db._connect() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                f"UPDATE {moodle_db.PREFIX}course_sections SET name = %s WHERE id = %s",
                                (name, sec["id"]),
                            )
                            conn.commit()
        # Section 0: News forum
        moodle_db.add_module(course_id, 0, "forum", "Новости курса", "Объявления и новости", {"type": "news"})
        # Section 1: Theory
        moodle_db.add_module(course_id, 1, "page", "Введение в DreamDocs", "<p>DreamDocs помогает автоматизировать документооборот. В этом модуле мы рассмотрим основные возможности.</p>", {"intro": "Краткое введение"})
        moodle_db.add_module(course_id, 1, "url", "Официальный сайт DreamDocs", "", {"intro": "Полезная ссылка", "url": "https://dreamdocs.ru"})
        moodle_db.add_module(course_id, 1, "label", "Важно", '<div class="alert alert-info">Изучите теорию перед прохождением теста.</div>', {"intro": ""})
        # Section 2: Practice
        moodle_db.add_module(course_id, 2, "quiz", "Проверка знаний", "Пройдите тест из 10 вопросов", {"intro": "Тестирование"})
        moodle_db.add_module(course_id, 2, "assign", "Практическое задание", "Загрузите готовый документ по шаблону", {"intro": "Задание", "duedate": 0, "grade": 100})
        moodle_db.add_module(course_id, 2, "forum", "Обсуждения", "Задавайте вопросы и делитесь опытом", {"type": "general"})
        _clear_moodle_cache(course_id)
        return {"status": "seeded", "course_id": course_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seed error: {str(e)}")


@router.post("/{course_id}/sections")
async def add_section(
    course_id: int,
    req: SectionCreateRequest,
    current_user: User = Depends(require_roles(["admin", "course_creator"])),
) -> Dict[str, Any]:
    section_id = moodle_db.add_section(course_id, req.name, req.summary)
    _clear_moodle_cache(course_id)
    return {"status": "created", "section_id": section_id}


@router.delete("/{course_id}/sections/{section_id}")
async def delete_section(
    course_id: int,
    section_id: int,
    current_user: User = Depends(require_roles(["admin", "course_creator"])),
) -> Dict[str, Any]:
    moodle_db.delete_section(course_id, section_id)
    _clear_moodle_cache(course_id)
    return {"status": "deleted", "section_id": section_id}


@router.post("/{course_id}/modules")
async def add_module(
    course_id: int,
    req: ModuleCreateRequest,
    current_user: User = Depends(require_roles(["admin", "course_creator"])),
) -> Dict[str, Any]:
    options = {"intro": req.intro, "duedate": req.duedate, "grade": req.grade}
    if req.url:
        options["url"] = req.url
    content = req.content
    cmid = moodle_db.add_module(course_id, req.section_num, req.modname, req.name, content, options)
    _clear_moodle_cache(course_id)
    return {"status": "created", "cmid": cmid}


@router.delete("/{course_id}/modules/{cmid}")
async def delete_module(
    course_id: int,
    cmid: int,
    current_user: User = Depends(require_roles(["admin", "course_creator"])),
) -> Dict[str, Any]:
    moodle_db.delete_module(cmid)
    _clear_moodle_cache(course_id)
    return {"status": "deleted", "cmid": cmid}
