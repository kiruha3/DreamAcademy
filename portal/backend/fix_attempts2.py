import sys, os
sys.path.insert(0, '/app')
os.environ['MOODLE_DATABASE_HOST'] = 'db'
import app.moodle_db as db

with db._connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, quiz, userid, state FROM mdl_quiz_attempts WHERE state = 'inprogress'")
        rows = cur.fetchall()
        print(f"Found {len(rows)} inprogress attempts")
        for row in rows:
            print(row)
        if rows:
            cur.execute("DELETE FROM mdl_quiz_attempts WHERE state = 'inprogress'")
            conn.commit()
            print(f"Deleted {cur.rowcount} inprogress attempts")
