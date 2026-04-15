import os
import secrets
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
                    INSERT INTO {PREFIX}quiz (course, name, intro, introformat, timeopen, timeclose, grade, sumgrades, timemodified)
                    VALUES (%s, %s, %s, 1, 0, 0, 10, 10, UNIX_TIMESTAMP())
                    """,
                    (course_id, name, content or options.get("intro", "")),
                )
                instance_id = cur.lastrowid
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


def get_course_images(course_ids: List[int], public_url: str, token: str) -> Dict[int, str]:
    """Return a mapping course_id -> image URL fetched from Moodle DB overviewfiles."""
    if not course_ids:
        return {}
    public_url = public_url.rstrip("/")
    with _connect() as conn:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(course_ids))
            cur.execute(
                f"""
                SELECT ctx.instanceid AS course_id, f.contextid, f.itemid, f.filename
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
            result: Dict[int, str] = {}
            for row in rows:
                cid = row["course_id"]
                if cid not in result:
                    url = f"{public_url}/webservice/pluginfile.php/{row['contextid']}/course/overviewfiles/{row['itemid']}/{row['filename']}?token={token}"
                    result[cid] = url
            return result
