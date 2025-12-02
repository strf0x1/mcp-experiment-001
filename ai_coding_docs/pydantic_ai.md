Based on the comprehensive research I've gathered, I'll now create a practical developer documentation for PydanticAI. This will be focused on what developers need to know for daily use in their IDEs and code editors.

# PydanticAI Developer Reference Guide

## Overview

**PydanticAI** is a Python agent framework that brings the "FastAPI feeling" to Generative AI application development. Built by the Pydantic team, it provides type-safe interfaces, structured outputs, and robust error handling for building production-grade AI applications [Official Documentation](https://ai.pydantic.dev/).

**Why use it:**
- **Type Safety**: Leverages Pydantic's validation for all AI interactions
- **Model Agnostic**: Supports OpenAI, Anthropic, Gemini, Deepseek, Ollama, Groq, Cohere, and Mistral
- **Production Ready**: Built-in retry logic, error handling, and observability
- **Developer Experience**: Excellent IDE support and comprehensive testing capabilities
- **Tool System**: Robust function calling with dependency injection

**Target Audience**: Python developers building AI-powered applications who need reliability, type safety, and production-grade features.

## Installation

### Basic Installation

```bash
# Standard installation
pip install pydantic-ai
# or with uv
uv add pydantic-ai

# For specific model providers
pip install "pydantic-ai-slim[openai]"  # OpenAI only
pip install "pydantic-ai[examples]"     # Include examples and extras
```

**Requirements**: Python 3.10+

### Environment Setup

```bash
# Configure API keys for your chosen provider
export OPENAI_API_KEY='your-openai-key'
export ANTHROPIC_API_KEY='your-anthropic-key' 
export GOOGLE_API_KEY='your-google-key'
```

### Verify Installation

```python
import pydantic_ai
print(f"PydanticAI version: {pydantic_ai.__version__}")

# Quick test
from pydantic_ai import Agent
agent = Agent('openai:gpt-4o', system_prompt='Say hello')
result = agent.run('Hello!')
print(result.data)
```

## Core Features

### 1. Basic Agent Creation

```python
from pydantic_ai import Agent

# Simple agent setup
agent = Agent(
    'openai:gpt-4o',
    system_prompt='You are a helpful assistant'
)

# Run and get result
result = agent.run('Explain quantum computing briefly')
print(result.data)  # Type-safe response
```

### 2. Structured Output with Pydantic Models

```python
from pydantic import BaseModel
from typing import List
from pydantic_ai import Agent

class UserProfile(BaseModel):
    name: str
    age: int
    skills: List[str]
    experience_level: str  # 'junior', 'mid', 'senior'

# Agent with structured output
agent = Agent(
    'openai:gpt-4',
    result_type=UserProfile,
    system_prompt='Extract user information from job descriptions'
)

# Get validated, typed output
result = agent.run('John is a senior Python developer with 8 years experience')
profile = result.data  # Fully typed UserProfile object
print(f"{profile.name} is {profile.experience_level} level")
```

### 3. Function Tools with Type Safety

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import Dict

class WeatherData(BaseModel):
    temperature: float
    humidity: int
    condition: str

class Location(BaseModel):
    city: str
    country: str

@agent.tool
def get_weather(location: Location, ctx: RunContext) -> WeatherData:
    """Get weather for a location using API key from context"""
    api_key = ctx.deps.weather_api_key
    # API call implementation here
    return WeatherData(temperature=22.5, humidity=65, condition="sunny")

@agent.tool_plain  # Simple tool without dependencies
def calculate_distance(city1: str, city2: str) -> float:
    """Calculate distance between two cities"""
    # Distance calculation logic
    return 1250.5

# Agent with tools
agent = Agent(
    'openai:gpt-4',
    tools=[get_weather, calculate_distance],
    system_prompt='You can get weather and calculate distances'
)

result = agent.run('What\'s the weather in London and how far is it from Paris?')
```

### 4. Dependency Injection

```python
from pydantic_ai import Agent, RunContext
from typing import TypedDict

class AppDeps(TypedDict):
    database_url: str
    api_key: str

@agent.tool
def query_database(query: str, ctx: RunContext) -> str:
    """Query the database using connection from context"""
    # Use ctx.deps.database_url for database operations
    db_result = "Sample query result"
    return db_result

# Agent with dependency injection
agent = Agent(
    'openai:gpt-4',
    tools=[query_database],
    deps_type=AppDeps
)

# Run with dependencies
deps = AppDeps(
    database_url="postgresql://localhost/mydb",
    api_key="secret-key"
)

result = agent.run('Query users older than 25', deps=deps)
```

### 5. Multi-Modal Support

```python
from pydantic_ai import Agent, ImageUrl, DocumentUrl
from pydantic import BaseModel

class ImageAnalysis(BaseModel):
    description: str
    objects_detected: list[str]
    confidence: float

agent = Agent(
    'openai:gpt-4o',  # Vision-capable model
    result_type=ImageAnalysis
)

# Analyze image
result = agent.run('Describe this image: https://example.com/photo.jpg')
analysis = result.data

# Handle multiple input types
@agent.tool
def process_document(doc_url: DocumentUrl) -> str:
    """Process uploaded document"""
    return f"Processed document from {doc_url.url}"

@agent.tool
def generate_image(prompt: str) -> ImageUrl:
    """Generate image from prompt"""
    return ImageUrl(url='https://generated-image-url.com/image.png')
```

## Common Workflows

### 1. Data Analysis Workflow

```python
from pydantic import BaseModel
from typing import List, Dict
from pydantic_ai import Agent

class DataSummary(BaseModel):
    total_records: int
    columns: List[str]
    data_types: Dict[str, str]
    missing_values: Dict[str, int]
    summary_stats: Dict[str, float]

class AnalysisAgent:
    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4',
            result_type=DataSummary,
            tools=[self.load_csv, self.calculate_stats],
            system_prompt='Analyze datasets and provide insights'
        )
    
    @agent.tool
    def load_csv(self, file_path: str) -> List[Dict]:
        """Load CSV data"""
        import pandas as pd
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    
    @agent.tool  
    def calculate_stats(self, data: List[Dict]) -> Dict[str, float]:
        """Calculate basic statistics"""
        import pandas as pd
        df = pd.DataFrame(data)
        return df.describe().to_dict()

