# UV: Fast Python Dependency Management - Practical Reference Guide

## Overview

UV is an extremely fast, unified Python package and project manager written in Rust by Astral (the makers of Ruff linter). It consolidates multiple Python development tools into a single high-performance binary, replacing `pip`, `poetry`, `pipx`, `pyenv`, `virtualenv`, and more. UV delivers 10-100x performance improvements over traditional package managers while providing comprehensive features for modern Python development workflows, including workspace management, dependency resolution, and IDE integration.

**Why use UV**: For developers tired of slow dependency resolution, fragmented toolchains, and complex setup processes, UV provides a single, blazing-fast solution that works seamlessly with modern IDEs and AI code assistants.

## Installation

### Quick Install Methods

**Using pip (recommended)**:
```bash
pip install uv
```

**Using curl (Linux/macOS)**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Using pipx (isolated)**:
```bash
pipx install uv
```

**Using Homebrew (macOS)**:
```bash
brew install uv
```

**Using Chocolatey (Windows)**:
```bash
choco install uv
```

### Verification
```bash
# Check UV version
uv --version

# Check help
uv --help

# Verify performance
uv --version && echo "UV installed successfully"
```

**Expected output**:
```
uv 0.4.7
A fast Python package manager.
```

## Core Features

### 1. Project Initialization

Create a new Python project with proper structure:

```bash
# Create new project
uv init my-project
cd my-project

# Initialize with specific Python version
uv init --python 3.12 my-project

# Initialize as package (creates src layout)
uv init --lib my-package
```

**What happens**: Creates `pyproject.toml`, installs Python 3.12 if needed, sets up virtual environment in `.venv/`

### 2. Virtual Environment Management

**Create and activate**:
```bash
# Create environment
uv venv

# Create with specific Python version
uv venv --python 3.11

# Activate (Unix/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

**The .venv approach**: UV manages environments in project directories, eliminating the need for manual activation in most IDEs.

### 3. Dependency Management

**Add dependencies**:
```bash
# Add production dependency
uv add requests

# Add with version constraint
uv add "fastapi>=0.100.0"

# Add development dependency
uv add --dev pytest black

# Add optional dependencies
uv add --optional test pytest

# Add from git
uv add git+https://github.com/some/package.git
```

**Dependencies section in pyproject.toml**:
```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"

[project.dependencies]
requests = "^2.31.0"
fastapi = ">=0.100.0"

[project.optional-dependencies]
test = ["pytest", "pytest-asyncio"]
dev = ["black", "ruff", "mypy"]
```

### 4. Environment Sync

**Keep environments consistent**:
```bash
# Sync with pyproject.toml
uv sync

# Sync with specific groups
uv sync --dev --test

# Sync all groups
uv sync --all-groups --all-extras

# Dry run (show what would change)
uv sync --dry-run
```

**Lock file behavior**: UV generates `uv.lock` for reproducible installations across machines and CI/CD.

### 5. Python Version Management

**Manage Python versions**:
```bash
# List available Python versions
uv python list

# Install specific Python version
uv python install 3.12

# Pin project to specific version
uv python pin 3.11

# Use specific version for current session
uv run --python 3.11 script.py
```

### 6. Tool Execution

**Run tools in temporary environments**:
```bash
# Run script with dependencies
uv run script.py

# Install and run tool temporarily
uvx black .
uvx pytest tests/

# With specific Python version
uvx --python 3.11 black .

# With extra dependencies
uvx --with-extra black .
```

## Common Workflows

### Workflow 1: New Project Setup

```bash
# 1. Create project
uv init my-api
cd my-api

# 2. Add dependencies
uv add fastapi uvicorn

# 3. Add dev dependencies
uv add --dev pytest black ruff mypy

# 4. Create main.py
cat > main.py << 'EOF'
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
EOF

# 5. Test it works
uv run uvicorn main:app --reload
```

### Workflow 2: Existing Project Migration

```bash
# 1. Convert requirements.txt to pyproject.toml
uv init --no-readme --no-workspace
uv add -r requirements.txt

# 2. Add dev dependencies from setup.cfg if exists
uv add --dev $(grep -E '\[dev\]|test|flake8|pytest' requirements-dev.txt | cut -d= -f1 || true)

# 3. Sync environment
uv sync

