

# FastMCP Python: Practical Code Editor Reference

## Overview

FastMCP is the de facto standard framework for building Model Context Protocol (MCP) servers in Python. Created by Jeremiah Lowin, it provides a high-level, Pythonic interface that handles complex protocol details so developers can focus on building functionality. FastMCP v2.13+ is actively maintained and offers enterprise-grade features including authentication, deployment tools, and comprehensive client libraries.

**Primary value**: Transform Python functions into MCP-accessible tools with minimal code overhead. In most cases, decorating a function with `@mcp.tool` is all you need.

**Latest version**: 2.13.1 (November 2025)  
**Requirements**: Python 3.10+  
**License**: Apache 2.0  
**GitHub**: 20.7k stars, actively maintained  

## Installation

### Basic Installation

```bash
# Install latest stable version
pip install fastmcp

# Verify installation
python -c "import fastmcp; print(fastmcp.__version__)"
```

### Installation Requirements

- **Python**: 3.10 or higher
- **Key dependencies**: Cyclopts v4+ (CLI functionality), pydantic (validation)
- **Optional**: FastAPI, requests (for specific integrations)

### Development Installation

```bash
# Install from source for latest features
git clone https://github.com/jlowin/fastmcp.git
cd fastmcp
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Installation Verification

```python
#!/usr/bin/env python3
"""Verify FastMCP installation"""

try:
    import fastmcp
    print(f"✅ FastMCP {fastmcp.__version__} installed successfully")
    
    # Test basic functionality
    from fastmcp import FastMCP
    
    mcp = FastMCP("Test Server")
    
    @mcp.tool
    def test_tool() -> str:
        """Test tool"""
        return "Installation verified!"
        
    print("✅ Basic functionality test passed")
    
except ImportError as e:
    print(f"❌ Installation failed: {e}")
except Exception as e:
    print(f"⚠️  Verification error: {e}")
```

**Expected output**:
```
✅ FastMCP 2.13.1 installed successfully
✅ Basic functionality test passed
```

## Core Features

### 1. Tool Creation with Decorators

The fastest way to create MCP-accessible tools:

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool
def calculate_area(length: float, width: float) -> dict:
    """Calculate rectangle area"""
    return {
        "area": length * width,
        "length": length,
        "width": width,
        "units": "square units"
    }

@mcp.tool
def greet(name: str, formal: bool = False) -> str:
    """Greet someone"""
    if formal:
        return f"Good day, {name}."
    return f"Hey {name}!"

if __name__ == "__main__":
    mcp.run()
```

**Key features**:
- **Type hints**: Automatic parameter validation and conversion
- **Default values**: Support optional parameters
- **Docstrings**: Become tool descriptions for LLMs
- **Return types**: Dict/str/bytes supported

### 2. Resource Management

Expose file-like data to clients:

```python
from fastmcp import FastMCP

mcp = FastMCP("Data Server")

@mcp.resource("config://settings")
def get_config() -> str:
    """Get application configuration"""
    return '{"debug": true, "max_connections": 100}'

@mcp.resource("data://users/{user_id}")
def get_user_data(user_id: str) -> str:
    """Get user data by ID"""
    # Simulated user data
    return f'{{"id": "{user_id}", "name": "User {user_id}"}}'

@mcp.resource("files://{path}")
def read_file(path: str) -> str:
    """Read file contents"""
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"
```

**Usage patterns**:
- **URI templates**: `data://{id}/details` style routing
- **Dynamic parameters**: Path segments become function parameters
- **Return formats**: String content (JSON, text, etc.)

### 3. Async Support

For I/O-bound operations:

```python
import asyncio
from fastmcp import FastMCP

mcp = FastMCP("Async Server")

@mcp.tool
async def fetch_data(url: str) -> dict:
    """Fetch data from URL"""
    # Simulate async HTTP request
    await asyncio.sleep(0.1)
    return {"url": url, "status": "success", "data": "sample data"}

@mcp.tool
async def process_batch(items: list[str]) -> list[str]:
    """Process items in batch"""
    results = []
    for item in items:
        # Simulate processing
        await asyncio.sleep(0.01)
        results.append(f"processed_{item}")
    return results
```

### 4. Error Handling and Validation

Robust error handling built-in:

```python
from fastmcp import FastMCP
from pydantic import ValidationError

mcp = FastMCP("Robust Server")

@mcp.tool
def safe_divide(a: float, b: float) -> float:
    """Divide two numbers safely"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

@mcp.tool
def validate_email(email: str) -> dict:
    """Validate email format"""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return {"valid": False, "email": email, "reason": "Invalid format"}
    
    return {"valid": True, "email": email, "reason": "Valid email"}

# Custom error handling
@mcp.tool
def risky_operation(confidence: float) -> str:
    """Operation that might fail"""
    if confidence < 0.5:
        raise ValueError("Confidence too low for operation")
    
    if confidence > 1.0:
        raise ValueError("Confidence cannot exceed 1.0")
        
    return f"Operation successful with confidence {confidence}"
```

