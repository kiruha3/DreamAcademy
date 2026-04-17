import os
import secrets
import subprocess
import base64
import json
import pymysql
from typing import List, Dict, Any, Optional

DB_HOST = os.getenv("MOODLE_DATABASE_HOST", "db")
DB_USER = os.getenv("MOODLE_DATABASE_USER", "moodle")
DB_PASS = os.getenv("MOODLE_DATABASE_PASSWORD", "moodlesecret")
DB_NAME = os.getenv("MOODLE_DATABASE_NAME", "moodle")
PREFIX = "mdl_"


def _connect():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def ensure_user_token(user_id: int, service_id: int = 2, creator_id: int = 2) -> str:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT token FROM {PREFIX}external_tokens WHERE userid = %s AND externalserviceid = %s LIMIT 1",
                (user_id, service_id),
            )
            row = cur.fetchone()
            if row and row.get("token"):
                return row["token"]
            token = secrets.token_hex(16)
            cur.execute(
                f"""
                INSERT INTO {PREFIX}external_tokens
                (token, tokentype, externalserviceid, userid, creatorid, iprestriction, validuntil, timecreated, lastaccess, contextid)
                VALUES (%s, 0, %s, %s, %s, '', 0, UNIX_TIMESTAMP(), 0, 1)
                """,
                (token, service_id, user_id, creator_id),
            )
            conn.commit()
            return token


ALLOWED_MODULES = {"page", "url", "label", "forum", "quiz", "assign", "resource", "book", "lesson", "wiki", "glossary", "choice", "feedback", "survey", "data", "scorm", "lti", "folder", "imscp"}

def _validate_modname(modname: str) -> None:
    if modname not in ALLOWED_MODULES:
        raise ValueError(f"Invalid module name: {modname}")

def get_module_instance(modname: str, instance_id: int) -> Optional[Dict[str, Any]]:
    _validate_modname(modname)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {PREFIX}{modname} WHERE id = %s LIMIT 1", (instance_id,))
            return cur.fetchone()


def get_course_contents(course_id: int) -> List[Dict[str, Any]]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {PREFIX}course_sections WHERE course = %s ORDER BY section",
                (course_id,),
            )
            sections = cur.fetchall()
            for sec in sections:
                sec["modules"] = []
                if sec.get("sequence"):
                    cmids = [int(x) for x in sec["sequence"].split(",") if x]
                    if cmids:
                        placeholders = ",".join(["%s"] * len(cmids))
                        cur.execute(
                            f"""
                            SELECT cm.id, cm.instance, m.name as modname, cm.visible
                            FROM {PREFIX}course_modules cm
                            JOIN {PREFIX}modules m ON cm.module = m.id
                            WHERE cm.id IN ({placeholders})
                            ORDER BY FIELD(cm.id, {placeholders})
                            """,
                            tuple(cmids + cmids),
                        )
                        modules = cur.fetchall()
                        for mod in modules:
                            # fetch module instance name
                            cur.execute(
                                f"SELECT name FROM {PREFIX}{mod['modname']} WHERE id = %s LIMIT 1",
                                (mod["instance"],),
                            )
                            row = cur.fetchone()
                            mod["name"] = row["name"] if row else mod["modname"]
                        sec["modules"] = modules
            return sections


def add_section(course_id: int, name: str, summary: str = "") -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            # find next section number
            cur.execute(
                f"SELECT MAX(section) as maxsec FROM {PREFIX}course_sections WHERE course = %s",
                (course_id,),
            )
            row = cur.fetchone()
            next_section = (row["maxsec"] or 0) + 1
            cur.execute(
                f"""
                INSERT INTO {PREFIX}course_sections (course, section, name, summary, summaryformat, sequence, visible, timemodified)
                VALUES (%s, %s, %s, %s, 1, '', 1, UNIX_TIMESTAMP())
                """,
                (course_id, next_section, name, summary),
            )
            conn.commit()
            return cur.lastrowid


