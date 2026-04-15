# Инструкция по настройке Moodle для DreamDocs Academy

## Предварительные требования

- Docker Desktop установлен и запущен
- Проект склонирован: `cd dreamdox-academy`

## 1. Запуск окружения

```powershell
cd dreamdox-academy
copy .env.example .env
docker compose up -d
```

Ожидание: ~2-3 минуты на первый запуск (Moodle инициализирует БД).

## 2. Проверка доступности

- Moodle: http://localhost:8080
- Backend API: http://localhost:8000
- Vue Frontend: http://localhost:5173

## 3. Настройка Moodle Web Services API

1. Войти в Moodle: `admin` / `AdminPass123!`
2. **Администрирование → Сервер → Веб-службы → Обзор**
3. Включить веб-службы
4. **Добавить внешнюю службу**
   - Имя: `DreamDocs Portal`
   - Включено: Да
   - Авторизованный пользователь: выбрать `admin`
5. **Добавить функции** в службу:
   - `core_user_create_users`
   - `core_user_get_users`
   - `core_course_get_courses`
   - `core_course_create_courses`
   - `core_course_update_courses`
   - `enrol_manual_enrol_users`
6. **Создать токен** для пользователя `admin` в этой службе
7. Скопировать токен и вставить в `.env`:
   ```
   MOODLE_TOKEN=ваш_токен_здесь
   ```
8. Перезапустить backend:
   ```powershell
   docker compose restart portal-backend
   ```

## 4. Создание первого курса

### Вариант А — через скрипт (быстрее)

```powershell
python scripts/setup_moodle_course.py http://localhost:8080 ваш_токен
```

### Вариант Б — ручная настройка в Moodle UI

1. **Мои курсы → Создать курс**
2. Название: `DreamDocs: Базовое обучение`
3. Короткое название: `DD_Basic`
4. Добавить разделы:
   - Модуль 1: Введение в DreamDocs
   - Модуль 2: Работа с документами
   - Модуль 3: Интеграции
5. В каждый модуль добавить:
   - Страница с текстом / видео
   - Тест (Moodle Quiz) — 3-5 вопросов
6. Добавить внешнюю форму:
   - Элемент "URL" → `https://forms.yandex.ru/...` (итоговая проверочная работа)

## 5. Проверка приглашения через API

```powershell
$body = '{"email":"test.student@example.com","firstname":"Тест","lastname":"Студент"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/courses/2/invite" -Method POST -Body $body -ContentType "application/json"
```

*ID курса может отличаться — уточнить через `GET /api/courses`.*

## 6. E2E проверка

1. Открыть http://localhost:5173
2. Перейти в "Каталог курсов"
3. Убедиться, что курс отображается
4. Войти в Moodle как `test.student@example.com` / `TestPass123!`
5. Пройти курс и тест
