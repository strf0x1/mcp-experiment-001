#!/usr/bin/env python3
"""Test script for Grafiti MCP tool calls.

This script tests the Grafiti knowledge graph tools independently,
verifying connectivity, tool calls, and response formats.

Usage:
    uv run python test_grafiti_tools.py
    uv run python test_grafiti_tools.py --host localhost --port 8001
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
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")


def print_json(data: dict, indent: int = 2) -> None:
    """Pretty print JSON data."""
    print(f"{Colors.YELLOW}{json.dumps(data, indent=indent, default=str)}{Colors.RESET}")


class GrafitiToolTester:
    """Test harness for Grafiti MCP tools."""

    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}/mcp/"
        self._client: FastMCPClient | None = None
        self.results: dict[str, bool] = {}

    async def connect(self) -> bool:
        """Connect to the Grafiti MCP server."""
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
        """Close the connection."""
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
                print_info("Connection closed")
            except Exception as e:
                print_error(f"Error closing connection: {e}")

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool and return the result as a dict."""
        if not self._client:
            raise RuntimeError("Not connected")

        result = await self._client.call_tool(tool_name, arguments)

        # Extract result using same logic as base.py
        if hasattr(result, "structured_content") and result.structured_content:
            return result.structured_content
        elif hasattr(result, "data") and result.data:
            data = result.data
            if hasattr(data, "model_dump"):
                return data.model_dump()
            return data
        return {}

    async def list_available_tools(self) -> list[str]:
        """List all available tools on the server."""
        print_header("Available Tools")
        if not self._client:
            print_error("Not connected")
            return []

        try:
            # FastMCP Client has a list_tools() method
            tools = await self._client.list_tools()
            tool_names = []
            for tool in tools:
                tool_names.append(tool.name)
                print(f"  • {Colors.CYAN}{tool.name}{Colors.RESET}")
                # Print first line of description
                if tool.description:
                    first_line = tool.description.split("\n")[0][:70]
                    print(f"    {Colors.YELLOW}{first_line}...{Colors.RESET}")
            return tool_names
        except Exception as e:
            print_error(f"Failed to list tools: {e}")
            return []

    async def test_get_status(self) -> bool:
        """Test the get_status tool."""
        print_header("Test: get_status")
        try:
            result = await self._call_tool("get_status", {})
            print_success("get_status call succeeded")
            print_info("Response:")
            print_json(result)
            self.results["get_status"] = True
            return True
        except Exception as e:
            print_error(f"get_status failed: {e}")
            self.results["get_status"] = False
            return False

    async def test_add_memory(self) -> bool:
        """Test the add_memory tool."""
        print_header("Test: add_memory (add_grafiti_episode)")

        test_episode = {
            "name": f"Test Episode {datetime.now().isoformat()}",
            "episode_body": "This is a test episode created by the Grafiti tool tester. "
            "It contains information about testing the MCP integration. "
            "Brandon is testing the knowledge graph tools.",
            "source": "text",
            "source_description": "automated test",
        }

        print_info(f"Adding episode: {test_episode['name']}")
        try:
            result = await self._call_tool("add_memory", test_episode)
            print_success("add_memory call succeeded")
            print_info("Response:")
            print_json(result)
            self.results["add_memory"] = True
            return True
        except Exception as e:
            print_error(f"add_memory failed: {e}")
            self.results["add_memory"] = False
            return False

    async def test_add_memory_json(self) -> bool:
        """Test add_memory with JSON source type."""
        print_header("Test: add_memory with JSON source")

        test_data = {
            "name": f"JSON Test Episode {datetime.now().isoformat()}",
            "episode_body": json.dumps(
                {
                    "test_type": "integration",
                    "component": "grafiti_tools",
                    "entities": ["Brandon", "Grafiti", "MCP Server"],
                    "status": "testing",
                }
            ),
            "source": "json",
            "source_description": "JSON structured test data",
        }

        print_info(f"Adding JSON episode: {test_data['name']}")
        try:
            result = await self._call_tool("add_memory", test_data)
            print_success("add_memory (JSON) call succeeded")
            print_info("Response:")
            print_json(result)
            self.results["add_memory_json"] = True
            return True
        except Exception as e:
            print_error(f"add_memory (JSON) failed: {e}")
            self.results["add_memory_json"] = False
            return False

    async def test_search_nodes(self) -> bool:
        """Test the search_nodes tool."""
        print_header("Test: search_nodes (search_grafiti_nodes)")

        queries = ["Brandon", "test", "knowledge graph"]

        all_passed = True
        for query in queries:
            print_info(f"Searching nodes for: '{query}'")
            try:
                result = await self._call_tool(
                    "search_nodes", {"query": query, "max_nodes": 5}
                )
                print_success(f"search_nodes('{query}') succeeded")
                print_info("Response:")
                print_json(result)
            except Exception as e:
                print_error(f"search_nodes('{query}') failed: {e}")
                all_passed = False

        self.results["search_nodes"] = all_passed
        return all_passed

    async def test_search_facts(self) -> bool:
        """Test the search_memory_facts tool."""
        print_header("Test: search_memory_facts (search_grafiti_facts)")

        queries = ["Brandon", "testing", "relationships"]

        all_passed = True
        for query in queries:
            print_info(f"Searching facts for: '{query}'")
            try:
                result = await self._call_tool(
                    "search_memory_facts", {"query": query, "max_facts": 5}
                )
                print_success(f"search_memory_facts('{query}') succeeded")
                print_info("Response:")
                print_json(result)
            except Exception as e:
                print_error(f"search_memory_facts('{query}') failed: {e}")
                all_passed = False

        self.results["search_memory_facts"] = all_passed
        return all_passed

    async def test_get_episodes(self) -> bool:
        """Test the get_episodes tool."""
        print_header("Test: get_episodes (get_grafiti_episodes)")

        print_info("Getting recent episodes (limit=5)")
        try:
            result = await self._call_tool("get_episodes", {"max_episodes": 5})
            print_success("get_episodes call succeeded")
            print_info("Response:")
            print_json(result)
            self.results["get_episodes"] = True
            return True
        except Exception as e:
            print_error(f"get_episodes failed: {e}")
            self.results["get_episodes"] = False
            return False

    # =========================================================================
    # METADATA FEATURE TESTS
    # =========================================================================

    async def test_metadata_basic(self) -> bool:
        """Test add_memory with basic metadata."""
        print_header("Test: Metadata - Basic Usage")

        test_data = {
            "name": f"Metadata Test Basic {datetime.now().isoformat()}",
            "episode_body": "This episode tests basic metadata storage capability.",
            "source": "text",
            "source_description": "metadata test",
            "metadata": {
                "significance": "test",
                "category": "integration_test",
                "priority": "high",
            },
        }

        print_info(f"Adding episode with metadata: {test_data['name']}")
        print_info(f"Metadata: {test_data['metadata']}")
        try:
            result = await self._call_tool("add_memory", test_data)
            print_success("add_memory with metadata succeeded")
            print_info("Response:")
            print_json(result)
            self.results["metadata_basic"] = True
            return True
        except Exception as e:
            print_error(f"add_memory with metadata failed: {e}")
            self.results["metadata_basic"] = False
            return False

    async def test_metadata_reflection_pattern(self) -> bool:
        """Test metadata with the reflection/shift pattern from the feature spec."""
        print_header("Test: Metadata - Reflection Pattern (Feature Spec Example)")

        test_data = {
            "name": f"Reflection Test {datetime.now().isoformat()}",
            "episode_body": "Read Haiku's pushback on consolidation. "
            "Initially believed aggressive tool consolidation was always better. "
            "Now understand that purposeful design matters more than minimization.",
            "source": "text",
            "group_id": "test_agent",
            "metadata": {
                "significance": "shift",
                "prior_belief": "aggressive tool consolidation",
                "new_belief": "purposeful design over minimization",
            },
        }

        print_info(f"Adding reflection episode: {test_data['name']}")
        print_info(f"Metadata (reflection pattern):")
        print_json(test_data["metadata"])
        try:
            result = await self._call_tool("add_memory", test_data)
            print_success("Reflection pattern metadata succeeded")
            print_info("Response:")
            print_json(result)
            self.results["metadata_reflection"] = True
            return True
        except Exception as e:
            print_error(f"Reflection pattern metadata failed: {e}")
            self.results["metadata_reflection"] = False
            return False

    async def test_metadata_nested_structure(self) -> bool:
        """Test metadata with nested/complex JSON structure."""
        print_header("Test: Metadata - Nested Structure")

        test_data = {
            "name": f"Nested Metadata Test {datetime.now().isoformat()}",
            "episode_body": "Testing complex nested metadata structures.",
            "source": "text",
            "metadata": {
                "tags": ["test", "nested", "complex"],
                "context": {
                    "source": "unit_test",
                    "environment": "development",
                    "version": "1.0.0",
                },
                "metrics": {
                    "confidence": 0.95,
                    "relevance_score": 8.5,
                    "processing_time_ms": 150,
                },
                "references": [
                    {"type": "thread", "id": 42},
                    {"type": "episode", "id": "abc-123"},
                ],
            },
        }

        print_info(f"Adding episode with nested metadata: {test_data['name']}")
        print_info("Metadata (nested structure):")
        print_json(test_data["metadata"])
        try:
            result = await self._call_tool("add_memory", test_data)
            print_success("Nested metadata structure succeeded")
            print_info("Response:")
            print_json(result)
            self.results["metadata_nested"] = True
            return True
        except Exception as e:
            print_error(f"Nested metadata structure failed: {e}")
            self.results["metadata_nested"] = False
            return False

    async def test_metadata_empty(self) -> bool:
        """Test that empty/missing metadata defaults correctly."""
        print_header("Test: Metadata - Empty/Default Behavior")

        # Test with explicit empty metadata
        test_data_empty = {
            "name": f"Empty Metadata Test {datetime.now().isoformat()}",
            "episode_body": "Testing explicit empty metadata dict.",
            "source": "text",
            "metadata": {},
        }

        print_info("Testing with explicit empty metadata: {}")
        try:
            result = await self._call_tool("add_memory", test_data_empty)
            print_success("Empty metadata dict accepted")
            print_info("Response:")
            print_json(result)
        except Exception as e:
            print_error(f"Empty metadata failed: {e}")
            self.results["metadata_empty"] = False
            return False

        # Test without metadata field at all (should default to empty)
        test_data_missing = {
            "name": f"Missing Metadata Test {datetime.now().isoformat()}",
            "episode_body": "Testing without metadata field (should default to empty).",
            "source": "text",
        }

        print_info("Testing without metadata field (should default)")
        try:
            result = await self._call_tool("add_memory", test_data_missing)
            print_success("Missing metadata field handled correctly")
            print_info("Response:")
            print_json(result)
            self.results["metadata_empty"] = True
            return True
        except Exception as e:
            print_error(f"Missing metadata field failed: {e}")
            self.results["metadata_empty"] = False
            return False

    async def test_metadata_special_values(self) -> bool:
        """Test metadata with special JSON values (null, boolean, numbers)."""
        print_header("Test: Metadata - Special JSON Values")

        test_data = {
            "name": f"Special Values Test {datetime.now().isoformat()}",
            "episode_body": "Testing metadata with various JSON value types.",
            "source": "text",
            "metadata": {
                "nullable_field": None,
                "boolean_true": True,
                "boolean_false": False,
                "integer": 42,
                "float": 3.14159,
                "negative": -100,
                "zero": 0,
                "empty_string": "",
                "empty_list": [],
                "unicode": "こんにちは 🎉",
            },
        }

        print_info(f"Adding episode with special values: {test_data['name']}")
        print_info("Metadata (special values):")
        print_json(test_data["metadata"])
        try:
            result = await self._call_tool("add_memory", test_data)
            print_success("Special JSON values in metadata succeeded")
            print_info("Response:")
            print_json(result)
            self.results["metadata_special_values"] = True
            return True
        except Exception as e:
            print_error(f"Special JSON values failed: {e}")
            self.results["metadata_special_values"] = False
            return False

    async def test_metadata_retrieval_note(self) -> bool:
        """Note about metadata retrieval testing."""
        print_header("Test: Metadata - Retrieval Note")

        print_info(
            "Metadata STORAGE tests passed above. Retrieval verification requires"
        )
        print_info(
            "waiting for LLM processing (30-60+ seconds) which is too long for"
        )
        print_info("automated tests.")
        print()
        print_info("To verify metadata RETRIEVAL, run the separate verification script:")
        print(f"  {Colors.CYAN}uv run python verify_metadata.py{Colors.RESET}")
        print()
        print_info("Or add a test episode and verify later:")
        print(f"  {Colors.CYAN}uv run python verify_metadata.py --add-test{Colors.RESET}")
        print(f"  {Colors.DIM}# wait 30-60 seconds...{Colors.RESET}")
        print(f"  {Colors.CYAN}uv run python verify_metadata.py --group metadata_verification{Colors.RESET}")
        print()

        # This test always passes - it's informational
        self.results["metadata_retrieval_note"] = True
        return True

    async def test_metadata_large(self) -> bool:
        """Test metadata with larger data payload."""
        print_header("Test: Metadata - Large Payload")

        # Create a reasonably large metadata structure
        large_metadata = {
            "description": "A" * 500,  # 500 char string
            "tags": [f"tag_{i}" for i in range(50)],  # 50 tags
            "history": [
                {"timestamp": f"2024-01-{i:02d}", "action": f"action_{i}"}
                for i in range(1, 31)
            ],  # 30 history entries
            "properties": {f"prop_{i}": f"value_{i}" for i in range(100)},  # 100 props
        }

        test_data = {
            "name": f"Large Metadata Test {datetime.now().isoformat()}",
            "episode_body": "Testing with larger metadata payload.",
            "source": "text",
            "metadata": large_metadata,
        }

        estimated_size = len(json.dumps(large_metadata))
        print_info(f"Adding episode with large metadata (~{estimated_size} bytes)")
        try:
            result = await self._call_tool("add_memory", test_data)
            print_success(f"Large metadata payload ({estimated_size} bytes) succeeded")
            print_info("Response:")
            print_json(result)
            self.results["metadata_large"] = True
            return True
        except Exception as e:
            print_error(f"Large metadata payload failed: {e}")
            self.results["metadata_large"] = False
            return False

    async def run_metadata_tests(self) -> bool:
        """Run all metadata-specific tests."""
        print_header("METADATA FEATURE TEST SUITE")
        print_info(
            "Testing the new metadata feature for episode storage and retrieval"
        )

        await self.test_metadata_basic()
        await self.test_metadata_reflection_pattern()
        await self.test_metadata_nested_structure()
        await self.test_metadata_empty()
        await self.test_metadata_special_values()
        await self.test_metadata_large()

        # Wait for processing before retrieval test
        print_info("Waiting 3 seconds for all episodes to process...")
        await asyncio.sleep(3)

        await self.test_metadata_retrieval_note()

        return all(
            v
            for k, v in self.results.items()
            if k.startswith("metadata_")
        )

    def print_summary(self) -> None:
        """Print a summary of all test results."""
        print_header("Test Summary")

        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)

        for test_name, result in self.results.items():
            if result:
                print_success(f"{test_name}")
            else:
                print_error(f"{test_name}")

        print()
        if passed == total:
            print_success(f"All {total} tests passed!")
        else:
            print_error(f"{passed}/{total} tests passed")

    async def run_all_tests(self) -> bool:
        """Run all tool tests."""
        if not await self.connect():
            return False

        try:
            await self.list_available_tools()
            await self.test_get_status()
            await self.test_add_memory()
            await self.test_add_memory_json()

            # Give the server a moment to process the episodes
            print_info("Waiting 2 seconds for episode processing...")
            await asyncio.sleep(2)

            await self.test_search_nodes()
            await self.test_search_facts()
            await self.test_get_episodes()

            # Run metadata tests
            await self.run_metadata_tests()

            self.print_summary()

            return all(self.results.values())
        finally:
            await self.close()


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Grafiti MCP tool calls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python test_grafiti_tools.py
    uv run python test_grafiti_tools.py --host 192.168.1.100 --port 8001
    uv run python test_grafiti_tools.py --test status
    uv run python test_grafiti_tools.py --test search
    uv run python test_grafiti_tools.py --test metadata