def delete_section(course_id: int, section_id: int) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT sequence FROM {PREFIX}course_sections WHERE id = %s AND course = %s",
                (section_id, course_id),
            )
            row = cur.fetchone()
            if row and row.get("sequence"):
                cmids = [int(x) for x in row["sequence"].split(",") if x]
                for cmid in cmids:
                    delete_module(cmid)
            cur.execute(
                f"DELETE FROM {PREFIX}course_sections WHERE id = %s AND course = %s",
                (section_id, course_id),
            )
            conn.commit()


def _get_module_id(modname: str) -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT id FROM {PREFIX}modules WHERE name = %s LIMIT 1", (modname,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Unknown module type: {modname}")
            return row["id"]


def _get_section_by_num(course_id: int, section_num: int) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {PREFIX}course_sections WHERE course = %s AND section = %s LIMIT 1",
                (course_id, section_num),
            )
            return cur.fetchone()


def add_module(course_id: int, section_num: int, modname: str, name: str, content: str = "", options: dict = None) -> int:
    options = options or {}
    module_id = _get_module_id(modname)
    with _connect() as conn:
        with conn.cursor() as cur:
            instance_id = None
            if modname == "page":
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}page (course, name, intro, introformat, content, contentformat, timemodified)
                    VALUES (%s, %s, %s, 1, %s, 1, UNIX_TIMESTAMP())
                    """,
                    (course_id, name, options.get("intro", ""), content),
                )
                instance_id = cur.lastrowid
            elif modname == "url":
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}url (course, name, intro, introformat, externalurl, display, timemodified)
                    VALUES (%s, %s, %s, 1, %s, 1, UNIX_TIMESTAMP())
                    """,
                    (course_id, name, options.get("intro", ""), content or options.get("url", "https://")),
                )
                instance_id = cur.lastrowid
            elif modname == "label":
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}label (course, name, intro, introformat, timemodified)
                    VALUES (%s, %s, %s, 1, UNIX_TIMESTAMP())
                    """,
                    (course_id, name, content),
                )
                instance_id = cur.lastrowid
            elif modname == "forum":
                forum_type = options.get("type", "general")
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}forum (course, name, intro, introformat, type, timemodified)
                    VALUES (%s, %s, %s, 1, %s, UNIX_TIMESTAMP())
                    """,
                    (course_id, name, content or options.get("intro", ""), forum_type),
                )
                instance_id = cur.lastrowid
            elif modname == "quiz":
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}quiz (
                        course, name, intro, introformat, timeopen, timeclose, grade, sumgrades,
                        preferredbehaviour, questionsperpage, timemodified,
                        reviewattempt, reviewcorrectness, reviewmarks, reviewmaxmarks,
                        reviewspecificfeedback, reviewgeneralfeedback, reviewrightanswer, reviewoverallfeedback
                    )
                    VALUES (%s, %s, %s, 1, 0, 0, %s, %s, 'deferredfeedback', 0, UNIX_TIMESTAMP(),
                            69952, 69952, 69952, 1, 69952, 69952, 69952, 69952)
                    """,
                    (course_id, name, content or options.get("intro", ""), options.get("grade", 10), options.get("sumgrades", 10)),
                )
                instance_id = cur.lastrowid
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}quiz_sections (quizid, firstslot, heading, shufflequestions)
                    VALUES (%s, 1, '', 0)
                    """,
                    (instance_id,),
                )
            elif modname == "assign":
                duedate = options.get("duedate", 0)
                grade = options.get("grade", 100)
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}assign (course, name, intro, introformat, duedate, grade, timemodified)
                    VALUES (%s, %s, %s, 1, %s, %s, UNIX_TIMESTAMP())
                    """,
                    (course_id, name, content or options.get("intro", ""), duedate, grade),
                )
                instance_id = cur.lastrowid
            elif modname == "book":
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}book (course, name, intro, introformat, numbering, navstyle, customtitles, revision, timecreated, timemodified)
                    VALUES (%s, %s, %s, 1, 0, 1, 0, 0, UNIX_TIMESTAMP(), UNIX_TIMESTAMP())
                    """,
                    (course_id, name, content or options.get("intro", "")),
                )
                instance_id = cur.lastrowid
            else:
                raise RuntimeError(f"Module type {modname} not supported in builder")

            sec = _get_section_by_num(course_id, section_num)
            section_id = sec["id"] if sec else section_num
            cur.execute(
                f"""
                INSERT INTO {PREFIX}course_modules (course, module, instance, section, added, visible, visibleold)
                VALUES (%s, %s, %s, %s, UNIX_TIMESTAMP(), 1, 1)
                """,
                (course_id, module_id, instance_id, section_id),
            )
            cmid = cur.lastrowid

            sec = _get_section_by_num(course_id, section_num)
            if sec:
                new_seq = f"{sec['sequence']},{cmid}" if sec.get("sequence") else str(cmid)
                cur.execute(
                    f"UPDATE {PREFIX}course_sections SET sequence = %s WHERE id = %s",
                    (new_seq, sec["id"]),
                )
            conn.commit()
            return cmid


