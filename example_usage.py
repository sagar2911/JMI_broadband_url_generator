"""
Example usage of the refactored broadband agent.

This script demonstrates:
1. Basic agent usage
2. Multi-turn conversation
3. URL extraction from responses
4. Parameter validation
"""

from agent import chat_with_agent, reset_agent
from config import create_default_dependencies


def print_response(response, turn_number):
    """Pretty print agent response."""
    print(f"\n{'='*60}")
    print(f"Turn {turn_number}")
    print(f"{'='*60}")
    print(f"\nAgent: {response.message}")
    
    if response.urls:
        print(f"\nGenerated URLs ({len(response.urls)}):")
        for i, url in enumerate(response.urls, 1):
            print(f"  {i}. {url}")
    print()


def example_basic_usage():
    """Example 1: Basic single-turn usage."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Usage")
    print("="*60)
    
    # Reset agent to start fresh
    reset_agent()
    
    # Simple query with postcode
    response = chat_with_agent("I need broadband in E14 9WB")
    print_response(response, 1)


def example_multi_turn():
    """Example 2: Multi-turn conversation with refinement."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Multi-turn Conversation")
    print("="*60)
    
    # Reset agent to start fresh
    reset_agent()
    
    # Turn 1: Initial query without postcode
    response1 = chat_with_agent("I'm looking for fast broadband")
    print_response(response1, 1)
    
    # Turn 2: Provide postcode
    response2 = chat_with_agent("My postcode is SW10 9PA")
    print_response(response2, 2)
    
    # Turn 3: Refine with specific requirements
    response3 = chat_with_agent("I want 100Mb speed and prefer BT or Sky")
    print_response(response3, 3)


def example_with_custom_deps():
    """Example 3: Using custom dependencies."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Custom Dependencies")
    print("="*60)
    
    # Create custom dependencies (with default config but demonstrating pattern)
    deps = create_default_dependencies()
    
    # Reset and use custom dependencies
    reset_agent()
    
    response = chat_with_agent(
        "Find broadband deals in E14 9WB with 55Mb speed",
        deps=deps
    )
    print_response(response, 1)


def example_validation():
    """Example 4: Parameter validation."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Invalid Input Handling")
    print("="*60)
    
    reset_agent()
    
    # Invalid postcode should be handled gracefully
    response = chat_with_agent("Get me broadband in 12345")
    print_response(response, 1)


def main():
    """Run all examples."""
    print("\n" + "🚀 "*20)
    print("BROADBAND AGENT - EXAMPLE USAGE")
    print("🚀 "*20)
    
    try:
        # Example 1: Basic usage
        example_basic_usage()
        
        # Example 2: Multi-turn conversation
        # Note: In real usage, frontend would manage message history
        # This is just demonstrating the API
        example_multi_turn()
        
        # Example 3: Custom dependencies
        example_with_custom_deps()
        
        # Example 4: Validation
        example_validation()
        
        print("\n" + "✅ "*20)
        print("All examples completed successfully!")
        print("✅ "*20 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

