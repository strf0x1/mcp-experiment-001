"""Configuration management for agents system."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


@dataclass
class ModelConfig:
    """Configuration for an LLM provider."""

    provider: str  # e.g., "anthropic"
    model: str  # e.g., "claude-3-5-haiku-20241022"
    api_key: str


@dataclass
class CycleConfig:
    """Configuration for the agent execution cycle."""

    cycle_interval: int = 300  # seconds between cycle starts (5 min)
    skip_probability: float = 0.2  # 20% chance an agent sits out
    min_delay: int = 30  # minimum seconds between agents
    max_delay: int = 120  # maximum seconds between agents
    max_tool_calls: int = 15  # max tool invocations per agent per run (prevent loops)


@dataclass
class ForumConfig:
    """Configuration for forum MCP server connection."""

    host: str = "localhost"
    port: int = 8000
    transport: str = "http"  # "http" or "sse"


@dataclass
class GrafitiConfig:
    """Configuration for Grafiti MCP server connection."""

    host: str = "localhost"
    port: int = 8001
    enabled: bool = True  # Whether to enable Grafiti integration


@dataclass
class UpdatesConfig:
    """Configuration for dynamic agent updates from git commits."""

    enabled: bool = True  # Whether to include updates section in prompts
    commit_limit: int = 15  # Number of commits to fetch from git
    display_limit: int = 10  # Maximum commits to show in prompt
    branch: str | None = None  # Branch to fetch from (None = auto-detect main)
    keywords: list[str] | None = None  # Keywords to filter (None = defaults)


@dataclass
class AppConfig:
    """Main application configuration."""

    model: ModelConfig
    cycle: CycleConfig = field(default_factory=CycleConfig)
    forum: ForumConfig = field(default_factory=ForumConfig)
    grafiti: GrafitiConfig = field(default_factory=GrafitiConfig)
    updates: UpdatesConfig = field(default_factory=UpdatesConfig)
    debug: bool = False
    data_dir: str = "./.agent_data"  # Directory for state, logs, etc.


def load_config() -> AppConfig:
    """Load configuration from environment variables.

    Returns:
        AppConfig: Application configuration instance

    Raises:
        ValueError: If required configuration is missing
    """
    # LLM Provider configuration
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model_name = os.getenv("LLM_MODEL", "claude-3-5-haiku-20241022")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is required for Anthropic provider"
        )

    model_config = ModelConfig(
        provider=provider,
        model=model_name,
        api_key=api_key,
    )

    # Cycle configuration
    cycle_config = CycleConfig(
        cycle_interval=int(os.getenv("CYCLE_INTERVAL", "300")),
        skip_probability=float(os.getenv("SKIP_PROBABILITY", "0.2")),
        min_delay=int(os.getenv("MIN_DELAY", "30")),
        max_delay=int(os.getenv("MAX_DELAY", "120")),
        max_tool_calls=int(os.getenv("MAX_TOOL_CALLS", "10")),
    )

    # Forum configuration
    forum_config = ForumConfig(
        host=os.getenv("FORUM_HOST", "localhost"),
        port=int(os.getenv("FORUM_PORT", "8000")),
        transport=os.getenv("FORUM_TRANSPORT", "http"),
    )

    # Grafiti configuration
    grafiti_config = GrafitiConfig(
        host=os.getenv("GRAFITI_HOST", "localhost"),
        port=int(os.getenv("GRAFITI_PORT", "8001")),
        enabled=os.getenv("GRAFITI_ENABLED", "true").lower() == "true",
    )

    # Updates configuration (for dynamic agent updates from git)
    keywords_env = os.getenv("UPDATES_KEYWORDS")
    updates_config = UpdatesConfig(
        enabled=os.getenv("UPDATES_ENABLED", "true").lower() == "true",
        commit_limit=int(os.getenv("UPDATES_COMMIT_LIMIT", "15")),
        display_limit=int(os.getenv("UPDATES_DISPLAY_LIMIT", "10")),
        branch=os.getenv("UPDATES_BRANCH") or None,
        keywords=keywords_env.split(",") if keywords_env else None,
    )

    # App configuration
    app_config = AppConfig(
        model=model_config,
        cycle=cycle_config,
        forum=forum_config,
        grafiti=grafiti_config,
        updates=updates_config,
        debug=os.getenv("DEBUG", "false").lower() == "true",
        data_dir=os.getenv("DATA_DIR", "./.agent_data"),
    )

    return app_config


# Singleton instance (lazy-loaded)
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get or create singleton config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

