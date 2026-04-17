# Moodle MCP Server

Minimal MCP (Model Context Protocol) server that wraps Moodle Web Services + direct DB helpers for operations not covered by the standard API.

## What it does

Exposes Moodle as MCP tools so an AI assistant can:
- List / create / update / delete courses
- List categories
- Get course contents (sections + modules)
- Add modules (page, url, label, forum, quiz, assign) via DB fallback
- Enrol users
- Upload files
- Introspect available API functions

## Running locally

```bash
cd mcp-server
# Ensure ../.env has MOODLE_URL and MOODLE_MCP_TOKEN
python server.py
```

## Docker

The service is included in the root `docker-compose.yml`:
```bash
cd ..
docker compose up -d mcp-server
```

## Connecting Claude Desktop / Cline / Cursor

Add to your MCP config:

```json
{
  "mcpServers": {
    "moodle": {
      "command": "python",
      "args": [
        "E:/DreamAcademy/dreamdox-academy/mcp-server/server.py"
      ],
      "env": {
        "MOODLE_URL": "http://185.112.226.84:62080",
        "MOODLE_MCP_TOKEN": "b5a285d6bd2972ccb9643c307d59e4fd"
      }
    }
  }
}
```

## Notes

- Module creation uses `moodle_db.add_module()` because Moodle 4.4 does not expose `mod_page_add_pages`, `mod_url_add_urls`, etc. via Web Services.
- The MCP server must have MySQL access (port 3306 mapped or run inside Docker network `academy_net`).
