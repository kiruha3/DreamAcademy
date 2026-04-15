# DreamDocs Academy — Руководство для AI-агентов

> Этот файл предназначен для AI-агентов, работающих с проектом. Вся ключевая информация о структуре, стеке, сборке, конвенциях и архитектуре — ниже.

---

## 1. Обзор проекта

**DreamDocs Academy** (также встречается название DreamDox Academy) — это образовательный портал с интеграцией LMS Moodle.

Архитектура состоит из трёх частей:
1. **Moodle** — ядро LMS (PHP 8.1/Apache, Docker), порт `8080`. Скачивается `v4.4.0` из GitHub.
2. **Portal Backend** — REST API на Python/FastAPI, порт `8000`.
3. **Portal Frontend** — одностраничное приложение (SPA) на Vue 3 + Vite, порт `5173`.

Бэкенд выступает прослойкой между фронтендом и Moodle: управляет пользователями, курсами, приглашениями, ролями, JWT-авторизацией и синхронизацией паролей с Moodle. Собственная БД бэкенда — SQLite (в Docker-контейнере хранится в `/app/data/academy.db` на volume `backend_data`). Локально можно переопределить через переменную окружения `DATABASE_URL`.

Язык документации, пользовательского интерфейса и комментариев — **русский**.

---

## 2. Размещение кода

Рабочая директория `e:\DreamAcademy` содержит несколько логических зон:

```
e:\DreamAcademy
├── dreamdox-academy/          ← Основное runtime-приложение (Backend + Frontend + Moodle)
│   ├── docker-compose.yml
│   ├── .env / .env.example
│   ├── .gitignore
│   ├── REPO_RULES.md
│   ├── portal/
│   │   ├── backend/           ← FastAPI-приложение
│   │   │   ├── app/           ← Исходный код бэкенда
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   └── frontend/          ← Vue 3 + Vite
│   │       ├── src/
│   │       ├── package.json
│   │       └── vite.config.js
│   ├── moodle/                ← Dockerfile и entrypoint для Moodle
│   ├── scripts/               ← Автоматизация (first_start.ps1, setup_moodle_course.py)
│   ├── tests/                 ← Тесты backend (pytest) + зарезервировано для frontend
│   ├── docs/                  ← Документация по запуску и настройке
│   ├── reviews/               ← Ревью и анализ проекта
│   └── *.php                  ← Вспомогательные PHP-скрипты для Moodle (seed, test_*)
├── graphify/                  ← Самостоятельный Python-пакет для анализа кодовой базы
├── .kimi/skills/              ← Кастомные Kimi-скилы проекта
├── plans/                     ← Планы реализации по фазам
├── specs/                     ← Технические спецификации
├── .vscode/                   ← Рекомендуемое расширение VS Code (moonshot-ai.kimi-code)
├── src/                       ← Пустая директория (зарезервирована)
└── tests/                     ← Пустая директория на верхнем уровне
```

> **Важно:** корневые `src/` и `tests/` на верхнем уровне не используются. Весь рабочий код находится внутри `dreamdox-academy/`.

---

## 3. Технологический стек

### Backend (`dreamdox-academy/portal/backend/`)
- **Python 3.11** (Docker-образ `python:3.11-slim`)
- **FastAPI** `0.111.0`
- **Uvicorn** `0.30.0` (с `--reload` в dev)
- **Pydantic v2** `2.7.0` + `pydantic-settings` `2.2.1`
- **SQLAlchemy 2.0** `2.0.30` + SQLite (портал)
- **PyMySQL** `1.1.1` — прямой доступ к БД Moodle из бэкенда (`moodle_db.py`)
- **httpx** `0.27.0` — асинхронные запросы к Moodle REST API
- **bcrypt** `5.0.0` + **python-jose[cryptography]** `3.3.0` — хеширование паролей и JWT
- **python-multipart** `0.0.9`
- **pytest** `8.2.0` — тестирование

