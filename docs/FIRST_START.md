# Первый запуск DreamDocs Academy

## Быстрый старт (одной командой)

Откройте PowerShell **от имени администратора** и выполните:

```powershell
cd E:\DreamAcademy\dreamdox-academy
.\scripts\first_start.ps1
```

Этот скрипт проверит Docker, запустит контейнеры и дождётся готовности Moodle.

---

## Ручной запуск (если скрипт не сработал)

### 1. Проверка Docker

```powershell
docker info
```

Если ошибка — установите [Docker Desktop](https://www.docker.com/products/docker-desktop/) и запустите его.

### 2. Подготовка окружения

```powershell
cd E:\DreamAcademy\dreamdox-academy
copy .env.example .env
docker compose up -d
```

### 3. Ожидание инициализации Moodle

Первый запуск занимает **2–3 минуты** (Moodle создаёт таблицы в БД).

```powershell
# Проверка готовности
while ($true) {
    try {
        $r = Invoke-WebRequest http://localhost:8080 -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { Write-Host "Ready!"; break }
    } catch {}
    Write-Host "Waiting..."
    Start-Sleep -Seconds 5
}
```

---

## Настройка Moodle Web Services API

### Шаг 1: Вход в Moodle
- Откройте http://localhost:8080
- Логин: `admin`
- Пароль: `AdminPass123!`

### Шаг 2: Включение веб-служб

1. **Site administration → Server → Web services → Overview**
2. Нажмите "Enable web services"
3. Нажмите "Enable protocols" → включите **REST**
4. Нажмите "Create a specific user" (опционально, можно использовать admin)
5. Нажмите "Check system capability" → убедитесь, что есть права

### Шаг 3: Создание внешней службы

1. **Site administration → Server → Web services → External services**
2. **Add** новую службу:
   - Name: `DreamDocs Portal`
   - Enabled: ☑️
   - Authorized users only: ☑️
3. Откройте службу → вкладка **Functions** → **Add functions**:
   - `core_user_create_users`
   - `core_user_get_users`
   - `core_course_get_courses`
   - `core_course_create_courses`
   - `core_course_update_courses`
   - `enrol_manual_enrol_users`

### Шаг 4: Генерация токена

1. **Site administration → Server → Web services → Manage tokens**
2. **Create token**:
   - User: `admin`
   - Service: `DreamDocs Portal`
3. Скопируйте токен (длинная строка букв и цифр)

### Шаг 5: Запись токена в проект

Откройте файл `.env` в корне проекта и вставьте токен:

```
MOODLE_TOKEN=ваш_токен_здесь
```

### Шаг 6: Перезапуск backend

```powershell
docker compose restart portal-backend
```

---

## Создание первого курса

### Автоматически (рекомендуется)

```powershell
python scripts/setup_moodle_course.py http://localhost:8080 ваш_токен
```

### Вручную в Moodle UI

1. **My courses → Create course**
2. Full name: `DreamDocs: Базовое обучение`
3. Short name: `DD_Basic`
4. Добавьте разделы:
   - Модуль 1: Введение в DreamDocs
   - Модуль 2: Работа с документами
   - Модуль 3: Интеграции
5. В каждый раздел добавьте:
   - **Page** — текст/видео материал
   - **Quiz** — тест из 3–5 вопросов
   - **URL** — ссылка на внешнюю форму (Яндекс/Google)

---

## Запуск фронтенда

```powershell
cd portal/frontend
npm run dev
```

Откройте в браузере: http://localhost:5173

---

## Проверка работы

### 1. Backend API
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/"
Invoke-RestMethod -Uri "http://localhost:8000/api/courses"
```

### 2. Приглашение студента
```powershell
$body = '{"email":"test.student@example.com","firstname":"Тест","lastname":"Студент"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/courses/2/invite" -Method POST -Body $body -ContentType "application/json"
```

*ID курса может отличаться — проверьте через `GET /api/courses`.*

### 3. Вход тестового студента в Moodle
- http://localhost:8080
- Логин: `test.student@example.com`
- Пароль: `TestPass123!`

---

## Полезные команды

```powershell
# Остановить всё
docker compose down

# Перезапустить
docker compose restart

# Логи Moodle
docker compose logs -f moodle

# Логи backend
docker compose logs -f portal-backend

# Все тесты backend
$env:PYTHONPATH="E:\DreamAcademy\dreamdox-academy;$env:PYTHONPATH"
python -m pytest tests/backend/ -v
```

---

## Если что-то пошло не так

| Проблема | Решение |
|----------|---------|
| `Port 8080 already in use` | Освободите порт или измените `docker-compose.yml` |
| Moodle долго загружается | Подождите 3–5 минут, первая инициализация длинная |
| `401 Unauthorized` в API | Проверьте правильность `MOODLE_TOKEN` в `.env` |
| Backend не видит Moodle | Убедитесь, что контейнеры в одной сети `academy_net` |
