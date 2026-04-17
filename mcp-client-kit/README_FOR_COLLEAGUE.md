# MCP-клиент для DreamDocs Academy

Это «тонкий клиент» MCP-сервера. Он запускается локально у тебя, но все команды (создание курсов, разделов, модулей, тестов) выполняются в удалённом Moodle.

## Что внутри

| Файл | Описание |
|------|----------|
| `server.py` | Сам MCP-сервер (stdio-транспорт) |
| `moodle_client.py` | HTTP-клиент для Moodle API |
| `moodle_db.py` | Прямой доступ к MySQL Moodle |
| `requirements.txt` | Python-зависимости |
| `.env.example` | Шаблон переменных окружения |
| `test_kit.py` | Скрипт для самопроверки |
| `create_smoking_course.py` | Демо-скрипт: создаёт полноценный курс |

## Быстрый старт

### 1. Установи Python 3.11+

### 2. Создай виртуальное окружение
```bash
python -m venv .venv
```

**Windows:**
```powershell
.\.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 3. Установи зависимости
```bash
pip install -r requirements.txt
```

### 4. Создай `.env`

Скопируй `.env.example` в `.env` и вставь реальные значения:

```env
MOODLE_URL=http://185.112.226.84:62080
MOODLE_MCP_TOKEN=b5a285d6bd2972ccb9643c307d59e4fd

# Данные для прямого подключения к MySQL (нужны некоторым инструментам MCP)
MOODLE_DATABASE_HOST=185.112.226.84
MOODLE_DATABASE_USER=moodle
MOODLE_DATABASE_PASSWORD=moodlesecret
MOODLE_DATABASE_NAME=moodle
```

> **Важно:** `.env` должен лежать в той же папке, что и `server.py`.

### 5. Проверь работоспособность
```bash
python test_kit.py
```

Ожидаемый результат:
```
==================================================
Testing MCP Moodle Client Kit
==================================================
...
All tests passed! Kit is fully operational.
==================================================
```

### 6. (Опционально) Запусти демо-курс
```bash
python create_smoking_course.py
```

Это создаст полноценный курс «Вред курения» с 6 разделами, книгой и тестом из 5 вопросов. По окончании скрипт выведет ссылку на курс.

## Подключение к Claude Desktop

Открой `claude_desktop_config.json`:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Добавь секцию (укажи **абсолютный** путь к `server.py`):

```json
{
  "mcpServers": {
    "dreamdocs-academy": {
      "command": "python",
      "args": [
        "C:\\Path\\To\\mcp-client-kit\\server.py"
      ],
      "env": {
        "MOODLE_URL": "http://185.112.226.84:62080",
        "MOODLE_MCP_TOKEN": "b5a285d6bd2972ccb9643c307d59e4fd",
        "MOODLE_DATABASE_HOST": "185.112.226.84",
        "MOODLE_DATABASE_USER": "moodle",
        "MOODLE_DATABASE_PASSWORD": "moodlesecret",
        "MOODLE_DATABASE_NAME": "moodle"
      }
    }
  }
}
```

> **Важно:** `python` в `command` должен вести на тот интерпретатор, в который установлены зависимости. Лучше указать полный путь к `python.exe` внутри `.venv`.

Перезапусти Claude Desktop. В чате должен появиться значок 🔌 с доступными инструментами (`list_courses`, `create_course`, `add_book_module`, `add_quiz_module` и др.).

## Подключение к Kimi CLI

Добавь в конфиг:

```json
{
  "mcpServers": {
    "dreamdocs-academy": {
      "command": "python",
      "args": ["C:\\Path\\To\\mcp-client-kit\\server.py"],
      "env": {
        "MOODLE_URL": "http://185.112.226.84:62080",
        "MOODLE_MCP_TOKEN": "b5a285d6bd2972ccb9643c307d59e4fd",
        "MOODLE_DATABASE_HOST": "185.112.226.84",
        "MOODLE_DATABASE_USER": "moodle",
        "MOODLE_DATABASE_PASSWORD": "moodlesecret",
        "MOODLE_DATABASE_NAME": "moodle"
      }
    }
  }
}
```

## Типичные проблемы

### `ModuleNotFoundError: No module named 'mcp'`
Решение: забыл активировать виртуальное окружение или не установил `requirements.txt`.

### `Connection refused` / `timed out` к базе данных
Убедись, что у тебя есть доступ к порту `3306` на сервере `185.112.226.84`. Если порт закрыт, инструменты, использующие прямой доступ к БД (например, `create_section`, `add_quiz_module`), могут падать с ошибкой соединения. Инструменты чисто через Moodle HTTP API (`list_courses`, `create_course`, `delete_course` и др.) будут работать нормально.

### Инструменты не появляются в Claude Desktop
- Проверь, что путь к `server.py` абсолютный.
- Открой **Developer Tools** в Claude Desktop (`View → Toggle Developer Tools`) и посмотри ошибки в Console.
- Убедись, что `python` в `command` — это тот же интерпретатор, в который установлены зависимости.

### Тест не запускается (500 ошибка в портале)
Если курс создан, но тест в портале падает с 500, скорее всего:
1. Пользователь не зачислен в курс (в демо-скрипте `create_smoking_course.py` есть автоматическое зачисление всех пользователей).
2. В квизе нет вопросов или нарушена связь вопросов с квизом в БД.

## Безопасность

- `.env` содержит чувствительные данные. **Не коммить его в git и не пересылай в открытых каналах.**
- Если токен или пароль БД скомпрометирован — попроси владельца сервера перевыпустить их.