# 4. Test migration
uv run python -c "import your_main_module; print('Migration successful')"
```

### Workflow 3: Monorepo/Workspace Management

**pyproject.toml for workspace**:
```toml
[project]
name = "my-workspace"
version = "0.0.0"
requires-python = ">=3.12"

[tool.uv]
workspace = "packages/*"
```

**Project structure**:
```
my-workspace/
├── pyproject.toml
├── packages/
│   ├── api/
│   │   ├── pyproject.toml
│   │   └── src/
│   └── cli/
│       ├── pyproject.toml
│       └── src/
```

```bash
# Install all workspace dependencies
uv sync --all-packages

# Run tool in specific package
uv run --package api pytest

# Install development tools for all packages
uv add --workspace --dev black
```

### Workflow 4: CI/CD Integration

**GitHub Actions**:
```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install UV
      run: pip install uv
    
    - name: Install dependencies
      run: uv sync --all-groups
    
    - name: Run tests
      run: uv run pytest
```

### Workflow 5: Development with Jupyter

```bash
# Add Jupyter dependencies
uv add --dev jupyter ipykernel

# Install kernel in current environment
uv run python -m ipykernel install --user --name=my-project

# Start Jupyter with UV environment
uv run jupyter lab
```

## Configuration

### pyproject.toml Configuration

**Basic project configuration**:
```toml
[project]
name = "my-project"
version = "0.1.0"
description = "A sample project"
readme = "README.md"
requires-python = ">=3.12"
authors = [
    {name = "Your Name", email = "you@example.com"}
]
dependencies = [
    "fastapi>=0.100.0",
    "requests>=2.31.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0"
]
```

**Advanced workspace configuration**:
```toml
[project]
name = "my-workspace"
version = "0.0.0"
requires-python = ">=3.12"

[tool.uv]
workspace = "packages/*"
dev-dependencies = [
    "pre-commit>=3.0.0",
    "mypy>=1.0.0"
]

[tool.uv.index]
url = "https://pypi.org/simple"
verify-ssl = true
```

**Index configuration for private packages**:
```toml
[tool.uv]
index = [
    {url = "https://private.pypi.example.com/simple", verify-ssl = false}
]

[[tool.uv.index]]
url = "https://pypi.org/simple"
verify-ssl = true
```

### Environment Configuration

**Global UV settings** (~/.config/uv/settings.toml):
```toml
[pip]
target = ".venv"
python = "3.12"

[index]
url = "https://pypi.org/simple"

[resolver]
strategy = "eager"  # or "resolve"
```

**Per-project environment settings**:
```toml
[tool.uv]
cache-dir = ".uv-cache"
no-binary = "tensorflow"  # Force source builds
no-build-isolation = false  # Use system setuptools
prefer-binary = true
```

## Best Practices

### 1. Project Structure

**Recommended layout**:
```
my-project/
├── pyproject.toml          # Project configuration
├── uv.lock                # Locked dependencies
├── .gitignore             # Exclude .venv, cache
├── README.md
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── main.py
└── tests/
    └── test_main.py
```

**pyproject.toml structure best practices**:
```toml
[project]
name = "descriptive-name"  # Use hyphens, not underscores
version = "0.1.0"         # Use semver
description = "Clear project description"
requires-python = ">=3.12"  # Set minimum supported

[project.dependencies]
# Pin to major versions, not specific patches
requests = "^2.31.0"
fastapi = ">=0.100.0,<1.0.0"

