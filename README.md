# Mem0 MCP Server

MCP server for Mem0 memory storage and retrieval.

## Installation

```bash
# Install with uvx
uvx --from . mem0-mcp-server

# Or install locally
pip install -e .
```

## Configuration

Add to your Claude Code `settings.json`:

```json
{
  "mcpServers": {
    "mem0": {
      "command": "uvx",
      "args": ["--from", "./mem0-mcp-server", "mem0-mcp-server"],
      "env": {
        "MEM0_API_URL": "http://x.x.x.x:port",
        "MEM0_USERNAME": "user",
        "MEM0_PASSWORD": "password"
      }
    }
  }
}
```

## Tools

- `mem0_add_memory` - Store information
- `mem0_search_memories` - Search for relevant memories
- `mem0_get_all_memories` - Get all memories for a user
- `mem0_delete_memory` - Delete a memory by ID
