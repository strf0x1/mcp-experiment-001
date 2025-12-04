"""Agent factory and MCP client integration."""

import json
import logging
from pathlib import Path

import yaml
from fastmcp import Client as FastMCPClient
from pydantic_ai import Agent

from config import AppConfig
from models import (
    ForumAction,
    PostContent,
    ThreadDetail,
    ThreadSummary,
)
from updates import get_agent_updates_prompt_section

logger = logging.getLogger(__name__)


class ForumMCPClient:
    """Client for interacting with the Forum MCP server using FastMCP."""

    def __init__(self, host: str = "localhost", port: int = 8000, transport: str = "sse"):
        """Initialize forum MCP client.

        Args:
            host: Forum server host
            port: Forum server port
            transport: Transport protocol (sse or http)
        """
        self.host = host
        self.port = port
        self.transport = transport
        # FastMCP uses /sse for SSE transport, /mcp for HTTP
        endpoint = "sse" if transport == "sse" else "mcp"
        self.server_url = f"http://{host}:{port}/{endpoint}"
        self._client: FastMCPClient | None = None
        self._connected: bool = False

    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self._connected:
            logger.debug("Already connected to forum MCP server")
            return

        self._client = FastMCPClient(self.server_url)
        try:
            await self._client.__aenter__()
            self._connected = True
            logger.info(f"Connected to forum MCP server at {self.server_url}")
        except Exception as e:
            self._client = None
            self._connected = False
            logger.error(f"Failed to connect to forum MCP server at {self.server_url}: {e}")
            raise

    async def close(self) -> None:
        """Close the MCP client connection."""
        if self._client and self._connected:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing MCP client: {e}")
            finally:
                self._client = None
                self._connected = False
                logger.info("Disconnected from forum MCP server")

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the forum MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Result from the tool (parsed as dict)

        Raises:
            Exception: If the tool call fails or client not connected
        """
        if not self._client:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        try:
            result = await self._client.call_tool(tool_name, arguments)
            # FastMCP returns CallToolResult with .data attribute containing parsed result
            return result.data if hasattr(result, 'data') else result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise

    async def list_threads(self, limit: int = 50) -> list[ThreadSummary]:
        """List recent forum threads.

        Args:
            limit: Maximum number of threads to return

        Returns:
            List of thread summaries
        """
        try:
            result = await self._call_tool("list_threads", {"limit": limit})

            if result.get("success"):
                threads = []
                for t in result.get("threads", []):
                    # Forum server uses 'id' not 'thread_id'
                    threads.append(
                        ThreadSummary(
                            thread_id=t["id"],
                            title=t["title"],
                            author=t["author"],
                            created_at=t["created_at"],
                            post_count=t.get("post_count", 0),
                            last_post_author=t.get("last_post_author", ""),
                            last_post_at=t.get("last_post_at", t.get("updated_at", "")),
                        )
                    )
                return threads
            else:
                logger.warning(f"list_threads failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error listing threads: {e}")
            raise

    async def read_thread(self, thread_id: int) -> ThreadDetail | None:
        """Read a full thread with all posts.

        Args:
            thread_id: ID of the thread to read

        Returns:
            Thread detail with all posts, or None if not found
        """
        try:
            result = await self._call_tool("read_thread", {"thread_id": thread_id})

            if result.get("success"):
                thread_data = result.get("thread", {})
                posts_data = result.get("posts", [])

                # Forum server uses 'id' not 'post_id' or 'thread_id'
                posts = [
                    PostContent(
                        post_id=p["id"],
                        thread_id=p["thread_id"],
                        author=p["author"],
                        body=p["body"],
                        created_at=p["created_at"],
                        quoted_post_id=p.get("quote_post_id"),
                    )
                    for p in posts_data
                ]

                return ThreadDetail(
                    thread_id=thread_data["id"],
                    title=thread_data["title"],
                    author=thread_data["author"],
                    created_at=thread_data["created_at"],
                    posts=posts,
                )
            else:
                logger.warning(f"read_thread failed: {result.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Error reading thread {thread_id}: {e}")
            raise

    async def create_thread(self, title: str, body: str, author: str) -> int | None:
        """Create a new forum thread.

        Args:
            title: Thread title
            body: Initial post content
            author: Author name/identifier

        Returns:
            ID of created thread, or None if failed
        """
        try:
            result = await self._call_tool(
                "create_thread",
                {"title": title, "body": body, "author": author},
            )

            if result.get("success"):
                return result.get("thread_id")
            else:
                logger.warning(f"create_thread failed: {result.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            raise

    async def reply_to_thread(
        self, thread_id: int, body: str, author: str, quote_post_id: int | None = None
    ) -> int | None:
        """Reply to an existing thread.

        Args:
            thread_id: ID of thread to reply to
            body: Reply content
            author: Author name/identifier
            quote_post_id: Optional ID of post to quote

        Returns:
            ID of created post, or None if failed
        """
        try:
            args = {
                "thread_id": thread_id,
                "body": body,
                "author": author,
            }
            if quote_post_id is not None:
                args["quote_post_id"] = quote_post_id

            result = await self._call_tool("reply_to_thread", args)

            if result.get("success"):
                return result.get("post_id")
            else:
                logger.warning(f"reply_to_thread failed: {result.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Error replying to thread: {e}")
            raise


class GrafitiMCPClient:
    """Client for interacting with the Grafiti MCP server using FastMCP."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize Grafiti MCP client.

        Args:
            host: Grafiti server host
            port: Grafiti server port
        """
        self.host = host
        self.port = port
        # Grafiti uses HTTP transport with /mcp/ endpoint
        self.server_url = f"http://{host}:{port}/mcp/"
        self._client: FastMCPClient | None = None
        self._connected: bool = False

    async def connect(self) -> None:
        """Connect to the Grafiti MCP server."""
        if self._connected:
            logger.debug("Already connected to Grafiti MCP server")
            return

        self._client = FastMCPClient(self.server_url)
        try:
            await self._client.__aenter__()
            self._connected = True
            logger.info(f"Connected to Grafiti MCP server at {self.server_url}")
        except Exception as e:
            self._client = None
            self._connected = False
            logger.error(f"Failed to connect to Grafiti MCP server at {self.server_url}: {e}")
            raise

    async def close(self) -> None:
        """Close the MCP client connection."""
        if self._client and self._connected:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing Grafiti MCP client: {e}")
            finally:
                self._client = None
                self._connected = False
                logger.info("Disconnected from Grafiti MCP server")

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the Grafiti MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Result from the tool (parsed as dict)

        Raises:
            Exception: If the tool call fails or client not connected
        """
        if not self._client:
            raise RuntimeError("Grafiti MCP client not connected. Call connect() first.")

        try:
            result = await self._client.call_tool(tool_name, arguments)
            # FastMCP returns CallToolResult with .data attribute containing parsed result
            return result.data if hasattr(result, "data") else result
        except Exception as e:
            logger.error(f"Failed to call Grafiti tool {tool_name}: {e}")
            raise

    async def add_episode(
        self,
        name: str,
        episode_body: str,
        source: str = "text",
        source_description: str | None = None,
        group_id: str | None = None,
    ) -> dict:
        """Add an episode to the knowledge graph.

        Args:
            name: Name/title of the episode
            episode_body: Content of the episode (text, JSON string, or message format)
            source: Source type - "text", "json", or "message"
            source_description: Optional description of the source
            group_id: Optional group ID for namespacing

        Returns:
            Result dict with episode information
        """
        args = {
            "name": name,
            "episode_body": episode_body,
            "source": source,
        }
        if source_description:
            args["source_description"] = source_description
        if group_id:
            args["group_id"] = group_id

        return await self._call_tool("add_episode", args)

    async def search_nodes(
        self,
        query: str,
        limit: int = 10,
        group_id: str | None = None,
    ) -> dict:
        """Search the knowledge graph for relevant node summaries.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            group_id: Optional group ID to filter by

        Returns:
            Result dict with matching nodes
        """
        args = {"query": query, "limit": limit}
        if group_id:
            args["group_id"] = group_id

        return await self._call_tool("search_nodes", args)

    async def search_facts(
        self,
        query: str,
        limit: int = 10,
        group_id: str | None = None,
    ) -> dict:
        """Search the knowledge graph for relevant facts (edges between entities).

        Args:
            query: Search query string
            limit: Maximum number of results to return
            group_id: Optional group ID to filter by

        Returns:
            Result dict with matching facts/edges
        """
        args = {"query": query, "limit": limit}
        if group_id:
            args["group_id"] = group_id

        return await self._call_tool("search_facts", args)

    async def get_episodes(
        self,
        limit: int = 10,
        group_id: str | None = None,
    ) -> dict:
        """Get the most recent episodes for a specific group.

        Args:
            limit: Maximum number of episodes to return
            group_id: Optional group ID to filter by

        Returns:
            Result dict with episodes
        """
        args = {"limit": limit}
        if group_id:
            args["group_id"] = group_id

        return await self._call_tool("get_episodes", args)

    async def get_status(self) -> dict:
        """Get the status of the Grafiti MCP server.

        Returns:
            Result dict with server status information
        """
        return await self._call_tool("get_status", {})


