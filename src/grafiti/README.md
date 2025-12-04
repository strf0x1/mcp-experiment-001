# Grafiti MCP Server Setup

This directory contains the Docker Compose configuration for running Grafiti MCP Server with FalkorDB as the graph database backend.

## Architecture

- **FalkorDB**: Graph database (Redis-based) running on port 6379 with web UI on port 3000
- **Grafiti MCP Server**: HTTP MCP server running on port 8000 at `/mcp/`

**Note**: FalkorDB is a Redis module, not a separate service. The `falkordb/falkordb` Docker image includes both Redis and the FalkorDB module pre-loaded.

## Quick Start

1. **Copy the environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** and add your API keys (at minimum, `OPENAI_API_KEY` is required):
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Start the services**:
   ```bash
   docker compose up -d
   ```

4. **Verify services are running**:
   ```bash
   docker compose ps
   ```

5. **Check logs**:
   ```bash
   docker compose logs -f grafiti-mcp
   ```

## Data Persistence

FalkorDB data is stored in a Docker named volume (`falkordb_data`) that persists across container restarts and removals. The data is stored at `/var/lib/falkordb/data` inside the container.

To backup the data:
```bash
docker run --rm -v grafiti_falkordb_data:/data -v $(pwd):/backup alpine tar czf /backup/falkordb-backup.tar.gz /data
```

To restore from backup:
```bash
docker run --rm -v grafiti_falkordb_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/falkordb-backup.tar.gz --strip-components=1"
```

## Access Points

- **FalkorDB Web UI**: http://localhost:3000
- **FalkorDB Protocol**: `redis://localhost:6379`
- **Grafiti MCP HTTP Endpoint**: http://localhost:8000/mcp/
- **Health Check**: http://localhost:8000/health

## Configuration

### LLM Provider Selection

The LLM provider is used by Grafiti for **knowledge graph construction** during episode ingestion. Specifically, the LLM performs:

1. **Entity Extraction**: Identifies entities (people, places, concepts, etc.) from text using the configured entity types (Preference, Requirement, Procedure, Location, Event, Organization, Document, Topic, Object)
2. **Entity Deduplication**: Determines when different mentions refer to the same entity (e.g., "John" and "John Smith")
3. **Summarization**: Creates summaries of nodes/entities for efficient retrieval

**Important**: Each episode ingestion involves multiple LLM calls (typically 3-5+ per episode), so the actual number of concurrent LLM requests will be several times higher than `SEMAPHORE_LIMIT`.

The Grafiti MCP server supports multiple LLM providers. Configure via environment variables:

- **OpenAI** (default): Set `OPENAI_API_KEY` - Best support for Structured Output
- **Anthropic**: Set `ANTHROPIC_API_KEY` - Good support for Structured Output
- **Google/Gemini**: Set `GOOGLE_API_KEY` - Excellent support for Structured Output
- **Groq**: Set `GROQ_API_KEY` - Fast inference, check Structured Output support
- **Azure OpenAI**: Set `AZURE_OPENAI_*` variables - Same as OpenAI

**Note**: Grafiti works best with LLM services that support Structured Output (OpenAI, Gemini, Anthropic). Using other services may result in incorrect output schemas and ingestion failures, especially with smaller models.

### Model Selection

You can control which specific model is used via environment variables in your `.env` file:

```bash
# LLM Model (for entity extraction, deduplication, summarization)
LLM_MODEL=gpt-4o-mini              # OpenAI default
# LLM_MODEL=claude-3-5-sonnet-20241022  # Anthropic
# LLM_MODEL=gemini-2.0-flash-exp        # Gemini
# LLM_MODEL=llama-3.1-70b-versatile     # Groq

# LLM Provider
LLM_PROVIDER=openai                # openai, anthropic, gemini, groq, azure_openai

# LLM Temperature (0.0-2.0, default: 0.0 for deterministic extraction)
LLM_TEMPERATURE=0.0

# Embedder Model (for semantic search)
# Note: Anthropic does NOT provide embedding models - use a different provider
EMBEDDER_MODEL=text-embedding-3-small  # OpenAI default
# EMBEDDER_MODEL=voyage-large-2         # Voyage (requires VOYAGE_API_KEY)
# EMBEDDER_MODEL=embedding-001         # Gemini (requires GOOGLE_API_KEY)
# EMBEDDER_MODEL=all-MiniLM-L6-v2      # Sentence Transformers (local/free)

# Embedder Provider
# Common: Use Anthropic for LLM + OpenAI for embeddings
EMBEDDER_PROVIDER=openai            # openai, azure_openai, gemini, voyage, sentence_transformers
```

**Model Examples by Provider:**

- **OpenAI**: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Anthropic**: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307`
- **Gemini**: `gemini-2.0-flash-exp`, `gemini-1.5-pro`, `gemini-1.5-flash`
- **Groq**: `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`

**Alternative Configuration**: You can also use a `config.yaml` file for more advanced configuration. Mount it as a volume in `docker-compose.yml` (uncomment the volumes section) and it will take precedence over environment variables.

### Concurrency Tuning

Adjust `SEMAPHORE_LIMIT` based on your LLM provider tier:

- **OpenAI Tier 1** (free): `SEMAPHORE_LIMIT=1-2`
- **OpenAI Tier 2**: `SEMAPHORE_LIMIT=5-8`
- **OpenAI Tier 3**: `SEMAPHORE_LIMIT=10-15` (default)
- **OpenAI Tier 4**: `SEMAPHORE_LIMIT=20-50`
- **Anthropic Default**: `SEMAPHORE_LIMIT=5-8`
- **Anthropic High Tier**: `SEMAPHORE_LIMIT=15-30`

Watch for 429 rate limit errors in logs if the limit is too high.

## Integration with MCP Clients

### Cursor IDE

Add to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "grafiti-memory": {
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

### VS Code / GitHub Copilot

Add to `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "grafiti": {
      "uri": "http://localhost:8000/mcp/",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

## Troubleshooting

### Check FalkorDB is running
```bash
docker compose exec falkordb redis-cli ping
# Should return: PONG
```

### Check Grafiti MCP health
```bash
curl http://localhost:8000/health
```

### View FalkorDB logs
```bash
docker compose logs -f falkordb
```

### Reset everything (⚠️ deletes all data)
```bash
docker compose down -v
docker compose up -d
```

## Building from Source

To build the Grafiti MCP server from source instead of using the pre-built image:

1. Uncomment the `build` section in `docker-compose.yml`
2. Comment out the `image` line
3. Create a `Dockerfile` based on the Grafiti repository

## References

- [Grafiti MCP Server Documentation](../../ai_coding_docs/grafiti-mcp.md)
- [FalkorDB Documentation](../../ai_coding_docs/FalkorDB.md)
- [Grafiti GitHub Repository](https://github.com/getzep/graphiti)

