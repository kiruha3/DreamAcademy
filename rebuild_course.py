import subprocess
import json


def send(proc, req):
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    return json.loads(line)


proc = subprocess.Popen(
    ["docker", "exec", "-i", "dd_academy_mcp", "python", "server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    encoding="utf-8",
    errors="replace",
)

# Initialize
send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "builder", "version": "1.0"},
}})

COURSE_ID = 4

# Helper for quick DB queries via docker
def db_query(sql, params):
    cmd = ["docker", "exec", "-i", "dd_academy_db", "mysql", "-umoodle", "-pmoodlesecret", "moodle", "-e", sql]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

# --- Clear course via backend container ---
clear_script = """
import sys
sys.path.insert(0, '/app/app')
import app.moodle_db as moodle_db
from app.course_builder import _clear_moodle_cache

course_id = 4
moodle_db.clear_course_contents(course_id)
with moodle_db._connect() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, section FROM mdl_course_sections WHERE course = %s AND section > 0",
            (course_id,),
        )
        for row in cur.fetchall():
            moodle_db.delete_section(course_id, row["id"])
_clear_moodle_cache(course_id)
print('cleared')
"""
import tempfile, os
tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
tmp.write(clear_script)
tmp.close()
subprocess.run(["docker", "cp", tmp.name, "dd_academy_backend:/app/clear.py"], check=True)
subprocess.run(["docker", "exec", "-i", "dd_academy_backend", "python", "/app/clear.py"], check=True)
subprocess.run(["docker", "exec", "-i", "dd_academy_backend", "rm", "-f", "/app/clear.py"])
os.unlink(tmp.name)
print("Course cleared")

# --- Create Section 1 ---
sec_resp = send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
    "name": "create_section",
    "arguments": {
        "course_id": COURSE_ID,
        "name": "Модуль 1. Введение в DreamDocs",
        "summary": "Базовая логика продукта, сущности, интерфейс, поиск, статусы и роли",
    },
}})
print("SECTION:", sec_resp)

# --- 1. Page: Как проходить модуль 1 ---
page_intro_content = """<p>В этом модуле вы познакомитесь с базовой логикой DreamDocs: поймете, какие задачи решает система, из каких сущностей она состоит, как устроена навигация и что означают основные статусы документов.</p>
<h3>Порядок прохождения</h3>
<ol>
<li>Изучите теорию.</li>
<li>Пройдите быструю самопроверку.</li>
<li>Выполните практическую работу.</li>
<li>Пройдите итоговый тест.</li>
</ol>
<p><strong>Модуль считается завершенным после сдачи практики и прохождения теста.</strong></p>
"""

page_intro = send(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
    "name": "add_page_module",
    "arguments": {
        "course_id": COURSE_ID,
        "section_num": 1,
        "name": "Как проходить модуль 1",
        "content": page_intro_content,
        "intro": "Краткая инструкция по прохождению модуля 1",
    },
}})
print("PAGE INTRO:", page_intro)

# --- 2. Book: Теория ---
book_resp = send(proc, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
    "name": "add_book_module",
    "arguments": {
        "course_id": COURSE_ID,
        "section_num": 1,
        "name": "Теория: введение в DreamDocs",
        "intro": "Основная теория модуля 1: 6 глав о продукте, сущностях, интерфейсе и ролях",
    },
}})
book_result = json.loads(book_resp["result"]["content"][0]["text"])
book_cmid = book_result["cmid"]
book_instance = book_result["book_id"]
print("BOOK cmid:", book_cmid, "instance:", book_instance)

