# Broadband Agent Architecture

This document describes the refactored architecture of the broadband comparison agent, following Pydantic AI best practices.

## Overview

The agent has been redesigned with:
- **Dependency Injection**: All services are injectable for testability
- **Type Safety**: Full type hints with Pydantic models
- **Separation of Concerns**: Clear boundaries between layers
- **Structured Outputs**: Tools return rich, typed results
- **Singleton Pattern**: Agent instance reused across calls
- **Stateless Design**: Frontend manages conversation history

## Architecture Components

### 1. Configuration (`config.py`)

**AgentConfig**
- Immutable configuration loaded from environment variables
- Contains model name, timeouts, feature flags, etc.
- Factory method: `create_default_config()`

**AgentDependencies**
- Container for all injectable dependencies
- Includes: config, logger, url_generator
- Immutable to ensure thread safety
- Factory method: `create_default_dependencies()`

### 2. URL Generator (`url_generator.py`)

**URLGenerator Class**
- Injectable service for URL generation
- Can be mocked for testing
- Returns structured `URLGenerationResult`

**URLGenerationResult**
- Success status and error messages
- Generated URL (when successful)
- Parameters used and missing parameters
- Suggestions for refinement

**BroadbandParams**
- Pydantic model with strict validation
- Enums for allowed values
- Helper methods like `get_missing_parameters()`

### 3. Observability (`observability.py`)

**InteractionLogger**
- Injectable logger (no global singleton)
- Logs interactions, tool calls, and errors
- JSONL format for structured logs
- Factory method: `create_interaction_logger()`

### 4. Agent (`agent.py`)

**Agent Factory Pattern**
```python
# Get singleton agent with default dependencies
agent = get_agent()

# Or with custom dependencies
deps = create_default_dependencies()
agent = get_agent(deps)

# Reset agent (useful for testing)
reset_agent()
```

**Tools**

1. `generate_url(params: BroadbandParams) -> URLGenerationResult`
   - Generates broadband comparison URLs
   - Requires postcode at minimum
   - Returns rich result with suggestions

2. `validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]`
   - Validates extracted parameters
   - Identifies missing fields
   - Provides context-aware suggestions

**Public API**

```python
def chat_with_agent(
    user_message: str,
    deps: Optional[AgentDependencies] = None
) -> AgentOutput
```

- Stateless function (no internal history)
- Frontend should pass message_history if needed
- Returns structured AgentOutput with message and URLs

## Key Design Decisions

### 1. Dependency Injection Over Global State

**Before:**
```python
# Global singleton
interaction_logger = InteractionLogger()

def tool():
    interaction_logger.log_tool_call(...)
```

**After:**
```python
def tool(ctx: RunContext[AgentDependencies]):
    ctx.deps.logger.log_tool_call(...)
```

**Benefits:**
- Testable (can inject mocks)
- Configurable (different loggers per environment)
- Clear dependencies

### 2. Structured Tool Outputs

**Before:**
```python
def generate_url_tool(...) -> str:
    return "Failed to generate URL: error"
    # or
    return validated_url  # HttpUrl type
```

**After:**
```python
def generate_url(...) -> URLGenerationResult:
    return URLGenerationResult(
        success=False,
        message="Failed to generate URL: error",
        ...
    )
```

**Benefits:**
- Type-safe contracts
- Rich error information
- Agent can extract URLs easily
- Suggestions for improvement

### 3. Agent Singleton with Proper Lifecycle

**Before:**
```python
def chat_with_agent(...):
    agent = _create_agent()  # Fresh agent each time
    result = agent.run_sync(...)
```

**After:**
```python
_agent_instance = None

def get_agent(deps):
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = _create_agent(deps)
    return _agent_instance

def chat_with_agent(...):
    agent = get_agent(deps)
    result = agent.run_sync(...)
```

**Benefits:**
- No event loop conflicts
- Better performance (reuse agent)
- Proper lifecycle management

### 4. Frontend-Managed History

**Before:**
```python
# Backend persists history to JSON file
_save_message_history_json(json_bytes)
```

