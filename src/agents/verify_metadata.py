#!/usr/bin/env python3
"""Verify metadata retrieval from Grafiti MCP server.

This script verifies that metadata is correctly stored and retrieved from episodes.
Run this AFTER running the metadata tests and waiting for LLM processing to complete.

The Grafiti server uses LLM for NER/entity extraction, which can take time.
This script is designed to be run separately after episodes have been processed.

Usage:
    # After running metadata tests, wait a bit, then:
    uv run python verify_metadata.py

    # Check specific group:
    uv run python verify_metadata.py --group metadata_test_group

    # Check recent episodes in main group:
    uv run python verify_metadata.py --group main --limit 20
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime

from fastmcp import Client as FastMCPClient


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def print_header(text: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")


def print_subheader(text: str) -> None:
    print(f"\n{Colors.CYAN}{'-' * 50}{Colors.RESET}")
    print(f"{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * 50}{Colors.RESET}")


def print_success(text: str) -> None:
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")


def print_json(data: dict, indent: int = 2) -> None:
    print(f"{Colors.YELLOW}{json.dumps(data, indent=indent, default=str)}{Colors.RESET}")


class MetadataVerifier:
    """Verify metadata storage and retrieval."""

    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}/mcp/"
        self._client: FastMCPClient | None = None

    async def connect(self) -> bool:
        print_info(f"Connecting to {self.server_url}...")
        try:
            self._client = FastMCPClient(self.server_url)
            await self._client.__aenter__()
            print_success("Connected to Grafiti MCP server")
            return True
        except Exception as e:
            print_error(f"Failed to connect: {e}")
            return False

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:
                pass

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        if not self._client:
            raise RuntimeError("Not connected")

        result = await self._client.call_tool(tool_name, arguments)

        if hasattr(result, "structured_content") and result.structured_content:
            return result.structured_content
        elif hasattr(result, "data") and result.data:
            data = result.data
            if hasattr(data, "model_dump"):
                return data.model_dump()
            return data
        return {}

    async def get_episodes(
        self, group_ids: list[str] | None = None, limit: int = 10
    ) -> list[dict]:
        """Retrieve episodes from the server."""
        args = {"max_episodes": limit}
        if group_ids:
            args["group_ids"] = group_ids

        result = await self._call_tool("get_episodes", args)
        return result.get("result", {}).get("episodes", [])

    async def verify_all_episodes(
        self, group_ids: list[str] | None = None, limit: int = 20
    ) -> dict:
        """Verify metadata on all retrieved episodes."""
        print_header("Metadata Verification Report")

        if group_ids:
            print_info(f"Checking group(s): {', '.join(group_ids)}")
        else:
            print_info("Checking all groups (no filter)")
        print_info(f"Limit: {limit} episodes")

        episodes = await self.get_episodes(group_ids=group_ids, limit=limit)

        if not episodes:
            print_warning("No episodes found!")
            print_info("Possible reasons:")
            print_info("  - Episodes are still being processed by the LLM")
            print_info("  - The group_id filter doesn't match any episodes")
            print_info("  - No episodes have been added yet")
            return {"total": 0, "with_metadata": 0, "without_metadata": 0}

        print_success(f"Retrieved {len(episodes)} episodes")

        # Analyze metadata
        with_metadata = []
        without_metadata = []
        metadata_stats = {
            "total": len(episodes),
            "with_metadata": 0,
            "without_metadata": 0,
            "metadata_keys_seen": set(),
            "episodes_by_group": {},
        }

        for ep in episodes:
            group = ep.get("group_id", "unknown")
            metadata_stats["episodes_by_group"][group] = (
                metadata_stats["episodes_by_group"].get(group, 0) + 1
            )

            metadata = ep.get("metadata")

            if metadata is not None and metadata != {}:
                with_metadata.append(ep)
                metadata_stats["with_metadata"] += 1
                if isinstance(metadata, dict):
                    metadata_stats["metadata_keys_seen"].update(metadata.keys())
            else:
                without_metadata.append(ep)
                metadata_stats["without_metadata"] += 1

        # Print summary
        print_subheader("Summary Statistics")
        print(f"  Total episodes:      {metadata_stats['total']}")
        print(
            f"  With metadata:       {Colors.GREEN}{metadata_stats['with_metadata']}{Colors.RESET}"
        )
        print(
            f"  Without metadata:    {Colors.YELLOW}{metadata_stats['without_metadata']}{Colors.RESET}"
        )

        if metadata_stats["metadata_keys_seen"]:
            print(f"\n  Metadata keys seen:  {sorted(metadata_stats['metadata_keys_seen'])}")

        print(f"\n  Episodes by group:")
        for group, count in sorted(metadata_stats["episodes_by_group"].items()):
            print(f"    - {group}: {count}")

        # Show episodes WITH metadata
        if with_metadata:
            print_subheader(f"Episodes WITH Metadata ({len(with_metadata)})")
            for i, ep in enumerate(with_metadata, 1):
                print(f"\n{Colors.BOLD}[{i}] {ep.get('name', 'Unnamed')}{Colors.RESET}")
                print(f"    {Colors.DIM}UUID: {ep.get('uuid', 'N/A')}{Colors.RESET}")
                print(f"    {Colors.DIM}Group: {ep.get('group_id', 'N/A')}{Colors.RESET}")
                print(f"    {Colors.DIM}Created: {ep.get('created_at', 'N/A')}{Colors.RESET}")

                content = ep.get("content", "")
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"    Content: {content}")

                print(f"    {Colors.GREEN}Metadata:{Colors.RESET}")
                metadata = ep.get("metadata", {})
                print(
                    f"    {Colors.YELLOW}{json.dumps(metadata, indent=6, default=str)}{Colors.RESET}"
                )

        # Show episodes WITHOUT metadata (just names)
        if without_metadata:
            print_subheader(f"Episodes WITHOUT Metadata ({len(without_metadata)})")
            for i, ep in enumerate(without_metadata, 1):
                name = ep.get("name", "Unnamed")
                group = ep.get("group_id", "N/A")
                created = ep.get("created_at", "N/A")
                if isinstance(created, str) and len(created) > 19:
                    created = created[:19]
                print(f"  [{i}] {name} (group: {group}, created: {created})")

        # Verification result
        print_subheader("Verification Result")

        if metadata_stats["with_metadata"] > 0:
            print_success(
                f"METADATA FEATURE WORKING: Found {metadata_stats['with_metadata']} "
                f"episode(s) with metadata"
            )

            # Check for specific test patterns
            test_patterns_found = []
            for ep in with_metadata:
                metadata = ep.get("metadata", {})
                if "significance" in metadata:
                    test_patterns_found.append("significance tag")
                if "prior_belief" in metadata and "new_belief" in metadata:
                    test_patterns_found.append("reflection pattern")
                if "test_marker" in metadata:
                    test_patterns_found.append("retrieval test marker")
                if "tags" in metadata and isinstance(metadata.get("tags"), list):
                    test_patterns_found.append("nested structure (tags)")
                if "context" in metadata and isinstance(metadata.get("context"), dict):
                    test_patterns_found.append("nested structure (context)")

            if test_patterns_found:
                print_info(f"Test patterns detected: {', '.join(set(test_patterns_found))}")

            return metadata_stats

        else:
            print_warning(
                "NO METADATA FOUND in any episodes. This could mean:"
            )
            print_info("  1. Episodes are still being processed (LLM NER takes time)")
            print_info("  2. Metadata feature isn't working on the server")
            print_info("  3. Test episodes haven't been added yet")
            print_info("\nTry again in 30-60 seconds, or check server logs.")
            return metadata_stats

    async def add_test_episode_with_metadata(self) -> str | None:
        """Add a test episode with metadata and return its marker."""
        print_subheader("Adding Test Episode with Metadata")

        marker = f"verify_test_{datetime.now().timestamp()}"
        test_data = {
            "name": f"Verification Test {datetime.now().isoformat()}",
            "episode_body": f"Test episode for metadata verification. Marker: {marker}",
            "source": "text",
            "group_id": "metadata_verification",
            "metadata": {
                "test_marker": marker,
                "verification_time": datetime.now().isoformat(),
                "purpose": "metadata_feature_verification",
                "nested": {"level": 1, "data": [1, 2, 3]},
            },
        }

        print_info(f"Adding episode with marker: {marker}")
        try:
            result = await self._call_tool("add_memory", test_data)
            print_success("Episode queued for processing")
            print_json(result)
            return marker
        except Exception as e:
            print_error(f"Failed to add episode: {e}")
            return None


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify metadata retrieval from Grafiti MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script verifies that the metadata feature is working correctly.
Run it after the test episodes have been processed by the LLM.

Examples:
    # Check all recent episodes
    uv run python verify_metadata.py

    # Check specific test group
    uv run python verify_metadata.py --group metadata_test_group

    # Check multiple groups
    uv run python verify_metadata.py --group main --group test_agent

    # Add a new test episode (then wait and re-run to verify)
    uv run python verify_metadata.py --add-test

    # Increase limit to see more episodes
    uv run python verify_metadata.py --limit 50
        """,
    )
    parser.add_argument(
        "--host", default="localhost", help="Grafiti server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8001, help="Grafiti server port (default: 8001)"
    )
    parser.add_argument(
        "--group",
        action="append",
        dest="groups",
        help="Group ID(s) to filter by (can specify multiple)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum episodes to retrieve (default: 20)",
    )
    parser.add_argument(
        "--add-test",
        action="store_true",
        help="Add a new test episode with metadata (then re-run later to verify)",
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}Grafiti Metadata Verification{Colors.RESET}")
    print(f"Server: http://{args.host}:{args.port}/mcp/")
    print(f"Time: {datetime.now().isoformat()}")

    verifier = MetadataVerifier(host=args.host, port=args.port)

    if not await verifier.connect():
        return 1

    try:
        if args.add_test:
            marker = await verifier.add_test_episode_with_metadata()
            if marker:
                print_info(
                    f"\nEpisode queued. Wait 30-60 seconds for LLM processing, then run:"
                )
                print(
                    f"  {Colors.CYAN}uv run python verify_metadata.py --group metadata_verification{Colors.RESET}"
                )
            return 0 if marker else 1

        stats = await verifier.verify_all_episodes(
            group_ids=args.groups, limit=args.limit
        )

        # Return success if we found episodes with metadata
        return 0 if stats.get("with_metadata", 0) > 0 else 1

    finally:
        await verifier.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