### Frontend (`dreamdox-academy/portal/frontend/`)
- **Vue 3** `^3.4.21` (Composition API, `<script setup>`)
- **Vue Router 4** `^4.3.0`
- **Pinia 3** `^3.0.4`
- **Vite 5** `^5.2.0`
- **Vitest** `^1.4.0` — юнит-тесты (настроен, но тестовые файлы пока отсутствуют)

### Инфраструктура
- **Docker Compose** — оркестрация трёх сервисов:
  - `db`: MySQL 8.0 (порт `3306`)
  - `moodle`: кастомный образ на PHP 8.1 + Apache (порт `8080`)
  - `portal-backend`: FastAPI (порт `8000`)
- В `docker-compose.yml` backend пробрасывает `/var/run/docker.sock` и содержит Docker CLI для выполнения `docker exec` внутри контейнера Moodle (используется для сброса кэша курсов).
- **MySQL 8.0** — БД для Moodle.
- **SQLite** — БД для бэкенд-портала.

---

## 4. Запуск и сборка

### Быстрый старт (рекомендуется)
```powershell
cd e:\DreamAcademy\dreamdox-academy
.\scripts\first_start.ps1
```
Скрипт проверит Docker, соберёт образ Moodle, запустит `docker compose up -d` и дождётся готовности Moodle (до 60 попыток с интервалом 5 сек).

### Ручной запуск
```powershell
cd e:\DreamAcademy\dreamdox-academy
copy .env.example .env
# Отредактируй .env, добавив MOODLE_TOKEN после настройки Moodle
docker compose up -d
```

### Запуск фронтенда (локально)
```powershell
cd e:\DreamAcademy\dreamdox-academy\portal\frontend
npm install   # если ещё не установлено
npm run dev
```
Фронтенд откроется на `http://localhost:5173`. В `vite.config.js` настроен прокси `/api` → `http://localhost:8000` и `/auth` → `http://localhost:8000`.
- Vite может автоматически переключиться на `5174`, `5175` или `5176`, если `5173` занят. Бэкенд уже разрешает CORS для этих портов.

### Сборка фронтенда для production
```powershell
cd e:\DreamAcademy\dreamdox-academy\portal\frontend
npm run build
```
Результат попадает в `dist/`.

### Остановка
```powershell
cd e:\DreamAcademy\dreamdox-academy
docker compose down
```

### Полезные команды
```powershell
# Логи
docker compose logs -f moodle
docker compose logs -f portal-backend

# Перезапуск бэкенда после изменения .env
docker compose restart portal-backend

# Создание тестового курса и пользователей в Moodle
python scripts/setup_moodle_course.py http://localhost:8080 YOUR_MOODLE_TOKEN
```

---

## 5. Организация кода

