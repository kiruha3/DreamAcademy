#!/usr/bin/env python3
"""Quick integration test for the MCP client kit."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from server import MCPMoodleServer, moodle_db


async def run_tests():
    print("=" * 50)
    print("Testing MCP Moodle Client Kit")
    print("=" * 50)

    server = MCPMoodleServer()
    print(f"Base URL: {server.base_url}")
    print(f"Token prefix: {server.token[:8]}...")

    # Test 1: list_tools
    print("\n[Test 1] list_tools ...")
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    print(f"Found {len(tools)} tools: {tool_names}")
    assert "list_courses" in tool_names, "list_courses tool missing!"
    assert "create_course" in tool_names, "create_course tool missing!"
    print("[PASS] list_tools OK")

    # Test 2: list_courses via call_tool
    print("\n[Test 2] call_tool('list_courses') ...")
    result = await server.call_tool("list_courses", {})
    text = result[0].text
    print(f"Result length: {len(text)} chars")
    assert len(text) > 0, "Empty response from list_courses"
    print("[PASS] list_courses OK")

    # Test 3: list_categories via call_tool
    print("\n[Test 3] call_tool('list_categories') ...")
    result = await server.call_tool("list_categories", {})
    text = result[0].text
    print(f"Result length: {len(text)} chars")
    assert len(text) > 0, "Empty response from list_categories"
    print("[PASS] list_categories OK")

    # Test 4: DB connectivity
    print("\n[Test 4] DB connectivity via moodle_db ...")
    try:
        contents = moodle_db.get_course_contents(1)
        print(f"DB returned {len(contents)} sections for course 1")
        print("[PASS] DB connectivity OK")
    except Exception as e:
        print(f"[FAIL] DB connectivity failed: {e}")
        raise

    # Test 5: Full cycle — create course, create section, get contents, delete course
    print("\n[Test 5] Full cycle: create_course -> create_section -> get_course_contents -> delete_course ...")
    import json
    create_res = await server.call_tool("create_course", {
        "fullname": "MCP Kit Test Course",
        "shortname": "mcptest_" + os.urandom(2).hex(),
        "categoryid": 1,
        "summary": "Auto-created by kit test"
    })
    course_data = json.loads(create_res[0].text)
    assert isinstance(course_data, list) and len(course_data) > 0, "create_course returned unexpected format"
    cid = course_data[0]["id"]
    print(f"Created course ID: {cid}")

    section_res = await server.call_tool("create_section", {
        "course_id": cid,
        "name": "Test Section",
        "summary": "Created by kit test"
    })
    print(f"create_section result: {section_res[0].text[:200]}")

    contents_res = await server.call_tool("get_course_contents", {"course_id": cid})
    contents_data = json.loads(contents_res[0].text)
    print(f"get_course_contents returned {len(contents_data)} sections")
    assert len(contents_data) >= 2, "Expected at least 2 sections (general + created)"

    del_res = await server.call_tool("delete_course", {"course_id": cid})
    print(f"delete_course result: {del_res[0].text[:200]}")
    print("[PASS] Full cycle OK")

    print("\n" + "=" * 50)
    print("All tests passed! Kit is fully operational.")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_tests())
