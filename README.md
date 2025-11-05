# Broadband Comparison Agent

An AI-powered agent that generates personalized broadband comparison URLs through natural language conversations. Built with **Pydantic AI** following best practices for type safety, dependency injection, and maintainability.

## 🚀 Quick Start

```bash
# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up API key (required)
export GEMINI_API_KEY="your-api-key"

# Run the Streamlit web app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

**Note**: If you encounter import errors, make sure the virtual environment is activated with `source venv/bin/activate`

## ✨ Features

- 🤖 **Natural Language Interface** - Chat naturally to find broadband deals
- 📍 **UK Postcode Validation** - Ensures valid UK postcodes (e.g., E14 9WB, SW10 9PA)
- 🎯 **Smart Filtering** - Speed, contract length, providers, phone calls, and more
- 💬 **Multi-Turn Conversations** - Refine searches across multiple messages
- 🔗 **URL Generation** - Creates valid comparison URLs with all filters applied
- 💾 **Auto-Save** - Conversation history persists automatically
- 📊 **Observability** - Comprehensive logging for monitoring

## 🎯 Usage Example

```
You: I need broadband in E14 9WB

Agent: Here are the broadband deals for E14 9WB...

🔗 Open Deal #1
https://broadband.justmovein.co/packages?location=E14+9WB#/?...

To make this more specific, you could tell me about:
- Speed: Do you have a preferred speed (10Mb, 30Mb, 55Mb, 100Mb)?
- Contract Length: How long (12, 18, or 24 months)?
...

You: Show me 100Mb deals with BT

Agent: Here's an updated URL filtered for BT with 100Mb speed...
```

## 🏗️ Architecture

The system is built with clean architecture and dependency injection:

```
┌──────────────────┐
│   app.py (UI)    │ - Streamlit interface
│                  │ - Message history management
└────────┬─────────┘
         │
┌────────▼─────────┐
│   agent.py       │ - Pydantic AI agent
│                  │ - Tool orchestration
│                  │ - Multi-turn conversation handling
└────────┬─────────┘
         │
         ├─────────────────────────┐
         │                         │
┌────────▼─────────┐   ┌──────────▼──────────┐
│  url_generator.py│   │  observability.py   │
│  - URL builder   │   │  - Logging          │
│  - Validation    │   │  - Monitoring       │
└──────────────────┘   └─────────────────────┘
```

**Key Components:**

- `agent.py` - Main AI agent with tools for URL generation and parameter validation
- `url_generator.py` - Pydantic-based URL generation with strict typing
- `config.py` - Configuration and dependency injection setup
- `observability.py` - Logging and monitoring infrastructure
- `app.py` - Streamlit web interface

## 🔧 Configuration

Optional environment variables (create `.env` file):

```bash
AGENT_MODEL_NAME=gemini-2.5-flash
BROADBAND_BASE_URL=https://broadband.justmovein.co/packages
AGENT_LOG_FILE=agent_interactions.jsonl
```

## 📁 Project Structure

```
jmi-broadband-agent/
├── agent.py                # Core AI agent
├── url_generator.py        # URL generation service
├── config.py              # Configuration & dependencies  
├── observability.py       # Logging & monitoring
├── app.py                 # Streamlit web interface
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🎨 Design Principles

### Type Safety
All parameters are validated using Pydantic models with strict typing:

```python
class BroadbandParams(BaseModel):
    postcode: str  # Required, UK format
    speedInMb: Optional[Speed]  # Enum: 10Mb, 30Mb, 55Mb, 100Mb
    contractLength: Optional[ContractLength]  # Enum: 12, 18, 24 months
    providers: Optional[List[str]]
    # ... more fields
```

### Dependency Injection
All services are injectable for testability and flexibility:

```python
class AgentDependencies(BaseModel):
    config: AgentConfig
    logger: InteractionLogger
    url_generator: URLGenerator
```

### Structured Outputs
Tools return rich, typed results:

```python
class URLGenerationResult(BaseModel):
    success: bool
    message: str
    url: Optional[HttpUrl]
    parameters_used: Dict[str, Any]
    missing_parameters: List[str]
    suggestions: List[str]
```

## 🛠️ Development

### Agent Tools

1. **generate_url** - Generates broadband comparison URLs
   - Input: `BroadbandParams` (postcode required)
   - Output: `URLGenerationResult` with URL and suggestions

2. **validate_parameters** - Analyzes parameters for multi-turn conversations
   - Input: Parameter dictionary
   - Output: Validation result with missing fields and suggestions

### Running the App

```bash
# Start the Streamlit app
streamlit run app.py

# The app includes:
# - Auto-load previous conversation
# - Auto-save after each message
# - Clear history button
# - Auto-open URLs option
```

## 📊 Technical Highlights

- **Pydantic AI** for type-safe agent development
- **Pydantic v2** for data validation and serialization
- **Gemini 2.5 Flash** as the LLM model
- **Streamlit** for the web interface
- **Dependency injection** throughout for testability
- **Immutable config** for thread safety
- **JSONL logging** for observability

## 📄 Requirements

- Python 3.9+
- Google API key (for Gemini model)
- Dependencies listed in `requirements.txt`

---

**Built for JMI AI Ops Take-home Assignment**