def add_book(course_id: int, section_num: int, name: str, intro: str = "") -> tuple:
    module_id = _get_module_id("book")
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {PREFIX}book (course, name, intro, introformat, numbering, navstyle, customtitles, revision, timecreated, timemodified)
                VALUES (%s, %s, %s, 1, 0, 1, 0, 0, UNIX_TIMESTAMP(), UNIX_TIMESTAMP())
                """,
                (course_id, name, intro),
            )
            book_id = cur.lastrowid
            sec = _get_section_by_num(course_id, section_num)
            section_id = sec["id"] if sec else section_num
            cur.execute(
                f"""
                INSERT INTO {PREFIX}course_modules (course, module, instance, section, added, visible, visibleold)
                VALUES (%s, %s, %s, %s, UNIX_TIMESTAMP(), 1, 1)
                """,
                (course_id, module_id, book_id, section_id),
            )
            cmid = cur.lastrowid
            if sec:
                new_seq = f"{sec['sequence']},{cmid}" if sec.get("sequence") else str(cmid)
                cur.execute(
                    f"UPDATE {PREFIX}course_sections SET sequence = %s WHERE id = %s",
                    (new_seq, sec["id"]),
                )
            conn.commit()
            return cmid, book_id


def add_book_chapter(book_id: int, title: str, content: str, chapter_num: int = 0, subchapter: int = 0) -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            # Determine next pagenum
            cur.execute(
                f"SELECT MAX(pagenum) as maxpage FROM {PREFIX}book_chapters WHERE bookid = %s",
                (book_id,),
            )
            row = cur.fetchone()
            next_pagenum = (row["maxpage"] or 0) + 1
            cur.execute(
                f"""
                INSERT INTO {PREFIX}book_chapters (bookid, pagenum, subchapter, title, content, contentformat, hidden, timecreated, timemodified, importsrc)
                VALUES (%s, %s, %s, %s, %s, 1, 0, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), '')
                """,
                (book_id, next_pagenum, subchapter, title, content),
            )
            chapter_id = cur.lastrowid
            # Update book revision
            cur.execute(
                f"UPDATE {PREFIX}book SET revision = revision + 1, timemodified = UNIX_TIMESTAMP() WHERE id = %s",
                (book_id,),
            )
            conn.commit()
            return chapter_id


def get_inprogress_attempt(user_id: int, quiz_id: int) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, quiz, userid, attempt, uniqueid, layout, currentpage, preview, state, timestart, timefinish, timemodified, timemodifiedoffline, timecheckstate, sumgrades, gradednotificationsenttime
                FROM {PREFIX}quiz_attempts
                WHERE userid = %s AND quiz = %s AND state = 'inprogress'
                ORDER BY timestart DESC
                LIMIT 1
                """,
                (user_id, quiz_id),
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "quiz": row["quiz"],
                    "userid": row["userid"],
                    "attempt": row["attempt"],
                    "uniqueid": row["uniqueid"],
                    "layout": row["layout"],
                    "currentpage": row["currentpage"],
                    "preview": row["preview"],
                    "state": row["state"],
                    "timestart": row["timestart"],
                    "timefinish": row["timefinish"],
                    "timemodified": row["timemodified"],
                    "timemodifiedoffline": row["timemodifiedoffline"],
                    "timecheckstate": row["timecheckstate"],
                    "sumgrades": row["sumgrades"],
                    "gradednotificationsenttime": row["gradednotificationsenttime"],
                }
            return None