chapters = [
    ("Глава 1. Что такое DreamDocs", """<p>DreamDocs — это система для интеллектуальной обработки документов. В базовом назначении системы указаны автоматическая классификация входящих документов, OCR-распознавание, извлечение структурированных данных и таблиц, нормализация, валидация и верификация, сравнение документов, формирование отчетов и метрик, интеграция с внешними системами через REST API, а также low/no-code настройка типов документов и правил обработки. Система может работать как on-prem, так и в облачном режиме.</p>
<p>Важно понимать, что DreamDocs — это <strong>не только OCR</strong>. OCR здесь является частью более длинной цепочки: документ загружается, классифицируется, распознается, из него извлекаются данные, затем они проверяются и могут быть отправлены во внешние системы. Именно эта полная цепочка — главный объект обучения.</p>"""),
    ("Глава 2. Какие задачи решает система на практике", """<p>DreamDocs применяется там, где есть большой поток документов и высокая цена ручной ошибки. Функциональные области: финансы, логистика и ВЭД, legal/compliance, HR, госсектор, производство и ритейл.</p>
<p>Примеры сценариев:</p>
<ul>
<li><strong>KYC:</strong> сбор данных из паспорта, СНИЛС, ИНН и проверка совпадения ФИО и даты рождения;</li>
<li><strong>Корпоративный KYC:</strong> сверка ИНН/КПП, реквизитов, полномочий подписанта;</li>
<li><strong>Первичная бухгалтерия:</strong> сопоставление счета, акта, УПД и проверка сумм и НДС;</li>
<li><strong>Логистика:</strong> сверка позиций, количества и дат приемки по комплекту документов.</li>
</ul>"""),
    ("Глава 3. Базовые сущности DreamDocs", """<p>Ключевые сущности в глоссарии DreamDocs:</p>
<ul>
<li><strong>Документ</strong> — объект, созданный из файла и содержащий атрибуты для распознавания; в одном файле может быть один или несколько документов.</li>
<li><strong>Воркспейс (Workspace)</strong> — рабочее пространство, связывающее несколько проектов.</li>
<li><strong>Проект</strong> — объект, куда загружаются и обрабатываются документы.</li>
<li><strong>Тип документа</strong> — задает набор полей.</li>
<li><strong>Тип поля</strong> — определяет, какие данные и в каком формате могут храниться в поле.</li>
<li><strong>Роль</strong> — объединяет пользователей и права доступа.</li>
</ul>
<p>Рабочая область — это контейнер верхнего уровня, который объединяет проекты, типы документов, типы полей и пользователей, изолирует данные и настройки между организациями или подразделениями и позволяет переиспользовать библиотеку типов документов и полей между проектами.</p>
<p>Простая учебная формула:</p>
<p><code>Workspace → Project → Document</code></p>"""),
    ("Глава 4. Как устроен интерфейс", """<p>В верхней панели DreamDocs находятся переключатель рабочей области, строка поиска, иконки помощи и уведомлений, а также меню профиля.</p>
<p>Основные рабочие разделы:</p>
<ul>
<li><strong>Проекты</strong> — для обзора групп документов и состава работы;</li>
<li><strong>Документы</strong> — для просмотра, фильтрации, верификации и обработки конкретных объектов.</li>
</ul>
<p>В проекте интерфейс может включать боковое меню с разделами: Files, Documents, Compare, Split, Uploads, Directories, Tasks, Settings. Состав меню зависит от роли пользователя и конфигурации системы.</p>
<p><strong>Важное различие:</strong> загрузка начинается в <strong>Uploads</strong>, затем файл попадает в <strong>Files</strong> как исходный объект, а после распознавания пользователь работает уже с <strong>Documents</strong> как с бизнес-сущностями.</p>"""),
    ("Глава 5. Поиск, статусы и движение документа", """<p>Верхнеуровневый сценарий работы в DreamDocs:</p>
<ol>
<li>Загрузка документа или пакета</li>
<li>Классификация</li>
<li>OCR</li>
<li>Извлечение данных</li>
<li>Нормализация</li>
<li>Верификация</li>
<li>Экспорт или интеграция</li>
</ol>
<p>В системе есть поиск по имени документа, по содержимому документа и по значениям полей. <strong>Поиск по содержимому работает по OCR-текстовому слою</strong>, то есть особенно полезен после распознавания.</p>
<p>Базовая логика статусов:</p>
<ul>
<li>Документ обрабатывается автоматически;</li>
<li>Готов к ручной проверке (статус <em>Размечено роботом</em>);</li>
<li>Требует исправления;</li>
<li>Утвержден;</li>
<li>Обработан с ошибкой (<em>Плохой файл</em>).</li>
</ul>"""),
    ("Глава 6. Кто работает в системе", """<p>Предустановленные прикладные роли в DreamDocs:</p>
<ul>
<li><strong>Admin</strong> — управляет рабочей областью и проектами;</li>
<li><strong>Manager</strong> — управляет процессом обработки;</li>
<li><strong>Annotator</strong> — работает с документами и разметкой;</li>
<li><strong>ReadOnly</strong> — видит данные без изменений;</li>
<li><strong>OnlyOwned</strong> — ограничен собственными документами.</li>
</ul>
<p>Ролевая модель используется для защиты данных и разделения обязанностей.</p>"""),
]

