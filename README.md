# Broadband Comparison Agent

An AI-powered agent that helps users find broadband deals through natural language conversation. Built with **Pydantic AI** following best practices for type safety, dependency injection, and maintainability.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit web app
streamlit run app.py

# Or run CLI app
python cli_app.py

# Or run examples
python example_usage.py
```

## ✨ Features

- 🤖 **Natural Language Interface** - Chat naturally to find broadband deals
- 📍 **Postcode-Based Search** - UK postcode validation and URL generation
- 🎯 **Smart Filtering** - Speed, contract length, providers, and more
- 💬 **Multi-Turn Conversations** - Refine searches across multiple messages
- 🔗 **Auto-Generated URLs** - Direct comparison links with auto-open option
- 💾 **Session Persistence** - Save and load conversation history
- 📊 **Observability** - Comprehensive logging and monitoring
- 🧪 **Fully Testable** - Dependency injection for easy mocking

## 🏗️ Architecture

The agent is built with clean architecture principles:

```
┌──────────────────────────────────────────────────────┐
│                  Frontend Layer                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  app.py     │  │ cli_app.py   │  │ example.py  │ │
│  │ (Streamlit) │  │   (CLI)      │  │  (Scripts)  │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘ │
└─────────┼────────────────┼─────────────────┼────────┘
          │                │                 │
          └────────────────┴─────────────────┘
                           │
              ┌────────────▼────────────┐
              │   Agent Layer           │
              │  ┌──────────────────┐   │
              │  │   agent.py       │   │
              │  │  • Singleton     │   │
              │  │  • Tools         │   │
              │  │  • Orchestration │   │
              │  └────────┬─────────┘   │
              └───────────┼─────────────┘
                          │
              ┌───────────▼─────────────┐
              │  Dependency Injection   │
              │  ┌──────────────────┐   │
              │  │   config.py      │   │
              │  │  • AgentConfig   │   │
              │  │  • Dependencies  │   │
              │  └────────┬─────────┘   │
              └───────────┼─────────────┘
                          │
      ┌───────────────────┼───────────────────┐
      │                   │                   │
┌─────▼──────┐  ┌─────────▼────────┐  ┌──────▼──────┐
│ url_       │  │ observability.py │  │ Other       │
│ generator  │  │ • Logging        │  │ Services    │
│ .py        │  │ • Monitoring     │  │             │
└────────────┘  └──────────────────┘  └─────────────┘
```

## 📁 Project Structure

```
jmi-broadband-agent/
├── agent.py                    # Main agent with tools
├── config.py                   # Configuration & dependencies
├── url_generator.py            # URL generation service
├── observability.py            # Logging & monitoring
│
├── app.py                      # Streamlit web UI
├── cli_app.py                  # Command-line interface
├── example_usage.py            # Usage examples
│
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (optional)
│
├── README.md                   # This file
├── ARCHITECTURE.md             # Detailed architecture docs
├── REFACTORING_SUMMARY.md      # Refactoring details
└── APP_GUIDE.md                # Application usage guide
```

## 🎯 Usage Examples

### Streamlit Web App

```bash
streamlit run app.py
```

**Features:**
- Beautiful chat interface
- Clickable URL links
- Save/Load conversations
- Auto-open URLs
- Session statistics

**Example conversation:**
```
You: I need broadband in E14 9WB

Agent: I found broadband deals for postcode E14 9WB. 
       Here's a comparison URL with available packages...
       
🔗 Generated URL: [Click to view deals]

You: Show me only BT deals with 100Mb speed

Agent: Here's an updated URL filtered for BT with 100Mb speed...
```

### CLI App

```bash
python cli_app.py
```

**Commands:**
- `/clear` - Clear history
- `/save` - Save conversation
- `/load` - Load conversation
- `/auto` - Toggle auto-open URLs
- `/quit` - Exit

### Programmatic Usage

```python
from agent import chat_with_agent

# Simple query
response = chat_with_agent("Find broadband in E14 9WB")

print(response.message)  # Human-friendly message
print(response.urls)     # List of generated URLs
```

With message history:

```python
from agent import get_agent
from config import create_default_dependencies

# Initialize once
deps = create_default_dependencies()
agent = get_agent(deps)

# Run with history
result = agent.run_sync(
    "I need broadband in E14 9WB",
    message_history=previous_messages,
    deps=deps
)

# Get response
output = result.output
print(output.message)
for url in output.urls:
    print(f"URL: {url}")

# Update history for next turn
messages = result.all_messages()
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# Model configuration
AGENT_MODEL_NAME=gemini-2.5-flash
AGENT_MAX_RETRIES=3