def get_book_chapters(book_id: int) -> List[Dict[str, Any]]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id, pagenum, subchapter, title, content, hidden FROM {PREFIX}book_chapters WHERE bookid = %s ORDER BY pagenum",
                (book_id,),
            )
            return cur.fetchall()


def add_quiz_question(quiz_id: int, qtype: str, name: str, questiontext: str, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add a question to a quiz using a PHP helper script inside the Moodle container."""
    MOODLE_CONTAINER = os.getenv("MOODLE_CONTAINER_NAME", "dd_academy_moodle")
    answers_b64 = base64.b64encode(json.dumps(answers).encode("utf-8")).decode("utf-8")
    cmd = [
        "docker", "exec", MOODLE_CONTAINER, "php", "/var/www/html/moodle_add_question.php",
        str(quiz_id), qtype, name, questiontext, answers_b64,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"PHP script failed: {result.stderr or result.stdout}")
    data = json.loads(result.stdout.strip().split("\n")[-1])
    if not data.get("success"):
        raise RuntimeError(f"Failed to add question: {data.get('error')}")
    return data


def clear_course_contents(course_id: int) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id, sequence FROM {PREFIX}course_sections WHERE course = %s",
                (course_id,),
            )
            sections = cur.fetchall()
            for sec in sections:
                if sec.get("sequence"):
                    cmids = [int(x) for x in sec["sequence"].split(",") if x]
                    for cmid in cmids:
                        delete_module(cmid)
            # Reset all sequences (keep sections)
            cur.execute(
                f"UPDATE {PREFIX}course_sections SET sequence = '' WHERE course = %s",
                (course_id,),
            )
            conn.commit()


def delete_module(cmid: int) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT module, instance, section, course FROM {PREFIX}course_modules WHERE id = %s LIMIT 1",
                (cmid,),
            )
            row = cur.fetchone()
            if not row:
                return
            modname_id = row["module"]
            instance_id = row["instance"]
            section_id = row["section"]
            course_id = row["course"]

            cur.execute(f"SELECT name FROM {PREFIX}modules WHERE id = %s LIMIT 1", (modname_id,))
            mod_row = cur.fetchone()
            modname = mod_row["name"] if mod_row else None

            cur.execute(f"DELETE FROM {PREFIX}course_modules WHERE id = %s", (cmid,))

            if modname:
                _validate_modname(modname)
                cur.execute(f"DELETE FROM {PREFIX}{modname} WHERE id = %s", (instance_id,))

            # Update sequence
            cur.execute(
                f"SELECT sequence FROM {PREFIX}course_sections WHERE id = %s LIMIT 1",
                (section_id,),
            )
            sec_row = cur.fetchone()
            if sec_row and sec_row.get("sequence"):
                cmids = [x for x in sec_row["sequence"].split(",") if x and int(x) != cmid]
                new_seq = ",".join(cmids)
                cur.execute(
                    f"UPDATE {PREFIX}course_sections SET sequence = %s WHERE id = %s",
                    (new_seq, section_id),
                )
            conn.commit()


def create_course(fullname: str, shortname: str, categoryid: int = 1, summary: str = "") -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {PREFIX}course (category, sortorder, fullname, shortname, idnumber,
                    summary, summaryformat, format, showgrades, newsitems, startdate, marker,
                    maxbytes, legacyfiles, showreports, visible, visibleold, groupmode,
                    groupmodeforce, defaultgroupingid, lang, calendartype, theme, timecreated,
                    timemodified, requested, enablecompletion, completionnotify, cacherev)
                VALUES (%s, 0, %s, %s, '', %s, 1, 'topics', 1, 5, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 'ru', 'gregorian', '', UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 0, 0, 0, UNIX_TIMESTAMP())
                """,
                (categoryid, fullname, shortname, summary),
            )
            course_id = cur.lastrowid
            # Ensure context record exists for the course
            cur.execute(
                f"SELECT id FROM {PREFIX}context WHERE contextlevel = 50 AND instanceid = %s",
                (course_id,),
            )
            if not cur.fetchone():
                cur.execute(
                    f"""
                    INSERT INTO {PREFIX}context (contextlevel, instanceid, depth, path, locked)
                    VALUES (50, %s, 0, '', 0)
                    """,
                    (course_id,),
                )
                ctx_id = cur.lastrowid
                cur.execute(
                    f"UPDATE {PREFIX}context SET path = %s, depth = 2 WHERE id = %s",
                    (f"/1/{ctx_id}", ctx_id),
                )
            # Add default general section
            cur.execute(
                f"""
                INSERT INTO {PREFIX}course_sections (course, section, name, summary, summaryformat, sequence, visible, timemodified)
                VALUES (%s, 0, '', '', 1, '', 1, UNIX_TIMESTAMP())
                """,
                (course_id,),
            )
            # Enable manual enrolment so users can be enrolled
            cur.execute(
                f"""
                INSERT INTO {PREFIX}enrol (enrol, status, courseid, sortorder, name, enrolperiod, enrolstartdate, enrolenddate, expirynotify, expirythreshold, roleid, customint1, customint2, customint3, customint4, customint5, customint6, customint7, customint8, customchar1, customchar2, customchar3, customdec1, customdec2, timecreated, timemodified)
                VALUES ('manual', 0, %s, 0, '', 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', 0.0, 0.0, UNIX_TIMESTAMP(), UNIX_TIMESTAMP())
                """,
                (course_id,),
            )
            conn.commit()
            return course_id


