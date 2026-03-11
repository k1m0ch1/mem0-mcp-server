import asyncio
import os
import json
from typing import Any
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    CallToolRequest,
)

# Configuration
MEM0_API_URL = os.getenv("MEM0_API_URL", "")
MEM0_USERNAME = os.getenv("MEM0_USERNAME", "")
MEM0_PASSWORD = os.getenv("MEM0_PASSWORD", "")

# Create server
app = Server("mem0-mcp-server")


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available Mem0 tools"""
    return [
        Tool(
            name="mem0_add_memory",
            description="Store information in memory for a specific user. Use this to remember important facts, preferences, or context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Unique identifier for the user (e.g., 'user_123', 'project_abc')",
                    },
                    "content": {
                        "type": "string",
                        "description": "The information to remember (e.g., 'User prefers Python', 'Project uses FastAPI')",
                    },
                },
                "required": ["user_id", "content"],
            },
        ),
        Tool(
            name="mem0_search_memories",
            description="Search for relevant memories based on a query. Use this to recall information about a user or topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier to search memories for",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'What does the user prefer?', 'programming languages')",
                    },
                },
                "required": ["user_id", "query"],
            },
        ),
        Tool(
            name="mem0_get_all_memories",
            description="Retrieve all stored memories for a specific user. Useful for getting complete context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier to get all memories for",
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="mem0_delete_memory",
            description="Delete a specific memory by ID. Use when information is no longer relevant.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The ID of the memory to delete",
                    },
                },
                "required": ["memory_id"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[TextContent]:
    """Handle tool execution"""

    if arguments is None:
        raise ValueError("Missing arguments")

    async with httpx.AsyncClient(
        auth=(MEM0_USERNAME, MEM0_PASSWORD),
        timeout=300.0
    ) as client:
        try:
            if name == "mem0_add_memory":
                response = await client.post(
                    f"{MEM0_API_URL}/v1/memories",
                    json={
                        "messages": [{"role": "user", "content": arguments["content"]}],
                        "user_id": arguments["user_id"],
                    },
                )
                response.raise_for_status()
                result = response.json()

                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message": "Memory stored successfully",
                            "data": result,
                        }, indent=2),
                    )
                ]

            elif name == "mem0_search_memories":
                response = await client.get(
                    f"{MEM0_API_URL}/v1/memories",
                    params={
                        "query": arguments["query"],
                        "user_id": arguments["user_id"],
                    },
                )
                response.raise_for_status()
                result = response.json()

                memories = result.get("results", result.get("memories", []))
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "count": len(memories),
                            "memories": [
                                {
                                    "memory": m.get("memory"),
                                    "score": m.get("score"),
                                    "memory_id": m.get("id", m.get("memory_id")),
                                }
                                for m in memories
                            ],
                        }, indent=2),
                    )
                ]

            elif name == "mem0_get_all_memories":
                response = await client.get(
                    f"{MEM0_API_URL}/v1/memories/all",
                    params={"user_id": arguments["user_id"]},
                )
                response.raise_for_status()
                result = response.json()

                memories = result.get("results", result.get("memories", []))
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "count": len(memories),
                            "memories": memories,
                        }, indent=2),
                    )
                ]

            elif name == "mem0_delete_memory":
                response = await client.delete(
                    f"{MEM0_API_URL}/v1/memories/{arguments['memory_id']}",
                )
                response.raise_for_status()

                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message": f"Memory {arguments['memory_id']} deleted successfully",
                        }, indent=2),
                    )
                ]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except httpx.TimeoutException:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Request timed out (LLM inference may take up to 5 minutes)",
                    }, indent=2),
                )
            ]
        except httpx.HTTPError as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = json.dumps(error_detail, indent=2)
                except:
                    error_msg = e.response.text

            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": error_msg,
                    }, indent=2),
                )
            ]


async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mem0-mcp-server",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def run():
    """Run the server"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
