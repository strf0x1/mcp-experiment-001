
import os
import json
import requests
from typing import Annotated
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SERVER_INSTRUCTIONS = """
You are an expert GitHub assistant for repo exploration and issue tracking.
Use the available tools to query GitHub's GraphQL API for api, project data, issues or anything else you are curious about.
"""

# Initialize FastMCP server
mcp = FastMCP(
    name="GitHub GraphQL Explorer",
    instructions=SERVER_INSTRUCTIONS
)

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "strf0x1")
GITHUB_API_URL = "https://api.github.com/graphql"

def get_github_token() -> str:
    """Get GitHub token from HTTP header or fall back to environment variable.
    
    Checks for X-GitHub-Token header in HTTP requests. If not present or
    not in HTTP context, falls back to GITHUB_TOKEN environment variable.
    
    Returns:
        GitHub personal access token
        
    Raises:
        ValueError: If token is not found in header or environment
    """
    headers = get_http_headers()
    # Check for custom token header (case-insensitive)
    token_from_header = headers.get("x-github-token")
    if token_from_header:
        return token_from_header
    
    # Fall back to environment variable
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable or X-GitHub-Token header not set")
    
    return GITHUB_TOKEN

def run_query(query, variables=None):
    """Execute a GraphQL query against the GitHub API."""
    token = get_github_token()
        
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(GITHUB_API_URL, json={'query': query, 'variables': variables}, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with code {response.status_code}: {query}")

# Health check endpoint for Docker/container orchestration
try:
    # Import will only work in HTTP context, safe to fail silently
    from starlette.responses import PlainTextResponse
    
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request) -> PlainTextResponse:
        """Health check endpoint for container orchestration systems."""
        return PlainTextResponse("OK", status_code=200)
except ImportError:
    pass  # Starlette not available in some contexts, health check won't be registered

@mcp.tool(description="Execute a custom GraphQL query against the GitHub API to query repositories, projects, issues, pull requests, and more.")
def github_graphql_query(
    query: Annotated[str, "The GraphQL query string to execute against the GitHub API"],
    variables: Annotated[str | None, "Optional JSON string of variables for the query (e.g., '{\"owner\": \"myorg\", \"repo\": \"myrepo\"}')"] = None
) -> str:
    """
    Execute a custom GraphQL query against the GitHub API.
    
    This tool provides direct access to GitHub's GraphQL API, allowing you to query any data
    available through the API. You can query repositories, projects, issues, pull requests,
    users, organizations, and more.
    
    The default repository owner and repo from environment variables are:
    - GITHUB_OWNER: {owner}
    
    Example queries:
    
    1. Get repository information:
       query {{
         repository(owner: "{owner}", name: "mcp-experiment-001") {{
           name
           description
           stargazerCount
         }}
       }}
    
    2. Get open projects with items:
       query {{
         repository(owner: "{owner}", name: "mcp-experiment-001") {{
           projectsV2(first: 10, query: "is:open") {{
             nodes {{
               id
               title
               items(first: 20) {{
                 nodes {{
                   content {{
                     ... on Issue {{
                       number
                       title
                       state
                     }}
                   }}
                 }}
               }}
             }}
           }}
         }}
       }}
    
    3. Get issues with custom fields:
       query {{
         repository(owner: "{owner}", name: "mcp-experiment-001") {{
           projectsV2(first: 1) {{
             nodes {{
               items(first: 50) {{
                 nodes {{
                   content {{
                     ... on Issue {{
                       number
                       title
                       body
                       assignees(first: 5) {{
                         nodes {{ login }}
                       }}
                     }}
                   }}
                   fieldValues(first: 20) {{
                     nodes {{
                       ... on ProjectV2ItemFieldTextValue {{
                         text
                         field {{ ... on ProjectV2FieldCommon {{ name }} }}
                       }}
                       ... on ProjectV2ItemFieldSingleSelectValue {{
                         name
                         field {{ ... on ProjectV2FieldCommon {{ name }} }}
                       }}
                       ... on ProjectV2ItemFieldIterationValue {{
                         title
                         field {{ ... on ProjectV2FieldCommon {{ name }} }}
                       }}
                     }}
                   }}
                 }}
               }}
             }}
           }}
         }}
       }}
    
    For more information on GitHub's GraphQL API:
    https://docs.github.com/en/graphql
    
    Use the GraphQL Explorer to test queries:
    https://docs.github.com/en/graphql/overview/explorer
    """.format(owner=GITHUB_OWNER)
    
    try:
        # Parse variables if provided
        parsed_variables = None
        if variables:
            try:
                parsed_variables = json.loads(variables)
            except json.JSONDecodeError as e:
                return json.dumps({
                    "error": f"Invalid JSON in variables parameter: {str(e)}"
                })
        
        result = run_query(query, parsed_variables)
        
        # Check for GraphQL errors
        if "errors" in result:
            return json.dumps({
                "errors": result["errors"],
                "data": result.get("data")
            }, indent=2)
        
        return json.dumps(result.get("data", {}), indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "error_type": type(e).__name__
        })

def main():
    """Main entry point for the GitHub MCP server."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="GitHub MCP Server - Natural language access to GitHub Project data"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode: stdio (default) or http for Streamable HTTP"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (http mode only, default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (http mode only, default: 8000)"
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="URL path for MCP endpoint (http mode only, default: /mcp)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "http":
        # Configure Uvicorn for long-lived streaming connections
        uvicorn_config = {
            "timeout_keep_alive": 300,  # Keep connection alive for 5 minutes
            "timeout_notify": 30,       # Timeout for shutdown notification
        }
        mcp.run(
            transport="http",
            host=args.host,
            port=args.port,
            path=args.path,
            log_level=args.log_level,
            uvicorn_config=uvicorn_config
        )
    else:
        print(f"Unknown transport: {args.transport}", file=sys.stderr)
        sys.exit(1)

def main_stdio():
    """Entry point for stdio transport mode."""
    mcp.run(transport="stdio")

def main_http():
    """Entry point for HTTP transport mode with Docker-friendly defaults."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="GitHub MCP Server - HTTP Mode"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="URL path for MCP endpoint (default: /mcp)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure Uvicorn for long-lived streaming connections
    uvicorn_config = {
        "timeout_keep_alive": 300,  # Keep connection alive for 5 minutes
        "timeout_notify": 30,       # Timeout for shutdown notification
    }
    
    mcp.run(
        transport="http",
        host=args.host,
        port=args.port,
        path=args.path,
        log_level=args.log_level,
        uvicorn_config=uvicorn_config
    )

if __name__ == "__main__":
    main()

