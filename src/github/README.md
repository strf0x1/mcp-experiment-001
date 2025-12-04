# GitHub MCP Server

MCP Server for GitHub - provides natural language access to GitHub project data through the Model Context Protocol. Supports multiple deployment modes:
- **STDIO**: Claude Desktop and other local integrations
- **Streamable HTTP**: Web APIs, remote clients, and production deployments

## 🚀 Quick Start

### Using UV (Recommended)

```bash
# Local mode (Claude Desktop)
uv run github-mcp

# HTTP mode (Web API)
uv run github-mcp --transport http --port 8000

# Production mode (bind to all interfaces)
uv run github-mcp --transport http --host 0.0.0.0 --port 8000
```

### Using Docker

```bash
# Production deployment
docker compose up -d

# Development with live reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Quick rebuild and restart
./build-container-run.sh
```

## Prerequisites

- Python 3.10+
- [UV](https://docs.astral.sh/uv/) for dependency management
- GitHub Personal Access Token (PAT) with appropriate scopes

## Installation

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies** (from workspace root):
   ```bash
   uv sync --dev
   ```
   
   **Note:** The `--dev` flag installs development dependencies including `ruff` for code linting.

## 📋 Configuration

### Local Development (Claude Desktop Integration)

1. Generate your GitHub Personal Access Token:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Or visit: https://github.com/settings/tokens
   - Create a new token with these scopes:
     - `repo` - Full control of private repositories
     - `read:project` - Read access to projects

2. Edit Claude Desktop config:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

3. Add this server configuration:
   ```json
   {
     "mcpServers": {
       "github": {
         "command": "/Users/YOUR_USERNAME/.local/bin/uv",
         "args": [
           "run",
           "--directory",
           "/path/to/mcp/src/github",
           "github-mcp"
         ],
         "env": {
           "GITHUB_TOKEN": "your_github_pat_here",
           "GITHUB_OWNER": "your-org-or-username",
           "GITHUB_REPO": "your-repo-name"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop** to load the server

### Docker Deployment

1. Create a `.env` file in the `src/github` directory:
   ```bash
   # GitHub Personal Access Token (required)
   GITHUB_TOKEN=your_github_token_here
   
   # GitHub repository owner (optional, defaults to altstaq-research)
   GITHUB_OWNER=your-org-or-username
   
   # Log level (optional, defaults to INFO)
   LOG_LEVEL=INFO
   ```

2. Start the container:
   ```bash
   docker compose up -d
   ```

3. The server will be available at `http://localhost:8003`

### Environment Variables

- `GITHUB_TOKEN` (required): Your GitHub Personal Access Token
- `GITHUB_OWNER` (optional): Repository owner/organization (default: `altstaq-research`)
- `LOG_LEVEL` (optional): Logging level - DEBUG, INFO, WARNING, ERROR (default: `INFO`)

### HTTP Mode Configuration Headers

When running in HTTP mode, you can override configuration per-request using headers:

- `X-GitHub-Token`: Override GitHub personal access token (falls back to `GITHUB_TOKEN` env var)

This is useful for multi-tenant deployments or when different clients need different tokens.

## 🛠️ Available Tools

### `github_graphql_query`

Execute a custom GraphQL query against the GitHub API to query repositories, projects, issues, pull requests, and more.


## 🐳 Docker Details

### Multi-Stage Build

The Dockerfile uses a multi-stage build with `uv` for optimal performance:
- **Build stage**: Compiles dependencies and bytecode
- **Runtime stage**: Minimal Alpine-based image with only runtime dependencies

### Security Features

- Runs as non-root user (`app`)
- Read-only root filesystem
- No new privileges
- Minimal attack surface with Alpine Linux

### Health Checks

The container includes a health check that pings `/health` endpoint every 30 seconds.

### Resource Limits

Default limits (adjust in `docker-compose.yml`):
- CPU: 1 core (0.5 reserved)
- Memory: 512MB (256MB reserved)

### Ports

- Production: `8003:8000` (mapped to host port 8003)
- Configurable in `docker-compose.yml`

## Development

### Project Structure
```
src/github/
├── src/
│   └── github_mcp_server/
│       ├── __init__.py
│       ├── server.py              # FastMCP server implementation
│       └── test_scripts/          # Testing utilities
├── pyproject.toml                 # Dependencies and script entry points
├── Dockerfile                     # Production Docker image
├── docker-compose.yml             # Production deployment
├── docker-compose.dev.yml         # Development overrides
├── build-container-run.sh         # Quick rebuild script
└── README.md                      # This file
```

### Running Locally

```bash
# STDIO mode (default)
uv run github-mcp

# HTTP mode for testing
uv run github-mcp --transport http --port 8000

# With debug logging
uv run github-mcp --transport http --log-level DEBUG
```

### Authentication Pattern

This server uses **Personal Access Tokens** for GitHub authentication:

```python
import requests

headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "https://api.github.com/graphql",
    json={'query': query, 'variables': variables},
    headers=headers
)
```

⚠️ **Never commit tokens** - always use environment variables or HTTP headers

### Docker Development Workflow

1. **Make code changes** in `src/github_mcp_server/`

2. **Test with live reload**:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```
   Changes to source files will be reflected immediately (volume mounted)

3. **Rebuild for production testing**:
   ```bash
   ./build-container-run.sh
   ```

4. **View logs**:
   ```bash
   docker compose logs -f github-mcp
   ```

5. **Stop and remove**:
   ```bash
   docker compose down
   ```

## Related Documentation

- [GitHub GraphQL API Docs](https://docs.github.com/en/graphql)
- [GitHub Projects V2 API](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
