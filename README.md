# DreamDocs Academy

Образовательный портал с интеграцией LMS Moodle. Позволяет управлять пользователями, курсами, зачислениями и ролями через современный веб-интерфейс, синхронизируя данные с ядром Moodle.

---

## Архитектура

Проект состоит из трёх частей:

| Компонент | Технологии | Порт | Описание |
|-----------|------------|------|----------|
| **Moodle** | PHP 8.1, Apache, MySQL 8.0 | `8080` | Ядро LMS (v4.4.0) |
| **Portal Backend** | Python 3.11, FastAPI, SQLAlchemy, SQLite | `8000` | REST API, JWT-авторизация, прослойка к Moodle |
| **Portal Frontend** | Vue 3, Vite, Pinia, Vue Router | `5173` | SPA-интерфейс портала |

---

## Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone https://github.com/kiruha3/DreamAcademy.git
cd DreamAcademy/dreamdox-academy
```

### 2. Настрой переменные окружения

```bash
cp .env.example .env
```

Отредактируй `.env`, указав реальные значения:

```env
MOODLE_URL=http://localhost:8080
MOODLE_PUBLIC_URL=http://localhost:8080
MOODLE_TOKEN=your_moodle_webservice_token
SECRET_KEY=your_jwt_secret_key
DATABASE_URL=sqlite:////app/data/academy.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Важно:** `.env` не коммитится в git. Никогда не добавляй реальные токены и пароли в репозиторий.

### 3. Запуск через Docker Compose (рекомендуется)

```powershell
# Windows (PowerShell)
.\scripts\first_start.ps1
```

Или вручную:

```bash
docker compose up -d
```

Скрипт `first_start.ps1` проверит Docker, соберёт образ Moodle, запустит сервисы и дождётся готовности Moodle (до 60 попыток).

### 4. Запуск фронтенда локально (для разработки)

```bash
cd portal/frontend
npm install
npm run dev
```

Фронтенд откроется на `http://localhost:5173`. Vite проксирует `/api` и `/auth` на бэкенд (`http://localhost:8000`).

---

## Технологический стек

### Backend
- **FastAPI** `0.111.0` — веб-фреймворк
- **Uvicorn** `0.30.0` — ASGI-сервер
- **Pydantic v2** + **pydantic-settings** — валидация и конфигурация
- **SQLAlchemy 2.0** — ORM, SQLite для портала
- **PyMySQL** `1.1.1` — прямой доступ к БД Moodle
- **httpx** `0.27.0` — асинхронные запросы к Moodle REST API
- **bcrypt** + **python-jose[cryptography]** — хеширование паролей и JWT
- **pytest** `8.2.0` — тестирование

### Frontend
- **Vue 3** `^3.4.21` (Composition API, `<script setup>`)
- **Vue Router 4** `^4.3.0`
- **Pinia 3** `^3.0.4`
- **Vite 5** `^5.2.0`
- **Vitest** `^1.4.0`

### Инфраструктура
- Docker Compose (3 сервиса: `db`, `moodle`, `portal-backend`)
- MySQL 8.0 — БД Moodle
- SQLite — БД бэкенд-портала

---

## Структура проекта

```
dreamdox-academy/
├── docker-compose.yml
├── .env.example
├── portal/
│   ├── backend/           # FastAPI-приложение
│   │   ├── app/           # Роутеры, модели, клиент Moodle
│   │   ├── tests/         # pytest
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── frontend/          # Vue 3 + Vite
│       ├── src/
│       ├── public/
│       ├── package.json
│       └── vite.config.js
├── moodle/                # Dockerfile и entrypoint для Moodle
├── mcp-server/            # MCP-сервер для AI-интеграции
├── mcp-client-kit/        # MCP-клиент (тонкий клиент)
├── scripts/               # Автоматизация (first_start.ps1 и др.)
├── tests/                 # Тесты backend
└── docs/                  # Документация (FIRST_START.md, MOODLE_SETUP.md)
```

---

## API и возможности

- **Аутентификация:** регистрация, вход, JWT-токены, синхронизация паролей с Moodle
- **Пользователи:** роли (admin, course_creator, teacher, student), управление через админ-панель
- **Курсы:** список курсов, содержимое курса, зачисление пользователей
- **Конструктор курсов:** добавление/удаление секций и модулей (page, url, label, forum, quiz, assign, book)
- **Приглашения:** приглашение пользователей на курсы с автоматическим созданием в Moodle
- **Админ-панель:** управление пользователями, создание/удаление курсов, seed демо-контента

---

## Тестирование

### Backend

```powershell
$env:PYTHONPATH="e:\DreamAcademy\dreamdox-academy;$env:PYTHONPATH"
python -m pytest tests/backend/ -v
```

### Frontend

```bash
cd portal/frontend
npm run test
```

---

## Полезные команды

```bash
# Логи
docker compose logs -f moodle
docker compose logs -f portal-backend

# Перезапуск бэкенда после изменения .env
docker compose restart portal-backend

# Остановка
docker compose down
```

---

## Безопасность

- **Никогда** не коммить `.env`, `.env.local`, `.env.production`.
- Не коммить API-токены, пароли БД, SSH-ключи, сертификаты.
- Не коммитить Docker volumes (`db_data/`, `moodle_data/`, `moodledata_data/`), `node_modules/`, `dist/`, `build/`.
- Если секрет случайно попал в git — немедленно ротировать токен/пароль и очистить историю.

---

## Документация

- [FIRST_START.md](docs/FIRST_START.md) — подробная инструкция по первому запуску
- [MOODLE_SETUP.md](docs/MOODLE_SETUP.md) — настройка Moodle Web Services API
- [REPO_RULES.md](REPO_RULES.md) — правила репозитория и безопасности

---

## Лицензия

Проект является закрытым (private). Распространение и использование без согласования запрещено.
