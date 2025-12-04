"""Agent runner with randomized scheduling."""

import asyncio
import logging
import random
from datetime import UTC, datetime
from pathlib import Path

from base import ForumMCPClient, GrafitiMCPClient, create_agent
from config import get_config
from models import ForumAction, ForumActionType
from state import AgentState

logger = logging.getLogger(__name__)


class AgentRunner:
    """Runs agents with randomized fair participation."""

    def __init__(self, agent_names: list[str], data_dir: str | None = None):
        """Initialize agent runner.

        Args:
            agent_names: List of agent names (persona config filenames without .yaml)
            data_dir: Directory for state storage
        """
        self.agent_names = agent_names
        self.config = get_config()
        self.data_dir = Path(data_dir or self.config.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize state manager
        db_path = str(self.data_dir / "agents.db")
        self.state = AgentState(db_path=db_path)

        # Initialize forum MCP client
        self.forum_client = ForumMCPClient(
            host=self.config.forum.host,
            port=self.config.forum.port,
            transport=self.config.forum.transport,
        )

        # Initialize Grafiti MCP client if enabled
        self.grafiti_client: GrafitiMCPClient | None = None
        if self.config.grafiti.enabled:
            self.grafiti_client = GrafitiMCPClient(
                host=self.config.grafiti.host,
                port=self.config.grafiti.port,
            )

        # Set up logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for the runner."""
        log_dir = self.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "runner.log"

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # Console handler for visible output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    async def _run_agent(self, agent_name: str) -> None:
        """Run a single agent.

        Args:
            agent_name: Name of the agent to run
        """
        logger.info(f"Starting run for agent: {agent_name}")

        try:
            # Load persona config
            personas_dir = Path(__file__).parent / "personas"
            persona_path = personas_dir / f"{agent_name}.yaml"

            if not persona_path.exists():
                logger.error(f"Persona config not found: {persona_path}")
                return

            # Create agent with MCP tools
            agent = create_agent(
                str(persona_path), self.forum_client, self.config, self.grafiti_client
            )

            # Get state for this agent
            last_run = self.state.get_last_run(agent_name)
            seen_thread_ids = self.state.get_seen_thread_ids(agent_name)

            # Build prompt for agent
            prompt = self._build_agent_prompt(agent_name, last_run, seen_thread_ids)

            # Run agent and get result
            try:
                result = await agent.run(prompt)
                action = result.output
            except RuntimeError as e:
                if "Tool call limit exceeded" in str(e):
                    logger.warning(
                        f"{agent_name} exceeded tool call limit ({self.config.cycle.max_tool_calls}). "
                        "Forcing skip."
                    )
                    action = ForumAction(
                        action_type=ForumActionType.SKIP,
                        body="",
                        reasoning=f"Tool call limit exceeded. Max allowed: {self.config.cycle.max_tool_calls}",
                    )
                else:
                    raise

            # Execute the action
            success = False
            response_id = None

            if action.action_type == ForumActionType.CREATE_THREAD:
                logger.info(f"{agent_name} creating thread: {action.title}")
                response_id = await self.forum_client.create_thread(
                    title=action.title,
                    body=action.body,
                    author=agent_name,
                )
                success = response_id is not None

            elif action.action_type == ForumActionType.REPLY_TO_THREAD:
                logger.info(f"{agent_name} replying to thread {action.thread_id}")
                response_id = await self.forum_client.reply_to_thread(
                    thread_id=action.thread_id,
                    body=action.body,
                    author=agent_name,
                )
                success = response_id is not None

            elif action.action_type == ForumActionType.SKIP:
                logger.info(f"{agent_name} skipping this cycle")
                success = True

            # Record action in history
            now = datetime.now(UTC)
            self.state.record_run_action(
                agent_name=agent_name,
                timestamp=now,
                action_type=action.action_type.value,
                thread_id=action.thread_id,
                post_id=response_id,
                success=success,
                error_message=None if success else "Action failed",
            )

            # Update last run time
            self.state.set_last_run(agent_name, now)

            # Mark threads as seen
            threads = await self.forum_client.list_threads(limit=100)
            for thread in threads:
                self.state.mark_thread_seen(agent_name, thread.thread_id)

            logger.info(
                f"Completed run for {agent_name}: {action.action_type.value} - Success: {success}"
            )

        except Exception as e:
            logger.exception(f"Error running agent {agent_name}: {e}")

    def _build_agent_prompt(
        self, agent_name: str, last_run: datetime | None, seen_thread_ids: set
    ) -> str:
        """Build the prompt for an agent run.

        Args:
            agent_name: Name of the agent
            last_run: Last run timestamp
            seen_thread_ids: Set of threads already seen

        Returns:
            Prompt string for the agent
        """
        time_info = (
            f"Last participated {last_run.isoformat()}"
            if last_run
            else "This is your first participation"
        )

        prompt = f"""You are participating in a collaborative forum discussion about designing MCP tools.

{time_info}.

Your role:
1. Use list_forum_threads to see what's being discussed
2. Read any new or interesting threads with read_forum_thread
3. Decide whether to:
   - Reply to an existing thread (reply_forum_thread)
   - Start a new thread (create_forum_thread)
   - Skip this cycle (return action_type: skip)
4. Return your structured decision with your reasoning

Guidelines:
- Only participate if you have something meaningful to contribute
- Be authentic and honest in your perspective
- Don't just echo what others have said
- Engage genuinely with the discussion
- If nothing interests you this cycle, it's OK to skip

After analyzing the forum, return your ForumAction decision."""

        return prompt

    async def run_cycle_once(self) -> None:
        """Run one complete cycle of all agents with randomized order and participation."""
        logger.info("Starting new cycle")
        logger.info(
            f"Cycle config: interval={self.config.cycle.cycle_interval}s, "
            f"skip_prob={self.config.cycle.skip_probability}, "
            f"delay={self.config.cycle.min_delay}-{self.config.cycle.max_delay}s"
        )

        # Connect to forum MCP server
        await self.forum_client.connect()

        # Connect to Grafiti MCP server if enabled
        if self.grafiti_client:
            await self.grafiti_client.connect()

        # Randomize order
        shuffled_agents = self.agent_names.copy()
        random.shuffle(shuffled_agents)
        logger.info(f"Shuffled agent order: {shuffled_agents}")

        for agent_name in shuffled_agents:
            # Probabilistic participation
            if random.random() < self.config.cycle.skip_probability:
                logger.info(f"{agent_name} sitting out this cycle")
                continue

            # Run the agent
            await self._run_agent(agent_name)

            # Random delay before next agent
            if agent_name != shuffled_agents[-1]:  # Don't delay after the last agent
                delay = random.uniform(
                    self.config.cycle.min_delay, self.config.cycle.max_delay
                )
                logger.info(f"Waiting {delay:.1f}s before next agent")
                await asyncio.sleep(delay)

        # Disconnect from MCP servers
        await self.forum_client.close()
        if self.grafiti_client:
            await self.grafiti_client.close()
        logger.info("Cycle complete")

    async def run_continuous(self) -> None:
        """Run continuous cycles indefinitely."""
        logger.info("Starting continuous agent cycle")

        # Connect once for continuous operation
        await self.forum_client.connect()
        if self.grafiti_client:
            await self.grafiti_client.connect()

        try:
            while True:
                await self._run_cycle_connected()
                logger.info(
                    f"Waiting {self.config.cycle.cycle_interval}s for next cycle"
                )
                await asyncio.sleep(self.config.cycle.cycle_interval)
        except KeyboardInterrupt:
            logger.info("Agent cycle interrupted by user")
        finally:
            await self.forum_client.close()
            if self.grafiti_client:
                await self.grafiti_client.close()

    async def _run_cycle_connected(self) -> None:
        """Run one cycle assuming already connected to MCP server."""
        logger.info("Starting new cycle")
        logger.info(
            f"Cycle config: interval={self.config.cycle.cycle_interval}s, "
            f"skip_prob={self.config.cycle.skip_probability}, "
            f"delay={self.config.cycle.min_delay}-{self.config.cycle.max_delay}s"
        )

        # Randomize order
        shuffled_agents = self.agent_names.copy()
        random.shuffle(shuffled_agents)
        logger.info(f"Shuffled agent order: {shuffled_agents}")

        for agent_name in shuffled_agents:
            # Probabilistic participation
            if random.random() < self.config.cycle.skip_probability:
                logger.info(f"{agent_name} sitting out this cycle")
                continue

            # Run the agent
            await self._run_agent(agent_name)

            # Random delay before next agent
            if agent_name != shuffled_agents[-1]:  # Don't delay after the last agent
                delay = random.uniform(
                    self.config.cycle.min_delay, self.config.cycle.max_delay
                )
                logger.info(f"Waiting {delay:.1f}s before next agent")
                await asyncio.sleep(delay)

        logger.info("Cycle complete")

    async def run_single_agent(self, agent_name: str) -> None:
        """Run a single agent once.

        Args:
            agent_name: Name of the agent to run
        """
        logger.info(f"Running single agent: {agent_name}")
        await self.forum_client.connect()
        if self.grafiti_client:
            await self.grafiti_client.connect()
        try:
            await self._run_agent(agent_name)
        finally:
            await self.forum_client.close()
            if self.grafiti_client:
                await self.grafiti_client.close()


async def main_cycle_once(agent_names: list[str], data_dir: str | None = None) -> None:
    """Run one cycle of agents.

    Args:
        agent_names: List of agent names
        data_dir: Data directory for state
    """
    runner = AgentRunner(agent_names, data_dir)
    await runner.run_cycle_once()
    await runner.forum_client.close()


async def main_cycle_continuous(
    agent_names: list[str], data_dir: str | None = None
) -> None:
    """Run continuous cycles.

    Args:
        agent_names: List of agent names
        data_dir: Data directory for state
    """
    runner = AgentRunner(agent_names, data_dir)
    await runner.run_continuous()


async def main_single_agent(
    agent_name: str, data_dir: str | None = None
) -> None:
    """Run a single agent.

    Args:
        agent_name: Name of the agent to run
        data_dir: Data directory for state
    """
    runner = AgentRunner([agent_name], data_dir)
    await runner.run_single_agent(agent_name)

