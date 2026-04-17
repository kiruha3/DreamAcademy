import sys, os
sys.path.insert(0, '/app')
os.environ['MOODLE_DATABASE_HOST'] = 'db'
import app.moodle_db as db

with db._connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM mdl_external_functions WHERE name = 'mod_quiz_process_attempt'")
        row = cur.fetchone()
        if row:
            func_id = row['id']
            cur.execute("SELECT id FROM mdl_external_services_functions WHERE externalserviceid = 2 AND functionname = 'mod_quiz_process_attempt'")
            if not cur.fetchone():
                cur.execute("INSERT INTO mdl_external_services_functions (externalserviceid, functionname) VALUES (2, 'mod_quiz_process_attempt')")
                conn.commit()
                print("Added mod_quiz_process_attempt to DreamDocs API")
            else:
                print("Already linked")
        else:
            print("Function mod_quiz_process_attempt not found")
