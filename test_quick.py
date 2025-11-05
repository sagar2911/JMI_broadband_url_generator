#!/usr/bin/env python3
"""
Quick integration test to catch import and dependency issues.

Run this before starting the app to ensure everything works.
"""

import sys
from pathlib import Path

# Color codes for output
class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def test_step(name):
    """Decorator for test steps."""
    def decorator(func):
        def wrapper():
            print(f"\n{C.BLUE}Testing: {name}...{C.END}", end=" ")
            try:
                result = func()
                print(f"{C.GREEN}✓ PASS{C.END}")
                return True, result
            except Exception as e:
                print(f"{C.RED}✗ FAIL{C.END}")
                print(f"  {C.RED}Error: {str(e)}{C.END}")
                import traceback
                traceback.print_exc()
                return False, None
        return wrapper
    return decorator


@test_step("Import config module")
def test_config_import():
    from config import AgentConfig, create_default_config
    return "config imported"


@test_step("Import observability module")
def test_observability_import():
    from observability import InteractionLogger, create_interaction_logger
    return "observability imported"


@test_step("Import url_generator module")
def test_url_generator_import():
    from url_generator import URLGenerator, BroadbandParams, URLGenerationResult
    return "url_generator imported"


@test_step("Create dependencies")
def test_create_dependencies():
    from config import create_default_dependencies
    deps = create_default_dependencies()
    return deps


@test_step("Import agent module")
def test_agent_import():
    from agent import get_agent, chat_with_agent
    return "agent imported"


@test_step("Create agent instance")
def test_create_agent():
    from agent import get_agent, reset_agent
    from config import create_default_dependencies
    
    reset_agent()
    deps = create_default_dependencies()
    agent = get_agent(deps)
    return agent


@test_step("Test URL generation")
def test_url_generation():
    from url_generator import URLGenerator, BroadbandParams
    
    generator = URLGenerator()
    params = BroadbandParams(postcode="E14 9WB")
    result = generator.generate(params)
    
    assert result.success, f"URL generation failed: {result.message}"
    assert result.url is not None, "No URL generated"
    return result


@test_step("Test agent chat (simple)")
def test_agent_chat_simple():
    from agent import chat_with_agent, reset_agent
    
    reset_agent()
    # This won't actually call the LLM without API keys, but tests the plumbing
    try:
        response = chat_with_agent("test")
        return response
    except Exception as e:
        # Expected if no API key configured
        if "API" in str(e) or "key" in str(e).lower():
            print(f"\n  {C.YELLOW}Note: API key not configured (expected for testing){C.END}")
            return "API key needed (ok for testing)"
        raise


@test_step("Test Pydantic message serialization")
def test_message_serialization():
    from pydantic_ai.messages import ModelMessagesTypeAdapter
    
    # Test round-trip serialization with JSON (handles datetime properly)
    messages = []
    json_bytes = ModelMessagesTypeAdapter.dump_json(messages)
    loaded = ModelMessagesTypeAdapter.validate_json(json_bytes)
    
    assert loaded == messages, "Message serialization failed"
    return "serialization works"


def main():
    """Run all tests."""
    print(f"\n{C.BOLD}{'='*60}")
    print("🧪 QUICK INTEGRATION TEST")
    print(f"{'='*60}{C.END}")
    
    tests = [
        test_config_import,
        test_observability_import,
        test_url_generator_import,
        test_create_dependencies,
        test_agent_import,
        test_create_agent,
        test_url_generation,
        test_message_serialization,
        test_agent_chat_simple,
    ]
    
    results = []
    for test in tests:
        passed, result = test()
        results.append(passed)
    
    # Summary
    print(f"\n{C.BOLD}{'='*60}")
    passed_count = sum(results)
    total_count = len(results)
    
    if passed_count == total_count:
        print(f"{C.GREEN}✓ ALL TESTS PASSED ({passed_count}/{total_count}){C.END}")
        print(f"{'='*60}{C.END}\n")
        print(f"{C.GREEN}You're good to go! Run:{C.END}")
        print(f"  {C.BOLD}streamlit run app.py{C.END}")
        print(f"  or")
        print(f"  {C.BOLD}python cli_app.py{C.END}\n")
        return 0
    else:
        print(f"{C.RED}✗ SOME TESTS FAILED ({passed_count}/{total_count} passed){C.END}")
        print(f"{'='*60}{C.END}\n")
        print(f"{C.YELLOW}Fix the errors above before running the app.{C.END}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

