# 🔍 Code Review Report — DreamDocs Academy

**Дата**: 2026-04-15  
**Аудитор**: Kimi Code CLI (code_reviewer + ручной аудит)  
**Область**: Backend (FastAPI) + Frontend (Vue 3)  
**Общая оценка**: 5.5/10 ⭐ — много критичных runtime-проблем

---

## 📊 Метрики

| Категория | Оценка | Статус |
|-----------|--------|--------|
| Безопасность | 4.5/10 | ❌ Требует внимания |
| Производительность | 6.0/10 | ⚠️ Улучшить |
| Читаемость | 7.5/10 | ✅ Хорошо |
| Архитектура | 6.0/10 | ⚠️ Улучшить |
| Тестирование | 3.0/10 | ❌ Требует внимания |

---

## 🚨 Критично (Нужно исправить)

### 1. Backend не запускается на Python 3.9 — синтаксис `int | None`
**Файл**: `portal/backend/app/auth_router.py:45`
```python
# Плохо (Python 3.10+):
moodle_user_id: int | None = None

# Хорошо:
from typing import Optional
moodle_user_id: Optional[int] = None
```
**Почему критично**: В `requirements.txt` и Dockerfile указан Python 3.11, но локально (и в CI) может быть 3.9. При импорте приложения падает `TypeError` — **тесты вообще не собираются**.

---

### 2. Backend не запускается на Python 3.9 — синтаксис `list[str]`
**Файл**: `portal/backend/app/security.py:64`
```python
# Плохо:
def require_roles(allowed_roles: list[str]):

# Хорошо:
from typing import List
def require_roles(allowed_roles: List[str]):
```
**Почему критично**: Та же причина — `TypeError` при импорте на Python < 3.10.

---

### 3. UnboundLocalError при приглашении существующего пользователя
**Файл**: `portal/backend/app/invite.py:30-61`
```python
if user_list:
    user_id = user_list[0]["id"]
else:
    temp_password = secrets.token_urlsafe(10) + "A1!"
    ...

return {
    ...
    "temp_password": temp_password,  # <-- ОШИБКА: если user_list не пустой, temp_password не определена
}
```
**Почему критично**: Приглашение пользователя, который уже есть в Moodle, приведет к `500 UnboundLocalError`.

**Исправление**:
```python
temp_password = None
if not user_list:
    temp_password = secrets.token_urlsafe(10) + "A1!"
    ...
```

---

### 4. Тихое обрезание пароля до 72 байт
**Файл**: `portal/backend/app/security.py:28`
```python
pwd_bytes = password.encode("utf-8")[:72]
```
**Почему критично**: Пользователь может ввести пароль длиной 100 символов, а фактически будет использоваться только первые 72 байта. Это снижает энтропию пароля без предупреждения.

**Исправление**: добавить валидацию длины пароля (например, max 72 байт) и отклонять слишком длинные.

---

### 5. Потенциальная SQL-инъекция через f-string с именем таблицы
**Файлы**: `portal/backend/app/moodle_db.py:50, 282`
```python
cur.execute(f"SELECT * FROM {PREFIX}{modname} WHERE id = %s LIMIT 1", (instance_id,))
cur.execute(f"DELETE FROM {PREFIX}{modname} WHERE id = %s", (instance_id,))
```
**Почему критично**: `modname` берется из БД Moodle, но если злоумышленник сможет записать произвольное значение в `mdl_modules.name`, получит SQL-инъекцию. Параметризация имен таблиц невозможна, но нужен whitelist.

**Исправление**:
```python
ALLOWED_MODULES = {"page", "url", "label", "forum", "quiz", "assign"}
if modname not in ALLOWED_MODULES:
    raise ValueError(f"Invalid module name: {modname}")
```

---

## ⚠️ Важно (Рекомендуется исправить)

### 6. Deprecated `declarative_base()` в SQLAlchemy 2.0
**Файл**: `portal/backend/app/database.py:2,13`
```python
from sqlalchemy.ext.declarative import declarative_base  # deprecated
Base = declarative_base()
```
**Исправление**:
```python
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

---

### 7. Deprecated `class Config` в Pydantic v2
**Файлы**: `portal/backend/app/auth_router.py:47`, `portal/backend/app/config.py:11`
```python
class Config:
    from_attributes = True
```
**Исправление**:
```python
from pydantic import ConfigDict
model_config = ConfigDict(from_attributes=True)
```

---

### 8. Хардкод имени Docker-контейнера Moodle
**Файл**: `portal/backend/app/course_builder.py:15`
```python
"docker", "exec", "dd_academy_moodle", "php", "-r",
```
**Проблема**: В `docker-compose.yml` сервис называется `moodle`, имя контейнера будет `dreamdox-academy-moodle-1` (Compose v2) или `moodle`. Сброс кэша курсов не будет работать.

**Исправление**: вынести имя контейнера в переменную окружения `MOODLE_CONTAINER_NAME` с дефолтом `moodle`.

---

### 9. Создание нового httpx.AsyncClient в каждом методе
**Файл**: `portal/backend/app/moodle_client.py`
Каждый метод делает `async with httpx.AsyncClient(...) as client:`. Это дорого и может привести к исчерпанию портов/файловых дескрипторов под нагрузкой.

**Исправление**: использовать один клиент на экземпляр `MoodleClient`:
```python
class MoodleClient:
    def __init__(...):
        self.client = httpx.AsyncClient(follow_redirects=True)
    async def close(self):
        await self.client.aclose()
