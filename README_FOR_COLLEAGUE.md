# MCP-клиент для DreamDocs Academy

Это «тонкий клиент» MCP-сервера. Он запускается локально у тебя, но все команды (создание курсов, разделов, модулей) выполняются в удалённом Moodle.

## Что внутри

| Файл | Описание |
|------|----------|
| `server.py` | Сам MCP-сервер (stdio-транспорт) |
| `moodle_client.py` | HTTP-клиент для Moodle API |
| `moodle_db.py` | Прямой доступ к БД Moodle |
| `requirements.txt` | Python-зависимости |
| `.env.example` | Шаблон переменных окружения |

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
Скопируй `.env.example` в `.env` и вставь реальные значения (их тебе передаст владелец сервера):

```env
MOODLE_URL=http://185.112.226.84:62080
MOODLE_MCP_TOKEN=твой_токен_здесь
MOODLE_DATABASE_HOST=185.112.226.84
MOODLE_DATABASE_USER=moodle
MOODLE_DATABASE_PASSWORD=moodlesecret
MOODLE_DATABASE_NAME=moodle
```

### 5. Проверь запуск
```bash
python server.py
```

Если всё ок, процесс просто повиснет без ошибок (stdio-сервер ждёт команд от MCP-клиента). Нажми `Ctrl+C` чтобы остановить.

## Подключение к Claude Desktop

Открой `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\claude_desktop_config.json`, macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`).

Добавь секцию:

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
        "MOODLE_MCP_TOKEN": "твой_токен_здесь",
        "MOODLE_DATABASE_HOST": "185.112.226.84",
        "MOODLE_DATABASE_USER": "moodle",
        "MOODLE_DATABASE_PASSWORD": "moodlesecret",
        "MOODLE_DATABASE_NAME": "moodle"
      }
    }
  }
}
```

> **Важно:** укажи полный абсолютный путь к `server.py` в `args`.

Перезапусти Claude Desktop. В чате должен появиться значок 🔌 с доступными инструментами (`list_courses`, `create_course`, `add_book_module` и др.).

## Подключение к Kimi CLI

Добавь в `~/.kimi/config.json` (или через `kimi config`):

```json
{
  "mcpServers": {
    "dreamdocs-academy": {
      "command": "python",
      "args": ["C:\\Path\\To\\mcp-client-kit\\server.py"],
      "env": {
        "MOODLE_URL": "http://185.112.226.84:62080",
        "MOODLE_MCP_TOKEN": "твой_токен_здесь",
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
Убедись, что у тебя есть доступ к порту `3306` на сервере `185.112.226.84` (владелец должен открыть его в фаерволе для твоего IP). Если порт закрыт, инструменты, использующие прямой доступ к БД (например, `get_course_contents`, `create_section`, добавление некоторых модулей), могут падать с ошибкой соединения. Инструменты, работающие чисто через Moodle HTTP API (`list_courses`, `create_course`, `delete_course` и др.), будут функционировать нормально.

### Инструменты не появляются в Claude Desktop
- Проверь, что путь к `server.py` абсолютный.
- Открой **Developer Tools** в Claude Desktop (`View → Toggle Developer Tools`) и посмотри ошибки в Console.
- Убедись, что `python` в `command` ведёт на тот же интерпретатор, в который установлены зависимости (можно указать полный путь к `python.exe` внутри `.venv`).

## Безопасность

- `.env` содержит чувствительные данные. **Не коммить его в git и не пересылай в открытых каналах.**
- Если токен или пароль БД скомпрометирован — попроси владельца сервера перевыпустить их.