[project.optional-dependencies]
test = ["pytest>=7.0.0"]
dev = ["black", "ruff", "mypy"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 2. Dependency Management

**Version strategy**:
```bash
# Use caret (^) for most dependencies (allows minor/patch updates)
uv add "fastapi>=0.100.0"

# Use == for critical stability
uv add "numpy==1.24.0"

# Use >= with upper bound for experimental features
uv add "pandas>=1.5.0,<3.0.0"

# Keep development tools updated
uv add --dev "ruff>=0.1.0"
```

**Dependency groups**:
```toml
[project.optional-dependencies]
# Core production dependencies
prod = ["fastapi>=0.100.0", "gunicorn>=20.0"]

# Testing
test = ["pytest>=7.0.0", "pytest-asyncio", "httpx"]

# Code quality
lint = ["black", "ruff", "mypy", "pre-commit"]

# Documentation
docs = ["mkdocs", "mkdocs-material", "mkdocstrings"]

# Development
dev = ["pytest", "black", "ruff", "mypy", "pre-commit"]
```

### 3. Performance Optimization

**Global cache configuration**:
```bash
# Enable global cache for all projects
uv config set global-cache true

# Set cache directory
uv config set cache-dir ~/.cache/uv

# Prefer binary packages for speed
uv config set prefer-binary true
```

**Parallel operations**:
```bash
# UV automatically uses parallel operations
# Monitor performance with verbose output
uv sync -v

# For CI/CD, use all CPU cores
export UV_CPU_COUNT=$(nproc)
uv sync
```

### 4. IDE Integration

**VS Code setup**:
1. Install "UV - Python Package Manager" extension
2. Set Python interpreter: `./.venv/bin/python`
3. Enable UV-specific settings in workspace:
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true
}
```

**PyCharm setup**:
1. Install PyCharm 2024.3.2+
2. Create project using "UV Project" template
3. PyCharm will auto-detect `.venv` and configure interpreter

### 5. Version Pinning Strategy

**When to pin specific versions**:
```toml
# Good: Pin ML/data science packages for reproducibility
[project.dependencies]
numpy = "==1.24.3"
pandas = "==2.0.3"
torch = "==2.0.1"

# Good: Use ranges for web APIs with compatibility
[project.dependencies]
requests = "^2.31.0"
fastapi = ">=0.100.0,<1.0.0"
```

**Pinning in CI/CD**:
```bash
# Install exact versions from lock file
uv sync --frozen

# For reproducible builds
uv export --format requirements-txt --no-dev > requirements.txt
```

## Troubleshooting

### Common Issues and Solutions

**Issue 1: "No Python interpreter found"**
```bash
# Solution: Install Python version
uv python install 3.12

# Or pin to existing version
uv python pin $(python3 --version | cut -d' ' -f2)
```

**Issue 2: "No dependencies specified"**
```toml
# Fix pyproject.toml - ensure [project] section exists
[project]
name = "my-project"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.31.0"
]
```

**Issue 3: "Package not found"**
```bash
# Check package name (use correct PyPI name)
uv add "python-dotenv"  # Correct
# uv add "dotenv"       # Wrong

# Check Python version compatibility
uv python list  # Shows available versions

# Try alternative index
uv add --index-url https://test.pypi.org/simple/ package-name
```

**Issue 4: "Version conflict during sync"**
```bash
# Show resolution conflicts
uv tree

# Update lock file with more aggressive resolution
uv sync --resolution eager

# Check for incompatible constraints
grep -E "(requires-python|version)" pyproject.toml
```

**Issue 5: "Permission denied" errors**
```bash
# Use --user flag for user installation
uv add --user package-name

# Or ensure .venv is in writable location
uv venv --python $(which python3)

# For global installation (not recommended)
sudo uv sync
```

**Issue 6: "Slow dependency resolution"**
```bash
# Clear cache and try again
uv cache clean
uv sync --reinstall

# Use pre-built wheels
uv config set prefer-binary true

# Skip optional dependencies
uv sync --no-optional
```

### Debug Mode

**Enable verbose output**:
```bash
uv sync -v              # Verbose sync
uv add package -v       # Verbose add
uv run script.py -v     # Verbose run

# Debug specific issues
RUST_LOG=debug uv sync
```

**Environment inspection**:
```bash
# Show current environment
uv pip show

# List all installed packages
uv pip list

# Check Python version in environment
uv python version

# Show dependency tree
uv tree
```

**Lock file issues**:
```bash
# Regenerate lock file
rm uv.lock
uv sync

# Show what's in lock file
uv tree --locked

# Check for outdated dependencies
uv pip list --outdated
```

### Migration Issues

**From requirements.txt**:
```bash
# Import existing requirements
uv add -r requirements.txt

# For setup.py projects, create temporary requirements
pip freeze > current-requirements.txt
uv add -r current-requirements.txt
```

**From Poetry**:
```bash
# Poetry has built-in export (install with: pip install poetry-plugin-export)
poetry export -f requirements.txt --output requirements.txt
uv add -r requirements.txt

# Or manually transfer dependencies
grep -A10 '\[tool.poetry.dependencies\]' pyproject.toml
```

**From pip-tools**:
```bash
# Direct conversion often works
uv add -r requirements.in

# Or check pip-tools documentation
# https://docs.astral.sh/uv/guides/integration/pip-tools/
```

## Quick Reference

### Essential Commands

```bash
# Project setup
uv init project-name          # Initialize new project
uv venv                       # Create virtual environment
uv sync                       # Sync dependencies from pyproject.toml
uv add package                # Add dependency
uv add --dev package          # Add development dependency

