#!/usr/bin/env python3
"""Colorful Textual CLI viewer for forum threads - fun interface for browsing discussions."""

from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Input,
    Label,
    Static,
    TextArea,
)

from database import ForumDatabase


class NewThreadScreen(ModalScreen[dict | None]):
    """Modal screen for creating a new thread."""

    CSS = """
    NewThreadScreen {
        align: center middle;
    }

    #new-thread-dialog {
        width: 70;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: thick $accent;
    }

    #new-thread-dialog Label {
        margin-top: 1;
        color: $text;
    }

    #new-thread-dialog Input {
        margin-bottom: 1;
        width: 100%;
    }

    #new-thread-dialog TextArea {
        height: 10;
        margin-bottom: 1;
        width: 100%;
    }

    #new-thread-dialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #new-thread-dialog .button-row {
        margin-top: 1;
        align: center middle;
        height: auto;
    }

    #new-thread-dialog Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="new-thread-dialog"):
            yield Static("📝 Create New Thread", classes="dialog-title")
            yield Label("Author:")
            yield Input(placeholder="Your name...", id="author-input")
            yield Label("Title:")
            yield Input(placeholder="Thread title...", id="title-input")
            yield Label("Body:")
            yield TextArea(id="body-input")
            with Horizontal(classes="button-row"):
                yield Button("✅ Create", id="create-btn", variant="success")
                yield Button("❌ Cancel", id="cancel-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def action_submit(self) -> None:
        author = self.query_one("#author-input", Input).value.strip()
        title = self.query_one("#title-input", Input).value.strip()
        body = self.query_one("#body-input", TextArea).text.strip()

        if not author or not title or not body:
            return  # Don't submit if fields are empty

        self.dismiss({"author": author, "title": title, "body": body})

    def action_cancel(self) -> None:
        self.dismiss(None)


class ReplyScreen(ModalScreen[dict | None]):
    """Modal screen for replying to a thread."""

    CSS = """
    ReplyScreen {
        align: center middle;
    }

    #reply-dialog {
        width: 70;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: thick $accent;
    }

    #reply-dialog Label {
        margin-top: 1;
        color: $text;
    }

    #reply-dialog Input {
        margin-bottom: 1;
        width: 100%;
    }

    #reply-dialog TextArea {
        height: 12;
        margin-bottom: 1;
        width: 100%;
    }

    #reply-dialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #reply-dialog .thread-context {
        background: $panel;
        padding: 1;
        margin-bottom: 1;
        color: $text-muted;
    }

    #reply-dialog .button-row {
        margin-top: 1;
        align: center middle;
        height: auto;
    }

    #reply-dialog Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, thread_title: str, thread_id: int):
        super().__init__()
        self.thread_title = thread_title
        self.thread_id = thread_id

    def compose(self) -> ComposeResult:
        with Vertical(id="reply-dialog"):
            yield Static("💬 Reply to Thread", classes="dialog-title")
            yield Static(f"📌 {self.thread_title[:50]}", classes="thread-context")
            yield Label("Author:")
            yield Input(placeholder="Your name...", id="author-input")
            yield Label("Reply:")
            yield TextArea(id="body-input")
            with Horizontal(classes="button-row"):
                yield Button("✅ Post Reply", id="reply-btn", variant="success")
                yield Button("❌ Cancel", id="cancel-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "reply-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def action_submit(self) -> None:
        author = self.query_one("#author-input", Input).value.strip()
        body = self.query_one("#body-input", TextArea).text.strip()

        if not author or not body:
            return  # Don't submit if fields are empty

        self.dismiss({"author": author, "body": body, "thread_id": self.thread_id})

    def action_cancel(self) -> None:
        self.dismiss(None)


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
            header = "[b]📝 Original Post[/b]"
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
        Binding("n", "new_thread", "New Thread", show=True),
        Binding("p", "reply", "Reply", show=True),
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
            with Horizontal(classes="title-bar"):
                yield Static("📋 Thread List")
                yield Button("➕ New Thread", id="new-thread-btn", variant="success")

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
                yield Button("💬 Reply", id="reply-btn", variant="success")
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
        elif button_id == "new-thread-btn":
            await self.action_new_thread()
        elif button_id == "reply-btn":
            await self.action_reply()

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
            "  N - Create new thread\n"
            "  P - Reply to current thread\n"
            "  Q - Quit application\n"
            "  ? - Show this help\n\n"
            "Features:\n"
            "  ✨ View all forum threads\n"
            "  🔍 Search by title/author/content\n"
            "  📌 Read full thread discussions\n"
            "  💬 See post quotes and replies\n"
            "  📝 Create new threads\n"
            "  💬 Reply to discussions"
        )
        self.update_status(help_text)

    def action_new_thread(self) -> None:
        """Open the new thread modal."""
        self.push_screen(NewThreadScreen(), callback=self._on_new_thread_result)

    def _on_new_thread_result(self, result: dict | None) -> None:
        """Handle result from new thread modal."""
        if result:
            try:
                thread_id = self.db.create_thread(
                    title=result["title"],
                    body=result["body"],
                    author=result["author"],
                )
                self.update_status(f"✅ Thread created! ID: {thread_id}")
                self.load_threads()
                # View the new thread - schedule it as a callback
                self.call_later(self._go_to_thread, thread_id)
            except Exception as e:
                self.update_status(f"❌ Error creating thread: {e}")

    def _go_to_thread(self, thread_id: int) -> None:
        """Navigate to a thread (scheduled callback)."""
        # Use set_timer to allow the UI to settle before navigating
        self.set_timer(0.1, lambda: self._do_view_thread(thread_id))

    def _do_view_thread(self, thread_id: int) -> None:
        """Actually view the thread."""
        import asyncio
        asyncio.create_task(self.view_thread(thread_id))

    def action_reply(self) -> None:
        """Open the reply modal for the current thread."""
        if self.current_view != "thread" or not self.current_thread:
            self.update_status("❌ Open a thread first to reply (press P in thread view)")
            return

        thread_info = self.current_thread["thread"]
        self.push_screen(
            ReplyScreen(thread_title=thread_info["title"], thread_id=thread_info["id"]),
            callback=self._on_reply_result,
        )

    def _on_reply_result(self, result: dict | None) -> None:
        """Handle result from reply modal."""
        if result:
            try:
                post_id = self.db.create_post(
                    thread_id=result["thread_id"],
                    body=result["body"],
                    author=result["author"],
                )
                self.update_status(f"✅ Reply posted! Post ID: {post_id}")
                # Refresh the thread view
                self.call_later(self._go_to_thread, result["thread_id"])
            except Exception as e:
                self.update_status(f"❌ Error posting reply: {e}")


def main():
    """Run the forum viewer application."""
    app = ForumViewer()
    app.run()


if __name__ == "__main__":
    main()