req_id = 5
for idx, (title, content) in enumerate(chapters, start=1):
    chap_resp = send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
        "name": "add_book_chapter",
        "arguments": {
            "book_id": book_instance,
            "title": title,
            "content": content,
            "subchapter": 0,
        },
    }})
    print(f"CHAPTER {idx}:", chap_resp)
    req_id += 1

# --- 3. Quiz: Быстрая самопроверка ---
quiz_self = send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
    "name": "add_quiz_module",
    "arguments": {
        "course_id": COURSE_ID,
        "section_num": 1,
        "name": "Быстрая самопроверка",
        "intro": "Проверьте базовые знания перед практической работой.",
    },
}})
req_id += 1
quiz_self_cmid = int(quiz_self["result"]["content"][0]["text"].replace("Created quiz module with cmid=", ""))
print("QUIZ SELF cmid:", quiz_self_cmid)

# Get quiz instance id
quiz_self_out = db_query(f"SELECT instance FROM mdl_course_modules WHERE id = {quiz_self_cmid};", [])
quiz_self_instance = int([l for l in quiz_self_out.splitlines() if l.strip() and not l.startswith('instance')][0])
print("QUIZ SELF instance:", quiz_self_instance)

selfcheck_questions = [
    {
        "name": "Соотнесите термин",
        "text": "<p>Какая сущность в DreamDocs объединяет проекты, пользователей и настройки?</p>",
        "answers": [
            {"text": "Документ", "fraction": 0},
            {"text": "Рабочая область (Workspace)", "fraction": 1},
            {"text": "Тип поля", "fraction": 0},
            {"text": "Роль", "fraction": 0},
        ],
    },
    {
        "name": "Цепочка обработки",
        "text": "<p>Какой этап идет сразу после OCR в DreamDocs?</p>",
        "answers": [
            {"text": "Экспорт", "fraction": 0},
            {"text": "Извлечение данных", "fraction": 1},
            {"text": "Верификация", "fraction": 0},
            {"text": "Классификация", "fraction": 0},
        ],
    },
    {
        "name": "Поиск документа",
        "text": "<p>Где пользователь чаще всего работает с уже распознанными и проверяемыми объектами?</p>",
        "answers": [
            {"text": "Files", "fraction": 0},
            {"text": "Documents", "fraction": 1},
            {"text": "Uploads", "fraction": 0},
            {"text": "Reports", "fraction": 0},
        ],
    },
    {
        "name": "Статус документа",
        "text": "<p>Какой статус означает, что документ готов к ручной проверке?</p>",
        "answers": [
            {"text": "Плохой файл", "fraction": 0},
            {"text": "Размечено роботом", "fraction": 1},
            {"text": "Удалено", "fraction": 0},
            {"text": "Передано", "fraction": 0},
        ],
    },
    {
        "name": "Поиск по содержимому",
        "text": "<p>Поиск по содержимому документа опирается на:</p>",
        "answers": [
            {"text": "OCR-текстовый слой", "fraction": 1},
            {"text": "Только название проекта", "fraction": 0},
            {"text": "Только комментарии пользователей", "fraction": 0},
            {"text": "Только справочники", "fraction": 0},
        ],
    },
]

