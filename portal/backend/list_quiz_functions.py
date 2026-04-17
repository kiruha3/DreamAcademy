import sys, os
sys.path.insert(0, '/app')
os.environ['MOODLE_DATABASE_HOST'] = 'db'
import app.moodle_db as db

with db._connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM mdl_external_functions WHERE name LIKE 'mod_quiz%' ORDER BY name")
        for row in cur.fetchall():
            print(row['name'])
