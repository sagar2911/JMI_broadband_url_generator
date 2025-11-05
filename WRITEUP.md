# JMI Broadband Agent - Technical Writeup

## 1. Approach and Architecture Decisions

### Overall Architecture

I implemented a **clean architecture** with clear separation of concerns:

```
Frontend (app.py) → Agent (agent.py) → Services (url_generator.py, observability.py)
                           ↓
                    Config & DI (config.py)
```

**Key Design Decisions:**

1. **Dependency Injection Pattern**: All services (URL generator, logger) are injectable through `AgentDependencies`. This makes the code:
   - Highly testable (can inject mocks)
   - Maintainable (loose coupling)
   - Flexible (easy to swap implementations)

2. **Pydantic-First Design**: Everything uses Pydantic models for:
   - Automatic validation
   - Type safety
   - Structured inputs/outputs
   - JSON serialization

3. **Structured Outputs**: The agent uses `result_type=AgentOutput` to return consistent, typed responses with both human-readable messages and machine-readable URLs.

4. **Singleton Agent Pattern**: The agent is created once and reused across requests, improving performance and maintaining consistency.

### URL Generator Design

The `URLGenerator` class was designed to be:
- **Defensive**: Validates all inputs through Pydantic models
- **Helpful**: Returns suggestions for missing parameters
- **Type-safe**: Uses Enums for constrained values (Speed, ContractLength)
- **URL-safe**: Proper encoding with `urllib.parse.quote`

The `URLGenerationResult` model provides rich feedback:
```python
class URLGenerationResult(BaseModel):
    success: bool
    message: str
    url: Optional[HttpUrl]
    parameters_used: Dict[str, Any]
    missing_parameters: List[str]
    suggestions: List[str]
```

## 2. Framework Choice: Pydantic AI

**Why Pydantic AI?**

1. **Type Safety**: Pydantic AI integrates seamlessly with Pydantic v2, providing compile-time type checking and runtime validation. This prevents many bugs before they happen.

2. **Modern Python**: Uses modern Python features (async/await, type hints, generics) making the code cleaner and more maintainable.

3. **Dependency Injection Built-in**: `RunContext[Deps]` provides first-class support for DI, which is essential for testable code.

4. **Structured Outputs**: Native support for returning Pydantic models from tools and agents, ensuring consistency.

5. **Lightweight**: Unlike LangChain, Pydantic AI has minimal abstractions and a smaller learning curve.

**Comparison with Alternatives:**

- **vs LangChain**: Pydantic AI is more focused and type-safe. LangChain has many abstractions that can be overwhelming.
- **vs LangGraph**: Better for complex workflows, but overkill for this use case.
- **vs Raw LLM API**: Pydantic AI provides structure without losing flexibility.

## 3. Challenges Encountered and Solutions

### Challenge 1: Message History Management

**Problem**: Pydantic AI's message format differs from simple chat history. The app needs to persist and display conversations correctly.

**Solution**: 
- Used `ModelMessagesTypeAdapter` for proper serialization to JSON
- Implemented `extract_conversation_from_history()` to parse Pydantic AI's internal message structure (looking for `kind='request'` and `kind='response'` with `part_kind='tool-call'` containing `final_result`)
- Auto-save history after each interaction

**Code snippet:**
```python
def save_history_to_file(messages: List, filename: str):
    try:
        json_data = ModelMessagesTypeAdapter.dump_json(messages, indent=2)
        Path(filename).write_bytes(json_data)
```

### Challenge 2: HttpUrl JSON Serialization

**Problem**: Pydantic's `HttpUrl` type is not JSON serializable by default, causing errors when logging tool outputs.

**Solution**: 
- Used `model_dump(mode='json')` which converts `HttpUrl` to strings
- Updated `InteractionLogger.log_tool_call()` to handle non-serializable types gracefully

**Code snippet:**
```python
serializable_output = {}
for key, value in output.items():
    try:
        json.dumps(value)
        serializable_output[key] = value
    except (TypeError, ValueError):
        if hasattr(value, 'model_dump'):
            serializable_output[key] = value.model_dump(mode='json')
        else:
            serializable_output[key] = str(value)
```

### Challenge 3: Forward References in Pydantic

**Problem**: `AgentDependencies` referenced `InteractionLogger` and `URLGenerator` before they were fully defined, causing `PydanticUserError: class not fully defined`.