for q in selfcheck_questions:
    q_resp = send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
        "name": "add_quiz_question",
        "arguments": {
            "quiz_id": quiz_self_instance,
            "qtype": "multichoice",
            "name": q["name"],
            "questiontext": q["text"],
            "answers": q["answers"],
        },
    }})
    print("SELF CHECK Q:", q_resp)
    req_id += 1

# --- 4. Assignment: Практическая работа 1 ---
assign_content = """<p>Войдите в DreamDocs и зафиксируйте, в какой рабочей области вы находитесь.</p>
<p>Откройте любой доступный проект.</p>
<p>Найдите внутри проекта один документ и выпишите:</p>
<ul>
<li>название файла;</li>
<li>тип документа;</li>
<li>текущий статус;</li>
<li>показатель качества или распознавания, если он виден.</li>
</ul>
<p>Выполните поиск по имени файла и приложите скриншот результата.</p>
<p>Выполните поиск по содержимому или по значению поля и приложите скриншот результата.</p>
<p>Коротко ответьте своими словами: чем отличаются рабочая область, проект и документ?</p>
<p><em>Дополнительно:</em> напишите, какие действия вы можете делать с документом, исходя из вашей роли или доступных кнопок интерфейса.</p>
<p><em>Если на стенде только одна рабочая область — просто зафиксируйте ее название. Если поиск по содержимому не сработал — укажите, что документ, вероятно, еще не имеет OCR-текстового слоя или в проекте нет подходящих данных.</em></p>
"""

assign = send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
    "name": "add_assignment_module",
    "arguments": {
        "course_id": COURSE_ID,
        "section_num": 1,
        "name": "Практическая работа 1. Базовая навигация в DreamDocs",
        "intro": assign_content,
        "duedate": 0,
        "grade": 100,
    },
}})
req_id += 1
print("ASSIGNMENT:", assign)

# --- 5. Quiz: Тест 1 ---
quiz_final = send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
    "name": "add_quiz_module",
    "arguments": {
        "course_id": COURSE_ID,
        "section_num": 1,
        "name": "Тест 1",
        "intro": "Итоговый тест модуля 1. 8 вопросов, 2 попытки, порог прохождения 80%, время 10–12 минут.",
    },
}})
req_id += 1
quiz_final_cmid = int(quiz_final["result"]["content"][0]["text"].replace("Created quiz module with cmid=", ""))
print("QUIZ FINAL cmid:", quiz_final_cmid)

quiz_final_out = db_query(f"SELECT instance FROM mdl_course_modules WHERE id = {quiz_final_cmid};", [])
quiz_final_instance = int([l for l in quiz_final_out.splitlines() if l.strip() and not l.startswith('instance')][0])
print("QUIZ FINAL instance:", quiz_final_instance)