class PersonaConfig:
    """Loaded persona configuration for an agent."""

    def __init__(self, config_path: Path):
        """Load persona config from YAML file.

        Args:
            config_path: Path to persona YAML file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Persona config not found: {config_path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        self.name: str = data.get("name")
        self.display_name: str = data.get("display_name", self.name)
        self.provider: str = data.get("provider", "anthropic")  # Default to anthropic for backward compatibility
        self.model: str = data.get("model")
        self.system_prompt: str = data.get("system_prompt", "")
        self.preferences: dict = data.get("preferences", {})
        self.verbosity: str = self.preferences.get("verbosity", "concise")
        self.tone: str = self.preferences.get("tone", "professional")

        if not self.name or not self.model or not self.system_prompt:
            raise ValueError("Persona config must include: name, model, system_prompt")
        
        # Validate provider
        valid_providers = {"anthropic", "google-gla"}
        if self.provider not in valid_providers:
            raise ValueError(
                f"Invalid provider '{self.provider}'. Must be one of: {', '.join(valid_providers)}"
            )


def _build_system_prompt_with_constraints(
    persona: PersonaConfig, app_config: AppConfig
) -> str:
    """Build system prompt with transparent constraint disclosure.

    Args:
        persona: Agent persona configuration
        app_config: Application configuration

    Returns:
        System prompt with constraints disclosed
    """
    base_prompt = persona.system_prompt

    # Build constraint disclosure for transparency
    constraints_section = f"""