# Running code
uv run script.py              # Run script with dependencies
uvx tool-name                 # Run tool in temporary environment
uv python                     # List available Python versions

# Dependency management
uv add "package>=1.0.0"       # Add with version constraint
uv remove package             # Remove dependency
uv update                     # Update dependencies to latest
uv tree                       # Show dependency tree

# Workspace commands
uv sync --all-packages        # Sync all packages in workspace
uv run --package pkg pytest  # Run in specific package
uv add --workspace package   # Add to workspace root
```

### Configuration Commands

```bash
# Show configuration
uv config list                # List all settings
uv config get key            # Get specific setting
uv config set key value      # Set configuration

# Cache management
uv cache clean               # Clean cache
uv cache prune               # Remove old cache entries

# Index management
uv index add url             # Add package index
uv index list                # List configured indices
```

### File Templates

**Minimal pyproject.toml**:
```toml
[project]
name = "project-name"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Complete pyproject.toml with groups**:
```toml
[project]
name = "complete-project"
version = "1.0.0"
description = "A complete project example"
readme = "README.md"
requires-python = ">=3.12"
authors = [{name = "Your Name", email = "you@example.com"}]

[project.dependencies]
fastapi = ">=0.100.0"
uvicorn = ">=0.20.0"
sqlalchemy = ">=2.0.0"
alembic = ">=1.11.0"

[project.optional-dependencies]
test = ["pytest>=7.0.0", "pytest-asyncio", "httpx"]
dev = ["black", "ruff", "mypy", "pre-commit"]
docs = ["mkdocs", "mkdocs-material"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.mypy]
python_version = "3.12"
warn_return_any = true
```

### Common Error Messages

| Error | Quick Fix |
|-------|-----------|
| `No Python interpreter found` | `uv python install 3.12` |
| `No dependencies specified` | Add `[project]` section to `pyproject.toml` |
| `Package not found` | Check package name and index |
| `Version conflict` | `uv sync --resolution eager` |
| `Permission denied` | Use `--user` flag or check directory permissions |
| `Too slow` | `uv config set prefer-binary true` |

## Resources

### Official Documentation
- **Main Documentation**: https://docs.astral.sh/uv/
- **Installation Guide**: https://docs.astral.sh/uv/getting-started/installation/
- **Python Package Guide**: https://docs.astral.sh/uv/guides/projects/
- **Workspace Guide**: https://docs.astral.sh/uv/guides/workspaces/

### IDE Integration
- **PyCharm Integration**: https://jetbrains.com/help/pycharm/uv.html
- **VS Code Extensions**:
  - UV - Python Package Manager: https://marketplace.visualstudio.com/items?itemName=the0807.uv-toolkit
  - UV Toolkit: https://marketplace.visualstudio.com/items?itemName=the0807.uv-toolkit

### Community Resources
- **GitHub Repository**: https://github.com/astral-sh/uv
- **Discussions**: https://github.com/astral-sh/uv/discussions
- **Astral Blog**: https://astral.sh/blog/
- **Discord Community**: https://discord.gg/astral-sh

### Migration Guides
- **From pip-tools**: https://docs.astral.sh/uv/guides/integration/pip-tools/
- **From Poetry**: https://medium.com/@yuxuzi/uv-vs-poetry-the-future-of-python-package-management-d704128509b6
- **From requirements.txt**: https://medium.com/@theomeb/move-from-pip-tools-to-uv-to-lock-python-dependencies-48c5aade1453

### Performance Benchmarks
- **Official Benchmarks**: https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md
- **Real-world Comparisons**: Various blog posts comparing UV with traditional tools

### Examples and Templates
- **Official Examples**: https://github.com/astral-sh/uv/tree/main/docs
- **Monorepo Examples**: https://github.com/juftin/uv-monorepo
- **Docker Templates**: https://github.com/loftwah/uv-docker-starter

### Latest Updates and Roadmap
- **Release Notes**: https://github.com/astral-sh/uv/releases
- **Roadmap**: Available in GitHub Discussions
- **Performance Updates**: Regular benchmarking improvements

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**UV Version**: 0.4.7+

This reference guide provides practical, hands-on documentation for developers using UV with AI code editors. Focus on the core workflows and examples that demonstrate real-world usage patterns.