final_questions = [
    {
        "name": "Вопрос 1",
        "text": "<p>Что наиболее точно описывает DreamDocs?</p>",
        "answers": [
            {"text": "Система хранения файлов без обработки", "fraction": 0},
            {"text": "Система интеллектуальной обработки документов с классификацией, OCR, извлечением данных, верификацией и интеграцией", "fraction": 1},
            {"text": "Только OCR-движок", "fraction": 0},
            {"text": "Только средство для сравнения документов", "fraction": 0},
        ],
    },
    {
        "name": "Вопрос 2",
        "text": "<p>Что такое рабочая область (workspace) в DreamDocs?</p>",
        "answers": [
            {"text": "Один конкретный документ", "fraction": 0},
            {"text": "Контейнер верхнего уровня, объединяющий проекты, пользователей и настройки", "fraction": 1},
            {"text": "Только папка для файлов", "fraction": 0},
            {"text": "Отчет по документам", "fraction": 0},
        ],
    },
    {
        "name": "Вопрос 3",
        "text": "<p>Что такое проект в DreamDocs?</p>",
        "answers": [
            {"text": "Объект, куда загружаются и обрабатываются документы", "fraction": 1},
            {"text": "Глобальная роль пользователя", "fraction": 0},
            {"text": "Таблица со справочниками", "fraction": 0},
            {"text": "Вид отчета", "fraction": 0},
        ],
    },
    {
        "name": "Вопрос 4",
        "text": "<p>Как соотносятся файл и документ в DreamDocs?</p>",
        "answers": [
            {"text": "Это всегда одно и то же", "fraction": 0},
            {"text": "Один документ может содержать много проектов", "fraction": 0},
            {"text": "Один файл может породить один или несколько документов", "fraction": 1},
            {"text": "Документ всегда создается без файла", "fraction": 0},
        ],
    },
    {
        "name": "Вопрос 5",
        "text": "<p>Поиск по содержимому документа опирается на:</p>",
        "answers": [
            {"text": "Название проекта", "fraction": 0},
            {"text": "OCR-текстовый слой", "fraction": 1},
            {"text": "Только комментарии пользователей", "fraction": 0},
            {"text": "Только справочники", "fraction": 0},
        ],
    },
    {
        "name": "Вопрос 6",
        "text": "<p>Какой статус означает, что автоматическая обработка уже завершена и документ готов к ручной проверке?</p>",
        "answers": [
            {"text": "Плохой файл", "fraction": 0},
            {"text": "Размечено роботом", "fraction": 1},
            {"text": "Передано", "fraction": 0},
            {"text": "Удалено", "fraction": 0},
        ],
    },
    {
        "name": "Вопрос 7",
        "text": "<p>Какая роль обычно дает полный контроль над рабочей областью и проектом?</p>",
        "answers": [
            {"text": "ReadOnly", "fraction": 0},
            {"text": "OnlyOwned", "fraction": 0},
            {"text": "Annotator", "fraction": 0},
            {"text": "Admin", "fraction": 1},
        ],
    },
    {
        "name": "Вопрос 8",
        "text": "<p>В каком разделе пользователь чаще всего работает с уже распознанными и проверяемыми объектами?</p>",
        "answers": [
            {"text": "Только в Reports", "fraction": 0},
            {"text": "В Documents", "fraction": 1},
            {"text": "Только в Profile", "fraction": 0},
            {"text": "В Calendar", "fraction": 0},
        ],
    },
]

for q in final_questions:
    q_resp = send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
        "name": "add_quiz_question",
        "arguments": {
            "quiz_id": quiz_final_instance,
            "qtype": "multichoice",
            "name": q["name"],
            "questiontext": q["text"],
            "answers": q["answers"],
        },
    }})
    print("FINAL Q:", q_resp)
    req_id += 1

# --- 6. Forum ---
forum = send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
    "name": "add_forum_module",
    "arguments": {
        "course_id": COURSE_ID,
        "section_num": 1,
        "name": "Обсуждения по модулю 1",
        "intro": "Задавайте вопросы и делитесь опытом прохождения модуля.",
        "forum_type": "general",
    },
}})
req_id += 1
print("FORUM:", forum)

# Verify
contents = send(proc, {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {
    "name": "get_course_contents",
    "arguments": {"course_id": COURSE_ID},
}})
sections = json.loads(contents["result"]["content"][0]["text"])
print(f"\nВсего разделов: {len(sections)}")
for s in sections:
    print(f"  Раздел {s['section']}: {s['name']} — {len(s.get('modules', []))} модулей")
    for m in s.get("modules", []):
        print(f"    - {m['name']} ({m['modname']}, id={m['id']})")

proc.stdin.close()
proc.wait()

# Clear cache
subprocess.run(["docker", "exec", "-i", "dd_academy_backend", "python", "-c",
    "from app.course_builder import _clear_moodle_cache; _clear_moodle_cache(4); print('cache cleared')"],
    check=True)

print("\nDone")