**After:**
```python
# Frontend passes history each call
result = agent.run_sync(
    user_message,
    message_history=previous_messages  # Frontend's responsibility
)
```

**Benefits:**
- Stateless backend (scalable)
- Better separation of concerns
- Frontend controls session lifecycle

### 5. Clean System Prompt

**Before:**
```
- Speed options: 10Mb, 30Mb, 55Mb, 100Mb
- Contract lengths: 12 months, 18 months, 24 months
- Phone calls options: Cheapest, Show me everything, ...
[... detailed validation rules ...]
```

**After:**
```
Your Workflow:
1. Understand user requirements
2. Extract parameters (postcode REQUIRED)
3. Use tools to generate URLs
...
```

**Benefits:**
- Validation in code (Pydantic validators)
- Prompt focuses on behavior, not rules
- Easier to maintain

## Usage Examples

### Basic Usage

```python
from agent import chat_with_agent

# Simple call with defaults
response = chat_with_agent("I need broadband in E14 9WB")

print(response.message)  # Human-friendly message
print(response.urls)     # List of generated URLs
```

### With Custom Dependencies

```python
from config import AgentConfig, AgentDependencies, create_default_config
from observability import create_interaction_logger
from url_generator import URLGenerator

# Create custom config
config = AgentConfig(
    model_name="gemini-2.5-flash",
    base_url="https://custom-url.com",
)

# Create dependencies
deps = AgentDependencies(
    config=config,
    logger=create_interaction_logger("custom.jsonl"),
    url_generator=URLGenerator(config.base_url),
)

# Use with agent
response = chat_with_agent("Find me broadband", deps=deps)
```

### Testing

```python
from unittest.mock import Mock
from config import AgentDependencies
from agent import reset_agent, get_agent

# Create mock dependencies
mock_logger = Mock()
mock_generator = Mock()

deps = AgentDependencies(
    config=create_default_config(),
    logger=mock_logger,
    url_generator=mock_generator,
)

# Reset and create agent with mocks
reset_agent()
agent = get_agent(deps)

# Now tool calls will use mocked dependencies
```

## Next Steps: Frontend Integration

The frontend should:

1. **Initialize Dependencies Once**
   ```python
   deps = create_default_dependencies()
   ```

2. **Manage Message History**
   ```python
   # In session state
   if 'messages' not in st.session_state:
       st.session_state.messages = []
   ```

3. **Call Agent with History**
   ```python
   result = agent.run_sync(
       user_message,
       message_history=st.session_state.messages,
       deps=deps
   )
   
   # Update history
   st.session_state.messages = result.all_messages()
   ```

4. **Display Results**
   ```python
   # Show message
   st.write(result.output.message)
   
   # Show URLs
   for url in result.output.urls:
       st.link_button("Compare Deals", url)
   ```

## File Structure

```
jmi-broadband-agent/
├── config.py              # Configuration and dependencies
├── url_generator.py       # URL generation service
├── observability.py       # Logging and monitoring
├── agent.py              # Main agent with tools
├── ARCHITECTURE.md       # This file
└── requirements.txt      # Dependencies (to be created)
```

## Configuration via Environment Variables

```bash
# .env file
AGENT_MODEL_NAME=gemini-2.5-flash
AGENT_MAX_RETRIES=3
AGENT_ENABLE_STREAMING=true
AGENT_DEFAULT_SORT=Recommended
AGENT_REQUIRE_POSTCODE=true
AGENT_LOG_FILE=agent_interactions.jsonl
BROADBAND_BASE_URL=https://broadband.justmovein.co/packages
```

## Benefits Summary

1. **Testable**: All dependencies injectable, easy to mock
2. **Type-Safe**: Full type hints, Pydantic validation
3. **Maintainable**: Clear separation of concerns
4. **Scalable**: Stateless design, singleton pattern
5. **Observable**: Rich logging via injectable logger
6. **Flexible**: Configuration via environment variables
7. **Robust**: Structured errors, validation in code
8. **Developer-Friendly**: Clear contracts, good defaults

