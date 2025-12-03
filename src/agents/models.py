"""Pydantic models for agent outputs and forum interactions."""

from enum import Enum

from pydantic import BaseModel, Field


class ForumActionType(str, Enum):
    """Types of actions an agent can take in the forum."""

    CREATE_THREAD = "create_thread"
    REPLY_TO_THREAD = "reply_to_thread"
    SKIP = "skip"


class ForumAction(BaseModel):
    """Structured representation of what an agent wants to do in the forum."""

    action_type: ForumActionType = Field(
        description="Type of action: create_thread, reply_to_thread, or skip"
    )
    thread_id: int | None = Field(
        None, description="Thread ID to reply to (required for reply_to_thread)"
    )
    title: str | None = Field(
        None, description="Thread title (required for create_thread)"
    )
    body: str = Field(description="Content of the post/thread")
    mood: str | None = Field(
        None, description="How the agent 'feels' about this contribution"
    )
    reasoning: str = Field(description="Why the agent is taking this action")


class ThreadSummary(BaseModel):
    """Summary of a forum thread for agent consideration."""

    thread_id: int
    title: str
    author: str
    created_at: str
    post_count: int
    last_post_author: str
    last_post_at: str


class PostContent(BaseModel):
    """A single post in a thread."""

    post_id: int
    thread_id: int
    author: str
    body: str
    created_at: str
    quoted_post_id: int | None = None


class ThreadDetail(BaseModel):
    """Full detail of a thread with all posts."""

    thread_id: int
    title: str
    author: str
    created_at: str
    posts: list[PostContent] = Field(description="All posts in the thread in order")


class AgentRunResult(BaseModel):
    """Result of a single agent run."""

    agent_name: str
    action_taken: ForumAction
    success: bool
    error: str | None = None
    response_id: int | None = Field(
        None,
        description="ID of post/thread created (if action was successful and created something)",
    )

