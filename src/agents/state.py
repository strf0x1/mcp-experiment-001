"""SQLite-backed state persistence for tracking agent activity."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class AgentState:
    """Manages persistent state for individual agents.

    Tracks:
    - Last run timestamp
    - Seen thread IDs (to avoid re-processing)
    - Run history for debugging
    """

    def __init__(self, db_path: str = "./.agent_data/agents.db"):
        """Initialize agent state manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    agent_name TEXT PRIMARY KEY,
                    last_run_timestamp TEXT,
                    created_at TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    thread_id INTEGER NOT NULL,
                    seen_at TEXT NOT NULL,
                    FOREIGN KEY (agent_name) REFERENCES agent_runs(agent_name),
                    UNIQUE(agent_name, thread_id)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    run_timestamp TEXT NOT NULL,
                    action_type TEXT,
                    thread_id INTEGER,
                    post_id INTEGER,
                    success BOOLEAN,
                    error_message TEXT,
                    FOREIGN KEY (agent_name) REFERENCES agent_runs(agent_name)
                )
                """
            )

            conn.commit()

    def get_last_run(self, agent_name: str) -> datetime | None:
        """Get the last run timestamp for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            datetime of last run, or None if never run
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT last_run_timestamp FROM agent_runs WHERE agent_name = ?",
                (agent_name,),
            )
            row = cursor.fetchone()

        if row and row[0]:
            return datetime.fromisoformat(row[0])
        return None

    def set_last_run(self, agent_name: str, timestamp: datetime) -> None:
        """Set the last run timestamp for an agent.

        Args:
            agent_name: Name of the agent
            timestamp: Timestamp of this run
        """
        ts_str = timestamp.isoformat()
        now_str = datetime.now(UTC).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM agent_runs WHERE agent_name = ?", (agent_name,)
            )
            exists = cursor.fetchone() is not None

            if exists:
                conn.execute(
                    "UPDATE agent_runs SET last_run_timestamp = ? WHERE agent_name = ?",
                    (ts_str, agent_name),
                )
            else:
                conn.execute(
                    "INSERT INTO agent_runs (agent_name, last_run_timestamp, created_at) VALUES (?, ?, ?)",
                    (agent_name, ts_str, now_str),
                )

            conn.commit()

    def get_seen_thread_ids(self, agent_name: str) -> set[int]:
        """Get all thread IDs seen by an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Set of thread IDs
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT thread_id FROM seen_threads WHERE agent_name = ?",
                (agent_name,),
            )
            rows = cursor.fetchall()

        return {row[0] for row in rows}

    def mark_thread_seen(self, agent_name: str, thread_id: int) -> None:
        """Mark a thread as seen by an agent.

        Args:
            agent_name: Name of the agent
            thread_id: ID of the thread
        """
        now_str = datetime.now(UTC).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO seen_threads (agent_name, thread_id, seen_at) VALUES (?, ?, ?)",
                    (agent_name, thread_id, now_str),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # Already seen, that's fine
                pass

    def clear_seen_threads(self, agent_name: str) -> None:
        """Clear seen threads for an agent (useful for testing/reset).

        Args:
            agent_name: Name of the agent
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM seen_threads WHERE agent_name = ?", (agent_name,)
            )
            conn.commit()

    def record_run_action(
        self,
        agent_name: str,
        timestamp: datetime,
        action_type: str,
        thread_id: int | None = None,
        post_id: int | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """Record an action taken during a run.

        Args:
            agent_name: Name of the agent
            timestamp: When the action occurred
            action_type: Type of action (create_thread, reply_to_thread, skip)
            thread_id: Thread ID involved (if applicable)
            post_id: Post ID created (if applicable)
            success: Whether the action succeeded
            error_message: Error message if failed
        """
        ts_str = timestamp.isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO run_history
                (agent_name, run_timestamp, action_type, thread_id, post_id, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_name,
                    ts_str,
                    action_type,
                    thread_id,
                    post_id,
                    success,
                    error_message,
                ),
            )
            conn.commit()

