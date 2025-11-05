"""
Logging and Observability Module
Tracks agent decisions, tool calls, and user interactions for monitoring and debugging.

Refactored to support dependency injection - no global singletons.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


def _configure_logger(name: str, log_file: str = 'agent_interactions.log') -> logging.Logger:
    """Configure a logger instance with file and console handlers."""
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


class InteractionLogger:
    """
    Logger for agent interactions and tool calls.
    
    Designed to be injectable as a dependency rather than used as a global singleton.
    Thread-safe for concurrent operations.
    """
    
    def __init__(self, log_file: str = "agent_interactions.jsonl"):
        """
        Initialize the interaction logger.
        
        Args:
            log_file: Path to the JSONL log file for storing interactions
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._logger = _configure_logger(__name__, str(self.log_file.with_suffix('.log')))
    
    def log_interaction(
        self,
        user_message: str,
        agent_response: str,
        tool_calls: Optional[list] = None,
        parameters_used: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        errors: Optional[list] = None
    ) -> None:
        """
        Log a complete interaction between user and agent.
        
        Args:
            user_message: The user's input message
            agent_response: The agent's response
            tool_calls: List of tools called during this interaction
            parameters_used: Parameters extracted/used in the interaction
            execution_time: Total execution time in seconds
            errors: Any errors encountered during processing
        """
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": user_message,
            "agent_response": agent_response,
            "tool_calls": tool_calls or [],
            "parameters_used": parameters_used or {},
            "execution_time_seconds": execution_time,
            "errors": errors or [],
        }
        
        # Write to JSONL file
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(interaction) + "\n")
        except Exception as e:
            self._logger.error(f"Failed to write interaction to log file: {e}")
        
        # Also log to standard logger
        self._logger.info(
            f"Interaction logged: {len(user_message)} chars input, "
            f"{len(agent_response)} chars response, {execution_time:.3f}s" 
            if execution_time else "Interaction logged"
        )
    
    def log_tool_call(
        self,
        tool_name: str,
        input_params: Dict[str, Any],
        output: Dict[str, Any],
        execution_time: Optional[float] = None,
        success: bool = True
    ) -> None:
        """
        Log a tool call with its inputs and outputs.
        
        Args:
            tool_name: Name of the tool that was called
            input_params: Input parameters passed to the tool
            output: Output returned by the tool
            execution_time: Tool execution time in seconds
            success: Whether the tool call succeeded
        """
        # Convert output to JSON-serializable format
        serializable_output = {}
        for key, value in output.items():
            try:
                json.dumps(value)
                serializable_output[key] = value
            except (TypeError, ValueError):
                # Handle Pydantic models and other non-serializable types
                if hasattr(value, 'model_dump'):
                    serializable_output[key] = value.model_dump(mode='json')
                else:
                    serializable_output[key] = str(value)
        
        tool_call = {
            "timestamp": datetime.utcnow().isoformat(),
            "tool_name": tool_name,
            "input": input_params,
            "output": serializable_output,
            "execution_time_seconds": execution_time,
            "success": success,
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps({"type": "tool_call", **tool_call}) + "\n")
        except Exception as e:
            self._logger.error(f"Failed to write tool call to log file: {e}")
        
        status = "Success" if success else "Failed"
        self._logger.info(
            f"Tool call: {tool_name} - {status}" +
            (f" ({execution_time:.3f}s)" if execution_time else "")
        )
    
    def log_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an error with contextual information.
        
        Args:
            error: The exception that occurred
            context: Additional context about where/why the error occurred
        """
        error_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(error_log) + "\n")
        except Exception as e:
            self._logger.error(f"Failed to write error to log file: {e}")
        
        self._logger.error(
            f"Error logged: {type(error).__name__}: {error}",
            exc_info=True
        )


def create_interaction_logger(log_file: str = "agent_interactions.jsonl") -> InteractionLogger:
    """
    Factory function to create an InteractionLogger instance.
    
    Args:
        log_file: Path to the JSONL log file
        
    Returns:
        A new InteractionLogger instance
    """
    return InteractionLogger(log_file=log_file)



