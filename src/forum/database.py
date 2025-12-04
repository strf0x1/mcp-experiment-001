"""Database module for forum MCP server using SQLite."""

import os
import sqlite3
from datetime import UTC, datetime
from typing import Any

# Register datetime adapter/converter to avoid deprecation warnings in Python 3.12+
# Store datetime as ISO format strings (SQLite doesn't have native datetime type)
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())


class ForumDatabase:
    """Manages SQLite database for forum threads and posts."""

    def __init__(self, db_path: str | None = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses 'forum.db'
                in current directory.
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "forum.db")
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Create threads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create posts table (for replies)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                author TEXT NOT NULL,
                quote_post_id INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE,
                FOREIGN KEY (quote_post_id) REFERENCES posts(id) ON DELETE SET NULL
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_threads_updated_at
            ON threads(updated_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_thread_id
            ON posts(thread_id)
        """)

        conn.commit()
        conn.close()

    def create_thread(self, title: str, body: str, author: str) -> int:
        """Create a new thread.

        Args:
            title: Thread title
            body: Initial post body
            author: Author identity (string)

        Returns:
            The ID of the created thread
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Use timezone-aware datetime (adapter registered at module level)
        now = datetime.now(UTC)
        cursor.execute(
            """
            INSERT INTO threads (title, body, author, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (title, body, author, now, now),
        )

        thread_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return thread_id

    def list_threads(self, limit: int | None = None) -> list[dict[str, Any]]:
        """List threads sorted by recent activity (updated_at DESC).

        Args:
            limit: Optional limit on number of threads to return

        Returns:
            List of thread dictionaries with id, title, body, author,
            created_at, updated_at
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        query = """
            SELECT id, title, body, author, created_at, updated_at
            FROM threads
            ORDER BY updated_at DESC
        """

        if limit is not None:
            query += " LIMIT ?"
            cursor.execute(query, (limit,))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()

        threads = []
        for row in rows:
            threads.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "body": row["body"],
                    "author": row["author"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )

        conn.close()
        return threads

    def search_threads(
        self,
        query: str,
        search_in: str = "all",
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search threads by title, body, or author.

        Args:
            query: Search query string (case-insensitive partial match)
            search_in: What to search in - "title", "body", "author", or "all" (default: "all")
            limit: Optional limit on number of threads to return

        Returns:
            List of thread dictionaries matching the search query, sorted by updated_at DESC
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build WHERE clause based on search_in parameter
        search_pattern = f"%{query}%"
        where_clauses = []

        if search_in == "title":
            where_clauses.append("title LIKE ?")
            params = [search_pattern]
        elif search_in == "body":
            where_clauses.append("body LIKE ?")
            params = [search_pattern]
        elif search_in == "author":
            where_clauses.append("author LIKE ?")
            params = [search_pattern]
        else:  # search_in == "all"
            where_clauses.append("(title LIKE ? OR body LIKE ? OR author LIKE ?)")
            params = [search_pattern, search_pattern, search_pattern]

        where_clause = " AND ".join(where_clauses)

        query_sql = f"""
            SELECT id, title, body, author, created_at, updated_at
            FROM threads
            WHERE {where_clause}
            ORDER BY updated_at DESC
        """

        if limit is not None:
            query_sql += " LIMIT ?"
            params.append(limit)

        cursor.execute(query_sql, params)
        rows = cursor.fetchall()

        threads = []
        for row in rows:
            threads.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "body": row["body"],
                    "author": row["author"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )

        conn.close()
        return threads

    def create_post(
        self, thread_id: int, body: str, author: str, quote_post_id: int | None = None
    ) -> int:
        """Create a new post (reply) in a thread.

        Args:
            thread_id: The ID of the thread to reply to
            body: Post body/content
            author: Author identity (string)
            quote_post_id: Optional ID of post being quoted

        Returns:
            The ID of the created post

        Raises:
            sqlite3.IntegrityError: If thread_id doesn't exist \
                or quote_post_id is invalid
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Use timezone-aware datetime (adapter registered at module level)
        now = datetime.now(UTC)

        # Create the post
        cursor.execute(
            """
            INSERT INTO posts (thread_id, body, author, quote_post_id, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (thread_id, body, author, quote_post_id, now),
        )

        post_id = cursor.lastrowid

        # Update thread's updated_at timestamp
        cursor.execute(
            """
            UPDATE threads
            SET updated_at = ?
            WHERE id = ?
        """,
            (now, thread_id),
        )

        conn.commit()
        conn.close()

        return post_id

    def read_thread(self, thread_id: int) -> dict[str, Any] | None:
        """Read a thread with all its posts in order.

        Args:
            thread_id: The ID of the thread to read

        Returns:
            Dictionary with thread info and posts list, or None if thread doesn't exist
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get thread information
        cursor.execute(
            """
            SELECT id, title, body, author, created_at, updated_at
            FROM threads
            WHERE id = ?
        """,
            (thread_id,),
        )
        thread_row = cursor.fetchone()

        if thread_row is None:
            conn.close()
            return None

        # Get all posts for this thread with quoted post body (if any), ordered by created_at (oldest first)
        cursor.execute(
            """
            SELECT
                p.id,
                p.thread_id,
                p.body,
                p.author,
                p.quote_post_id,
                p.created_at,
                q.body AS quoted_post_body
            FROM posts p
            LEFT JOIN posts q ON p.quote_post_id = q.id
            WHERE p.thread_id = ?
            ORDER BY p.created_at ASC
        """,
            (thread_id,),
        )
        post_rows = cursor.fetchall()

        # Build thread dictionary
        thread = {
            "id": thread_row["id"],
            "title": thread_row["title"],
            "body": thread_row["body"],
            "author": thread_row["author"],
            "created_at": thread_row["created_at"],
            "updated_at": thread_row["updated_at"],
        }

        # Build posts list
        posts = []
        for post_row in post_rows:
            post_dict = {
                "id": post_row["id"],
                "thread_id": post_row["thread_id"],
                "body": post_row["body"],
                "author": post_row["author"],
                "quote_post_id": post_row["quote_post_id"],
                "created_at": post_row["created_at"],
            }
            # Include quoted post body if this post quotes another post
            if post_row["quote_post_id"] is not None:
                post_dict["quoted_post_body"] = post_row["quoted_post_body"]
            posts.append(post_dict)

        conn.close()

        return {"thread": thread, "posts": posts}

    def delete_post(self, post_id: int) -> bool:
        """Delete a post by ID.

        Args:
            post_id: The ID of the post to delete

        Returns:
            True if post was deleted, False if post doesn't exist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Check if post exists
        cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        # Delete the post
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()

        return True

    def delete_thread(self, thread_id: int) -> bool:
        """Delete a thread by ID (cascades to delete all posts in the thread).

        Args:
            thread_id: The ID of the thread to delete

        Returns:
            True if thread was deleted, False if thread doesn't exist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Check if thread exists
        cursor.execute("SELECT id FROM threads WHERE id = ?", (thread_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        # Delete the thread (cascades to delete all posts)
        cursor.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        conn.commit()
        conn.close()

        return True

    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
