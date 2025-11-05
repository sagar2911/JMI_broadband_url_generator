# Application Guide

This guide explains how to use the demo applications with the refactored broadband agent.

## Available Applications

### 1. Streamlit Web App (`app.py`)
Full-featured web UI with nice visuals and interactive controls.

### 2. CLI App (`cli_app.py`)
Simple command-line interface for testing and debugging.

### 3. Example Scripts (`example_usage.py`)
Programmatic examples showing the API.

## Installation

### Prerequisites
```bash
# Python 3.9+ required
python --version
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file (optional):
```bash
# .env
AGENT_MODEL_NAME=gemini-2.5-flash
AGENT_LOG_FILE=agent_interactions.jsonl
BROADBAND_BASE_URL=https://broadband.justmovein.co/packages
```

## Running the Applications

### Streamlit Web App

**Start the app:**
```bash
streamlit run app.py
```

**Features:**
- 💬 Interactive chat interface
- 🔗 Clickable URL links with "Open" buttons
- 💾 Save/Load conversation history
- 🗑️ Clear history
- ⚙️ Auto-open URLs option
- 📊 Session statistics
- 💡 Example queries

**Usage:**
1. Open the app in your browser (typically http://localhost:8501)
2. Type your query in the chat input
3. View generated URLs and click to open
4. Use sidebar controls to manage session

**Example Queries:**
- "I need broadband in E14 9WB"
- "Find deals in SW10 9PA with 100Mb speed"
- "Show me BT and Sky deals for 12 months"

### CLI App

**Start the app:**
```bash
python cli_app.py
```

**Commands:**
- `/clear` - Clear conversation history
- `/load` - Load saved conversation
- `/save` - Save current conversation
- `/auto` - Toggle auto-open URLs
- `/help` - Show available commands
- `/quit` - Exit application

**Usage:**
```
You: I need broadband in E14 9WB

Agent: I found broadband deals for postcode E14 9WB...

🔗 Generated URLs:
  1. https://broadband.justmovein.co/packages?location=...

You: Show me only BT deals with 100Mb speed

Agent: Here are BT deals with 100Mb speed...
```

### Example Scripts

**Run examples:**
```bash
python example_usage.py
```

This demonstrates:
- Basic single-turn usage
- Multi-turn conversations
- Custom dependencies
- Error handling

## Message History Management

Both apps properly manage Pydantic AI message history:

### Format
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
      "urls": ["https://..."]
    }
  }
]
```

### Storage
- **Streamlit**: `app_session_history.json`
- **CLI**: `cli_session_history.json`

### How It Works

**1. Initialization**
```python
from config import create_default_dependencies
from agent import get_agent

# Create dependencies once
deps = create_default_dependencies()
agent = get_agent(deps)
```

**2. Running with History**
```python
# Run agent with previous messages
result = agent.run_sync(
    user_input,
    message_history=previous_messages,
    deps=deps
)

# Get updated history
updated_messages = result.all_messages()
```

**3. Persistence**
```python
from pydantic_ai.messages import ModelMessagesTypeAdapter
import json

# Save
json_data = ModelMessagesTypeAdapter.dump_python(messages)
with open('history.json', 'w') as f:
    json.dump(json_data, f)

# Load
with open('history.json', 'r') as f:
    json_data = json.load(f)
messages = ModelMessagesTypeAdapter.validate_python(json_data)
```

## URL Display Features

### Streamlit App

**Clickable Links:**
```python
st.markdown(f"[{url}]({url})")
```

**Open Button:**
```python
if st.button("Open", key=f"open_{i}"):
    webbrowser.open_new_tab(url)
```

**Auto-Open:**
- Enable in sidebar settings
- Automatically opens first URL when generated

### CLI App

**Formatted Output:**
```
🔗 Generated URLs:
  1. https://broadband.justmovein.co/packages?location=E14+9WB...
  2. https://broadband.justmovein.co/packages?location=E14+9WB...
```

**Auto-Open:**
- Toggle with `/auto` command
- Opens first URL in default browser

## Architecture Integration

The apps integrate with the refactored agent architecture:

```
┌─────────────────────────────────────────────┐
│           Frontend (app.py)                 │
│  • Manages message history                  │
│  • Displays conversation                    │
│  • Handles user input                       │
└─────────────────┬───────────────────────────┘
                  │
                  │ chat_with_agent()
                  │ agent.run_sync()
                  │
┌─────────────────▼───────────────────────────┐
│           Agent Layer (agent.py)            │
│  • Singleton agent instance                 │
│  • Tool orchestration                       │
│  • Structured outputs                       │
└─────────────────┬───────────────────────────┘
                  │
                  │ Uses deps
                  │
┌─────────────────▼───────────────────────────┐
│      Dependencies (config.py)               │
│  • AgentConfig                              │
│  • InteractionLogger                        │
│  • URLGenerator                             │
└─────────────────────────────────────────────┘
```

## Troubleshooting

### Import Errors
```bash
# Ensure all dependencies installed
pip install -r requirements.txt

# Check Python version (3.9+)
python --version
```

### Streamlit Issues
```bash
# Clear Streamlit cache
streamlit cache clear

# Restart the app
# Press Ctrl+C and run again
streamlit run app.py
```

### Message History Issues
```bash
# Clear history files if corrupted
rm app_session_history.json
rm cli_session_history.json

# Or use the clear command in the app
/clear  # In CLI
```

### Agent Issues
```bash
# Check logs
cat agent_interactions.jsonl

# Verify environment variables
cat .env
```

## Best Practices

### 1. Session Management
- Save conversations regularly
- Clear history when starting new topic
- Use descriptive session names if implementing multi-session support

### 2. URL Handling
- Test URLs before auto-opening
- Consider rate limiting for multiple URLs
- Provide fallback if browser open fails

### 3. Error Handling
- Display user-friendly error messages
- Log errors to observability system
- Allow retry on failures

### 4. Performance
- Reuse agent instance (singleton pattern)
- Batch message history updates
- Consider pagination for long conversations

## Customization

### Adding New Features

**1. Add Custom Tool**
```python
# In agent.py
@agent.tool
def custom_tool(ctx: RunContext[AgentDependencies], ...):
    # Your logic here
    pass
```

**2. Custom UI Component**
```python
# In app.py
def render_custom_component(data):
    with st.container():
        # Your UI code
        pass
```

**3. Custom Configuration**
```python
# In config.py
class AgentConfig(BaseModel):
    # Add new fields
    custom_setting: str = "default"
```

## Next Steps

1. **Add Authentication** - Secure multi-user access
2. **Database Storage** - Replace JSON with database
3. **Analytics Dashboard** - Track usage patterns
4. **API Wrapper** - Create REST API around agent
5. **Enhanced UI** - Better styling and animations

## Support

For issues or questions:
1. Check the ARCHITECTURE.md for design details
2. Review REFACTORING_SUMMARY.md for recent changes
3. Run example_usage.py to verify setup
4. Check agent_interactions.jsonl for debugging