def create_category(name: str, parent: int = 0, idnumber: str = "") -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT MAX(sortorder) as maxsort FROM {PREFIX}course_categories"
            )
            row = cur.fetchone()
            next_sort = (row["maxsort"] or 0) + 1
            cur.execute(
                f"""
                INSERT INTO {PREFIX}course_categories (name, idnumber, description, descriptionformat, parent, sortorder, coursecount, visible, visibleold, timemodified, depth, path, theme)
                VALUES (%s, %s, '', 1, %s, %s, 0, 1, 1, UNIX_TIMESTAMP(), 0, '', '')
                """,
                (name, idnumber, parent, next_sort),
            )
            cat_id = cur.lastrowid
            cur.execute(
                f"UPDATE {PREFIX}course_categories SET path = %s, depth = %s WHERE id = %s",
                (f"/{cat_id}", 1 if parent == 0 else 2, cat_id),
            )
            conn.commit()
            return cat_id


def get_course_images(course_ids: List[int], public_url: str = "", token: str = "") -> Dict[int, Dict[str, Any]]:
    """Return a mapping course_id -> image metadata fetched from Moodle DB overviewfiles."""
    if not course_ids:
        return {}
    with _connect() as conn:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(course_ids))
            cur.execute(
                f"""
                SELECT ctx.instanceid AS course_id, f.contextid, f.itemid, f.filename,
                       f.contenthash, f.mimetype
                FROM {PREFIX}files f
                JOIN {PREFIX}context ctx ON ctx.id = f.contextid
                WHERE ctx.contextlevel = 50
                  AND ctx.instanceid IN ({placeholders})
                  AND f.component = 'course'
                  AND f.filearea = 'overviewfiles'
                  AND f.filename != '.'
                  AND f.filename != ''
                """,
                tuple(course_ids),
            )
            rows = cur.fetchall()
            result: Dict[int, Dict[str, Any]] = {}
            for row in rows:
                cid = row["course_id"]
                if cid not in result:
                    result[cid] = {
                        "contextid": row["contextid"],
                        "itemid": row["itemid"],
                        "filename": row["filename"],
                        "contenthash": row["contenthash"],
                        "mimetype": row["mimetype"],
                    }
            return result