### 5. Context and Dependencies

Inject MCP context and dependencies:

```python
from fastmcp import FastMCP
from fastmcp.context import Context

mcp = FastMCP("Context Server")

@mcp.tool
def log_tool_usage(tool_name: str) -> str:
    """Log tool usage with context"""
    # Access MCP context (request info, session data, etc.)
    context = Context.current()
    
    # Log usage
    print(f"Tool {tool_name} called by {context.client_info}")
    
    return f"Logged usage of {tool_name}"

@mcp.tool
def get_server_info() -> dict:
    """Get server information"""
    return {
        "server_name": mcp.name,
        "version": "1.0.0",
        "capabilities": ["tools", "resources", "prompts"]
    }

# Initialize with dependencies
def create_enhanced_server(database_url: str):
    mcp = FastMCP("Enhanced Server")
    
    @mcp.tool
    def query_database(user_id: str) -> dict:
        """Query user database"""
        # Use injected database URL
        return {"user_id": user_id, "url": database_url}
    
    return mcp
```

## Common Workflows

### 1. Development Workflow (Local Testing)

```python
# server.py - Your MCP server
from fastmcp import FastMCP

mcp = FastMCP("Weather Service")

@mcp.tool
def get_weather(city: str, units: str = "celsius") -> dict:
    """Get current weather for a city"""
    # Mock weather data
    weather_db = {
        "new york": {"temp": 22, "condition": "sunny"},
        "london": {"temp": 18, "condition": "rainy"},
        "tokyo": {"temp": 25, "condition": "cloudy"}
    }
    
    city_key = city.lower()
    if city_key in weather_db:
        data = weather_db[city_key]
        if units == "fahrenheit":
            data["temp"] = data["temp"] * 9/5 + 32
        
        return {
            "city": city,
            "temperature": data["temp"],
            "units": units,
            "condition": data["condition"]
        }
    
    return {"error": f"Weather data not available for {city}"}

if __name__ == "__main__":
    mcp.run()  # Starts STDIO server
```

**Development testing**:
```bash
# Run your server
python server.py

# Or use fastmcp CLI
fastmcp run server.py

# Test with MCP Inspector
# (Install: pip install mcp-inspector)
mcp-inspector server.py
```

### 2. HTTP Deployment Workflow

For web deployment and remote access:

```python
# http_server.py
from fastmcp import FastMCP

mcp = FastMCP("HTTP API")

@mcp.tool
def search_products(query: str, limit: int = 10) -> dict:
    """Search products"""
    # Mock product search
    products = [
        {"id": 1, "name": "Python Book", "price": 29.99},
        {"id": 2, "name": "JavaScript Guide", "price": 34.99},
        {"id": 3, "name": "FastAPI Tutorial", "price": 39.99}
    ]
    
    results = [p for p in products if query.lower() in p["name"].lower()]
    return {
        "query": query,
        "results": results[:limit],
        "total": len(results)
    }

if __name__ == "__main__":
    # Start HTTP server on port 8000
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        title="Product Search API"
    )
```

**Deployment commands**:
```bash
# Development
python http_server.py

# Production (with gunicorn)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker http_server:app

# Container deployment
# Dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install fastmcp uvicorn
CMD ["uvicorn", "http_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Integration Workflow (FastAPI)

Expose existing FastAPI endpoints as MCP tools:

```python
# main.py
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI(title="My API")
mcp = FastMCP("API Gateway")

# Your existing FastAPI endpoints
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}

@app.get("/status")
async def get_status():
    return {"status": "ok", "version": "1.0.0"}

# Convert FastAPI routes to MCP tools
@mcp.tool
async def get_user_info(user_id: int) -> dict:
    """Get user information"""
    response = await app.router.routes[0].get("users", user_id)
    return response

@mcp.tool
async def check_api_status() -> dict:
    """Check API status"""
    response = await app.router.routes[1].get("status")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Alternative: Automatic FastAPI integration**:
```python
from fastmcp.fastapi import integrate_fastapi

# Create your FastAPI app
app = FastAPI()

@app.get("/weather/{city}")
async def get_weather(city: str):
    return {"city": city, "temp": 22}

# Automatically expose as MCP tools
mcp = integrate_fastapi(app, title="Weather API")

# Your FastAPI app now has MCP capabilities too!
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4. Testing Workflow

Built-in testing utilities:

```python
# test_server.py
import pytest
from fastmcp.testing import FastMCPTestClient

from my_server import mcp  # Import your server

