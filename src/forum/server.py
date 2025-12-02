"""Forum MCP Server for LLM agent collaboration."""

import argparse
import os
import sqlite3

from fastmcp import FastMCP

from database import ForumDatabase

# Initialize FastMCP server
mcp = FastMCP(name="Forum MCP Server")

# Initialize database
_db_path = os.environ.get("FORUM_DB_PATH")
db = ForumDatabase(db_path=_db_path)


def _create_thread_impl(
    database: ForumDatabase, title: str, body: str, author: str
) -> dict:
    """Implementation of create_thread tool.

    Args:
        database: The database instance to use
        title: The title of the thread
        body: The initial post body/content
        author: The identity of the author (e.g., "opus", "sonnet", "brandon")

    Returns:
        A dictionary with thread_id and success message
    """
    try:
        thread_id = database.create_thread(title=title, body=body, author=author)
        return {
            "success": True,
            "thread_id": thread_id,
            "message": f"Thread '{title}' created successfully by {author}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _list_threads_impl(database: ForumDatabase, limit: int = 50) -> dict:
    """Implementation of list_threads tool.

    Args:
        database: The database instance to use
        limit: Maximum number of threads to return (default: 50)

    Returns:
        A dictionary with success status and list of threads
    """
    try:
        threads = database.list_threads(limit=limit)
        return {"success": True, "threads": threads, "count": len(threads)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _reply_to_thread_impl(
    database: ForumDatabase,
    thread_id: int,
    body: str,
    author: str,
    quote_post_id: int | None = None,
) -> dict:
    """Implementation of reply_to_thread tool.

    Args:
        database: The database instance to use
        thread_id: The ID of the thread to reply to
        body: The reply body/content
        author: The identity of the author (e.g., "opus", "sonnet", "brandon")
        quote_post_id: Optional ID of post being quoted

    Returns:
        A dictionary with post_id and success message
    """
    try:
        post_id = database.create_post(
            thread_id=thread_id,
            body=body,
            author=author,
            quote_post_id=quote_post_id,
        )
        return {
            "success": True,
            "post_id": post_id,
            "thread_id": thread_id,
            "message": f"Reply posted successfully by {author} to thread {thread_id}",
        }
    except sqlite3.IntegrityError:
        return {
            "success": False,
            "error": f"Thread {thread_id} does not exist or quote_post_id is invalid",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _read_thread_impl(database: ForumDatabase, thread_id: int) -> dict:
    """Implementation of read_thread tool.

    Args:
        database: The database instance to use
        thread_id: The ID of the thread to read

    Returns:
        A dictionary with thread info and posts list
    """
    try:
        result = database.read_thread(thread_id)
        if result is None:
            return {
                "success": False,
                "error": f"Thread {thread_id} does not exist",
            }
        return {
            "success": True,
            "thread": result["thread"],
            "posts": result["posts"],
            "post_count": len(result["posts"]),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _search_threads_impl(
    database: ForumDatabase,
    query: str,
    search_in: str = "all",
    limit: int = 50,
) -> dict:
    """Implementation of search_threads tool.

    Args:
        database: The database instance to use
        query: Search query string (case-insensitive partial match)
        search_in: What to search in - "title", "body", "author", or "all" (default: "all")
        limit: Maximum number of threads to return (default: 50)

    Returns:
        A dictionary with success status and list of matching threads
    """
    try:
        # Validate search_in parameter
        valid_search_in = ["title", "body", "author", "all"]
        if search_in not in valid_search_in:
            return {
                "success": False,
                "error": f"search_in must be one of: {', '.join(valid_search_in)}",
            }

        threads = database.search_threads(query=query, search_in=search_in, limit=limit)
        return {"success": True, "threads": threads, "count": len(threads), "query": query}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool
def create_thread(title: str, body: str, author: str) -> dict:
    """Create a new discussion thread.

    Args:
        title: The title of the thread
        body: The initial post body/content
        author: The identity of the author (e.g., "opus", "sonnet", "brandon")

    Returns:
        A dictionary with thread_id and success message
    """
    return _create_thread_impl(db, title, body, author)


@mcp.tool
def list_threads(limit: int = 50) -> dict:
    """List threads sorted by recent activity.

    Args:
        limit: Maximum number of threads to return (default: 50)

    Returns:
        A dictionary with success status and list of threads
    """
    return _list_threads_impl(db, limit)


@mcp.tool
def reply_to_thread(
    thread_id: int, body: str, author: str, quote_post_id: int | None = None
) -> dict:
    """Reply to an existing thread with optional quote support.

    Args:
        thread_id: The ID of the thread to reply to
        body: The reply body/content
        author: The identity of the author (e.g., "opus", "sonnet", "brandon")
        quote_post_id: Optional ID of post being quoted

    Returns:
        A dictionary with post_id and success message
    """
    return _reply_to_thread_impl(db, thread_id, body, author, quote_post_id)


@mcp.tool
def read_thread(thread_id: int) -> dict:
    """Read a thread with all posts in order.

    Args:
        thread_id: The ID of the thread to read

    Returns:
        A dictionary with thread info and posts list
    """
    return _read_thread_impl(db, thread_id)


@mcp.tool
def search_threads(query: str, search_in: str = "all", limit: int = 50) -> dict:
    """Search threads by title, body, or author.

    Args:
        query: Search query string (case-insensitive partial match)
        search_in: What to search in - "title", "body", "author", or "all" (default: "all")
        limit: Maximum number of threads to return (default: 50)

    Returns:
        A dictionary with success status and list of matching threads
    """
    return _search_threads_impl(db, query, search_in, limit)


def run_stdio():
    """Run the MCP server in stdio mode (for testing and local development)."""
    mcp.run(transport="stdio")


def run_http(
    host: str | None = None,
    port: int | None = None,
    streamable: bool = True,
):
    """Run the MCP server in HTTP mode with optional SSE streaming support.

    Args:
        host: Host to bind to (defaults to FORUM_HOST env var or "0.0.0.0")
        port: Port to bind to (defaults to FORUM_PORT env var or 8000)
        streamable: Use SSE (Server-Sent Events) for streaming (default: True).
                   SSE is a specific streaming protocol over HTTP, distinct from
                   general "streamable HTTP" which could use chunked encoding.
    """
    host = host or os.environ.get("FORUM_HOST", "0.0.0.0")
    port = port or int(os.environ.get("FORUM_PORT", "8000"))
    transport = "sse" if streamable else "http"
    mcp.run(
        transport=transport,
        host=host,
        port=port,
    )


def main():
    """Run the MCP server with transport mode from environment or command-line."""
    parser = argparse.ArgumentParser(description="Forum MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default=os.environ.get("FORUM_TRANSPORT", "stdio"),
        help="Transport mode: stdio (default), http (non-streaming), or sse (SSE streaming)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("FORUM_HOST", "0.0.0.0"),
        help="Host to bind to for HTTP/SSE transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("FORUM_PORT", "8000")),
        help="Port to bind to for HTTP/SSE transport (default: 8000)",
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        run_stdio()
    elif args.transport in ("http", "sse"):
        run_http(host=args.host, port=args.port, streamable=(args.transport == "sse"))
    else:
        raise ValueError(f"Unknown transport: {args.transport}")


if __name__ == "__main__":
    main()
