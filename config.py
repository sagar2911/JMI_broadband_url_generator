"""
Configuration and Dependency Management for Broadband Agent

Provides type-safe configuration and dependency injection patterns.
"""

import os
from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

# Avoid circular imports
if TYPE_CHECKING:
    from observability import InteractionLogger
    from url_generator import URLGenerator


class AgentConfig(BaseModel):
    """Configuration for the broadband agent with environment variable support."""
    
    model_name: str = Field(
        default="gemini-2.5-flash",
        description="LLM model to use for the agent"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed operations"
    )
    
    enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses (future use)"
    )
    
    default_sort_by: str = Field(
        default="Recommended",
        description="Default sort order for broadband results"
    )
    
    require_explicit_postcode: bool = Field(
        default=True,
        description="Whether to require explicit postcode before generating URLs"
    )
    
    log_file: str = Field(
        default="agent_interactions.jsonl",
        description="Path to the interaction log file"
    )
    
    base_url: str = Field(
        default="https://broadband.justmovein.co/packages",
        description="Base URL for broadband comparison site"
    )
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create configuration from environment variables with fallbacks."""
        return cls(
            model_name=os.getenv("AGENT_MODEL_NAME", "gemini-2.5-flash"),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "3")),
            enable_streaming=os.getenv("AGENT_ENABLE_STREAMING", "true").lower() == "true",
            default_sort_by=os.getenv("AGENT_DEFAULT_SORT", "Recommended"),
            require_explicit_postcode=os.getenv("AGENT_REQUIRE_POSTCODE", "true").lower() == "true",
            log_file=os.getenv("AGENT_LOG_FILE", "agent_interactions.jsonl"),
            base_url=os.getenv("BROADBAND_BASE_URL", "https://broadband.justmovein.co/packages"),
        )
    
    model_config = {"frozen": True}  # Immutable configuration


class AgentDependencies(BaseModel):
    """
    Type-safe dependencies injected into agent tools via RunContext.
    
    All dependencies are immutable to ensure thread safety and predictable behavior.
    """
    
    config: AgentConfig = Field(
        description="Agent configuration"
    )
    
    logger: "InteractionLogger" = Field(
        description="Interaction logger for observability"
    )
    
    url_generator: "URLGenerator" = Field(
        description="URL generator service"
    )
    
    model_config = {
        "frozen": True,  # Immutable dependencies
        "arbitrary_types_allowed": True  # Allow non-Pydantic types
    }


def create_default_config() -> AgentConfig:
    """Factory function to create default configuration."""
    return AgentConfig.from_env()


def create_default_dependencies() -> AgentDependencies:
    """
    Factory function to create default dependencies with all required services.
    
    This should be called once at application startup.
    """
    # Import here to avoid circular dependencies
    from observability import InteractionLogger, create_interaction_logger
    from url_generator import URLGenerator
    
    # Rebuild the model with the actual types in namespace
    AgentDependencies.model_rebuild(
        _types_namespace={
            'InteractionLogger': InteractionLogger,
            'URLGenerator': URLGenerator
        }
    )
    
    config = create_default_config()
    
    return AgentDependencies(
        config=config,
        logger=create_interaction_logger(log_file=config.log_file),
        url_generator=URLGenerator(base_url=config.base_url),
    )

