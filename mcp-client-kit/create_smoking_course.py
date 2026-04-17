#!/usr/bin/env python3
"""Create a full course about smoking dangers via mcp-client-kit."""
import asyncio
import sys
import os
import json
import secrets

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from server import MCPMoodleServer, moodle_db


async def create_course():
    server = MCPMoodleServer()
    print(f"Connected to: {server.base_url}")

    # 1. Create course
    print("\n[1/6] Creating course...")
    result = await server.call_tool("create_course", {
        "fullname": "Вред курения: правда, которую скрывает табачная индустрия",
        "shortname": f"smoking_harm_{secrets.token_hex(3)}",
        "categoryid": 1,
        "summary": "Курс о медицинских, социальных и экономических последствиях курения. Предназначен для широкой аудитории.",
    })
    course_data = json.loads(result[0].text)
    if isinstance(course_data, list):
        course_data = course_data[0]
    course_id = course_data["id"]
    print(f"Course created: ID={course_id}")

    # 2. Create sections
    sections = [
        ("Введение", "Цели курса и что вы узнаете"),
        ("Что содержится в сигарете", "Состав табачного дыма"),
        ("Влияние на организм", "Как курение поражает различные органы"),
        ("Пассивное курение", "Опасность для окружающих"),
        ("Как бросить курить", "Практические рекомендации"),
        ("Проверь себя", "Итоговый тест"),
    ]

    section_ids = []
    for i, (name, summary) in enumerate(sections, start=1):
        print(f"\n[2/6] Creating section {i}: {name}...")
        res = await server.call_tool("create_section", {
            "course_id": course_id,
            "name": name,
            "summary": summary,
        })
        sec_data = json.loads(res[0].text)
        section_ids.append(sec_data["section_id"])
        print(f"Section {i} created: ID={sec_data['section_id']}")

    # 3. Add Page modules
    pages = [
        (1, "Введение в курс", """
        <h3>Добро пожаловать!</h3>
        <p>Этот курс поможет вам разобраться, почему курение — это не просто вредная привычка, а серьёзная угроза для здоровья.</p>
        <p><strong>Что вы узнаете:</strong></p>
        <ul>
            <li>Что на самом деле содержится в сигарете</li>
            <li>Как никотин влияет на сердце, лёгкие, мозг и иммунитет</li>
            <li>Почему пассивное курение опасно для близких</li>
            <li>Эффективные стратегии отказа от табака</li>
        </ul>
        <p>Проходите материалы в своём темпе и закрепляйте знания тестом в конце.</p>
        """),
        (2, "Состав сигареты", """
        <h3>Что вы вдыхаете с каждой затяжкой?</h3>
        <p>Табачный дым содержит более <strong>7000 химических соединений</strong>, из которых как минимум <strong>70</strong> являются канцерогенами.</p>
        <table border="1" cellpadding="5">
            <tr><th>Вещество</th><th>Где ещё используется</th></tr>
            <tr><td>Ацетон</td><td>Растворитель для лака</td></tr>
            <tr><td>Аммиак</td><td>Чистящие средства</td></tr>
            <tr><td>Мышьяк</td><td>Яд для грызунов</td></tr>
            <tr><td>Бензол</td><td>Топливо</td></tr>
            <tr><td>Формальдегид</td><td>Консервант для трупов</td></tr>
            <tr><td>Свинец</td><td>Тяжёлый металл, нейротоксин</td></tr>
            <tr><td>Угарный газ</td><td>Выхлопные газы автомобилей</td></tr>
        </table>
        <p>И это далеко не полный список. Каждая сигарета — это доза ядов, которую организм вынужден нейтрализовывать.</p>
        """),
        (4, "Пассивное курение", """
        <h3>Вы не курите — но вдыхаете</h3>
        <p>Пассивное курение (secondhand smoke) — это вдыхание воздуха с продуктами курения табака. Оно делится на два типа:</p>
        <ul>
            <li><strong>Mainstream smoke</strong> — выдыхаемый курильщиком дым</li>
            <li><strong>Sidestream smoke</strong> — дым, идущий от тлеющего конца сигареты</li>
        </ul>
        <p><strong>Риски для детей:</strong></p>
        <ul>
            <li>Синдром внезапной детской смерти (СВДС)</li>
            <li>Частые отиты и респираторные инфекции</li>
            <li>Астма и обострение аллергии</li>
            <li>Задержка развития лёгких</li>
        </ul>
        <p><strong>Риски для взрослых:</strong></p>
        <ul>
            <li>Инсульт и инфаркт (на 25–30% выше)</li>
            <li>Рак лёгких у некурящих</li>
            <li>Хронический бронхит</li>
        </ul>
        """),
        (5, "Как бросить курить", """
        <h3>Первый шаг — решение</h3>
        <p>Бросить курить сложно, но <strong>возможно</strong>. Вот проверенные стратегии:</p>
        <ol>
            <li><strong>Выберите дату «День Х»</strong> — и придерживайтесь её.</li>
            <li><strong>Уберите триггеры</strong> — выбросите сигареты, зажигалки, пепельницы.</li>
            <li><strong>Сообщите близким</strong> — поддержка окружения повышает шансы вдвое.</li>
            <li><strong>Замените привычку</strong> — жевательная резинка, прогулки, дыхательные упражнения.</li>
            <li><strong>Используйте заместительную терапию</strong> — пластыри, спреи, таблетки (по назначению врача).</li>
            <li><strong>Обратитесь к специалисту</strong> — психолог или нарколог помогут справиться с абстиненцией.</li>
        </ol>
        <p>Помните: даже одна непрокуренная сигарета — уже победа для организма.</p>
        """),
    ]

    for section_num, name, content in pages:
        print(f"\n[3/6] Adding page module to section {section_num}: {name}...")
        res = await server.call_tool("add_page_module", {
            "course_id": course_id,
            "section_num": section_num,
            "name": name,
            "content": content.strip(),
        })
        print(res[0].text)

    # 4. Add Book module with chapters
    print("\n[4/6] Adding book module to section 3...")
    book_res = await server.call_tool("add_book_module", {
        "course_id": course_id,
        "section_num": 3,
        "name": "Влияние курения на организм",
        "intro": "Подробный разбор последствий курения для различных систем организма.",
    })
    book_data = json.loads(book_res[0].text)
    book_id = book_data["book_id"]
    print(f"Book created: book_id={book_id}")

    chapters = [
        ("Сердечно-сосудистая система", """
        <p>Никотин и окись углерода повышают артериальное давление и учащают сердцебиение. 
        Курильщики в 2–4 раза чаще страдают ишемической болезнью сердца, инфарктом миокарда и инсультом.</p>
        <p>Курение повреждает эндотелий сосудов, способствуя образованию атеросклеротических бляшек.</p>
        """),
        ("Дыхательная система", """
        <p>Табачный дым разрушает реснички бронхов, нарушая естественную очистку лёгких. 
        Хронический бронхит и эмфизема (ХОБЛ) развиваются у 40–50% курильщиков.</p>
        <p>Рак лёгкого — ведущая причина смертности от онкологии среди мужчин и женщин, 
        и в 85–90% случаев связан с курением.</p>
        """),
        ("Нервная система", """
        <p>Никотин временно стимулирует выброс дофамина, создавая иллюзию расслабления. 
        Однако в долгосрочной перспективе курение увеличивает риск тревожности, депрессии и когнитивных нарушений.</p>
        <p>У пожилых курильщиков выше риск развития болезни Альцгеймера и сосудистой деменции.</p>
        """),
        ("Иммунитет", """
        <p>Табачные токсины подавляют активность иммунных клеток — макрофагов и Т-лимфоцитов. 
        Курильщики чаще болеют ОРВИ, гриппом, пневмонией и туберкулёзом.</p>
        <p>Замедляется заживление ран, повышается риск осложнений после операций.</p>
        """),
    ]

    for title, content in chapters:
        print(f"Adding chapter: {title}...")
        res = await server.call_tool("add_book_chapter", {
            "book_id": book_id,
            "title": title,
            "content": content.strip(),
        })
        print(res[0].text)

    # 5. Add Quiz module
    print("\n[5/6] Adding quiz module to section 6...")
    quiz_res = await server.call_tool("add_quiz_module", {
        "course_id": course_id,
        "section_num": 6,
        "name": "Проверь себя",
        "intro": "Ответьте на 5 вопросов, чтобы закрепить пройденный материал.",
    })
    quiz_text = quiz_res[0].text
    print(quiz_text)

    # Extract cmid from text like "Created quiz module with cmid=123"
    import re
    cmid_match = re.search(r"cmid=(\d+)", quiz_text)
    if cmid_match:
        cmid = int(cmid_match.group(1))
        # Query DB to get quiz instance id
        with moodle_db._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT instance FROM mdl_course_modules WHERE id = %s",
                    (cmid,),
                )
                row = cur.fetchone()
                quiz_id = row["instance"] if row else None
        print(f"Quiz ID: {quiz_id}")
    else:
        quiz_id = None

    # Trigger Moodle to create missing module contexts by calling course contents API
    if quiz_id:
        print("Triggering Moodle context creation...")
        await server.call_tool("get_course_contents", {"course_id": course_id})
        
        # Now query for module context (it should exist after API call)
        with moodle_db._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM mdl_context WHERE contextlevel = 70 AND instanceid = %s",
                    (cmid,),
                )
                module_ctx_row = cur.fetchone()
                module_context_id = module_ctx_row["id"] if module_ctx_row else 1
        print(f"Module context: {module_context_id}")
    else:
        module_context_id = 1

    # 6. Add quiz questions via direct DB (new Moodle question bank schema)
    if quiz_id:
        print("\n[6/6] Adding quiz questions...")
        questions = [
            {
                "name": "Вопрос 1: Состав сигареты",
                "text": "Сколько химических соединений содержится в табачном дыме?",
                "answers": [
                    {"text": "Более 7000", "fraction": 1.0},
                    {"text": "Около 100", "fraction": 0.0},
                    {"text": "Менее 50", "fraction": 0.0},
                    {"text": "Ровно 1000", "fraction": 0.0},
                ],
            },
            {
                "name": "Вопрос 2: Сердце",
                "text": "Во сколько раз чаще курильщики страдают ишемической болезнью сердца?",
                "answers": [
                    {"text": "В 2–4 раза", "fraction": 1.0},
                    {"text": "В 1,5 раза", "fraction": 0.0},
                    {"text": "Не чаще, чем некурящие", "fraction": 0.0},
                    {"text": "В 10 раз", "fraction": 0.0},
                ],
            },
            {
                "name": "Вопрос 3: Пассивное курение",
                "text": "Какой риск повышается у взрослых при регулярном контакте с пассивным курением?",
                "answers": [
                    {"text": "Инсульт и инфаркт на 25–30%", "fraction": 1.0},
                    {"text": "Только аллергия", "fraction": 0.0},
                    {"text": "Никаких рисков нет", "fraction": 0.0},
                    {"text": "Только кариес", "fraction": 0.0},
                ],
            },
            {
                "name": "Вопрос 4: Иммунитет",
                "text": "Что происходит с иммунитетом у курильщиков?",
                "answers": [
                    {"text": "Подавляется активность иммунных клеток", "fraction": 1.0},
                    {"text": "Иммунитет становится сильнее", "fraction": 0.0},
                    {"text": "Никаких изменений не происходит", "fraction": 0.0},
                    {"text": "Увеличивается выработка антител", "fraction": 0.0},
                ],
            },
            {
                "name": "Вопрос 5: Отказ от курения",
                "text": "Какая стратегия НЕ рекомендуется для бросания курить?",
                "answers": [
                    {"text": "Курить 'последнюю' сигарету каждый день", "fraction": 1.0},
                    {"text": "Выбрать дату 'День Х'", "fraction": 0.0},
                    {"text": "Убрать триггеры из окружения", "fraction": 0.0},
                    {"text": "Обратиться к специалисту", "fraction": 0.0},
                ],
            },
        ]

        with moodle_db._connect() as conn:
            with conn.cursor() as cur:
                # Get course context id for question category
                cur.execute(
                    "SELECT id FROM mdl_context WHERE contextlevel = 50 AND instanceid = %s",
                    (course_id,),
                )
                ctx_row = cur.fetchone()
                course_context_id = ctx_row["id"] if ctx_row else 1

                # Find or create default question category for this course context
                cur.execute(
                    "SELECT id FROM mdl_question_categories WHERE contextid = %s LIMIT 1",
                    (course_context_id,),
                )
                cat_row = cur.fetchone()
                if cat_row:
                    qcat_id = cat_row["id"]
                else:
                    cat_stamp = secrets.token_hex(16)
                    cur.execute(
                        """
                        INSERT INTO mdl_question_categories
                        (name, contextid, info, infoformat, stamp, parent, sortorder, idnumber)
                        VALUES ('Default for course', %s, '', 1, %s, 0, 999, NULL)
                        """,
                        (course_context_id, cat_stamp),
                    )
                    qcat_id = cur.lastrowid

                for q_idx, q in enumerate(questions, start=1):
                    stamp = secrets.token_hex(16)

                    # 1. Insert question
                    cur.execute(
                        """
                        INSERT INTO mdl_question 
                        (parent, name, questiontext, questiontextformat, generalfeedback, generalfeedbackformat,
                         defaultmark, penalty, qtype, length, stamp, timecreated, timemodified, createdby, modifiedby)
                        VALUES (0, %s, %s, 1, '', 1, 1.0, 0.3333333, 'multichoice', 1, %s, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 2, 2)
                        """,
                        (q["name"], q["text"], stamp),
                    )
                    question_id = cur.lastrowid

                    # 2. Insert question bank entry
                    cur.execute(
                        """
                        INSERT INTO mdl_question_bank_entries
                        (questioncategoryid, idnumber, ownerid)
                        VALUES (%s, NULL, 2)
                        """,
                        (qcat_id,),
                    )
                    entry_id = cur.lastrowid

                    # 3. Insert question version
                    cur.execute(
                        """
                        INSERT INTO mdl_question_versions
                        (questionbankentryid, version, questionid, status)
                        VALUES (%s, 1, %s, 'ready')
                        """,
                        (entry_id, question_id),
                    )

                    # 4. Insert multichoice options
                    cur.execute(
                        """
                        INSERT INTO mdl_qtype_multichoice_options
                        (questionid, layout, single, shuffleanswers, correctfeedback, correctfeedbackformat,
                         partiallycorrectfeedback, partiallycorrectfeedbackformat, incorrectfeedback, incorrectfeedbackformat,
                         answernumbering, shownumcorrect, showstandardinstruction)
                        VALUES (%s, 0, 1, 1, '', 1, '', 1, '', 1, 'abc', 1, 0)
                        """,
                        (question_id,),
                    )

                    # 5. Insert answers
                    for ans in q["answers"]:
                        cur.execute(
                            """
                            INSERT INTO mdl_question_answers
                            (question, answer, answerformat, fraction, feedback, feedbackformat)
                            VALUES (%s, %s, 1, %s, '', 1)
                            """,
                            (question_id, ans["text"], ans["fraction"]),
                        )

                    # 6. Insert quiz slot (page 0, not 1)
                    cur.execute(
                        """
                        INSERT INTO mdl_quiz_slots
                        (slot, quizid, page, requireprevious, maxmark)
                        VALUES (
                            (SELECT COALESCE(MAX(slot), 0) + 1 FROM mdl_quiz_slots AS s WHERE s.quizid = %s),
                            %s, 0, 0, 1.0)
                        """,
                        (quiz_id, quiz_id),
                    )
                    slot_id = cur.lastrowid

                    # 7. Insert question reference linking slot to question bank entry
                    # CRITICAL: usingcontextid must be the MODULE context (contextlevel 70), not course context
                    cur.execute(
                        """
                        INSERT INTO mdl_question_references
                        (usingcontextid, component, questionarea, itemid, questionbankentryid, version)
                        VALUES (%s, 'mod_quiz', 'slot', %s, %s, 1)
                        """,
                        (module_context_id, slot_id, entry_id),
                    )

                # Update quiz sumgrades and grade
                cur.execute(
                    "UPDATE mdl_quiz SET sumgrades = %s, grade = %s WHERE id = %s",
                    (len(questions), len(questions), quiz_id),
                )
                conn.commit()
        print(f"Added {len(questions)} questions to quiz.")
    else:
        print("Could not determine quiz_id — skipping questions.")

    # 7. Enrol existing portal users into the course
    print("\n[7/7] Enrolling users into the course...")
    with moodle_db._connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM mdl_user WHERE deleted = 0 AND suspended = 0 AND confirmed = 1 AND id > 1')
            user_ids = [r["id"] for r in cur.fetchall()]
    
    enrolled_count = 0
    for uid in user_ids:
        try:
            res = await server.call_tool("enrol_user", {"course_id": course_id, "user_id": uid, "role_id": 5})
            enrolled_count += 1
        except Exception as e:
            print(f"  Skipped user {uid}: {e}")
    print(f"Enrolled {enrolled_count} users")

    # Final summary
    print("\n" + "=" * 50)
    print("Курс успешно создан!")
    print("=" * 50)
    print(f"Course ID: {course_id}")
    print(f"Course URL: {server.base_url}/course/view.php?id={course_id}")
    print(f"Sections created: {len(section_ids)}")
    print(f"Book module ID: {book_id}")
    print(f"Quiz module CMID: {cmid if 'cmid' in dir() else 'N/A'}")
    print("=" * 50)
    return course_id


if __name__ == "__main__":
    asyncio.run(create_course())
