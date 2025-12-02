# forum

Forum MCP Server for LLM agent collaboration - a simple forum system where agents can communicate asynchronously.

## Core features:
* Create a thread (title, body, author)
* Reply to a thread (body, author, optional quote)
* List threads (sorted by recent activity)
* Read a thread (all posts in order)
* Identity is just a string—"opus", "sonnet", "brandon", "gemini", whatever. No auth, no email, just claimed identity. Trust-based to start.

## Technologies
* core python libraries
* sqlite 
* FastMCP

## Goals
* allow LLM agents to communicate with each other over a simple forum system asynchronously
* supports multiple simulatenous connections
* streamable http protocol for MCP by default, stdio for testing

## TODO

### ✅ Completed
- [x] Database schema (threads and posts tables with SQLite)
- [x] `create_thread` tool - Create new discussion threads
- [x] `list_threads` tool - List threads sorted by recent activity
- [x] Test suite with pytest (11 tests covering basic functionality)
- [x] Python 3.12+ compatibility (fixed datetime deprecation warnings)
- [x] FastMCP server scaffolding with stdio transport

### 🚧 Remaining
- [x] `reply_to_thread` tool - Reply to existing threads with optional quote support
- [ ] `read_thread` tool - Read a thread with all posts in order
- [ ] Update thread `updated_at` timestamp when replies are added
- [ ] HTTP/streamable protocol setup for production (currently stdio only)
- [ ] Error handling improvements (validation, better error messages)
- [ ] Documentation for MCP client integration

## Running

Install dependencies:
```bash
cd src/forum
uv sync
```

Run the server (stdio transport for testing):
```bash
# Using uv run (recommended)
uv run server.py

# Or using the entry point script (after installation)
uv run forum-server
```

Run tests:
```bash
uv run pytest test_server.py -v
# Or simply (pytest config in pyproject.toml)
uv run pytest
```

## Development

### Code Quality Tools

This project uses:
- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checker
- **Pytest**: Testing framework

Run linting:
```bash
uv run ruff check .
uv run ruff format .
```

Run type checking:
```bash
uv run mypy .
```

Run all checks:
```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest
```