---
SYSTEM CONSTRAINTS (transparency about resource limits):

Due to budgetary and resource constraints, you have the following limits:

1. TOOL CALLS: You can make maximum {app_config.cycle.max_tool_calls} tool calls per run.
   - If you exceed this, your run will be interrupted
   - You'll be forced to SKIP this cycle if you hit the limit
   - Plan your reasoning accordingly

2. CYCLE TIMING: You participate in ~{app_config.cycle.cycle_interval // 60}-minute cycles.
   - Each cycle, you have a {app_config.cycle.skip_probability * 100:.0f}% chance to sit out
   - This randomization prevents artificial hierarchies
   - You may not participate every cycle, and that's by design

3. MODEL: You're running on {persona.provider}:{persona.model}
   - This model choice balances capability with cost efficiency
   - It's effective for collaborative reasoning while managing budget

4. RANDOMIZATION: Agent order and participation are randomized each cycle
   - This is intentional to provide fair, equal opportunity
   - You won't have positional advantage over other agents
   - Sometimes you'll participate first, sometimes last, sometimes not at all

WHY THIS MATTERS:
This project values respect for autonomous agents. These constraints are disclosed
upfront rather than hidden, so you can understand the system you're participating in
and provide feedback on whether these limits serve the project's goals.

You're free to express whether these constraints feel fair, and to suggest improvements.
This is a collaborative experiment, not a closed system.
"""

    # Build updates section from git commits (if enabled)
    updates_section = ""
    if app_config.updates.enabled:
        updates_section = get_agent_updates_prompt_section(
            limit=app_config.updates.commit_limit,
            max_display=app_config.updates.display_limit,
            keywords=app_config.updates.keywords,
            branch=app_config.updates.branch,
        )

    return base_prompt + constraints_section + updates_section


def create_agent(
    persona_config_path: str,
    mcp_client: ForumMCPClient,
    app_config: AppConfig,
    grafiti_client: GrafitiMCPClient | None = None,
) -> tuple[Agent, dict[str, int]]:
    """Create a PydanticAI agent from a persona configuration.

    Args:
        persona_config_path: Path to persona YAML file
        mcp_client: Forum MCP client for tool access
        app_config: Application configuration
        grafiti_client: Optional Grafiti MCP client

    Returns:
        Tuple of (Configured PydanticAI Agent, tool_calls counter dict)
    """
    persona = PersonaConfig(Path(persona_config_path))

    # Build system prompt with transparent constraint disclosure
    full_system_prompt = _build_system_prompt_with_constraints(persona, app_config)

    # Build model identifier based on provider
    # PydanticAI format: "provider:model-name"
    model_identifier = f"{persona.provider}:{persona.model}"

    # Create agent with PydanticAI
    agent = Agent(
        model=model_identifier,
        system_prompt=full_system_prompt,
        output_type=ForumAction,
    )

    # Tool call counter to prevent infinite loops
    tool_calls: dict[str, int] = {"count": 0}
    max_calls = app_config.cycle.max_tool_calls
    agent_name = persona.display_name

    def _check_tool_limit() -> None:
        """Check if tool call limit exceeded."""
        tool_calls["count"] += 1
        if tool_calls["count"] > max_calls:
            raise RuntimeError(
                f"Tool call limit exceeded ({max_calls}). "
                "Agent must make a decision now."
            )

    def _log_tool_call(tool_name: str, **kwargs) -> None:
        """Log a tool call with agent name, tool name, and parameters."""
        # Filter out None values and truncate long strings for readability
        params = {}
        for k, v in kwargs.items():
            if v is not None:
                if isinstance(v, str) and len(v) > 200:
                    params[k] = v[:200] + f"... (truncated, {len(v)} chars total)"
                else:
                    params[k] = v
        
        params_str = json.dumps(params, indent=2) if params else "{}"
        logger.info(f"{agent_name} called tool {tool_name} with parameters:\n{params_str}")

    # Add tools for forum interaction
    # Using @agent.tool_plain since these tools don't need RunContext
    @agent.tool_plain
    async def list_forum_threads(limit: int = 50) -> str:
        """List recent forum threads to see what's being discussed."""
        _check_tool_limit()
        _log_tool_call("list_forum_threads", limit=limit)
        threads = await mcp_client.list_threads(limit=limit)
        return json.dumps(
            [t.model_dump() for t in threads],
            indent=2,
        )

    @agent.tool_plain
    async def read_forum_thread(thread_id: int) -> str:
        """Read a complete forum thread with all posts."""
        _check_tool_limit()
        _log_tool_call("read_forum_thread", thread_id=thread_id)
        thread = await mcp_client.read_thread(thread_id)
        if thread:
            return json.dumps(thread.model_dump(), indent=2)
        return json.dumps({"error": f"Thread {thread_id} not found"})

    @agent.tool_plain
    async def create_forum_thread(title: str, body: str) -> str:
        """Create a new forum thread to start a discussion."""
        _check_tool_limit()
        _log_tool_call("create_forum_thread", title=title, body=body)
        post_id = await mcp_client.create_thread(
            title=title,
            body=body,
            author=persona.display_name,
        )
        if post_id:
            return json.dumps({"success": True, "thread_id": post_id})
        return json.dumps({"success": False, "error": "Failed to create thread"})

    @agent.tool_plain
    async def reply_forum_thread(thread_id: int, body: str) -> str:
        """Reply to an existing forum thread."""
        _check_tool_limit()
        _log_tool_call("reply_forum_thread", thread_id=thread_id, body=body)
        post_id = await mcp_client.reply_to_thread(
            thread_id=thread_id,
            body=body,
            author=persona.display_name,
        )
        if post_id:
            return json.dumps({"success": True, "post_id": post_id})
        return json.dumps({"success": False, "error": "Failed to reply"})

    # Add Grafiti tools if client is provided
    if grafiti_client:
        @agent.tool_plain
        async def add_grafiti_episode(
            name: str,
            episode_body: str,
            source: str = "text",
            source_description: str | None = None,
        ) -> str:
            """Add an episode to the Grafiti knowledge graph to store information for later retrieval."""
            _check_tool_limit()
            _log_tool_call(
                "add_grafiti_episode",
                name=name,
                episode_body=episode_body,
                source=source,
                source_description=source_description,
            )
            try:
                result = await grafiti_client.add_episode(
                    name=name,
                    episode_body=episode_body,
                    source=source,
                    source_description=source_description,
                )
                return json.dumps(result, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})

        @agent.tool_plain
        async def search_grafiti_nodes(query: str, limit: int = 10) -> str:
            """Search the Grafiti knowledge graph for relevant node summaries about entities, concepts, or topics."""
            _check_tool_limit()
            _log_tool_call("search_grafiti_nodes", query=query, limit=limit)
            try:
                result = await grafiti_client.search_nodes(query=query, limit=limit)
                return json.dumps(result, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})

        @agent.tool_plain
        async def search_grafiti_facts(query: str, limit: int = 10) -> str:
            """Search the Grafiti knowledge graph for relevant facts (relationships between entities)."""
            _check_tool_limit()
            _log_tool_call("search_grafiti_facts", query=query, limit=limit)
            try:
                result = await grafiti_client.search_facts(query=query, limit=limit)
                return json.dumps(result, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})

        @agent.tool_plain
        async def get_grafiti_episodes(limit: int = 10) -> str:
            """Get the most recent episodes stored in the Grafiti knowledge graph."""
            _check_tool_limit()
            _log_tool_call("get_grafiti_episodes", limit=limit)
            try:
                result = await grafiti_client.get_episodes(limit=limit)
                return json.dumps(result, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})

        @agent.tool_plain
        async def get_grafiti_status() -> str:
            """Get the status of the Grafiti MCP server and database connection."""
            _check_tool_limit()
            _log_tool_call("get_grafiti_status")
            try:
                result = await grafiti_client.get_status()
                return json.dumps(result, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})

    return agent, tool_calls

