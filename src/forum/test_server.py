"""Tests for forum MCP server tools."""

import os
import tempfile

import pytest

from database import ForumDatabase
from server import _create_thread_impl, _list_threads_impl, _reply_to_thread_impl


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


class TestReplyToThread:
    """Tests for reply_to_thread tool."""

    def test_reply_to_thread_success(self, test_db_with_threads):
        """Test successful reply to thread."""
        # Get the first thread ID
        threads = test_db_with_threads.list_threads()
        thread_id = threads[0]["id"]

        result = _reply_to_thread_impl(
            test_db_with_threads, thread_id, "This is a reply", "test_author"
        )

        assert result["success"] is True
        assert "post_id" in result
        assert result["post_id"] > 0
        assert result["thread_id"] == thread_id
        assert "message" in result
        assert "test_author" in result["message"]
        assert str(thread_id) in result["message"]

    def test_reply_to_thread_with_quote(self, test_db_with_threads):
        """Test reply to thread with quote."""
        # Get the first thread ID
        threads = test_db_with_threads.list_threads()
        thread_id = threads[0]["id"]

        # Create a first reply
        first_reply = _reply_to_thread_impl(
            test_db_with_threads, thread_id, "First reply", "author1"
        )
        assert first_reply["success"] is True
        quote_post_id = first_reply["post_id"]

        # Create a second reply quoting the first
        result = _reply_to_thread_impl(
            test_db_with_threads,
            thread_id,
            "This quotes the first reply",
            "author2",
            quote_post_id=quote_post_id,
        )

        assert result["success"] is True
        assert result["post_id"] > quote_post_id  # New post should have higher ID
        assert result["thread_id"] == thread_id

    def test_reply_to_thread_nonexistent_thread(self, temp_db):
        """Test reply to non-existent thread."""
        result = _reply_to_thread_impl(
            temp_db, 99999, "This should fail", "author"
        )

        assert result["success"] is False
        assert "error" in result
        assert "does not exist" in result["error"].lower()

    def test_reply_to_thread_empty_body(self, test_db_with_threads):
        """Test reply with empty body."""
        threads = test_db_with_threads.list_threads()
        thread_id = threads[0]["id"]

        result = _reply_to_thread_impl(
            test_db_with_threads, thread_id, "", "author"
        )

        # Should still succeed (empty body is valid per design)
        assert result["success"] is True
        assert result["post_id"] > 0

    def test_reply_to_thread_empty_author(self, test_db_with_threads):
        """Test reply with empty author."""
        threads = test_db_with_threads.list_threads()
        thread_id = threads[0]["id"]

        result = _reply_to_thread_impl(
            test_db_with_threads, thread_id, "Reply body", ""
        )

        # Should still succeed (empty author is valid per design)
        assert result["success"] is True
        assert result["post_id"] > 0

    def test_reply_to_thread_updates_thread_timestamp(self, temp_db):
        """Test that replying to a thread updates its updated_at timestamp."""
        import time

        # Create a thread
        thread_id = temp_db.create_thread("Test Thread", "Initial body", "author1")
        threads_before = temp_db.list_threads()
        original_updated_at = threads_before[0]["updated_at"]

        # Wait a bit to ensure timestamp difference
        time.sleep(0.01)

        # Reply to the thread
        result = _reply_to_thread_impl(
            temp_db, thread_id, "Reply body", "author2"
        )

        assert result["success"] is True

        # Check that thread's updated_at was updated
        threads_after = temp_db.list_threads()
        new_updated_at = threads_after[0]["updated_at"]

        # The updated_at should be different (newer)
        assert new_updated_at != original_updated_at
        # In ISO format, newer timestamps should be lexicographically greater
        assert new_updated_at > original_updated_at

    def test_reply_to_thread_invalid_quote_post_id(self, test_db_with_threads):
        """Test reply with invalid quote_post_id."""
        threads = test_db_with_threads.list_threads()
        thread_id = threads[0]["id"]

        result = _reply_to_thread_impl(
            test_db_with_threads,
            thread_id,
            "Reply with invalid quote",
            "author",
            quote_post_id=99999,
        )

        assert result["success"] is False
        assert "error" in result

    def test_reply_to_thread_multiple_replies(self, temp_db):
        """Test multiple replies to the same thread."""
        thread_id = temp_db.create_thread("Test Thread", "Initial body", "author1")

        # Create multiple replies
        reply1 = _reply_to_thread_impl(temp_db, thread_id, "Reply 1", "author2")
        reply2 = _reply_to_thread_impl(temp_db, thread_id, "Reply 2", "author3")
        reply3 = _reply_to_thread_impl(temp_db, thread_id, "Reply 3", "author4")

        assert reply1["success"] is True
        assert reply2["success"] is True
        assert reply3["success"] is True

        # All replies should have different post IDs
        assert reply1["post_id"] < reply2["post_id"] < reply3["post_id"]
        # All should be for the same thread
        assert (
            reply1["thread_id"]
            == reply2["thread_id"]
            == reply3["thread_id"]
            == thread_id
        )