**Solution**: 
- Used `TYPE_CHECKING` to import types only for type checking
- Called `AgentDependencies.model_rebuild(_types_namespace={...})` with actual class objects in the factory function

**Code snippet:**
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from observability import InteractionLogger
    from url_generator import URLGenerator

# Later, in factory:
AgentDependencies.model_rebuild(
    _types_namespace={
        'InteractionLogger': InteractionLogger,
        'URLGenerator': URLGenerator
    }
)
```

### Challenge 4: UI State Management

**Problem**: Streamlit reruns the entire script on each interaction, causing the UI to clear and lose conversation history.

**Solution**:
- Properly update `st.session_state[SESSION_KEY_MESSAGES]` with `result.all_messages()`
- Use `st.rerun()` to ensure the entire conversation re-renders
- Implement auto-load from JSON file on first render

## 4. Enhanced Features Implemented

I implemented **two optional enhanced features**:

### Feature 1: Logging and Observability ✅

Comprehensive logging system with:
- **Tool call tracking**: Every tool invocation is logged with inputs, outputs, and execution time
- **Error tracking**: All errors are captured with context
- **JSONL format**: Machine-readable logs for analysis
- **Session tracking**: Each interaction is timestamped and traceable

**Files**: `observability.py`, `agent_interactions.jsonl`

### Feature 2: URL Navigation ✅

- Streamlit's `st.link_button()` opens URLs in a new tab
- Clean UI with "Open Deal #N" buttons
- No page clearing (preserves chat history)

## 5. What I Would Improve with More Time

### 1. Enhanced User Experience & Education

**Help Users Understand Filters**:
- Provide contextual explanations for technical terms (e.g., "What does 55Mb speed mean in practice?")
- Add examples for each parameter (e.g., "55Mb is suitable for HD streaming on 2-3 devices")
- Implement a beginner-friendly mode with simpler language
- Tone tuning: Make the agent more conversational and patient when users are unsure
- Add comparison helpers: "Is 100Mb worth it over 55Mb for my usage?"

**Web Scraping for Live Data**:
- Use Puppeteer/Playwright to fetch actual deal details from generated URLs
- Display real-time pricing, availability, and package details in the chat
- Show deal highlights directly in the UI without requiring users to click through
- Auto-refresh deals if they change while user is browsing
- Compare multiple deals side-by-side with scraped data

### 2. Real UK Postcode Validation

**Comprehensive Postcode Validation**:
- Integrate with postcodes.io API to verify postcode exists
- Check broadband availability by postcode (using Ofcom data or provider APIs)
- Inform users upfront if their area has limited options
- Suggest nearby postcodes if theirs has no availability
- Display coverage maps for different providers by postcode

**Implementation**:
```python
async def validate_uk_postcode(postcode: str) -> PostcodeValidationResult:
    # Call postcodes.io API
    # Check Ofcom broadband availability database
    # Return availability + providers in area
```

### 3. Personalization with Database & Memory

**User Profile Management**:
- SQLite/PostgreSQL database for user data
- Store user preferences (favorite providers, typical speed needs, budget)
- Track search history and patterns
- Personalized recommendations based on past interactions
- "Welcome back! Based on your last search for 100Mb deals..."

**Database Schema**:
```sql
users (id, name, email, created_at)
preferences (user_id, preferred_speed, preferred_providers, budget_range)
search_history (user_id, postcode, parameters, timestamp)
interactions (user_id, query, agent_response, satisfaction_score)
```

**Smart Memory**:
- Remember context across sessions: "You were looking at BT deals last time"
- Learn user preferences: "You always prefer shorter contracts"
- Proactive suggestions: "Prices dropped on the 100Mb plans you liked!"

### 4. Comprehensive Testing & Evaluation

**Pydantic AI Evals Integration**:
- Create evaluation dataset with diverse user queries
- Test agent's parameter extraction accuracy
- Measure response quality and helpfulness
- Track success rate of URL generation
- A/B test different system prompts

**Eval Examples**:
```python
from pydantic_ai import EvalDataset

eval_cases = [
    {"query": "broadband in E14 9WB", "expected_postcode": "E14 9WB"},
    {"query": "fastest BT deals", "expected_provider": "BT", "expected_speed": "100Mb"},
    # Multi-turn scenarios
]

