# Code Review Report — DreamDocs Academy MVP

**Дата:** 15.04.2026  
**Ревьюер:** AI Assistant (скилл `code_reviewer`)  
**Объём:** backend core (FastAPI + Moodle integration), Vue frontend skeleton

---

## 📊 Метрики

| Категория | Оценка | Статус |
|-----------|--------|--------|
| Безопасность | 7.0/10 | ⚠️ Улучшить |
| Производительность | 8.5/10 | ✅ Хорошо |
| Читаемость | 8.5/10 | ✅ Хорошо |
| Архитектура | 8.0/10 | ✅ Хорошо |
| Тестирование | 9.0/10 | ✅ Отлично |

---

## 🚨 Критично (Нужно исправить перед продакшеном)

### 1. Нет авторизации в `invite.py`
**Файл:** `portal/backend/app/invite.py`  
**Проблема:** Любой анонимный запрос может пригласить пользователя на любой курс.  
**Решение:** Добавить JWT/OAuth2 зависимость и проверку `has_permission(current_user.role, Permission.COURSE_ENROLL_MANAGE)`.

### 2. `username` может конфликтовать
**Файл:** `portal/backend/app/invite.py:34`  
**Проблема:** `invite.email.split("@")[0]` — два разных email `ivan@gmail.com` и `ivan@yandex.ru` дадут один username. Moodle не позволит создать дубликат.  
**Решение:** Добавить рандомный суффикс или использовать полный email как username.

### 3. URL-параметры не экранируются
**Файл:** `portal/backend/app/moodle_client.py:12`  
**Проблема:** `f"{k}={v}"` без `urllib.parse.quote`. Спецсимволы в email или пароле сломают URL.  
**Решение:** Использовать `urllib.parse.urlencode(params)`.

### 4. Moodle возвращает ошибки в HTTP 200
**Файл:** `portal/backend/app/moodle_client.py`  
**Проблема:** `response.raise_for_status()` не ловит бизнес-ошибки Moodle (например, дублирующий username), которые приходят в JSON с полем `exception`.  
**Решение:** Проверять ответ на наличие `exception` / `errorcode`.

### 5. Пароль никуда не отправляется
**Файл:** `portal/backend/app/invite.py:32`  
**Проблема:** `temp_password` генерируется, но пользователь никогда его не получает — не сможет войти.  
**Решение:** Отправлять welcome-email с временным паролем или генерировать ссылку на сброс пароля.

---

## ⚠️ Важно (Рекомендуется исправить)

### 6. Нет rate limiting на invite
**Решение:** Добавить `slowapi` или обёртку с лимитом запросов.

### 7. `role` query parameter не валидируется
**Файл:** `portal/backend/app/invite.py:23`  
**Проблема:** Можно передать `role=hackerman` — упадёт с `KeyError` в `moodle_roles.py`.  
**Решение:** Использовать `Literal["student", "teacher", "course_creator", "admin"]` или Enum.

### 8. Vue `stripHtml` использует DOM в runtime
**Файл:** `portal/frontend/src/components/CourseCard.vue`  
**Проблема:** `document.createElement('div')` — не работает при SSR, потенциально уязвимо к XSS если данные приходят ненадёжные.  
**Решение:** Использовать `DOMPurify` или заменить на простой regex.

---

## 💡 Желательно (Можно улучшить)

### 9. Добавить docstrings
Функции в `moodle_client.py` публичные — стоит добавить Google-style docstrings.

### 10. Добавить type hints в Vue
В Composition API можно использовать JSDoc `@type` для лучшей поддержки IDE.

### 11. Логирование Moodle API calls
Для отладки полезно логировать URL (без токена) и статус ответа.

---

## ✅ Что сделано хорошо

- Чистое разделение ответственности: `moodle_client`, `auth`, `courses`, `invite`
- Полное покрытие backend тестами (7/7 ✅)
- CORS настроен строго (`localhost:5173`)
- RBAC реализован через Enum + матрицу прав
- `.gitignore` и `REPO_RULES.md` защищают от случайной утечки секретов

---

## 📝 Итог

**Рекомендация:** 🟡 Исправить критичные проблемы безопасности перед merge в основную ветку.

**Следующие шаги:**
1. Добавить `urllib.parse.urlencode` в `moodle_client.py`
2. Добавить валидацию роли в `invite.py`
3. Продумать доставку временного пароля (email/ссылка)
4. Добавить middleware авторизации