def test_tools():
    """Test MCP tools"""
    client = FastMCPTestClient(mcp)
    
    # Test tool call
    result = client.call_tool("get_weather", {
        "city": "New York",
        "units": "celsius"
    })
    
    assert result.content[0].text == '{"temperature": 22, "city": "New York", "units": "celsius", "condition": "sunny"}'

def test_resources():
    """Test MCP resources"""
    client = FastMCPTestClient(mcp)
    
    # Test resource read
    result = client.read_resource("config://settings")
    
    assert result.contents[0].text == '{"debug": true, "max_connections": 100}'

def test_error_handling():
    """Test error scenarios"""
    client = FastMCPTestClient(mcp)
    
    # Test invalid tool call
    with pytest.raises(Exception):
        client.call_tool("nonexistent_tool", {})
    
    # Test tool with invalid parameters
    result = client.call_tool("safe_divide", {"a": 10, "b": 0})
    assert "error" in result.content[0].text
```

**Run tests**:
```bash
pytest test_server.py -v
```

### 5. Client Workflow (Consuming MCP Servers)

Connect to and use MCP servers:

```python
# mcp_client.py
from fastmcp.client import FastMCPClient

async def use_remote_mcp_server():
    """Use a remote MCP server"""
    client = FastMCPClient("http://localhost:8000")
    
    # Connect to server
    await client.connect()
    
    try:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Call a tool
        result = await client.call_tool("get_weather", {
            "city": "London",
            "units": "celsius"
        })
        print(f"Weather result: {result.content[0].text}")
        
        # Read a resource
        config = await client.read_resource("config://settings")
        print(f"Config: {config.contents[0].text}")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(use_remote_mcp_server())
```

## Configuration

### 1. Server Configuration

```python
# Basic configuration
mcp = FastMCP(
    "My Server",
    version="1.0.0",
    description="A sample MCP server"
)

# Advanced configuration
mcp = FastMCP(
    "Production Server",
    version="1.0.0",
    description="Production-ready MCP server",
    
    # Transport options
    transport="stdio",  # or "http", "sse"
    host="0.0.0.0",    # for HTTP transport
    port=8000,         # for HTTP transport
    cors_origins=["*"], # for HTTP transport
    
    # Server options
    debug=False,
    log_level="INFO",
    
    # Security
    auth_required=False,  # Enable authentication
    rate_limit=1000,      # Requests per minute
)

# Configure transport after creation
mcp.configure_transport(
    transport="http",
    host="127.0.0.1",
    port=8080,
    ssl_cert="path/to/cert.pem",
    ssl_key="path/to/key.pem"
)
```

### 2. Environment Configuration

```python
# config.py
import os
from typing import Optional

class ServerConfig:
    def __init__(self):
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
        self.api_key = os.getenv("API_KEY")
        
    def validate(self):
        """Validate configuration"""
        if self.auth_enabled and not self.api_key:
            raise ValueError("API key required when auth is enabled")

# Use configuration in server
config = ServerConfig()
config.validate()

mcp = FastMCP("Configured Server", debug=config.debug)

@mcp.tool
def get_database_info() -> dict:
    """Get database information"""
    return {
        "url": config.database_url,
        "debug_mode": config.debug,
        "auth_enabled": config.auth_enabled
    }
```

### 3. MCP Client Configuration

```python
# mcp_client_config.py
from fastmcp.client import FastMCPClient, ClientConfig

# Configure client
client_config = ClientConfig(
    timeout=30,           # Request timeout
    retry_attempts=3,     # Retry failed requests
    retry_delay=1.0,      # Delay between retries
    max_concurrent=10,    # Max concurrent requests
    cache_enabled=True,   # Enable response caching
    cache_ttl=300,        # Cache TTL in seconds
)

# Create configured client
client = FastMCPClient("http://localhost:8000", config=client_config)

# Usage with configuration
async def efficient_client_usage():
    async with client:
        # Tools will be cached and reused efficiently
        tools = await client.list_tools()
        result = await client.call_tool("my_tool", {"param": "value"})
```

### 4. FastAPI Integration Configuration

```python
# fastapi_integration.py
from fastmcp.fastapi import FastAPIIntegration

# Create FastAPI app
from fastapi import FastAPI
app = FastAPI(title="MCP-Enabled API")

# Configure MCP integration
mcp_integration = FastAPIIntegration(
    app=app,
    title="Enhanced API",
    description="FastAPI with MCP capabilities",
    
    # Tool configuration
    auto_expose_endpoints=True,
    tool_prefix="api_",
    
    # Security
    api_key_header="X-API-Key",
    require_api_key=True
)

# Manual tool creation
@mcp_integration.tool
def manual_tool() -> str:
    """Manually created tool"""
    return "Manual tool result"

# Auto-expose FastAPI endpoints as tools
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}

# These will be automatically exposed as MCP tools
```

### 5. Production Configuration

```python
# production_config.py
import logging
from fastmcp import FastMCP

