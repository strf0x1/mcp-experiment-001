"""Tests for forum MCP server tools."""

import os
import tempfile

import pytest

from database import ForumDatabase
from server import _create_thread_impl, _list_threads_impl


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = ForumDatabase(db_path=db_path)
    yield db
    os.unlink(db_path)


@pytest.fixture
def test_db_with_threads(temp_db):
    """Create a database with some test threads."""
    # Create a few threads
    temp_db.create_thread("First Thread", "This is the first thread body", "opus")
    temp_db.create_thread("Second Thread", "This is the second thread body", "sonnet")
    temp_db.create_thread("Third Thread", "This is the third thread body", "brandon")
    return temp_db


class TestCreateThread:
    """Tests for create_thread tool."""

    def test_create_thread_success(self, temp_db):
        """Test successful thread creation."""
        result = _create_thread_impl(
            temp_db, "Test Thread", "Test body content", "test_author"
        )

        assert result["success"] is True
        assert "thread_id" in result
        assert result["thread_id"] > 0
        assert "message" in result
        assert "Test Thread" in result["message"]
        assert "test_author" in result["message"]

    def test_create_thread_empty_title(self, temp_db):
        """Test thread creation with empty title."""
        result = _create_thread_impl(temp_db, "", "Test body", "author")

        # Should still succeed (empty title is valid)
        assert result["success"] is True
        assert result["thread_id"] > 0

    def test_create_thread_empty_body(self, temp_db):
        """Test thread creation with empty body."""
        result = _create_thread_impl(temp_db, "Test Title", "", "author")

        # Should still succeed (empty body is valid)
        assert result["success"] is True
        assert result["thread_id"] > 0

    def test_create_thread_empty_author(self, temp_db):
        """Test thread creation with empty author."""
        result = _create_thread_impl(temp_db, "Test Title", "Test body", "")

        # Should still succeed (empty author is valid per design)
        assert result["success"] is True
        assert result["thread_id"] > 0

    def test_create_thread_long_content(self, temp_db):
        """Test thread creation with very long content."""
        long_body = "x" * 10000
        result = _create_thread_impl(temp_db, "Long Thread", long_body, "author")

        assert result["success"] is True
        assert result["thread_id"] > 0


class TestListThreads:
    """Tests for list_threads tool."""

    def test_list_threads_empty(self, temp_db):
        """Test listing threads when database is empty."""
        result = _list_threads_impl(temp_db)

        assert result["success"] is True
        assert result["threads"] == []
        assert result["count"] == 0

    def test_list_threads_with_threads(self, test_db_with_threads):
        """Test listing threads when threads exist."""
        result = _list_threads_impl(test_db_with_threads)

        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["threads"]) == 3

        # Check thread structure
        thread = result["threads"][0]
        assert "id" in thread
        assert "title" in thread
        assert "body" in thread
        assert "author" in thread
        assert "created_at" in thread
        assert "updated_at" in thread

    def test_list_threads_limit(self, test_db_with_threads):
        """Test listing threads with limit."""
        result = _list_threads_impl(test_db_with_threads, limit=2)

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["threads"]) == 2

    def test_list_threads_limit_zero(self, test_db_with_threads):
        """Test listing threads with limit of 0."""
        result = _list_threads_impl(test_db_with_threads, limit=0)

        assert result["success"] is True
        assert result["count"] == 0
        assert len(result["threads"]) == 0

    def test_list_threads_sorted_by_recent_activity(self, temp_db):
        """Test that threads are sorted by recent activity (most recent first)."""
        # Create threads with slight delays to ensure different timestamps
        import time

        temp_db.create_thread("Oldest", "Body 1", "author1")
        time.sleep(0.01)  # Small delay to ensure different timestamp
        temp_db.create_thread("Newest", "Body 2", "author2")
        time.sleep(0.01)
        temp_db.create_thread("Middle", "Body 3", "author3")

        result = _list_threads_impl(temp_db)

        assert result["success"] is True
        assert result["count"] == 3

        # The most recently updated should be first
        # Note: This test might be flaky if timestamps are identical,
        # but in practice with database timestamps they should differ
        threads = result["threads"]
        assert threads[0]["title"] == "Middle"  # Last created
        assert threads[1]["title"] == "Newest"
        assert threads[2]["title"] == "Oldest"

    def test_list_threads_default_limit(self, temp_db):
        """Test that default limit works correctly."""
        # Create more than 50 threads
        for i in range(60):
            temp_db.create_thread(f"Thread {i}", f"Body {i}", f"author{i}")

        result = _list_threads_impl(temp_db)

        assert result["success"] is True
        assert result["count"] == 50  # Default limit
        assert len(result["threads"]) == 50
