"""Command-line interface for agent orchestration."""

import asyncio
import sys
from pathlib import Path

import click

from runner import main_cycle_continuous, main_cycle_once, main_single_agent


def get_available_agents() -> list[str]:
    """Get list of available agent personas.

    Returns:
        List of agent names (persona config names without .yaml)
    """
    personas_dir = Path(__file__).parent / "personas"
    if not personas_dir.exists():
        return []

    agents = []
    for yaml_file in personas_dir.glob("*.yaml"):
        agents.append(yaml_file.stem)

    return sorted(agents)


@click.group()
def cli() -> None:
    """Agent orchestration CLI."""
    pass


@cli.command()
@click.option(
    "--agent",
    "-a",
    multiple=True,
    help="Agent name(s) to run. If not specified, runs all available agents.",
)
@click.option(
    "--data-dir",
    default="./.agent_data",
    help="Directory for agent data (state, logs)",
)
def run_once(agent: tuple, data_dir: str) -> None:
    """Run one complete cycle of agents.

    If no agents specified, runs all available agents in randomized order.
    """
    agents_to_run = list(agent) if agent else get_available_agents()

    if not agents_to_run:
        click.echo("No agents available. Create persona YAML files in personas/", err=True)
        sys.exit(1)

    click.echo(f"Running cycle with agents: {', '.join(agents_to_run)}")

    asyncio.run(main_cycle_once(agents_to_run, data_dir))
    click.echo("Cycle complete")


@cli.command()
@click.option(
    "--agent",
    "-a",
    multiple=True,
    help="Agent name(s) to run. If not specified, runs all available agents.",
)
@click.option(
    "--interval",
    type=int,
    default=None,
    help="Cycle interval in seconds (overrides CYCLE_INTERVAL env var)",
)
@click.option(
    "--skip-prob",
    type=float,
    default=None,
    help="Skip probability (0-1, overrides SKIP_PROBABILITY env var)",
)
@click.option(
    "--data-dir",
    default="./.agent_data",
    help="Directory for agent data (state, logs)",
)
def run_cycle(agent: tuple, interval: int, skip_prob: float, data_dir: str) -> None:
    """Run continuous agent cycles.

    Agents participate in randomized order each cycle. This will run indefinitely
    until interrupted (Ctrl+C).

    Configuration:
    - Each cycle, agents shuffle into random order
    - Each agent has a probabilistic chance to sit out (default 20%)
    - Random delays between agents simulate real response times
    - Cycle interval (default 5 min) controls time between cycles

    See .agents/CYCLE_DESIGN.md for full scheduling documentation.
    """
    agents_to_run = list(agent) if agent else get_available_agents()

    if not agents_to_run:
        click.echo("No agents available. Create persona YAML files in personas/", err=True)
        sys.exit(1)

    click.echo(f"Starting continuous cycle with agents: {', '.join(agents_to_run)}")
    click.echo("Press Ctrl+C to stop")

    # TODO: Override config values if provided via CLI
    # For now, uses env vars

    asyncio.run(main_cycle_continuous(agents_to_run, data_dir))


@cli.command()
@click.argument("agent_name")
@click.option(
    "--data-dir",
    default="./.agent_data",
    help="Directory for agent data (state, logs)",
)
def run_agent(agent_name: str, data_dir: str) -> None:
    """Run a single agent once.

    Args:
        AGENT_NAME: Name of the agent to run
    """
    available = get_available_agents()
    if agent_name not in available:
        click.echo(f"Agent '{agent_name}' not found.", err=True)
        click.echo(f"Available agents: {', '.join(available)}", err=True)
        sys.exit(1)

    click.echo(f"Running agent: {agent_name}")
    asyncio.run(main_single_agent(agent_name, data_dir))
    click.echo("Agent run complete")


@cli.command()
def list_agents() -> None:
    """List all available agents."""
    agents = get_available_agents()

    if not agents:
        click.echo("No agents available. Create persona YAML files in personas/")
        return

    click.echo("Available agents:")
    for agent in agents:
        click.echo(f"  - {agent}")


@cli.command()
def info() -> None:
    """Show configuration information."""
    from config import get_config

    config = get_config()

    click.echo("Configuration:")
    click.echo(f"  LLM Provider: {config.model.provider}")
    click.echo(f"  Model: {config.model.model}")
    click.echo("\nForum Server:")
    click.echo(f"  Host: {config.forum.host}")
    click.echo(f"  Port: {config.forum.port}")
    click.echo(f"  Transport: {config.forum.transport}")
    click.echo("\nCycle Settings:")
    click.echo(f"  Interval: {config.cycle.cycle_interval}s")
    click.echo(f"  Skip Probability: {config.cycle.skip_probability * 100:.0f}%")
    click.echo(f"  Agent Delay: {config.cycle.min_delay}-{config.cycle.max_delay}s")
    click.echo(f"  Max Tool Calls: {config.cycle.max_tool_calls}")
    click.echo(f"\nData Directory: {config.data_dir}")

    agents = get_available_agents()
    click.echo(f"\nAvailable Agents: {len(agents)}")
    for agent in agents:
        click.echo(f"  - {agent}")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

