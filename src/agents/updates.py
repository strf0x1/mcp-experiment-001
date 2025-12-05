"""Dynamic agent updates from git commits.

This module fetches recent commits from the main branch to keep agents
informed about new MCP tooling and repository changes without manual edits.
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Default keywords that indicate agent-relevant commits
DEFAULT_KEYWORDS = [
    "mcp",
    "agent",
    "tool",
    "persona",
    "prompt",
    "grafiti",
    "memory",
]

# Special prefix for explicitly marked agent updates
AGENT_UPDATE_MARKER = "[agent-update]"


@dataclass
class CommitInfo:
    """Information about a git commit."""

    hash: str
    subject: str
    body: str
    author: str
    date: str

    @property
    def is_agent_update(self) -> bool:
        """Check if commit is explicitly marked as an agent update."""
        return AGENT_UPDATE_MARKER.lower() in self.subject.lower()

    def matches_keywords(self, keywords: list[str]) -> bool:
        """Check if commit message contains any relevant keywords."""
        text = (self.subject + " " + self.body).lower()
        return any(kw.lower() in text for kw in keywords)


def get_repo_root() -> Path | None:
    """Get the root directory of the git repository.

    Returns:
        Path to repo root, or None if not in a git repo
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_main_branch_name() -> str:
    """Detect the name of the main branch (main or master).

    Returns:
        Full branch reference (e.g., 'origin/main' if only remote exists)
    """
    try:
        # Try to get the default branch from remote
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Returns something like "refs/remotes/origin/main"
            branch_name = result.stdout.strip().split("/")[-1]
            # Check if local branch exists
            local_check = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if local_check.returncode == 0:
                return branch_name
            # Use remote branch
            return f"origin/{branch_name}"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: check if main or master exists (local or remote)
    for branch in ["main", "master"]:
        # Try local first
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return branch
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try remote
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", f"origin/{branch}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return f"origin/{branch}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return "origin/main"  # Default fallback


def _ensure_branch_available(branch: str) -> bool:
    """Ensure the branch ref is available locally (fetch if needed).

    Args:
        branch: Branch reference to check

    Returns:
        True if branch is available, False otherwise
    """
    # Check if branch ref exists
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # If it's a remote branch, try to fetch it
    if branch.startswith("origin/"):
        remote_branch = branch.replace("origin/", "")
        try:
            result = subprocess.run(
                ["git", "fetch", "origin", remote_branch],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info(f"Fetched {branch} from origin")
                return True
            else:
                logger.warning(f"Failed to fetch {branch}: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout fetching {branch}")
        except FileNotFoundError:
            logger.warning("Git not found")

    return False


def fetch_recent_commits(
    limit: int = 15,
    branch: str | None = None,
) -> list[CommitInfo]:
    """Fetch recent commits from the specified branch.

    Args:
        limit: Maximum number of commits to fetch
        branch: Branch name (defaults to main branch)

    Returns:
        List of CommitInfo objects
    """
    if branch is None:
        branch = get_main_branch_name()

    # Ensure the branch is available locally
    if not _ensure_branch_available(branch):
        logger.warning(f"Branch {branch} is not available")
        return []

    commits = []

    try:
        # Use a separator that's unlikely to appear in commit messages
        sep = "---COMMIT_SEP---"
        field_sep = "---FIELD_SEP---"

        # Format: hash, subject, body, author, date
        format_str = f"%H{field_sep}%s{field_sep}%b{field_sep}%an{field_sep}%ci{sep}"

        result = subprocess.run(
            ["git", "log", branch, f"-{limit}", f"--format={format_str}"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            logger.warning(f"Failed to fetch commits from {branch}: {result.stderr}")
            return []

        raw_commits = result.stdout.strip().split(sep)

        for raw in raw_commits:
            raw = raw.strip()
            if not raw:
                continue

            parts = raw.split(field_sep)
            if len(parts) >= 5:
                commits.append(
                    CommitInfo(
                        hash=parts[0][:8],  # Short hash
                        subject=parts[1].strip(),
                        body=parts[2].strip(),
                        author=parts[3].strip(),
                        date=parts[4].strip()[:10],  # Just the date part
                    )
                )

    except subprocess.TimeoutExpired:
        logger.warning("Timeout fetching git commits")
    except FileNotFoundError:
        logger.warning("Git not found, cannot fetch commits")
    except Exception as e:
        logger.warning(f"Error fetching commits: {e}")

    return commits


def filter_relevant_commits(
    commits: list[CommitInfo],
    keywords: list[str] | None = None,
    include_all_if_none_match: bool = True,
) -> list[CommitInfo]:
    """Filter commits for agent-relevant updates.

    Priority:
    1. Commits explicitly marked with [agent-update]
    2. Commits matching keywords
    3. All commits (if include_all_if_none_match and nothing else matches)

    Args:
        commits: List of commits to filter
        keywords: Keywords to match (defaults to DEFAULT_KEYWORDS)
        include_all_if_none_match: Whether to include all commits if none match

    Returns:
        Filtered list of relevant commits
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    # First, look for explicitly marked agent updates
    marked_updates = [c for c in commits if c.is_agent_update]
    if marked_updates:
        return marked_updates

    # Then, look for keyword matches
    keyword_matches = [c for c in commits if c.matches_keywords(keywords)]
    if keyword_matches:
        return keyword_matches

    # Fallback to all commits if configured
    if include_all_if_none_match:
        return commits

    return []


def format_updates_section(
    commits: list[CommitInfo],
    max_commits: int = 10,
) -> str:
    """Format commits into a system prompt section.

    Args:
        commits: List of commits to format
        max_commits: Maximum commits to include

    Returns:
        Formatted string for system prompt
    """
    if not commits:
        return ""

    commits = commits[:max_commits]

    lines = [
        "",
        "---",
        "RECENT UPDATES (from main branch commits):",
        "",
        "The following recent changes to this project may be relevant to your work:",
        "",
    ]

    for commit in commits:
        marker = " [AGENT UPDATE]" if commit.is_agent_update else ""
        lines.append(f"- [{commit.hash}] {commit.subject}{marker}")

        # Include body if it's an agent update and has meaningful content
        if commit.is_agent_update and commit.body:
            # Indent body lines and limit length
            body_lines = commit.body.split("\n")[:3]  # Max 3 lines from body
            for body_line in body_lines:
                body_line = body_line.strip()
                if body_line:
                    lines.append(f"    {body_line}")

    lines.extend(
        [
            "",
            "NOTE: Commits marked [AGENT UPDATE] contain information specifically intended",
            "for agents. Pay special attention to these for new capabilities or changes.",
            "",
            "To add an agent update, commit with a message starting with '[agent-update]'.",
        ]
    )

    return "\n".join(lines)


def get_agent_updates_prompt_section(
    limit: int = 15,
    max_display: int = 10,
    keywords: list[str] | None = None,
    branch: str | None = None,
) -> str:
    """Get the formatted updates section for the system prompt.

    This is the main entry point for getting agent updates.

    Args:
        limit: Number of commits to fetch from git
        max_display: Maximum commits to display in the section
        keywords: Keywords for filtering (defaults to DEFAULT_KEYWORDS)
        branch: Branch to fetch from (defaults to main)

    Returns:
        Formatted updates section string, or empty string if no updates
    """
    try:
        commits = fetch_recent_commits(limit=limit, branch=branch)
        relevant = filter_relevant_commits(commits, keywords=keywords)
        return format_updates_section(relevant, max_commits=max_display)
    except Exception as e:
        logger.warning(f"Failed to generate agent updates section: {e}")
        return ""
