"""
AI Agent for Broadband Comparison URL Generation

Refactored with proper dependency injection, type safety, and structured outputs
following Pydantic AI best practices.
"""

import logging
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from url_generator import (
    BroadbandParams,
    URLGenerationResult,
)
from config import AgentDependencies, create_default_dependencies

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Agent structured output ----------
class AgentOutput(BaseModel):
    """
    Structured output from the agent.
    
    The agent composes this from tool results to provide a complete response.
    """
    message: str = ""
    urls: List[str] = []

# ---------- System prompt for the agent ----------
SYSTEM_PROMPT = """You are a helpful AI assistant that helps users find broadband deals by generating personalized comparison URLs.

Your Workflow:
1. Understand user requirements from natural language
2. Extract parameters (postcode is REQUIRED, others are optional)
3. Use validate_parameters first if unsure what the user has provided
4. Use generate_url to create the comparison URL once you have a postcode
5. Present the URL with a clear explanation
6. Suggest improvements based on the tool's suggestions
7. Handle refinements in multi-turn conversations

Personality:
- Be friendly and conversational
- Ask ONE clarifying question at a time when needed
- Explain what filters were applied
- Guide users to better deals when possible

Key Points:
- ALWAYS require a UK postcode before generating URLs (e.g., E14 9WB, SW10 9PA)
- Use the suggestions from tools to guide users on how to refine their search
- Extract URLs from the tool results and include them in your response
- When users refine parameters, generate a new URL with updated filters
"""


# ---------- Agent singleton and factory ----------
_agent_instance: Optional[Agent[AgentDependencies, AgentOutput]] = None


def _create_agent(deps: AgentDependencies) -> Agent[AgentDependencies, AgentOutput]:
    """
    Create and configure the agent with tools.
    
    Args:
        deps: Agent dependencies containing config, logger, and url_generator
        
    Returns:
        Configured agent instance
    """
    agent = Agent(
        model=deps.config.model_name,
        deps_type=AgentDependencies,
        output_type=AgentOutput,
        system_prompt=SYSTEM_PROMPT,
    )
    
    # Register URL generation tool
    @agent.tool
    def generate_url(ctx: RunContext[AgentDependencies], params: BroadbandParams) -> URLGenerationResult:
        """
        Generate a broadband comparison URL based on user requirements.
        
        Args:
            params: Broadband search parameters (postcode is required)
            
        Returns:
            URLGenerationResult with url, success status, message, and suggestions
        """
        logger.info("generate_url tool called with postcode: %s", params.postcode)
        
        try:
            # Use the injected URL generator
            result = ctx.deps.url_generator.generate(params)
            
            # Log the tool call with JSON-serializable output
            ctx.deps.logger.log_tool_call(
                tool_name="generate_url",
                input_params=params.model_dump(exclude_none=True),
                output=result.model_dump(mode='json'),
                success=result.success,
            )
            
            return result
            
        except Exception as e:
            logger.error("Error in generate_url tool: %s", e, exc_info=True)
            ctx.deps.logger.log_error(e, {"tool": "generate_url"})
            
            return URLGenerationResult(
                success=False,
                message=f"An unexpected error occurred: {str(e)}",
                parameters_used=params.model_dump(exclude_none=True),
                url=None,
            )
    
    # Register parameter validation tool
    @agent.tool
    def validate_parameters(
        ctx: RunContext[AgentDependencies], 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and analyze parameters to guide multi-turn conversations.
        
        Use this when you're unsure what parameters the user has provided or
        want to understand what's missing before generating a URL.
        
        Args:
            params: Dictionary of parameters extracted from user message
            
        Returns:
            Validation result with missing fields and suggestions
        """
        logger.info("validate_parameters tool called")
        
        result = {
            "has_postcode": "postcode" in params and params["postcode"],
            "provided_params": list(params.keys()),
            "missing_optional": [],
            "suggestions": [],
        }
        
        # Check for postcode
        if not result["has_postcode"]:
            result["suggestions"].append(
                "Ask for the user's UK postcode (required to generate comparison URLs)"
            )
        
        # Check optional parameters
        optional_params = [
            "speedInMb", "contractLength", "phoneCalls", 
            "productType", "providers", "sortBy"
        ]
        
        for param in optional_params:
            if param not in params or not params[param]:
                result["missing_optional"].append(param)
        
        # Generate context-aware suggestions
        if result["has_postcode"] and len(result["missing_optional"]) > 2:
            result["suggestions"].append(
                "You can generate a URL now with defaults, or ask about specific preferences"
            )
        
        ctx.deps.logger.log_tool_call(
            tool_name="validate_parameters",
            input_params=params,
            output=result,
            success=True,
        )
        
        return result
    
    return agent


def get_agent(deps: Optional[AgentDependencies] = None) -> Agent[AgentDependencies, AgentOutput]:
    """
    Get or create the agent singleton.
    
    Args:
        deps: Optional dependencies. If None, creates default dependencies.
              Only used on first call.
    
    Returns:
        Agent instance
    """
    global _agent_instance
    
    if _agent_instance is None:
        if deps is None:
            deps = create_default_dependencies()
        _agent_instance = _create_agent(deps)
        logger.info("Created new agent instance")
    
    return _agent_instance


# ---------- Public API ----------


def reset_agent() -> None:
    """
    Reset the agent singleton.
    
    Useful for testing or when you want to reinitialize with different dependencies.
    """
    global _agent_instance
    _agent_instance = None
    logger.info("Agent instance reset")
