#!/usr/bin/env python3
import sys
import os
import json
import base64

# Allow importing moodle_client and moodle_db from local directory or portal backend
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..', 'portal', 'backend', 'app'))

from dotenv import load_dotenv
# Load .env from the same directory as this script (for standalone kit)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
# Also try loading from parent directory (when running inside full repo)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Default DB host for local dev; overridden by env in Docker
os.environ.setdefault('MOODLE_DATABASE_HOST', 'localhost')
os.environ.setdefault('MOODLE_DATABASE_USER', 'moodle')
os.environ.setdefault('MOODLE_DATABASE_PASSWORD', 'moodlesecret')
os.environ.setdefault('MOODLE_DATABASE_NAME', 'moodle')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

try:
    from app.moodle_client import MoodleClient
    import app.moodle_db as moodle_db
except ImportError:
    from moodle_client import MoodleClient
    import moodle_db


class MCPMoodleServer:
    def __init__(self):
        self.base_url = os.getenv('MOODLE_URL', 'http://localhost:62080')
        self.token = os.getenv('MOODLE_MCP_TOKEN', '')
        self.client = MoodleClient(base_url=self.base_url, token=self.token)

    async def list_tools(self) -> list[Tool]:
        return [
            Tool(name="list_courses", description="List all Moodle courses", inputSchema={"type": "object", "properties": {}}),
            Tool(name="list_categories", description="List Moodle course categories", inputSchema={"type": "object", "properties": {}}),
            Tool(name="create_course", description="Create a new Moodle course", inputSchema={
                "type": "object",
                "properties": {
                    "fullname": {"type": "string", "description": "Course full name"},
                    "shortname": {"type": "string", "description": "Course short name"},
                    "categoryid": {"type": "integer", "description": "Category ID", "default": 1},
                    "summary": {"type": "string", "description": "Course description", "default": ""},
                },
                "required": ["fullname", "shortname"],
            }),
            Tool(name="update_course", description="Update an existing Moodle course", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "fields": {"type": "object", "description": "Fields to update (e.g. fullname, summary, visible)"},
                },
                "required": ["course_id", "fields"],
            }),
            Tool(name="delete_course", description="Delete a Moodle course", inputSchema={
                "type": "object",
                "properties": {"course_id": {"type": "integer"}},
                "required": ["course_id"],
            }),
            Tool(name="create_category", description="Create a course category", inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "parent": {"type": "integer", "default": 0},
                },
                "required": ["name"],
            }),
            Tool(name="create_section", description="Create a new section (topic) in a course", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "summary": {"type": "string", "default": ""},
                },
                "required": ["course_id", "name"],
            }),
            Tool(name="get_course_contents", description="Get sections and modules of a course", inputSchema={
                "type": "object",
                "properties": {"course_id": {"type": "integer"}},
                "required": ["course_id"],
            }),
            Tool(name="add_book_module", description="Add a Book module to a course section (via DB fallback)", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "section_num": {"type": "integer", "description": "Section number (0 = general, 1 = first topic)"},
                    "name": {"type": "string"},
                    "intro": {"type": "string", "default": ""},
                },
                "required": ["course_id", "section_num", "name"],
            }),
            Tool(name="add_book_chapter", description="Add a chapter to an existing Book module (via DB fallback)", inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {"type": "integer", "description": "Book instance ID (not cmid)"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "subchapter": {"type": "integer", "default": 0},
                },
                "required": ["book_id", "title", "content"],
            }),
            Tool(name="add_page_module", description="Add a Page module to a course section (via DB fallback)", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "section_num": {"type": "integer", "description": "Section number (0 = general, 1 = first topic)"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                    "intro": {"type": "string", "default": ""},
                },
                "required": ["course_id", "section_num", "name", "content"],
            }),
            Tool(name="add_url_module", description="Add a URL module to a course section (via DB fallback)", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "section_num": {"type": "integer"},
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "intro": {"type": "string", "default": ""},
                },
                "required": ["course_id", "section_num", "name", "url"],
            }),
            Tool(name="add_label_module", description="Add a Label module to a course section (via DB fallback)", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "section_num": {"type": "integer"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["course_id", "section_num", "name", "content"],
            }),
            Tool(name="add_forum_module", description="Add a Forum module to a course section (via DB fallback)", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "section_num": {"type": "integer"},
                    "name": {"type": "string"},
                    "intro": {"type": "string", "default": ""},
                    "forum_type": {"type": "string", "default": "general"},
                },
                "required": ["course_id", "section_num", "name"],
            }),
            Tool(name="add_quiz_module", description="Add a Quiz module to a course section (via DB fallback)", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "section_num": {"type": "integer"},
                    "name": {"type": "string"},
                    "intro": {"type": "string", "default": ""},
                },
                "required": ["course_id", "section_num", "name"],
            }),
            Tool(name="add_quiz_question", description="Add a multichoice question to a quiz (via PHP helper)", inputSchema={
                "type": "object",
                "properties": {
                    "quiz_id": {"type": "integer"},
                    "qtype": {"type": "string", "enum": ["multichoice", "truefalse"], "default": "multichoice"},
                    "name": {"type": "string"},
                    "questiontext": {"type": "string"},
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "fraction": {"type": "number"},
                            },
                            "required": ["text", "fraction"],
                        },
                    },
                },
                "required": ["quiz_id", "name", "questiontext", "answers"],
            }),
            Tool(name="add_assignment_module", description="Add an Assignment module to a course section (via DB fallback)", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "section_num": {"type": "integer"},
                    "name": {"type": "string"},
                    "intro": {"type": "string", "default": ""},
                    "duedate": {"type": "integer", "description": "Due date as Unix timestamp", "default": 0},
                    "grade": {"type": "integer", "default": 100},
                },
                "required": ["course_id", "section_num", "name"],
            }),
            Tool(name="enrol_user", description="Enrol a user into a course", inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                    "role_id": {"type": "integer", "default": 5},
                },
                "required": ["course_id", "user_id"],
            }),
            Tool(name="upload_file", description="Upload a file to Moodle (returns draft file info)", inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "file_bytes_b64": {"type": "string", "description": "Base64-encoded file bytes"},
                    "filearea": {"type": "string", "default": "draft"},
                    "itemid": {"type": "integer", "default": 0},
                },
                "required": ["filename", "file_bytes_b64"],
            }),
            Tool(name="list_available_api_functions", description="List Moodle API functions available to this token", inputSchema={"type": "object", "properties": {}}),
        ]

    async def call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "list_courses":
                result = await self.client.get_courses()
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            if name == "list_categories":
                result = await self.client.list_categories()
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            if name == "create_course":
                try:
                    result = await self.client.create_course(
                        arguments["fullname"],
                        arguments["shortname"],
                        arguments.get("categoryid", 1),
                        arguments.get("summary", ""),
                    )
                    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                except Exception:
                    # Fallback to direct DB insert if WS fails
                    course_id = moodle_db.create_course(
                        arguments["fullname"],
                        arguments["shortname"],
                        arguments.get("categoryid", 1),
                        arguments.get("summary", ""),
                    )
                    return [TextContent(type="text", text=json.dumps({"id": course_id, "shortname": arguments["shortname"], "source": "db_fallback"}, ensure_ascii=False))]

            if name == "update_course":
                result = await self.client.update_course(arguments["course_id"], arguments["fields"])
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            if name == "delete_course":
                result = await self.client.delete_course(arguments["course_id"])
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            if name == "create_category":
                try:
                    result = await self.client.create_category(arguments["name"], arguments.get("parent", 0))
                    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                except Exception:
                    cat_id = moodle_db.create_category(arguments["name"], arguments.get("parent", 0))
                    return [TextContent(type="text", text=json.dumps({"id": cat_id, "name": arguments["name"], "source": "db_fallback"}, ensure_ascii=False))]

            if name == "create_section":
                section_id = moodle_db.add_section(
                    arguments["course_id"],
                    arguments["name"],
                    arguments.get("summary", ""),
                )
                return [TextContent(type="text", text=json.dumps({"section_id": section_id}, ensure_ascii=False))]

            if name == "get_course_contents":
                result = await self.client.get_course_contents(arguments["course_id"])
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            if name == "add_book_module":
                cmid, book_id = moodle_db.add_book(
                    arguments["course_id"],
                    arguments["section_num"],
                    arguments["name"],
                    arguments.get("intro", ""),
                )
                return [TextContent(type="text", text=json.dumps({"cmid": cmid, "book_id": book_id}))]

            if name == "add_book_chapter":
                chapter_id = moodle_db.add_book_chapter(
                    arguments["book_id"],
                    arguments["title"],
                    arguments["content"],
                    subchapter=arguments.get("subchapter", 0),
                )
                return [TextContent(type="text", text=f"Created book chapter with id={chapter_id}")]

            if name == "add_page_module":
                cmid = moodle_db.add_module(
                    arguments["course_id"],
                    arguments["section_num"],
                    "page",
                    arguments["name"],
                    arguments["content"],
                    {"intro": arguments.get("intro", "")},
                )
                return [TextContent(type="text", text=f"Created page module with cmid={cmid}")]

            if name == "add_url_module":
                cmid = moodle_db.add_module(
                    arguments["course_id"],
                    arguments["section_num"],
                    "url",
                    arguments["name"],
                    "",
                    {"url": arguments["url"], "intro": arguments.get("intro", "")},
                )
                return [TextContent(type="text", text=f"Created url module with cmid={cmid}")]

            if name == "add_label_module":
                cmid = moodle_db.add_module(
                    arguments["course_id"],
                    arguments["section_num"],
                    "label",
                    arguments["name"],
                    arguments["content"],
                )
                return [TextContent(type="text", text=f"Created label module with cmid={cmid}")]

            if name == "add_forum_module":
                cmid = moodle_db.add_module(
                    arguments["course_id"],
                    arguments["section_num"],
                    "forum",
                    arguments["name"],
                    "",
                    {"type": arguments.get("forum_type", "general"), "intro": arguments.get("intro", "")},
                )
                return [TextContent(type="text", text=f"Created forum module with cmid={cmid}")]

            if name == "add_quiz_module":
                cmid = moodle_db.add_module(
                    arguments["course_id"],
                    arguments["section_num"],
                    "quiz",
                    arguments["name"],
                    "",
                    {"intro": arguments.get("intro", "")},
                )
                return [TextContent(type="text", text=f"Created quiz module with cmid={cmid}")]

            if name == "add_quiz_question":
                result = moodle_db.add_quiz_question(
                    arguments["quiz_id"],
                    arguments["qtype"],
                    arguments["name"],
                    arguments["questiontext"],
                    arguments["answers"],
                )
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            if name == "add_assignment_module":
                cmid = moodle_db.add_module(
                    arguments["course_id"],
                    arguments["section_num"],
                    "assign",
                    arguments["name"],
                    "",
                    {
                        "intro": arguments.get("intro", ""),
                        "duedate": arguments.get("duedate", 0),
                        "grade": arguments.get("grade", 100),
                    },
                )
                return [TextContent(type="text", text=f"Created assignment module with cmid={cmid}")]

            if name == "enrol_user":
                result = await self.client.enrol_user(
                    arguments["course_id"],
                    arguments["user_id"],
                    arguments.get("role_id", 5),
                )
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            if name == "upload_file":
                file_bytes = base64.b64decode(arguments["file_bytes_b64"])
                result = await self.client.upload_file(
                    file_bytes,
                    arguments["filename"],
                    arguments.get("filearea", "draft"),
                    arguments.get("itemid", 0),
                )
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            if name == "list_available_api_functions":
                result = await self.client.list_external_functions()
                funcs = result.get("functions", [])
                return [TextContent(type="text", text=json.dumps([f["name"] for f in funcs], indent=2))]

            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]


async def main():
    mcp = Server("moodle-mcp")
    moodle = MCPMoodleServer()

    @mcp.list_tools()
    async def list_tools() -> list[Tool]:
        return await moodle.list_tools()

    @mcp.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        return await moodle.call_tool(name, arguments)

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
