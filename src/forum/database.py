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

    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