# URLs and paths
BROADBAND_BASE_URL=https://broadband.justmovein.co/packages
AGENT_LOG_FILE=agent_interactions.jsonl

# Features
AGENT_ENABLE_STREAMING=true
AGENT_REQUIRE_POSTCODE=true
AGENT_DEFAULT_SORT=Recommended
```

### Programmatic Configuration

```python
from config import AgentConfig, AgentDependencies
from observability import create_interaction_logger
from url_generator import URLGenerator

# Custom config
config = AgentConfig(
    model_name="gemini-2.5-flash",
    base_url="https://custom-url.com",
    log_file="custom.jsonl"
)

# Custom dependencies
deps = AgentDependencies(
    config=config,
    logger=create_interaction_logger(config.log_file),
    url_generator=URLGenerator(config.base_url)
)

# Use with agent
from agent import chat_with_agent
response = chat_with_agent("Find broadband", deps=deps)
```

## 🛠️ Development

### Running Tests

```bash
# Run example to verify setup
python example_usage.py

# Check logs
cat agent_interactions.jsonl
```

### Code Structure

**Agent Tools:**
1. `generate_url(params: BroadbandParams)` - Generate comparison URLs
2. `validate_parameters(params: dict)` - Validate and suggest missing params

**Key Classes:**
- `AgentConfig` - Immutable configuration
- `AgentDependencies` - Injectable dependencies
- `URLGenerator` - URL generation service
- `InteractionLogger` - Logging and monitoring
- `BroadbandParams` - Validated search parameters
- `URLGenerationResult` - Structured tool output
- `AgentOutput` - Agent response format

## 📊 Message History Format

Uses Pydantic AI's native message format:

```json
[
  {
    "role": "user",
    "content": "I need broadband in E14 9WB"
  },
  {
    "role": "model",
    "content": {
      "message": "Generated URL for postcode E14 9WB...",
      "urls": ["https://broadband.justmovein.co/packages?location=E14+9WB..."]
    },
    "timestamp": "2025-11-05T12:34:56Z"
  }
]
```

**Persistence:**
- Saved to JSON files (`app_session_history.json`, `cli_session_history.json`)
- Loaded using `ModelMessagesTypeAdapter`
- Maintained across sessions

## 🎨 Design Principles

### 1. Dependency Injection
All services are injectable for testability:
```python
@agent.tool
def generate_url(ctx: RunContext[AgentDependencies], ...):
    ctx.deps.url_generator.generate(...)
    ctx.deps.logger.log_tool_call(...)
```

### 2. Type Safety
Full Pydantic validation:
```python
class BroadbandParams(BaseModel):
    postcode: str
    speedInMb: Optional[Speed]
    contractLength: Optional[ContractLength]
```

### 3. Structured Outputs
Rich, typed results:
```python
class URLGenerationResult(BaseModel):
    success: bool
    message: str
    url: Optional[HttpUrl]
    suggestions: List[str]
```

### 4. Separation of Concerns
- **Frontend**: UI and message history
- **Agent**: Tool orchestration
- **Services**: URL generation, logging
- **Config**: Settings and dependencies

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture and design decisions
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - What changed and why
- **[APP_GUIDE.md](APP_GUIDE.md)** - Complete application usage guide

## 🧪 Testing

### Unit Testing Example

```python
from unittest.mock import Mock
from config import AgentDependencies, AgentConfig
from agent import get_agent, reset_agent

# Create mocks
mock_logger = Mock()
mock_generator = Mock()
mock_generator.generate.return_value = URLGenerationResult(
    success=True,
    url="https://test.com",
    message="Test URL",
    parameters_used={},
    missing_parameters=[],
    suggestions=[]
)

# Inject mocks
deps = AgentDependencies(
    config=AgentConfig(),
    logger=mock_logger,
    url_generator=mock_generator
)

# Test
reset_agent()
agent = get_agent(deps)
# ... run tests with mocked dependencies
```

## 🚦 Status

✅ **Completed:**
- Dependency injection architecture
- Type-safe agent with tools
- URL generation service
- Observability and logging
- Streamlit web UI
- CLI interface
- Message history management
- Comprehensive documentation

🎯 **Next Steps:**
- Add authentication for multi-user
- Database storage for history
- Analytics dashboard
- REST API wrapper
- Enhanced UI styling

## 📄 License

This project is part of an interview assignment.

## 🤝 Contributing

This is a demonstration project. For questions or feedback, refer to the documentation files.

---

**Built with:**
- [Pydantic AI](https://ai.pydantic.dev/) - Framework
- [Pydantic](https://docs.pydantic.dev/) - Validation
- [Streamlit](https://streamlit.io/) - Web UI
- [Python 3.9+](https://www.python.org/) - Language