# Usage
analyzer = AnalysisAgent()
summary = analyzer.agent.run('Analyze the sales data in sales.csv')
print(f"Found {summary.data.total_records} records")
```

### 2. RAG (Retrieval-Augmented Generation) Workflow

```python
from pydantic import BaseModel
from typing import List
from pydantic_ai import Agent

class DocumentChunk(BaseModel):
    content: str
    source: str
    relevance_score: float

class QAResult(BaseModel):
    answer: str
    sources: List[DocumentChunk]
    confidence: float

class RAGAgent:
    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4',
            result_type=QAResult,
            tools=[self.search_documents, self.rank_results],
            system_prompt='Answer questions based on provided documents'
        )
    
    @agent.tool
    def search_documents(self, query: str, limit: int = 5) -> List[DocumentChunk]:
        """Search through document collection"""
        # Vector search implementation
        results = [
            DocumentChunk(
                content="Relevant content...",
                source="document1.pdf",
                relevance_score=0.95
            )
        ]
        return results[:limit]
    
    @agent.tool
    def rank_results(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Re-rank results by relevance"""
        return sorted(chunks, key=lambda x: x.relevance_score, reverse=True)

# Usage
rag = RAGAgent()
result = rag.agent.run('What are the main benefits of using Python?')
print(f"Answer: {result.data.answer}")
```

### 3. Planning-Executor Pattern

```python
from pydantic import BaseModel
from typing import List
from pydantic_ai import Agent

class PlanStep(BaseModel):
    step_number: int
    action: str
    description: str
    dependencies: List[int]
    status: str = "pending"

class ExecutionPlan(BaseModel):
    steps: List[PlanStep]
    estimated_duration: int
    complexity_score: float

class PlannerAgent:
    def __init__(self):
        self.planner = Agent(
            'openai:gpt-4',
            result_type=ExecutionPlan,
            system_prompt='Create detailed execution plans'
        )
        self.executor = Agent(
            'openai:gpt-4',
            tools=[self.execute_step],
            system_prompt='Execute planned steps efficiently'
        )
    
    @executor.tool
    def execute_step(self, step: PlanStep) -> str:
        """Execute individual plan step"""
        # Implementation depends on step type
        return f"Completed step {step.step_number}: {step.action}"

    def plan_and_execute(self, task: str):
        # Planning phase
        plan_result = self.planner.run(f'Plan how to accomplish: {task}')
        plan = plan_result.data
        
        # Execution phase  
        for step in plan.steps:
            self.executor.run(f'Execute step: {step.description}')

# Usage
planner = PlannerAgent()
planner.plan_and_execute('Build a web scraper for product prices')
```

### 4. Multi-Agent Workflow

```python
from pydantic import BaseModel
from typing import List
from pydantic_ai import Agent

class TaskAssignment(BaseModel):
    task: str
    assigned_agent: str
    priority: int
    dependencies: List[str]

class WorkflowResult(BaseModel):
    task: str
    result: str
    agent_used: str
    duration: float

class TaskCoordinator:
    def __init__(self):
        self.agents = {
            'researcher': Agent(
                'openai:gpt-4',
                system_prompt='Research and gather information'
            ),
            'analyst': Agent(
                'openai:gpt-4',
                system_prompt='Analyze data and provide insights'
            ),
            'writer': Agent(
                'openai:gpt-4',
                system_prompt='Create clear, well-structured content'
            )
        }

    @property
    def coordinator(self):
        return Agent(
            'openai:gpt-4',
            tools=[task for agent in self.agents.values() for task in agent.tools],
            system_prompt='Coordinate between specialized agents'
        )

    def run_workflow(self, request: str):
        coordinator = self.coordinator
        
        # Coordinator determines task breakdown
        assignment = coordinator.run(
            f'Break down this task: {request}',
            tools=[self.assign_task],
            deps=self
        )
        
        # Execute assigned tasks
        results = []
        for task in assignment.data.tasks:
            agent = self.agents[task.assigned_agent]
            result = agent.run(task.task)
            results.append(WorkflowResult(
                task=task.task,
                result=result.data,
                agent_used=task.assigned_agent,
                duration=0.0  # You'd track actual timing
            ))
        
        return results

# Usage
coordinator = TaskCoordinator()
results = coordinator.run_workflow('Research market trends and create a report')
```

## Configuration

### Model Provider Configuration

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

# Custom OpenAI configuration
model = OpenAIChatModel(
    'gpt-4-turbo',
    provider=OpenAIProvider(
        api_key='your-key',
        base_url='https://api.openai.com/v1',
        organization='your-org'
    )
)

# Custom model settings
settings = ModelSettings(
    temperature=0.7,
    max_tokens=1000,
    top_p=0.9,
    frequency_penalty=0.1,
    presence_penalty=0.1
)

agent = Agent(
    model,
    settings=settings,
    system_prompt='You are a helpful assistant'
)
```

### Retry Configuration

```python
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig
from tenacity import wait_exponential, stop_after_attempt

# Configure retry behavior
retry_config = RetryConfig(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3)
)

transport = AsyncTenacityTransport(retry_config=retry_config)

# Agent with custom retry behavior
agent = Agent(
    'openai:gpt-4',
    transport=transport,
    system_prompt='Handle temporary failures gracefully'
)
```

### Environment-Specific Configuration

```python
import os
from typing import Dict, Any
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

class Config:
    def __init__(self):
        self.env = os.getenv('ENVIRONMENT', 'development')
        self.model = self._get_model()
        self.settings = self._get_settings()
    
    def _get_model(self) -> str:
        if self.env == 'production':
            return 'openai:gpt-4'
        elif self.env == 'staging':
            return 'openai:gpt-4-turbo'
        else:
            return 'openai:gpt-3.5-turbo'
    
    def _get_settings(self) -> ModelSettings:
        base_settings = {
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        if self.env == 'development':
            base_settings.update({
                'temperature': 0.9,  # More creative in dev
                'max_tokens': 500    # Limit costs
            })
        
        return ModelSettings(**base_settings)

# Usage
config = Config()
agent = Agent(config.model, settings=config.settings)
```

## CLI Usage (clai)

### Interactive CLI

```bash
# Install CLI
uvx clai
# or install globally
uv tool install clai

# Set environment
export OPENAI_API_KEY='your-key'

# Start interactive session
clai

# In the CLI:
/markdown    # Enable markdown formatting
/multiline  # Toggle multiline input
/history    # Show conversation history
/exit       # Exit CLI
```

### Agent to CLI Conversion

```python
from pydantic_ai import Agent

agent = Agent(
    'openai:gpt-4',
    system_prompt='You are a helpful coding assistant'
)

if __name__ == '__main__':
    agent.to_cli()
```

Run the converted script:
```bash
python my_agent.py --help
python my_agent.py
```

## Best Practices

### 1. Type Safety and Validation

```python
# ✅ Good: Define clear interfaces
from pydantic import BaseModel, Field
from typing import Optional, List

class UserRequest(BaseModel):
    query: str = Field(..., description="The user's question")
    max_results: int = Field(default=10, ge=1, le=100)
    include_sources: bool = Field(default=True)

class SearchResult(BaseModel):
    title: str
    url: str
    summary: str
    relevance_score: float = Field(..., ge=0, le=1)

# ✅ Good: Use dependency injection
@agent.tool
def search_web(request: UserRequest, ctx: RunContext) -> List[SearchResult]:
    api_key = ctx.deps.search_api_key
    # Search implementation
    return results

# ❌ Avoid: Untyped interactions
def bad_tool(query):  # No types!
    return "results"
```

### 2. Error Handling

```python
from pydantic_ai.exceptions import ModelRetry, ModelError

@agent.tool
def robust_api_call(data: str) -> str:
    try:
        # API call with error handling
        result = external_api_call(data)
        return result
    except TransientError:
        raise ModelRetry("Temporary failure, please retry")
    except AuthenticationError:
        raise ModelError("Invalid API credentials")
    except Exception as e:
        raise ModelError(f"Unexpected error: {e}")

# Handle errors in main code
try:
    result = agent.run("Search for python tutorials")
except ModelRetry as e:
    print(f"Retrying: {e}")
    # Implement backoff strategy
except ModelError as e:
    print(f"Model error: {e}")
    # Handle permanent failures
```

### 3. Resource Management

```python
import asyncio
from contextlib import asynccontextmanager
from pydantic_ai import Agent

@asynccontextmanager
async def agent_session(model: str = 'openai:gpt-4'):
    """Manage agent lifecycle"""
    agent = Agent(model)
    try:
        yield agent
    finally:
        # Cleanup resources
        await agent.cleanup()

# Usage with proper resource management
async def main():
    async with agent_session() as agent:
        result = await agent.run("Hello world")
        print(result.data)

# Batch processing with limits
async def batch_process(requests: List[str], max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single(request):
        async with semaphore:
            async with agent_session() as agent:
                return await agent.run(request)
    
    tasks = [process_single(req) for req in requests]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### 4. Testing Patterns

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic_ai import Agent
from pydantic import BaseModel

class TestResult(BaseModel):
    status: str
    message: str

@pytest.fixture
def mock_agent():
    agent = Agent('openai:gpt-4', result_type=TestResult)
    agent.tools = []  # Remove real tools for testing
    return agent

@pytest.mark.asyncio
async def test_agent_response(mock_agent):
    # Mock the actual LLM call
    mock_agent._raw_run = AsyncMock(return_value=MagicMock(
        data=TestResult(status="success", message="Test passed")
    ))
    
    result = await mock_agent.run("test prompt")
    assert result.data.status == "success"
    assert "Test passed" in result.data.message

def test_tool_function():
    """Test tool functions independently"""
    from my_agent import search_tool
    
    # Test tool function directly
    result = search_tool("python", MockDeps())
    assert isinstance(result, SearchResult)
    assert result.query == "python"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Errors

```python
# Issue: API key not found
import os

# ✅ Solution: Check environment variables
print("OpenAI API Key:", "set" if os.getenv('OPENAI_API_KEY') else "NOT SET")

# ✅ Solution: Validate credentials
from pydantic_ai.providers.openai import OpenAIProvider

try:
    provider = OpenAIProvider(api_key=os.getenv('OPENAI_API_KEY'))
    # Test the connection
    models = provider.models()
    print(f"Available models: {models}")
except Exception as e:
    print(f"Authentication failed: {e}")
```

#### 2. Model Compatibility

```python
# Issue: Model doesn't support required features
from pydantic_ai.models import Model

# ✅ Solution: Check model capabilities
def check_model_compatibility(model_name: str, needs_tools: bool = True) -> bool:
    model = Model(model_name)
    capabilities = model.capabilities
    
    if needs_tools and not capabilities.supports_tools:
        print(f"Model {model_name} doesn't support tools")
        return False
    
    if not capabilities.supports_structured_outputs:
        print(f"Model {model_name} doesn't support structured outputs")
        return False
    
    return True

# Usage
if check_model_compatibility('openai:gpt-3.5-turbo', needs_tools=True):
    agent = Agent('openai:gpt-3.5-turbo')
else:
    agent = Agent('openai:gpt-4')  # Fallback to capable model
```

#### 3. Tool Execution Errors

```python
# Issue: Tools failing during execution
import logging
from pydantic_ai import Agent, RunContext

# ✅ Solution: Add comprehensive logging
logging.basicConfig(level=logging.DEBUG)

@agent.tool
def monitored_tool(data: str, ctx: RunContext) -> str:
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Executing tool with data: {data}")
        
        result = external_api_call(data)
        logger.info(f"Tool execution successful: {result}")
        
        return result
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise ModelRetry(f"Tool failed: {str(e)}")

# ✅ Solution: Implement tool timeouts
import asyncio

@agent.tool
async def timeout_tool(query: str) -> str:
    try:
        # Set timeout for external calls
        result = await asyncio.wait_for(
            external_api_call_async(query),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        raise ModelRetry("Tool execution timed out")
```

#### 4. Validation Errors

```python
# Issue: LLM output doesn't match Pydantic schema
from pydantic import ValidationError
from pydantic_ai import Agent

class StructuredOutput(BaseModel):
    name: str
    age: int
    email: str

agent = Agent('openai:gpt-4', result_type=StructuredOutput)

# ✅ Solution: Handle validation errors gracefully
async def safe_agent_call(prompt: str) -> StructuredOutput:
    try:
        result = await agent.run(prompt)
        return result.data
    except ValidationError as e:
        # Log the error and try again with more specific instructions
        logging.error(f"Validation failed: {e}")
        
        # Retry with improved prompt
        improved_prompt = f"""{prompt}

Please respond with valid JSON matching this schema:
{{
    "name": "string",
    "age": "integer", 
    "email": "string"
}}"""
        
        result = await agent.run(improved_prompt)
        return result.data
```

### Debugging Tools

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add detailed agent logging
from pydantic_ai import Agent

agent = Agent('openai:gpt-4', system_prompt='You are helpful')

# Enable request/response logging
agent.run(
    "test prompt",
    stream_handler=lambda chunk: print(f"Streaming: {chunk}"),
    verbose=True  # Enable verbose logging
)

# Trace tool execution
@agent.tool
def logged_tool(data: str) -> str:
    import inspect
    frame = inspect.currentframe()
    print(f"Tool called from: {frame.f_back.f_code.co_filename}:{frame.f_back.f_lineno}")
    
    result = process_data(data)
    print(f"Tool returned: {result}")
    return result
```

## Quick Reference

### Essential Commands

```bash
# Installation
pip install pydantic-ai
uv add pydantic-ai

# CLI usage
clai                    # Interactive mode
python script.py        # Run agent script

# Environment setup
export OPENAI_API_KEY='key'
export ANTHROPIC_API_KEY='key'
```

### Common Patterns

```python
# Quick agent setup
Agent('openai:gpt-4')                              # Basic agent
Agent('openai:gpt-4', result_type=MyModel)         # With structured output
Agent('openai:gpt-4', tools=[my_tool])             # With tools
Agent('openai:gpt-4', deps_type=MyDeps)            # With dependencies

# Quick run patterns
agent.run("prompt")                                 # Sync call
await agent.run("prompt")                          # Async call
agent.run("prompt", stream=True)                   # Streaming

# Quick tool decorators
@agent.tool                                         # Standard tool
@agent.tool_plain                                  # Simple tool
@agent.tool_plain                                # Async tool
```

### Error Handling Quick Reference

```python
from pydantic_ai.exceptions import ModelRetry, ModelError

try:
    result = agent.run("prompt")
except ModelRetry:
    # Temporary failure, retry
    pass
except ModelError:
    # Permanent failure
    pass
except ValidationError:
    # Output validation failed
    pass
```

## Resources

### Official Documentation
- **Main Documentation**: [ai.pydantic.dev](https://ai.pydantic.dev/)
- **GitHub Repository**: [github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai)
- **API Reference**: [ai.pydantic.dev/api/](https://ai.pydantic.dev/api/)

### Examples and Tutorials
- **Official Examples**: [ai.pydantic.dev/examples/](https://ai.pydantic.dev/examples/)
- **Setup Guide**: [ai.pydantic.dev/examples/setup](https://ai.pydantic.dev/examples/setup)
- **Weather Agent Tutorial**: [ai.pydantic.dev/examples/weather-agent](https://ai.pydantic.dev/examples/weather-agent)

### Model Providers
- **OpenAI**: [ai.pydantic.dev/models/openai](https://ai.pydantic.dev/models/openai)
- **Anthropic**: [ai.pydantic.dev/models/anthropic](https://ai.pydantic.dev/models/anthropic)
- **Google Gemini**: [ai.pydantic.dev/models/google-gemini](https://ai.pydantic.dev/models/google-gemini)
- **Model Overview**: [ai.pydantic.dev/models/overview](https://ai.pydantic.dev/models/overview/)

### Community and Support
- **GitHub Issues**: [github.com/pydantic/pydantic-ai/issues](https://github.com/pydantic/pydantic-ai/issues)
- **Pydantic Slack**: #pydantic-ai channel
- **Help Documentation**: [ai.pydantic.dev/help](https://ai.pydantic.dev/help)

### Advanced Topics
- **Multi-Agent Applications**: [ai.pydantic.dev/multi-agent-applications/](https://ai.pydantic.dev/multi-agent-applications/)
- **Tools Advanced**: [ai.pydantic.dev/tools-advanced](https://ai.pydantic.dev/tools-advanced)
- **Retries**: [ai.pydantic.dev/retries](https://ai.pydantic.dev/retries)
- **Settings API**: [ai.pydantic.dev/api/settings/](https://ai.pydantic.dev/api/settings/)

### Third-Party Integrations
- **Third-Party Tools**: [ai.pydantic.dev/third-party-tools](https://ai.pydantic.dev/third-party-tools)
- **Logfire Integration**: [ai.pydantic.dev/logfire/](https://ai.pydantic.dev/logfire/)

---

This reference guide covers the essential aspects of PydanticAI for daily developer use. The framework's strength lies in its type safety, production-ready features, and excellent developer experience. Focus on the structured output patterns and dependency injection features for the most benefit in production applications.