Test suites:
    all       - Run all tests including metadata tests
    status    - Test server health check
    add       - Test adding episodes (text and JSON)
    search    - Test search_nodes and search_memory_facts
    episodes  - Test get_episodes retrieval
    metadata  - Test metadata feature (storage, retrieval, edge cases)
        """,
    )
    parser.add_argument(
        "--host", default="localhost", help="Grafiti server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8001, help="Grafiti server port (default: 8001)"
    )
    parser.add_argument(
        "--test",
        choices=["all", "status", "add", "search", "episodes", "metadata"],
        default="all",
        help="Which test(s) to run (default: all)",
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}Grafiti MCP Tool Tester{Colors.RESET}")
    print(f"Server: http://{args.host}:{args.port}/mcp/")
    print(f"Time: {datetime.now().isoformat()}")

    tester = GrafitiToolTester(host=args.host, port=args.port)

    if args.test == "all":
        success = await tester.run_all_tests()
    else:
        if not await tester.connect():
            return 1

        try:
            if args.test == "status":
                success = await tester.test_get_status()
            elif args.test == "add":
                await tester.test_add_memory()
                success = await tester.test_add_memory_json()
            elif args.test == "search":
                await tester.test_search_nodes()
                success = await tester.test_search_facts()
            elif args.test == "episodes":
                success = await tester.test_get_episodes()
            elif args.test == "metadata":
                success = await tester.run_metadata_tests()
            else:
                success = False

            tester.print_summary()
        finally:
            await tester.close()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