# Run evals on each deployment
results = agent.evaluate(eval_cases)
```

**Additional Testing**:
- Unit tests for URL generator with edge cases
- Integration tests for agent tools
- Mock-based tests for external dependencies
- Property-based testing for URL validation
- Load testing for concurrent users

### 5. Production-Grade Observability with Logfire

**Migrate to Logfire** (Pydantic's recommended observability platform):
- Automatic agent tracing with minimal code changes
- Rich visualization of tool calls and decision paths
- Real-time debugging of agent behavior
- Cost tracking per query (token usage, API calls)
- Performance metrics (latency, cache hit rates)

**Implementation**:
```python
import logfire

# Configure once
logfire.configure(token=os.getenv('LOGFIRE_TOKEN'))

# Automatic instrumentation
with logfire.span('agent_query', user_query=query):
    result = agent.run_sync(query)
```

**Benefits over current JSONL logging**:
- Visual query tracing (see exact LLM calls)
- Aggregated metrics and dashboards
- Alerting on errors or performance degradation
- Integration with Pydantic AI's structured outputs

### 6. Self-Improving Agent

**Learn from User Interactions**:
- Collect user feedback on agent responses (thumbs up/down)
- Track which URLs users actually click vs ignore
- Analyze successful vs failed parameter extractions
- Fine-tune prompts based on common user patterns

**Feedback Loop**:
```python
# After each interaction
feedback = st.radio("Was this helpful?", ["👍 Yes", "👎 No"])
if feedback == "👎 No":
    reason = st.text_input("What could be improved?")
    store_feedback(query, agent_response, reason)
```

**Continuous Improvement**:
- Monthly analysis of stored interactions
- Identify common failure patterns
- Update system prompt with learnings
- Retrain/fine-tune on successful examples
- A/B test improvements against baseline

**Example Insights**:
- "Users who say 'fastest' want 100Mb, not just recommendations"
- "When users mention 'cheap', prioritize 'First Year Cost' sorting"
- "Users often forget to specify contract length - ask proactively"

### 7. Advanced Features

**Better Conversation Flow**:
- Context retention: "Show me something similar to my last search"
- Comparison mode: "Compare this BT deal with Virgin Media"
- Deal alerts: "Notify me when 100Mb deals drop below £25/month"

**Advanced UI**:
- Side-by-side deal comparison table
- Visual parameter editor (sliders for speed, dropdowns for providers)
- Conversation branching (explore multiple scenarios simultaneously)
- Export as PDF/email for later review

**Performance Optimization**:
- Response caching for identical queries (Redis)
- Async/await for concurrent tool calls
- Prefetch common postcodes' provider data
- Edge caching for static content

### 8. Production Readiness

**Security**:
- User authentication (OAuth, email/password)
- API key rotation and secret management
- Rate limiting per user/IP (prevent abuse)
- GDPR compliance for stored user data
- XSS protection in chat interface

**Scalability**:
- Horizontal scaling with load balancer
- Database read replicas
- Message queue for background tasks (deal scraping)
- CDN for static assets

**Monitoring & Alerting**:
- Uptime monitoring (health checks)
- Error rate alerts (Sentry, Logfire)
- Cost tracking (LLM API usage)
- User analytics (Mixpanel, Amplitude)

## 6. Code Structure

**Core Files** (5):
- `agent.py` (293 lines) - Pydantic AI agent with tools
- `url_generator.py` (393 lines) - URL generation and validation
- `config.py` (127 lines) - Configuration and dependency injection
- `observability.py` (325 lines) - Logging infrastructure
- `app.py` (322 lines) - Streamlit user interface

**Total**: ~1,460 lines of production-quality Python code

## 7. Time Investment

- **Research & Setup**: 2 hours (Pydantic AI docs, architecture planning)
- **Core Implementation**: 6 hours (URL generator, agent, tools)
- **UI Development**: 3 hours (Streamlit app, message history)
- **Debugging & Polish**: 4 hours (serialization issues, state management)
- **Documentation & Cleanup**: 2 hours (README, code cleanup)

**Total**: ~17 hours over 4 days

## Conclusion

This implementation demonstrates:
- ✅ **Strong software engineering**: Clean architecture, dependency injection, type safety
- ✅ **AI agent expertise**: Proper use of Pydantic AI, structured outputs, multi-turn conversations
- ✅ **Production mindset**: Logging, error handling, maintainability
- ✅ **User experience**: Intuitive UI, helpful error messages, persistent history

The codebase is **testable, maintainable, and extensible** - ready for real-world use with minor additions for authentication and scaling.

---

**Repository**: https://github.com/sagar2911/JMI_broadband_url_generator