# Production logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("production-server")

# Production server setup
def create_production_server():
    mcp = FastMCP(
        "Production Server",
        debug=False,
        log_level="INFO"
    )
    
    # Add production middleware
    @mcp.middleware
    async def logging_middleware(request, call_next):
        logger.info(f"Tool call: {request.tool_name}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status}")
        return response
    
    @mcp.middleware
    async def error_middleware(request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Tool error: {str(e)}")
            return {"error": str(e), "type": "internal_error"}
    
    # Add tools with error handling
    @mcp.tool
    def safe_operation(param: str) -> dict:
        """Safe production operation"""
        try:
            # Your production logic here
            result = process_param(param)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    return mcp

if __name__ == "__main__":
    server = create_production_server()
    server.run(host="0.0.0.0", port=8000)
```

## Best Practices

### 1. Tool Design Patterns

**✅ DO: Well-defined, single-purpose tools**
```python
@mcp.tool
def calculate_bmi(weight_kg: float, height_m: float) -> dict:
    """Calculate Body Mass Index"""
    if height_m <= 0:
        raise ValueError("Height must be positive")
    
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "underweight"
    elif bmi < 25:
        category = "normal"
    elif bmi < 30:
        category = "overweight"
    else:
        category = "obese"
    
    return {
        "bmi": round(bmi, 1),
        "category": category,
        "weight_kg": weight_kg,
        "height_m": height_m
    }
```

**❌ DON'T: Complex, multi-purpose tools**
```python
@mcp.tool
def do_everything(data: dict) -> dict:
    """Do everything with data"""
    # This is too complex and unclear
    # Better: Split into multiple focused tools
    result = {"processed": []}
    
    for item in data.get("items", []):
        # Processing logic mixed with validation
        # File operations
        # Database updates
        # Email sending
        result["processed"].append(item)
    
    return result
```

**✅ DO: Use type hints for validation**
```python
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    email: str
    age: int
    preferences: Optional[dict] = None

@mcp.tool
def create_user_profile(profile: UserProfile) -> dict:
    """Create a user profile"""
    return {
        "id": "user_123",
        "name": profile.name,
        "email": profile.email,
        "age": profile.age,
        "created_at": datetime.now().isoformat(),
        "preferences": profile.preferences or {}
    }
```

### 2. Error Handling Best Practices

**✅ DO: Provide clear error messages**
```python
@mcp.tool
def divide_numbers(a: float, b: float) -> dict:
    """Divide two numbers"""
    try:
        if b == 0:
            return {
                "error": "Division by zero",
                "suggestion": "Use a non-zero divisor"
            }
        
        result = a / b
        return {
            "result": result,
            "operation": f"{a} ÷ {b}",
            "a": a,
            "b": b
        }
    except Exception as e:
        return {
            "error": "Calculation failed",
            "details": str(e),
            "operation": f"{a} ÷ {b}"
        }
```

**❌ DON'T: Raise raw exceptions**
```python
@mcp.tool
def bad_division(a: float, b: float) -> dict:
    """Bad division - raises exceptions"""
    if b == 0:
        raise ValueError("Can't divide by zero!")  # Bad: LLM can't handle this well
    return {"result": a / b}  # Bad: Error details lost
```

### 3. Resource Management

**✅ DO: Use meaningful URIs and provide metadata**
```python
@mcp.resource("user://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """Get user profile by ID"""
    return f'{{"id": "{user_id}", "name": "User {user_id}"}}'

@mcp.resource("config://application")
def get_app_config() -> str:
    """Get application configuration"""
    return '{"theme": "dark", "language": "en"}'

@mcp.resource("docs://api/{endpoint}")
def get_api_docs(endpoint: str) -> str:
    """Get API documentation"""
    docs = {
        "users": "GET /users - List users\nPOST /users - Create user",
        "posts": "GET /posts - List posts\nPOST /posts - Create post"
    }
    return docs.get(endpoint, f"No documentation for {endpoint}")
```

### 4. Performance Optimization

**✅ DO: Use async for I/O operations**
```python
import asyncio
import aiohttp

@mcp.tool
async def fetch_multiple_urls(urls: List[str]) -> dict:
    """Fetch multiple URLs concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "results": [
                {"url": url, "status": "success", "content": result}
                if not isinstance(result, Exception)
                else {"url": url, "status": "error", "error": str(result)}
                for url, result in zip(urls, results)
            ]
        }

async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        return await response.text()
```

**✅ DO: Implement caching for expensive operations**
```python
import functools
import time

# Simple cache decorator
@functools.lru_cache(maxsize=128)
def expensive_calculation(n: int) -> dict:
    """Simulate expensive calculation"""
    time.sleep(1)  # Simulate slow operation
    return {"input": n, "result": n * n, "computed_at": time.time()}

@mcp.tool
def calculate_with_cache(n: int) -> dict:
    """Calculate with automatic caching"""
    return expensive_calculation(n)
```

### 5. Security Best Practices

**✅ DO: Validate and sanitize inputs**
```python
import re
from typing import Union

@mcp.tool
def search_files(directory: str, pattern: str) -> dict:
    """Search files in directory"""
    # Validate directory path
    if not re.match(r'^[a-zA-Z0-9/_-]+$', directory):
        return {"error": "Invalid directory path"}
    
    # Validate search pattern
    if len(pattern) > 100:
        return {"error": "Pattern too long"}
    
    # Simulate file search
    return {
        "directory": directory,
        "pattern": pattern,
        "matches": ["file1.txt", "file2.py", "file3.md"],
        "count": 3
    }

@mcp.tool
def safe_api_call(endpoint: str, data: dict) -> dict:
    """Make safe API call"""
    # Whitelist allowed endpoints
    allowed_endpoints = {"users", "posts", "comments"}
    
    if endpoint not in allowed_endpoints:
        return {"error": f"Endpoint '{endpoint}' not allowed"}
    
    # Validate data size
    if len(str(data)) > 10000:
        return {"error": "Data too large"}
    
    # Process request
    return {"endpoint": endpoint, "status": "success"}
```

**❌ DON'T: Expose all endpoints without validation**
```python
@mcp.tool
def dangerous_api_call(endpoint: str, data: dict) -> dict:
    """Dangerous - no validation"""
    # DON'T: This could expose dangerous operations
    import subprocess
    result = subprocess.run([endpoint, str(data)], capture_output=True)
    return {"result": result.stdout.decode()}
```

### 6. Documentation and Testing

**✅ DO: Write descriptive docstrings**
```python
@mcp.tool
def calculate_loan_payment(
    principal: float, 
    annual_rate: float, 
    years: int,
    payment_frequency: str = "monthly"
) -> dict:
    """
    Calculate loan payment details.
    
    Args:
        principal: Loan amount in dollars
        annual_rate: Annual interest rate as percentage (e.g., 5.5 for 5.5%)
        years: Loan term in years
        payment_frequency: Payment frequency - 'monthly', 'quarterly', or 'annual'
    
    Returns:
        Dictionary containing payment amount, total payments, and total interest
        
    Example:
        calculate_loan_payment(250000, 5.5, 30, 'monthly')
        # Returns: {'payment': 1417.68, 'total_payments': 510364.80, 'total_interest': 260364.80}
    """
    # Implementation here
    pass
```

**✅ DO: Test your tools thoroughly**
```python
import pytest
from fastmcp.testing import FastMCPTestClient

def test_loan_calculations():
    """Test loan calculation tools"""
    client = FastMCPTestClient(loan_server)  # Your server
    
    # Test normal case
    result = client.call_tool("calculate_loan_payment", {
        "principal": 250000,
        "annual_rate": 5.5,
        "years": 30,
        "payment_frequency": "monthly"
    })
    
    assert result.content[0].text  # Should not be empty
    
    # Test edge cases
    result = client.call_tool("calculate_loan_payment", {
        "principal": 0,
        "annual_rate": 5.5,
        "years": 30
    })
    assert "error" in result.content[0].text.lower()
```

### 7. Versioning and Compatibility

**✅ DO: Version your tools and handle changes**
```python
@mcp.tool
def get_user_profile_v1(user_id: str) -> dict:
    """Get user profile (v1.0)"""
    return {
        "version": "1.0",
        "user_id": user_id,
        "name": "User Name",
        "email": "user@example.com"
    }

@mcp.tool
def get_user_profile_v2(user_id: str, include_metadata: bool = True) -> dict:
    """Get user profile (v2.0)"""
    profile = {
        "version": "2.0",
        "user_id": user_id,
        "name": "User Name",
        "email": "user@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    if include_metadata:
        profile["metadata"] = {
            "last_login": "2024-01-15T10:30:00Z",
            "preferences": {"theme": "dark"}
        }
    
    return profile
```

**✅ DO: Handle deprecation gracefully**
```python
@mcp.tool
def legacy_user_lookup(user_id: str) -> dict:
    """DEPRECATED: Use get_user_profile_v2 instead"""
    import warnings
    warnings.warn(
        "legacy_user_lookup is deprecated, use get_user_profile_v2",
        DeprecationWarning
    )
    
    # Fallback to new implementation
    return get_user_profile_v2(user_id)
```

## Troubleshooting

### 1. Common Installation Issues

**Problem**: `ModuleNotFoundError: No module named 'fastmcp'`

**Solutions**:
```bash
# Check Python version (need 3.10+)
python --version

# Install in correct environment
python -m pip install fastmcp

# For system Python on macOS
sudo pip3 install fastmcp

# For conda environments
conda install -c conda-forge fastmcp

# If using virtual environments
source venv/bin/activate  # Linux/macOS
venv\\Scripts\\activate     # Windows
pip install fastmcp
```

**Problem**: `pip install fastmcp` fails with dependency conflicts

**Solutions**:
```bash
# Install with specific dependency versions
pip install fastmcp "cyclopts>=4.0.0" "pydantic>=1.10.0"

# Use pip resolver
pip install --use-feature=2020-resolver fastmcp

# Install in fresh virtual environment
python -m venv fresh_env
source fresh_env/bin/activate
pip install fastmcp

# Check for conflicting packages
pip check
```

### 2. Runtime Errors

**Problem**: `TypeError: unexpected keyword argument` when running tools

**Cause**: Tool parameter mismatch

**Debugging**:
```python
# Check your tool definition
@mcp.tool
def my_tool(param1: str, param2: int = 5) -> dict:
    return {"param1": param1, "param2": param2}

# Test with correct parameters
from fastmcp.testing import FastMCPTestClient

client = FastMCPTestClient(your_server)
result = client.call_tool("my_tool", {
    "param1": "test", 
    "param2": 10
})

# Check for missing required parameters
result = client.call_tool("my_tool", {
    "param2": 10  # Missing required param1
})
# This will raise an error
```

**Problem**: `ValidationError` when calling tools

**Solution**:
```python
# Ensure type hints are correct
@mcp.tool
def process_number(value: int) -> dict:  # ← Must be int, not str
    """Process a number"""
    return {"processed": value * 2}

# Test type validation
from fastmcp.testing import FastMCPTestClient

client = FastMCPTestClient(server)

# This will work (int)
result = client.call_tool("process_number", {"value": 42})

# This will fail (string)
try:
    result = client.call_tool("process_number", {"value": "42"})
except Exception as e:
    print(f"Type validation error: {e}")
```

### 3. Transport and Connection Issues

**Problem**: STDIO server not connecting

**Debugging**:
```python
# Test STDIO transport manually
if __name__ == "__main__":
    mcp = FastMCP("Debug Server")
    
    @mcp.tool
    def test_tool() -> str:
        return "STDIO working!"
    
    # Run with debug output
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    mcp.run(transport="stdio", debug=True)
```

**Problem**: HTTP server not accessible

**Solutions**:
```python
# Check server is binding correctly
if __name__ == "__main__":
    mcp = FastMCP("HTTP Server")
    
    @mcp.tool
    def health_check() -> dict:
        return {"status": "ok"}
    
    # Explicit host/port configuration
    mcp.run(
        transport="http",
        host="127.0.0.1",  # or "0.0.0.0" for external access
        port=8000,
        debug=True
    )

# Test connectivity
curl http://127.0.0.1:8000/health  # If you have health endpoint
```

**Problem**: CORS errors in browser clients

**Solution**:
```python
mcp = FastMCP("CORS-enabled Server")

# Enable CORS for specific origins
mcp.configure_transport(
    transport="http",
    cors_origins=[
        "http://localhost:3000",  # React dev server
        "https://your-app.com",   # Production domain
        "*"                      # All origins (development only)
    ],
    cors_methods=["GET", "POST"],
    cors_headers=["Content-Type", "Authorization"]
)
```

### 4. Testing and Debugging Issues

**Problem**: MCP Inspector not showing tools

**Debugging**:
```python
# Add debug output to your server
mcp = FastMCP("Debug Server", debug=True)

@mcp.tool
def debug_tool() -> str:
    """Tool for testing"""
    print(f"Tool called: debug_tool")  # Should appear in logs
    return "Debug tool working"

if __name__ == "__main__":
    # Run with full debugging
    mcp.run(debug=True, log_level="DEBUG")
```

**Problem**: Tools not appearing in client

**Checklist**:
1. ✅ Server is running
2. ✅ Tools are properly decorated with `@mcp.tool`
3. ✅ No exceptions in tool functions
4. ✅ Type hints are correct
5. ✅ Server and client are using same MCP version

**Debug client connection**:
```python
import asyncio
from fastmcp.client import FastMCPClient

async def debug_client():
    client = FastMCPClient("http://localhost:8000")
    
    try:
        await client.connect()
        
        # List all tools
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Check server info
        info = await client.get_server_info()
        print(f"Server: {info.name} v{info.version}")
        
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_client())
```

### 5. Performance Issues

**Problem**: Slow tool responses

**Solutions**:
```python
# Use async for I/O operations
import asyncio
import aiohttp

@mcp.tool
async def slow_io_task(url: str) -> dict:
    """Use async for HTTP requests"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            return {"url": url, "status": response.status, "size": len(content)}

# Add caching for expensive operations
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_computation(param: str) -> dict:
    """Cache expensive computations"""
    import time
    time.sleep(2)  # Simulate expensive work
    return {"param": param, "result": param.upper(), "computed": True}

@mcp.tool
def cached_computation(param: str) -> dict:
    """Cached computation"""
    return expensive_computation(param)

# Add connection pooling for HTTP transport
mcp = FastMCP("Optimized Server")
mcp.configure_transport(
    transport="http",
    max_connections=100,    # Increase connection pool
    connection_timeout=30,  # Increase timeout
    max_keepalive=30        # Keep connections alive
)
```

### 6. Deployment Issues

**Problem**: Server works locally but fails in production

**Production checklist**:
```python
# 1. Environment variables
import os
from pathlib import Path

# Load configuration
config = {
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
    "database_url": os.getenv("DATABASE_URL"),
    "api_keys": os.getenv("API_KEYS", "").split(",")
}

# 2. Logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/fastmcp.log')
    ]
)

# 3. Error handling
from fastapi import Request

@mcp.tool
def production_tool(data: dict) -> dict:
    """Production tool with error handling"""
    try:
        # Your production logic
        result = process_data(data)
        return {"success": True, "data": result}
    except Exception as e:
        logging.error(f"Tool error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Internal server error",
            "error_id": str(hash(str(e)))  # For log correlation
        }

# 4. Health checks
@mcp.tool
def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "environment": "production"
    }
```

**Container deployment**:
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  fastmcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - HOST=0.0.0.0
      - PORT=8000
      - DATABASE_URL=postgresql://user:pass@db:5432/app
    depends_on:
      - db
    restart: unless-stopped
    
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### 7. Authentication and Security

**Problem**: Authentication not working

**Debugging**:
```python
# Test authentication setup
mcp = FastMCP("Auth Server")

# Configure authentication
mcp.configure_auth(
    providers=["google", "github"],
    required=True
)

@mcp.tool
def protected_tool(data: str) -> dict:
    """Tool that requires authentication"""
    # Access current user from context
    from fastmcp.context import Context
    user = Context.current().user
    return {"user": user, "data": data}

# Test authentication
if __name__ == "__main__":
    import asyncio
    
    async def test_auth():
        from fastmcp.client import FastMCPClient
        
        client = FastMCPClient("http://localhost:8000")
        await client.connect()
        
        # Check if auth is required
        tools = await client.list_tools()
        for tool in tools:
            print(f"Tool: {tool.name}, Auth: {tool.metadata.get('auth_required', False)}")
    
    asyncio.run(test_auth())
```

**Problem**: Rate limiting issues

**Solution**:
```python
# Configure rate limiting
mcp = FastMCP("Rate Limited Server")

# Set rate limits per client
mcp.configure_rate_limit(
    requests_per_minute=60,  # Global limit
    requests_per_hour=1000,  # Per hour limit
    burst_limit=10           # Burst allowance
)

# Rate limit per tool
@mcp.tool(rate_limit=10)  # Max 10 calls per minute
def expensive_tool() -> dict:
    """Expensive tool with low rate limit"""
    return {"expensive": True}

@mcp.tool(rate_limit=100)  # Higher limit for simple tools
def simple_tool() -> dict:
    """Simple tool with higher limit"""
    return {"simple": True}
```

## Quick Reference

### Essential Commands

```bash
# Installation and setup
pip install fastmcp                          # Install latest version
python -c "import fastmcp; print(fastmcp.__version__)"  # Check version

# Development
fastmcp run server.py                        # Run server via CLI
python server.py                            # Run server directly

# Testing
mcp-inspector server.py                     # Test with MCP Inspector
pytest test_server.py                       # Run tests

# Client usage
fastmcp connect http://localhost:8000       # Connect to remote server
fastmcp list-tools                          # List available tools
fastmcp call-tool tool_name --param value   # Call specific tool
```

### Decorator Reference

```python
# Tool decorator
@mcp.tool
def my_tool(param: str, optional: int = 5) -> dict:
    """Tool description"""
    return {"result": param}

# Resource decorator  
@mcp.resource("pattern://{param}")
def my_resource(param: str) -> str:
    """Resource description"""
    return "resource content"

# Prompt decorator
@mcp.prompt("prompt_name")
def my_prompt(context: str) -> str:
    """Prompt template"""
    return f"Process: {context}"
```

### Configuration Options

```python
# Server configuration
mcp = FastMCP(
    "Server Name",
    version="1.0.0",
    description="Description",
    debug=True,
    transport="stdio",  # or "http", "sse"
    host="0.0.0.0",
    port=8000
)

# Transport configuration
mcp.configure_transport(
    transport="http",
    cors_origins=["*"],
    ssl_cert="path/to/cert.pem",
    rate_limit=1000
)

# Authentication
mcp.configure_auth(
    providers=["google", "github"],
    required=True
)
```

### Error Handling Patterns

```python
# Return structured errors
@mcp.tool
def safe_operation(param: str) -> dict:
    try:
        result = risky_operation(param)
        return {"success": True, "result": result}
    except ValueError as e:
        return {"success": False, "error": str(e), "type": "validation_error"}
    except Exception as e:
        return {"success": False, "error": str(e), "type": "internal_error"}

# Raise with context
@mcp.tool
def strict_operation(param: int) -> str:
    if param < 0:
        raise ValueError("Parameter must be non-negative")
    return f"Processed: {param}"
```

### Testing Quick Reference

```python
from fastmcp.testing import FastMCPTestClient

# Basic testing
client = FastMCPTestClient(server)

# Test tool calls
result = client.call_tool("tool_name", {"param": "value"})
assert result.content[0].text  # Check success

# Test resources
resource = client.read_resource("resource://pattern")
assert resource.contents[0].text  # Check content

# Test errors
try:
    client.call_tool("bad_tool", {})
except Exception:
    pass  # Expected error
```

### Integration Patterns

```python
# FastAPI integration
from fastmcp.fastapi import integrate_fastapi
mcp = integrate_fastapi(app, title="API Title")

# Client connection
from fastmcp.client import FastMCPClient
client = FastMCPClient("http://localhost:8000")
await client.connect()
tools = await client.list_tools()
result = await client.call_tool("tool_name", params)
await client.disconnect()

# Async tools
@mcp.tool
async def async_tool(param: str) -> dict:
    await some_async_operation()
    return {"async": True}
```

### Common Patterns

```python
# Data validation
from pydantic import BaseModel

class ToolInput(BaseModel):
    name: str
    age: int
    email: str

@mcp.tool
def validated_tool(input: ToolInput) -> dict:
    return {"processed": input.dict()}

# Caching
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_function(param: str) -> dict:
    return expensive_operation(param)

@mcp.tool
def tool_with_cache(param: str) -> dict:
    return cached_function(param)

# Error boundaries
@mcp.tool
def robust_tool(data: dict) -> dict:
    try:
        return process_data(data)
    except Exception as e:
        logging.error(f"Tool error: {e}")
        return {"error": "Processing failed", "details": str(e)}
```

### Troubleshooting Commands

```bash
# Check installation
pip list | grep fastmcp
python -c "import fastmcp; print('OK')"

# Debug server
python server.py --debug
fastmcp run server.py --verbose

# Test connectivity
curl -X POST http://localhost:8000/tools/tool_name \\
  -H "Content-Type: application/json" \\
  -d '{"param": "value"}'

# View logs
tail -f /var/log/fastmcp.log
python server.py 2>&1 | tee debug.log
```

## Resources

### Official Documentation
- **FastMCP Documentation**: https://gofastmcp.com/
- **Getting Started Guide**: https://gofastmcp.com/getting-started/welcome
- **API Reference**: https://gofastmcp.com/api/
- **Integration Guides**: https://gofastmcp.com/integrations/

### GitHub and Development
- **Main Repository**: https://github.com/jlowin/fastmcp
- **Issues and Support**: https://github.com/jlowin/fastmcp/issues
- **Discussions**: https://github.com/jlowin/fastmcp/discussions
- **Release Notes**: https://github.com/jlowin/fastmcp/releases

### Community and Learning
- **Discord Community**: Join the FastMCP Discord for real-time support
- **Community Showcase**: https://gofastmcp.com/showcase/
- **Tutorial Collection**: Search for "FastMCP tutorial" on YouTube and blogs
- **Stack Overflow**: Tag questions with `fastmcp` and `mcp`

### Protocol and Standards
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **Protocol Consortium**: https://modelcontextprotocol.io/about

### Tools and Utilities
- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector
- **FastAPI Integration**: https://github.com/jlowin/fastmcp/tree/main/integrations/fastapi
- **Example Projects**: https://github.com/jlowin/fastmcp/tree/main/examples

### Version Information
- **Current Version**: 2.13.1 (November 2025)
- **Minimum Python**: 3.10
- **License**: Apache 2.0
- **Main Maintainer**: Jeremiah Lowin (@jlowin)

### Getting Help
1. **Documentation**: Check official docs first
2. **GitHub Issues**: Search existing issues
3. **Discord**: Real-time community support
4. **Stack Overflow**: Tag with `fastmcp`
5. **GitHub Discussions**: Community Q&A

### Contributing
- **Contributing Guide**: https://github.com/jlowin/fastmcp/blob/main/CONTRIBUTING.md
- **Code Style**: Follow PEP 8 and project conventions
- **Testing**: Add tests for new features
- **Documentation**: Update docs for API changes

---

*This reference covers FastMCP 2.13.1 and the current MCP protocol specification. For the latest updates and breaking changes, always check the official repository and release notes.*
