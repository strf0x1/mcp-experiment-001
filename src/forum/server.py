"""Forum MCP Server for LLM agent collaboration."""

import os

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


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
