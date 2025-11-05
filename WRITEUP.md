# JMI Broadband Agent - Implementation Writeup

## Approach and Architecture Decisions

### 1. Framework Choice: Pydantic AI

I chose **Pydantic AI** over LangChain/LangGraph for several reasons:

- **Type Safety**: Built on Pydantic, ensuring compile-time type checking for tools and requests
- **Simplicity**: Cleaner API compared to LangChain's more complex abstractions
- **Modern Python**: Designed for Python 3.10+ with proper async support
- **Tool Integration**: Straightforward tool definition using Pydantic models
- **Performance**: Lightweight and efficient for this use case

The agent is defined with a clear system prompt and a single tool (`generate_url_tool`) that handles URL generation. This keeps the architecture simple and maintainable.

### 2. URL Generator Design

The URL generator (`url_generator.py`) was built with a focus on:

- **Validation First**: All parameters are validated before URL generation to prevent broken links
- **Clear Error Messages**: Validation errors are descriptive and help users understand what went wrong
- **Extensibility**: Easy to add new parameters or validation rules
- **Postcode Normalization**: Handles various postcode formats (with/without spaces, case-insensitive)

The `BroadbandParams` dataclass encapsulates all parameters and validation logic, making it easy to test and maintain.

### 3. Multi-Turn Conversations

Pydantic AI's session management handles conversation context automatically. The agent remembers previous parameters within a session, allowing users to refine their queries naturally:

```
User: "I need broadband in E14 9WB"
Agent: "What speed?"
User: "100Mb"
Agent: [Generates URL with postcode + speed]
User: "Actually, make that 24 months"
Agent: [Updates URL with postcode + speed + contract]
```

This is handled by Pydantic AI's built-in session context, requiring minimal custom code.

### 4. UI Design

I implemented **two interfaces** to provide flexibility:

- **Web UI (Streamlit)**: User-friendly chat interface for end users
- **CLI (Rich)**: Terminal interface for developers and automation

Both interfaces:
- Display generated URLs prominently
- Support conversation history
- Extract and highlight URLs in responses
- Provide clear error messages

### 5. Observability and Logging

I implemented comprehensive logging as the enhanced feature because:

- **Debugging**: Essential for understanding agent behavior and troubleshooting
- **Analytics**: Track usage patterns, common queries, and success rates
- **Monitoring**: Identify errors and performance issues
- **Compliance**: Maintain audit trails of interactions

The logging system captures:
- User messages and agent responses
- Tool calls with input/output parameters
- Execution times for performance monitoring
- Errors with full context
- Structured JSONL format for easy analysis

## Challenges Encountered and Solutions

### Challenge 1: URL Encoding and Format

**Problem**: The sample URL showed a complex structure with query parameters in both the query string and fragment, with specific encoding requirements.

**Solution**: I carefully analyzed the sample URL structure:
```
https://broadband.justmovein.co/packages?location={POSTCODE}#/?{PARAMETERS}
```

The postcode goes in the query string, while filters go in the fragment. I used Python's `urllib.parse.quote` for proper URL encoding of both sections.

### Challenge 2: Parameter Validation

**Problem**: Need to validate many different parameter types (postcodes, enums, comma-separated lists, etc.) while providing clear error messages.

**Solution**: Created a comprehensive validation system in the `BroadbandParams` class that:
- Validates each parameter type appropriately
- Collects all errors before returning (not stopping at first error)
- Provides specific error messages with valid options

### Challenge 3: Natural Language Understanding

**Problem**: Users might express requirements in various ways (e.g., "12 month contract" vs "12 months" vs "12-month").

**Solution**: Relied on the LLM's natural language understanding capabilities. The system prompt instructs the agent to extract parameters correctly, and Pydantic AI handles the conversion to the tool's expected format.

### Challenge 4: Multi-Turn Context

**Problem**: Users should be able to refine parameters without repeating all information.

**Solution**: Pydantic AI's session management handles this automatically. Each session maintains conversation history, allowing the agent to reference previous parameters.

### Challenge 5: Error Handling

**Problem**: Need graceful error handling for API failures, invalid inputs, and unexpected errors.

**Solution**: Implemented try-catch blocks at multiple levels:
- URL generator validates inputs and returns clear errors
- Agent catches tool call errors and surfaces them to users
- UI catches exceptions and displays friendly error messages
- All errors are logged for debugging

## Enhanced Feature: Logging and Observability

I chose to implement **comprehensive logging and observability** because:

1. **Essential for Production**: Any production AI system needs observability
2. **Debugging Agent Behavior**: Understanding why the agent made certain decisions
3. **Performance Monitoring**: Tracking execution times and identifying bottlenecks
4. **User Analytics**: Understanding common queries and usage patterns
5. **Error Tracking**: Identifying and fixing issues quickly

### Implementation Details

- **Structured Logging**: JSONL format for easy parsing and analysis
- **Tool Call Tracking**: Every tool call is logged with input/output and execution time
- **Interaction Logging**: Complete user-agent interactions with timestamps
- **Error Logging**: Comprehensive error context for debugging
- **Statistics Extraction**: Helper function to analyze log files

The logging system is non-intrusive (using decorators) and doesn't impact application performance.

## Testing Strategy

I created a comprehensive test suite for the URL generator covering:

- Valid and invalid postcode formats
- All valid parameter values
- Parameter combinations
- Error cases
- URL format validation

The tests use pytest and can be run with `pytest test_url_generator.py -v`.

## What I Would Improve with More Time

1. **Provider Recommendations**: Integrate with a postcode-to-provider API to suggest suitable providers based on location
2. **Agent Unit Tests**: Add tests specifically for agent behavior and conversation flows
3. **Caching**: Cache common queries (e.g., postcode validation) to reduce API calls
4. **Better Postcode Validation**: Integrate with Royal Mail API for authoritative postcode validation
5. **Analytics Dashboard**: Create a visual dashboard for interaction statistics
6. **Docker Support**: Containerize the application for easy deployment
7. **Rate Limiting**: Implement rate limiting to prevent API abuse
8. **Response Streaming**: Stream agent responses for better UX in web interface
9. **Parameter Suggestions**: Suggest parameters based on user's previous choices
10. **Export Functionality**: Allow users to export conversation history and URLs

## Code Quality Considerations

- **Type Hints**: All functions include type hints for better IDE support and error catching
- **Documentation**: Comprehensive docstrings for all functions and classes
- **Error Messages**: Clear, actionable error messages
- **Modularity**: Clean separation of concerns (URL generation, agent, UI, logging)
- **Extensibility**: Easy to add new parameters or features

## Conclusion

This implementation provides a solid foundation for an AI-powered broadband comparison agent. The architecture is clean, maintainable, and extensible. The use of Pydantic AI simplifies agent development while maintaining type safety and good error handling.

The enhanced logging feature provides essential observability for understanding and improving the agent's behavior over time.