### Backend (`portal/backend/app/`)
- `main.py` — точка входа FastAPI. Подключает CORS (разрешены `localhost:5173-5176`) и все роутеры. Создаёт таблицы БД через `models.Base.metadata.create_all(bind=engine)`.
- `config.py` — настройки через `pydantic-settings`, читает `.env` (`MOODLE_URL`, `MOODLE_PUBLIC_URL`, `MOODLE_TOKEN`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`).
- `database.py` — SQLAlchemy `engine`/`SessionLocal`, `Base`. SQLite по умолчанию, путь `/app/data/academy.db` в Docker.
- `models.py` — ORM-модели. Пока только `User` (поля: `id`, `email`, `username`, `firstname`, `lastname`, `hashed_password`, `role`, `moodle_user_id`, `created_at`).
- `security.py` — bcrypt, JWT (`create_access_token`, `get_current_user`), `OAuth2PasswordBearer`, dependency `get_db`, `require_roles(allowed_roles)`.
- `auth_router.py` — эндпоинты аутентификации и регистрации (`/auth/register`, `/auth/login`, `/auth/me`, `/auth/moodle-credentials`, `/auth/change-password`). Создание пользователя в Moodle при регистрации и синхронизация паролей.
- `auth.py` — перечисление `Permission` (Enum) и `DEFAULT_ROLE_PERMISSIONS` (admin, course_creator, teacher, student) + `has_permission()`.
- `moodle_client.py` — асинхронный клиент `MoodleClient` для REST API Moodle. Методы: `get_users`, `create_user`, `get_courses`, `enrol_user`, `update_user_password`, `get_user_courses`, `get_course_contents`, `create_course`, `delete_course`.
- `moodle_roles.py` — маппинг ролей Portal → Moodle `role_id` (admin:1, course_creator:3, teacher:3, student:5).
- `moodle_db.py` — прямой доступ к MySQL Moodle через PyMySQL. Работает с таблицами `mdl_course_sections`, `mdl_course_modules`, `mdl_modules` и instance-таблицами (`mdl_page`, `mdl_url`, `mdl_label`, `mdl_forum`, `mdl_quiz`, `mdl_assign`). Функции: `get_course_contents`, `add_section`, `delete_section`, `add_module`, `delete_module`.
- `courses.py` — `GET /api/courses` — список всех курсов из Moodle.
- `course_content.py` — `GET /api/courses/{course_id}/contents` — богатое содержимое курса (секции и модули с иконками, URL) через Moodle REST API. Автоматически подменяет внутренние URL Moodle на публичные (`MOODLE_PUBLIC_URL`).
- `my_courses.py` — `GET /api/my-courses` — курсы текущего авторизованного пользователя.
- `invite.py` — `POST /api/courses/{course_id}/invite` — приглашение пользователя на курс (создание в Moodle при необходимости + зачисление).
- `admin.py` — административные эндпоинты:
  - `GET /api/admin/users` — список пользователей портала
  - `POST /api/admin/courses` — создание курса в Moodle
  - `DELETE /api/admin/courses/{course_id}` — удаление курса из Moodle
- `course_builder.py` — конструктор курсов (`/api/admin/courses/{course_id}/...`):
  - `GET /contents` — содержимое курса (секции и модули) через прямой SQL-запрос к MySQL Moodle
  - `POST /seed` — программное наполнение курса демо-контентом (8 модулей: форум, страница, ссылка, label, тест, задание) через `moodle_db.py`
  - `POST /sections` — добавить секцию
  - `DELETE /sections/{section_id}` — удалить секцию
  - `POST /modules` — добавить модуль (page, url, label, forum, quiz, assign)
  - `DELETE /modules/{cmid}` — удалить модуль
  - После каждой модификации вызывается `rebuild_course_cache()` в контейнере Moodle

### Frontend (`portal/frontend/src/`)
- `main.js` — инициализация Vue-приложения, Pinia, роутера, загрузка пользователя.
- `App.vue` — корневой шаблон с `<HeaderNav />` и `<router-view />`.
- `router/index.js` — маршруты: `/`, `/login`, `/register`, `/courses`, `/courses/:id`, `/dashboard`, `/admin`.
- `api/client.js` — тонкая обёртка над `fetch` (`apiGet`, `apiPost`) + endpoint-функции (`login`, `register`, `fetchCourses`, `inviteToCourse`, `fetchMyCourses`, `fetchUsers`, `createCourse`, `deleteCourse`, `changePassword`, etc.).
- `stores/auth.js` — Pinia store для аутентификации. Хранит `token` в `localStorage`.
- `views/` — страницы:
  - `HomeView.vue`
  - `LoginView.vue`
  - `RegisterView.vue`
  - `CoursesView.vue`
  - `CourseDetailView.vue` — детальная страница курса с визуализацией секций и модулей (иконки, типы, ссылки, HTML-labels)
  - `DashboardView.vue` — личный кабинет (мои курсы, прогресс, доступ к Moodle, смена пароля)
  - `AdminView.vue` — админ-панель (пользователи, создание/удаление курсов, Seed, конструктор курса с добавлением/удалением разделов и модулей)
- `components/` — переиспользуемые компоненты:
  - `HeaderNav.vue`
  - `CourseCard.vue`
  - `InviteModal.vue`
- `assets/global.css` — глобальные стили и CSS-переменные (цвета, типографика, утилиты).

---

## 6. Тестирование

### Backend
Тесты расположены в `dreamdox-academy/tests/backend/`.

Запуск:
```powershell
$env:PYTHONPATH="e:\DreamAcademy\dreamdox-academy;$env:PYTHONPATH"
python -m pytest tests/backend/ -v
```

Стратегия тестирования:
- Используется `TestClient` из FastAPI.
- `MoodleClient` мокается через `app.dependency_overrides` (см. `test_courses.py`, `test_invite.py`).
- Покрыты модули: `auth`, `courses`, `invite`, `main`, `moodle_client`.

### Frontend
В `package.json` настроена команда `npm run test` (Vitest), но на данный момент тестовые файлы в `tests/frontend/` отсутствуют.

---

## 7. Переменные окружения и секреты

Файл конфигурации — `dreamdox-academy/.env` (не коммитится!). Образец — `.env.example`.

Ключевые переменные:
- `MOODLE_TOKEN` — токен администратора Moodle Web Services.
- `MOODLE_URL` — URL Moodle (внутри Docker-сети: `http://moodle`, локально: `http://localhost:8080`).
- `MOODLE_PUBLIC_URL` — публичный URL Moodle, отдаётся фронтенду (`http://localhost:8080`).
- `SECRET_KEY` — ключ для подписи JWT.
- `DATABASE_URL` — URL SQLAlchemy (по умолчанию `sqlite:////app/data/academy.db` в контейнере).

### Правила безопасности (из `REPO_RULES.md`)
- **Никогда** не коммитить `.env`, `.env.local`, `.env.production`.
- Не коммитить API-токены, пароли БД, SSH-ключи, сертификаты (`*.pem`, `*.key`, `*.p12`, `*.pfx`).
- Не коммитить Docker volumes (`db_data/`, `moodle_data/`, `moodledata_data/`), `uploads/`, логи.
- Не коммитить `node_modules/`, `__pycache__/`, `dist/`, `build/`.
- Не коммитить авто-сгенерированные отчёты `graphify-out/` и `.graphify_*`.

Если секрет случайно попал в git — немедленно ротировать токен/пароль и переписать историю (`git filter-repo` или BFG).

---

## 8. Процедура перед коммитом

1. Убедиться, что новые артефакты/секреты добавлены в `.gitignore`.
2. Запустить тесты бэкенда: `pytest tests/backend/ -v`.
3. Прочитать diff перед `git push`.
4. В коммите должны быть только шаблоны окружения (`.env.example`), но не реальные `.env`.

---

## 9. graphify — инструмент анализа кодовой базы

В корне репозитория находится Python-пакет `graphify/`. Это **не часть runtime-приложения**, а вспомогательный инструмент для:
- извлечения структуры проекта (AST + семантический анализ),
- построения knowledge graph,
- кластеризации модулей,
- генерации HTML/JSON/SVG/GraphML-отчётов,
- запросов к графу (`query`, `path`, `explain`).

Запуск полного анализа:
```powershell
python -m graphify
```

Запуск обновления (только AST, без LLM):
```powershell
python -m graphify update .
```

Вывод попадает в `graphify-out/` (уже есть `.gitignore`-исключение). Перед архитектурными вопросами рекомендуется читать `graphify-out/GRAPH_REPORT.md`.

---

## 10. Дополнительные материалы

- `dreamdox-academy/docs/FIRST_START.md` — подробная инструкция по первому запуску.
- `dreamdox-academy/docs/MOODLE_SETUP.md` — настройка Moodle Web Services API.
- `dreamdox-academy/REPO_RULES.md` — правила репозитория и безопасности.
- `dreamdox-academy/scripts/setup_moodle_course.py` — скрипт для создания первого тестового курса и пользователей.
- `plans/` и `specs/` — планы реализации и технические спецификации проекта.
- `.kimi/skills/` — проектные Kimi-скилы (brainstorming, design-system, TDD, code reviewer, graphify, firecrawl и др.).
