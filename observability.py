"""
Logging and Observability Module
Tracks agent decisions, tool calls, and user interactions for monitoring and debugging.

Refactored to support dependency injection - no global singletons.
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from functools import wraps


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
        def make_serializable(obj):
            """Convert Pydantic models and HttpUrl to JSON-serializable format."""
            if hasattr(obj, 'model_dump'):
                return obj.model_dump(mode='json')
            elif hasattr(obj, '__str__'):
                return str(obj)
            return obj
        
        # Process output to ensure it's JSON serializable
        serializable_output = {}
        for key, value in output.items():
            try:
                # Try to serialize to test if it's already serializable
                json.dumps(value)
                serializable_output[key] = value
            except (TypeError, ValueError):
                serializable_output[key] = make_serializable(value)
        
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


def trace_tool_call(logger_instance: InteractionLogger) -> Callable:
    """
    Create a decorator to trace tool function calls with a specific logger.
    
    Args:
        logger_instance: The InteractionLogger instance to use for logging
        
    Returns:
        A decorator function that traces tool calls
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            tool_name = func.__name__
            
            # Extract input parameters
            # Skip first arg if it's RunContext (common in Pydantic AI tools)
            input_params: Dict[str, Any] = {}
            if args:
                # Check if first arg looks like RunContext (has certain attributes)
                # or if we have more than one arg, start from second arg
                start_idx = 1 if len(args) > 1 and hasattr(args[0], 'deps') else 0
                
                if start_idx < len(args):
                    # Assume first arg after RunContext is the request model
                    if hasattr(args[start_idx], 'model_dump'):
                        input_params = args[start_idx].model_dump()
                    else:
                        input_params = {"args": str(args[start_idx:])}
                else:
                    input_params = {"args": str(args)}
            input_params.update(kwargs)
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Extract output
                if hasattr(result, 'model_dump'):
                    output = result.model_dump()
                else:
                    output = {"result": str(result)}
                
                execution_time = time.time() - start_time
                
                # Log successful tool call
                logger_instance.log_tool_call(
                    tool_name=tool_name,
                    input_params=input_params,
                    output=output,
                    execution_time=execution_time,
                    success=True
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log failed tool call
                logger_instance.log_tool_call(
                    tool_name=tool_name,
                    input_params=input_params,
                    output={"error": str(e)},
                    execution_time=execution_time,
                    success=False
                )
                
                logger_instance.log_error(e, {"tool_name": tool_name})
                raise
        
        return wrapper
    
    return decorator


def get_interaction_stats(log_file: str = "agent_interactions.jsonl") -> Dict[str, Any]:
    """Get statistics from interaction logs."""
    log_path = Path(log_file)
    if not log_path.exists():
        return {"total_interactions": 0, "total_tool_calls": 0}
    
    stats = {
        "total_interactions": 0,
        "total_tool_calls": 0,
        "total_errors": 0,
        "avg_execution_time": 0.0,
        "tool_call_counts": {},
    }
    
    execution_times = []
    
    with open(log_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("type") == "tool_call":
                    stats["total_tool_calls"] += 1
                    tool_name = entry.get("tool_name", "unknown")
                    stats["tool_call_counts"][tool_name] = stats["tool_call_counts"].get(tool_name, 0) + 1
                    
                    if entry.get("execution_time_seconds"):
                        execution_times.append(entry["execution_time_seconds"])
                    
                    if not entry.get("success", True):
                        stats["total_errors"] += 1
                elif "user_message" in entry:
                    stats["total_interactions"] += 1
                    if entry.get("execution_time_seconds"):
                        execution_times.append(entry["execution_time_seconds"])
                elif entry.get("type") == "error":
                    stats["total_errors"] += 1
            except json.JSONDecodeError:
                continue
    
    if execution_times:
        stats["avg_execution_time"] = sum(execution_times) / len(execution_times)
        stats["min_execution_time"] = min(execution_times)
        stats["max_execution_time"] = max(execution_times)
    
    return stats

