# GitHub MCP Server - Optimized Docker Build
# Uses multi-stage build with uv for fast, reproducible builds

FROM ghcr.io/astral-sh/uv:python3.10-alpine AS uv

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy from cache instead of linking for mounted volumes
ENV UV_LINK_MODE=copy

# Prefer system Python
ENV UV_PYTHON_PREFERENCE=only-system

# Run without updating uv.lock (frozen lockfile)
ENV UV_FROZEN=true

# Copy dependency files first for optimal layer caching
COPY pyproject.toml uv.lock ./

# Python optimization
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system build dependencies
RUN apk update && \
    apk add --no-cache --virtual .build-deps \
    build-base \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev

# Install dependencies using lockfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python 3.10 --frozen --no-install-project --no-dev --no-editable

# Copy application source and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python 3.10 --frozen --no-dev --no-editable

# Runtime stage - minimal image
FROM python:3.10-alpine

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Install runtime dependencies and create app user
RUN apk update && \
    apk add --no-cache ca-certificates && \
    update-ca-certificates && \
    addgroup -S app && \
    adduser -S app -G app -h /app

# Copy virtual environment from build stage
COPY --from=uv --chown=app:app /app /app

# Switch to non-root user
USER app
WORKDIR /app

# Expose HTTP port
EXPOSE 8000

# Health check for HTTP mode (uses simple /health endpoint, not MCP protocol)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8000/health || exit 1

# Run in HTTP mode by default
ENTRYPOINT ["github-mcp-http"]
CMD ["--host", "0.0.0.0", "--port", "8000"]