```

---

### 10. `add_forum_discussion` не использует `user_id`
**Файл**: `portal/backend/app/moodle_client.py:265-276`
Параметр `user_id` принимается, но не передается в Moodle API. В `modules_router.py:431` вызывается с `current_user.moodle_user_id`, но значение игнорируется.

**Исправление**: убрать неиспользуемый параметр или передать его в запрос (Moodle WS `mod_forum_add_discussion` не требует `userid` при валидном токене, но сигнатура вводит в заблуждение).

---

### 11. Naive datetime в timezone-aware колонках
**Файл**: `portal/backend/app/modules_router.py:198,256`
```python
existing.submitted_at = datetime.utcnow()
sub.graded_at = datetime.utcnow()
```
Колонки в модели определены как `DateTime(timezone=True)`. `datetime.utcnow()` возвращает naive datetime — на некоторых БД/драйверах это может вызывать warning или некорректное поведение.

**Исправление**:
```python
from datetime import datetime, timezone
existing.submitted_at = datetime.now(timezone.utc)
```

---

### 12. Отсутствие guard'ов на фронтенде
**Файл**: `portal/frontend/src/router/index.js`
Роут `/admin` доступен любому пользователю (включая неавторизованных). Проверка прав делается только на бэкенде, но UX страдает: пользователь видит админ-панель, а API возвращает 403.

**Исправление**: добавить `beforeEach` guard с проверкой `authStore.isAuthenticated` и роли.

---

### 13. Ненадежная генерация username при регистрации
**Файл**: `portal/frontend/src/views/RegisterView.vue:49`
```javascript
username: email.value.split('@')[0] + '_' + Math.floor(Math.random() * 1000),
```
**Проблемы**:
- Коллизии username (1/1000 шанс) — приведет к 500 на бэкенде.
- Email вроде `user+test@domain.com` даст `user+test_123` — Moodle может отклонить `+`.
- Нет валидации длины/сложности пароля на фронтенде.

**Исправление**: генерировать username на бэкенде или использовать `secrets.token_hex(4)`.

---

### 14. DELETE-запросы фронтенда падают при пустом теле ответа
**Файл**: `portal/frontend/src/api/client.js:65-71, 94-100, 107-114`
```javascript
return fetch(...).then(r => { if (!r.ok) throw ...; return r.json() })
```
Если бэкенд вернет `204 No Content` (что логично для DELETE), `r.json()` выбросит `SyntaxError`.

**Исправление**: проверять `r.status !== 204` перед `.json()`.

---

### 15. Отсутствие валидации роли в `/auth/register`
**Файл**: `portal/backend/app/auth_router.py:19-25`
```python
class RegisterRequest(BaseModel):
    ...
    role: str = "student"
```
Можно передать `role: "hacker"` — бэкенд запишет это в БД. Система разрешений (`auth.py`) не используется при регистрации.

**Исправление**: ограничить `role` через `Literal["student", "teacher", ...]` или валидатор Pydantic.

---

## 💡 Желательно (Можно улучшить)

### 16. Тесты не покрывают критичные баги
- `test_invite.py` не тестирует случай с существующим пользователем (где баг #3).
- Нет тестов на `change-password`, `course_builder`, `modules_router`.
- Frontend тесты отсутствуют (Vitest настроен, но тестовых файлов нет).

### 17. `has_permission` в `auth.py` практически не используется
Весь доступ контролируется через `require_roles([...])` в `security.py`. Система permissions (`auth.py`) была введена, но не интегрирована в роутеры.

### 18. CORS origins захардкожены в `main.py`
Лучше вынести в настройки (`config.py`) для гибкости dev/staging/prod.

### 19. `get_moodle_client()` дублируется в 8+ файлах
Нарушение DRY. Лучше сделать один dependency в `security.py` или отдельном модуле.

---

## ✅ Что сделано хорошо

- Четкое разделение на роутеры по доменам (auth, courses, admin, etc.)
- Использование Pydantic v2 и SQLAlchemy 2.0 (современный стек)
- Асинхронный клиент Moodle на `httpx`
- Конструктор курсов с прямым доступом к MySQL Moodle — функционально работает
- Pinia + Vue Router 4 на фронтенде — правильный стек

---

## 📝 Итог

**Рекомендация**: 🔴 **Не деплоить в продакшн до исправления критичных багов.**

**Приоритет исправлений**:
1. Исправить `int | None` → `Optional[int]` (баг #1)
2. Исправить `list[str]` → `List[str]` (баг #2)
3. Исправить `UnboundLocalError` в `invite.py` (баг #3)
4. Добавить whitelist для имен таблиц в `moodle_db.py` (баг #5)
5. Добавить валидацию пароля вместо тихого обрезания (баг #4)
6. После этого запустить тесты и дописать недостающие кейсы
