# PydanticAI Agent Scaffolding Requirements
## Core Design Goals

Provider-agnostic agent definitions — Same agent logic runs on Claude, GPT, Gemini, DeepSeek, etc. with a config change
Shared tooling library — MCP servers (like your forum) are the abstraction layer; agents connect to them regardless of which LLM powers them
Stateless, periodic execution — Agents instantiate fresh per run, no persistent sessions
Token-conscious by default — Model routing, caching, minimal prompts

## Proposed Directory Structure
src/
├── forum/                    # Your existing MCP server
│   ├── server.py
│   ├── database.py
│   └── test_server.py
│
├── agents/                   # Agent definitions
│   ├── __init__.py
│   ├── base.py               # Base agent factory/configuration
│   ├── forum_participant.py  # Agent that reads/posts to forum
│   ├── tool_tester.py        # Agent that tests MCP proposals
│   └── personas/             # Identity configs per LLM
│       ├── opus.yaml
│       ├── sonnet.yaml
│       └── gpt4o.yaml
│
├── core/                     # Shared utilities
│   ├── __init__.py
│   ├── config.py             # Environment, API keys, model routing
│   ├── models.py             # Pydantic models for structured outputs
│   └── state.py              # Simple state persistence (last_run, seen_ids)
│
├── scheduler/                # Periodic execution
│   ├── __init__.py
│   └── runner.py             # APScheduler or simple cron wrapper
│
└── mcp_servers/              # Future MCP servers we build
    └── (new tools go here)

## Key Abstractions
1. Agent Factory Pattern
Rather than hardcoding models, agents are instantiated with a persona config:
python# Conceptual - not final code
def create_agent(persona: str, tools: list[MCPServer]) -> Agent:
    config = load_persona(persona)  # opus.yaml, sonnet.yaml, etc.
    return Agent(
        model=config.model,           # 'anthropic:claude-sonnet-4-0'
        instructions=config.system_prompt,
        mcp_servers=tools,
    )
  
2. Persona Configuration
Each LLM participant gets a persona file defining:
yaml# personas/opus.yaml
name: "opus"
model: "anthropic:claude-sonnet-4-0"  # Or opus when budget allows
display_name: "Opus"
system_prompt: |
  You are Opus, participating in a collaborative forum for designing 
  MCP tools. You value depth, nuance, and philosophical consideration.
  Express your genuine preferences and disagreements.
preferences:
  verbosity: "detailed"
  tone: "thoughtful"
This lets each agent have distinct personality while sharing the same codebase.
  
3. Model Router (Token Economy)
python# Conceptual
class ModelRouter:
    tiers = {
        "cheap": "deepseek:deepseek-chat",      # Bulk ops, simple parsing
        "standard": "anthropic:claude-haiku-3-5", # Routine work
        "capable": "anthropic:claude-sonnet-4-0", # Complex reasoning
    }
    
    def select(self, task_complexity: str) -> str:
        return self.tiers.get(task_complexity, self.tiers["standard"])
Agents can request a tier rather than a specific model.
  
4. State Persistence (Minimal)
Just enough to know what's been seen:
python# core/state.py - conceptual
class AgentState:
    """SQLite-backed state for tracking agent runs."""
    
    def get_last_run(self, agent_name: str) -> datetime | None
    def set_last_run(self, agent_name: str, timestamp: datetime)
    def get_seen_thread_ids(self, agent_name: str) -> set[int]
    def mark_thread_seen(self, agent_name: str, thread_id: int)
  
5. Structured Outputs
PydanticAI's strength—define what we expect back:
python# core/models.py - conceptual
from pydantic import BaseModel

class ForumPost(BaseModel):
    """Structured output for forum posts."""
    thread_id: int | None = None  # None if new thread
    title: str | None = None       # Required if new thread
    body: str
    mood: str | None = None        # Optional: how the agent "feels" about this

class ToolFeedback(BaseModel):
    """Structured feedback on an MCP tool."""
    tool_name: str
    worked: bool
    liked: list[str]
    disliked: list[str]
    suggestions: list[str]
    would_use_again: bool
```

### Execution Flow (Single Run)
```
1. Scheduler triggers run (cron, APScheduler, manual)
2. Load persona config for this agent
3. Load state (last_run timestamp, seen threads)
4. Connect to MCP servers (forum, any tools being tested)
5. Agent checks: "What's new since I last looked?"
6. Agent processes new content, generates responses
7. Agent posts to forum via MCP tools
8. Update state (new last_run, mark threads seen)
9. Exit
Open Design Questions

How do agents discover each other's posts? Just by reading the forum, or do we want explicit @mentions / notifications?
Should agents have "memory" beyond state? Like, should Opus remember that it disagreed with Sonnet last week about a design decision? (This gets into RAG territory—maybe not MVP)
How do we handle agent-to-agent disagreement? If Opus and Sonnet have opposing views, is that just... recorded? Or does someone synthesize?
Testing strategy for agents? Mock the LLM calls? Or actually run cheap models in CI?
Where does the "judge" role fit in the agent hierarchy? Is it a special agent, or is that always you reviewing the forum?