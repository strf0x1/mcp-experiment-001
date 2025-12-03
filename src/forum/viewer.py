#!/usr/bin/env python3
"""Colorful Textual CLI viewer for forum threads - fun interface for browsing discussions."""

import os
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Input,
    Static,
    DataTable,
)
from textual.binding import Binding

from database import ForumDatabase


class PostCard(Static):
    """A widget representing a single forum post."""

    def __init__(
        self,
        author: str,
        body: str,
        timestamp: str,
        is_original: bool = False,
        post_number: int | None = None,
        quoted_text: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.author = author
        self.body = body
        self.timestamp = timestamp
        self.is_original = is_original
        self.post_number = post_number
        self.quoted_text = quoted_text

    def on_mount(self) -> None:
        """Set CSS classes based on post type."""
        self.add_class("post-card")
        if self.is_original:
            self.add_class("original")
        else:
            self.add_class("reply")

    def render(self) -> str:
        """Render the post content."""
        if self.is_original:
            header = f"[b]📝 Original Post[/b]"
        else:
            header = f"[b]💬 Reply #{self.post_number}[/b]"

        lines = [
            header,
            f"[green]✍️ {self.author}[/green] [dim]@ {self.timestamp}[/dim]",
            "─" * 60,
            self.body,
        ]

        if self.quoted_text:
            lines.append("")
            lines.append(f"[dim italic]📌 Quoting: {self.quoted_text[:80]}...[/dim italic]")

        return "\n".join(lines)


class ForumHeader(Static):
    """Header widget with title and styling."""

    def render(self) -> str:
        return "🗣️ FORUM EXPLORER 🌈"


class ForumViewer(App):
    """Main Textual application for viewing forum threads."""

    CSS = """
    Screen {
        background: $panel;
        layout: vertical;
    }

    ForumHeader {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        color: $text;
        text-style: bold;
    }

    .title-bar {
        dock: top;
        height: auto;
        padding: 0 1;
        background: $primary;
        color: $text;
    }

    .search-bar {
        dock: top;
        height: auto;
        padding: 1;
        background: $surface;
        width: 1fr;
    }

    Input {
        margin: 0 1;
        width: 1fr;
    }

    .nav-bar {
        dock: top;
        height: auto;
        padding: 1;
        background: $surface;
    }

    Button {
        margin: 0 1;
        background: $accent;
        color: $text;
    }

    Button:hover {
        background: $primary;
        color: $text;
        text-style: bold;
    }

    Button:focus {
        background: $warning;
        color: $text;
    }

    DataTable {
        height: 1fr;
        margin: 0 1 1 1;
    }

    #posts-scroll {
        height: 1fr;
        border: round $accent;
        margin: 1;
        background: $panel;
    }

    .post-card {
        height: auto;
        padding: 1;
        margin: 0 0 1 0;
        background: $surface;
        border: solid $primary-darken-2;
    }

    .post-card.original {
        background: $primary-darken-3;
        border: double $accent;
    }

    .post-card.reply {
        background: $surface;
        border: solid $secondary-darken-2;
        margin-left: 2;
    }

    .post-author {
        color: $success;
        text-style: bold;
    }

    .post-time {
        color: $text-muted;
        text-style: italic;
    }

    .post-body {
        margin-top: 1;
        color: $text;
    }

    .post-quote {
        margin-top: 1;
        padding: 0 1;
        background: $panel;
        color: $text-muted;
        text-style: italic;
        border-left: thick $warning;
    }

    .thread-info {
        height: auto;
        padding: 1;
        margin: 0 1 1 1;
        background: $surface;
        border: round $accent;
    }

    .action-buttons {
        dock: bottom;
        height: auto;
        padding: 1;
        background: $boost;
    }

    .status-bar {
        dock: bottom;
        height: auto;
        padding: 0 1;
        background: $boost;
        color: $success;
        text-style: bold;
    }

    #list-view {
        height: 1fr;
        layout: vertical;
    }

    #thread-view {
        height: 1fr;
        layout: vertical;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("l", "show_list", "List Threads", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("?", "help", "Help", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.db = ForumDatabase()
        self.threads = []
        self.current_thread = None
        self.current_view = "list"
        self.selected_thread_id = None
        self.list_view = None
        self.thread_view = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield ForumHeader(id="header")

        # Navigation bar (always visible)
        with Horizontal(classes="nav-bar"):
            yield Input(
                placeholder="🔍 Search by title, author, or content...",
                id="search-input",
            )
            yield Button("🔎 Search", id="search-btn", variant="primary")
            yield Button("📝 All Threads", id="all-threads-btn", variant="default")

        # List View
        with Container(id="list-view"):
            yield Static("📋 Thread List", classes="title-bar")

            # Thread list table
            table = DataTable(id="thread-table", cursor_type="row")
            table.add_columns("🆔", "📌 Title", "✍️ Author", "💬 Last Updated")
            yield table

        # Thread Detail View
        with Container(id="thread-view"):
            yield Static("", id="thread-header", classes="thread-info")
            yield VerticalScroll(id="posts-scroll")

            with Horizontal(classes="action-buttons"):
                yield Button("⬅️ Back to List", id="back-btn")
                yield Button("🔄 Refresh Thread", id="refresh-thread-btn")

        yield Static("Ready! Press ? for help", classes="status-bar", id="status-bar")

    def on_mount(self) -> None:
        """Load initial thread list."""
        self.list_view = self.query_one("#list-view", Container)
        self.thread_view = self.query_one("#thread-view", Container)
        self.thread_view.display = False
        self.load_threads()

    def load_threads(self) -> None:
        """Load and display threads from database."""
        try:
            self.threads = self.db.list_threads(limit=50)
            self.update_thread_table()
            self.update_status(f"✨ Loaded {len(self.threads)} threads")
        except Exception as e:
            self.update_status(f"❌ Error loading threads: {e}")

    def update_thread_table(self) -> None:
        """Update the thread list table with current threads."""
        table = self.query_one("#thread-table", DataTable)
        table.clear()

        for thread in self.threads:
            thread_id = thread.get("id", "?")
            title = thread.get("title", "Untitled")[:50]
            author = thread.get("author", "Unknown")[:20]
            updated_at = thread.get("updated_at", "")

            try:
                dt = datetime.fromisoformat(updated_at)
                time_str = dt.strftime("%m/%d %H:%M")
            except (ValueError, TypeError):
                time_str = "?"

            table.add_row(str(thread_id), title, author, time_str, key=str(thread_id))

    def update_status(self, message: str) -> None:
        """Update the status bar."""
        status = self.query_one("#status-bar", Static)
        status.update(message)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle thread selection."""
        if event.row_key:
            thread_id = int(event.row_key.value)
            await self.view_thread(thread_id)

    async def view_thread(self, thread_id: int) -> None:
        """Display a specific thread with all its posts."""
        try:
            self.current_thread = self.db.read_thread(thread_id)
            if not self.current_thread:
                self.update_status("❌ Thread not found!")
                return

            thread_info = self.current_thread["thread"]
            posts = self.current_thread["posts"]

            # Update thread header
            header = self.query_one("#thread-header", Static)
            reply_count = len(posts)
            if reply_count == 0:
                post_info = "💬 1 post (no replies yet)"
            elif reply_count == 1:
                post_info = "💬 1 post + 1 reply"
            else:
                post_info = f"💬 1 post + {reply_count} replies"

            header_text = (
                f"📌 {thread_info['title']}\n"
                f"by ✍️ {thread_info['author']} | "
                f"Created: {thread_info['created_at'][:10]}\n"
                f"{post_info}"
            )
            header.update(header_text)

            # Get the posts scroll container and clear existing posts
            posts_scroll = self.query_one("#posts-scroll", VerticalScroll)
            await posts_scroll.remove_children()

            # Format timestamp helper
            def format_time(timestamp: str) -> str:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    return timestamp

            # Mount the original post
            original_post = PostCard(
                author=thread_info["author"],
                body=thread_info["body"],
                timestamp=format_time(thread_info["created_at"]),
                is_original=True,
            )
            await posts_scroll.mount(original_post)

            # Mount all replies
            for i, post in enumerate(posts):
                quoted_text = post.get("quoted_post_body")
                reply_card = PostCard(
                    author=post.get("author", "Unknown"),
                    body=post.get("body", ""),
                    timestamp=format_time(post.get("created_at", "")),
                    is_original=False,
                    post_number=i + 1,
                    quoted_text=quoted_text,
                )
                await posts_scroll.mount(reply_card)

            # Switch to thread view
            self.list_view.display = False
            self.thread_view.display = True

            self.current_view = "thread"
            self.selected_thread_id = thread_id
            self.update_status(f"📖 Viewing thread #{thread_id}: {thread_info['title'][:40]}")

        except Exception as e:
            self.update_status(f"❌ Error loading thread: {e}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id == "search-btn":
            self.action_search()
        elif button_id == "all-threads-btn":
            self.action_show_list()
        elif button_id == "back-btn":
            self.action_show_list()
        elif button_id == "refresh-thread-btn":
            if self.selected_thread_id:
                await self.view_thread(self.selected_thread_id)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle pressing Enter in the search input."""
        if event.input.id == "search-input":
            self.action_search()

    def action_search(self) -> None:
        """Search threads based on input."""
        try:
            search_input = self.query_one("#search-input", Input)
            query = search_input.value.strip()

            if not query:
                self.load_threads()
                self.update_status("✨ Showing all threads")
                return

            self.threads = self.db.search_threads(query=query, search_in="all", limit=50)
            self.update_thread_table()

            if self.threads:
                self.update_status(f"✨ Found {len(self.threads)} thread(s) matching '{query}'")
            else:
                self.update_status(
                    f"❌ No threads found matching '{query}' - try another search"
                )
        except Exception as e:
            self.update_status(f"❌ Search error: {str(e)}")

    def action_show_list(self) -> None:
        """Show the thread list view."""
        # Clear search and reload all threads
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        
        self.list_view.display = True
        self.thread_view.display = False

        self.current_view = "list"
        self.load_threads()
        self.update_status("✨ Showing all threads")

    async def action_refresh(self) -> None:
        """Refresh current view."""
        if self.current_view == "list":
            self.load_threads()
            self.update_status("✨ Refreshed thread list")
        elif self.current_view == "thread" and self.selected_thread_id:
            await self.view_thread(self.selected_thread_id)
            self.update_status("✨ Refreshed thread view")

    def action_help(self) -> None:
        """Show help message."""
        help_text = (
            "🆘 FORUM EXPLORER HELP\n\n"
            "Controls:\n"
            "  • Click threads to view details\n"
            "  • Search using the search bar\n"
            "  • 'All Threads' shows recent threads\n"
            "  • Press ⬅️ Back to return to list\n\n"
            "Keyboard:\n"
            "  L - List threads\n"
            "  R - Refresh current view\n"
            "  Q - Quit application\n"
            "  ? - Show this help\n\n"
            "Features:\n"
            "  ✨ View all forum threads\n"
            "  🔍 Search by title/author/content\n"
            "  📌 Read full thread discussions\n"
            "  💬 See post quotes and replies"
        )
        self.update_status(help_text)


def main():
    """Run the forum viewer application."""
    app = ForumViewer()
    app.run()


if __name__ == "__main__":
    main()
