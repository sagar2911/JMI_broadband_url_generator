"""
Simple CLI Demo App for Broadband Comparison Agent

A lightweight alternative to the Streamlit app for testing and debugging.
Manages message history and displays results in the terminal.
"""

from pathlib import Path
from typing import List
import webbrowser

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from agent import chat_with_agent, get_agent, reset_agent
from config import create_default_dependencies


# Configuration
HISTORY_FILE = "cli_session_history.json"


class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def save_history(messages: List[ModelMessage], filepath: str = HISTORY_FILE):
    """Save message history to JSON file."""
    try:
        # Use dump_json to properly serialize datetime and other special types
        json_bytes = ModelMessagesTypeAdapter.dump_json(messages, indent=2)
        with open(filepath, 'wb') as f:
            f.write(json_bytes)
        return True
    except Exception as e:
        print(f"{Colors.RED}Failed to save history: {e}{Colors.END}")
        return False


def load_history(filepath: str = HISTORY_FILE) -> List[ModelMessage]:
    """Load message history from JSON file."""
    try:
        if not Path(filepath).exists():
            return []
        
        with open(filepath, 'rb') as f:
            json_bytes = f.read()
        
        messages = ModelMessagesTypeAdapter.validate_json(json_bytes)
        return messages
    except Exception as e:
        print(f"{Colors.RED}Failed to load history: {e}{Colors.END}")
        return []


def clear_history(filepath: str = HISTORY_FILE):
    """Clear conversation history."""
    if Path(filepath).exists():
        Path(filepath).unlink()
    reset_agent()
    print(f"{Colors.GREEN}✓ History cleared{Colors.END}")


def print_separator():
    """Print a visual separator."""
    print("\n" + "─" * 80 + "\n")


def print_welcome():
    """Print welcome message."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}")
    print("📡 BROADBAND COMPARISON AGENT - CLI Demo")
    print(f"{'='*80}{Colors.END}\n")
    
    print("I can help you find the best broadband deals!")
    print("\nTo get started, provide:")
    print("  • Your UK postcode (required)")
    print("  • Desired speed (optional)")
    print("  • Contract length preference (optional)")
    print("  • Preferred providers (optional)")
    
    print(f"\n{Colors.YELLOW}Commands:{Colors.END}")
    print("  /clear  - Clear conversation history")
    print("  /load   - Load saved conversation")
    print("  /save   - Save current conversation")
    print("  /quit   - Exit the application")
    
    print_separator()


def print_urls(urls: List[str], auto_open: bool = False):
    """Print URLs in a nice format."""
    if not urls:
        return
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}🔗 Generated URLs:{Colors.END}")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {Colors.UNDERLINE}{url}{Colors.END}")
    
    if urls and auto_open:
        try:
            print(f"\n{Colors.YELLOW}Opening first URL in browser...{Colors.END}")
            webbrowser.open_new_tab(urls[0])
        except Exception as e:
            print(f"{Colors.RED}Failed to open URL: {e}{Colors.END}")


def main():
    """Main CLI app loop."""
    
    # Initialize
    deps = create_default_dependencies()
    agent = get_agent(deps)
    messages = []
    auto_open = False
    
    # Welcome
    print_welcome()
    
    # Try to load existing history
    messages = load_history()
    if messages:
        print(f"{Colors.GREEN}✓ Loaded {len(messages)} messages from previous session{Colors.END}")
        print_separator()
    
    # Main loop
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.BOLD}You:{Colors.END} ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command == '/quit' or command == '/exit' or command == '/q':
                    print(f"\n{Colors.YELLOW}Saving conversation...{Colors.END}")
                    save_history(messages)
                    print(f"{Colors.GREEN}Goodbye!{Colors.END}\n")
                    break
                
                elif command == '/clear':
                    clear_history()
                    messages = []
                    reset_agent()
                    agent = get_agent(deps)
                    continue
                
                elif command == '/load':
                    messages = load_history()
                    print(f"{Colors.GREEN}✓ Loaded {len(messages)} messages{Colors.END}")
                    continue
                
                elif command == '/save':
                    if save_history(messages):
                        print(f"{Colors.GREEN}✓ History saved{Colors.END}")
                    continue
                
                elif command == '/auto':
                    auto_open = not auto_open
                    status = "enabled" if auto_open else "disabled"
                    print(f"{Colors.GREEN}✓ Auto-open URLs {status}{Colors.END}")
                    continue
                
                elif command == '/help':
                    print(f"\n{Colors.YELLOW}Available commands:{Colors.END}")
                    print("  /clear - Clear conversation history")
                    print("  /load  - Load saved conversation")
                    print("  /save  - Save current conversation")
                    print("  /auto  - Toggle auto-open URLs")
                    print("  /help  - Show this help")
                    print("  /quit  - Exit the application")
                    continue
                
                else:
                    print(f"{Colors.RED}Unknown command. Type /help for available commands.{Colors.END}")
                    continue
            
            # Get agent response
            print(f"\n{Colors.YELLOW}Agent: Thinking...{Colors.END}", end='\r')
            
            result = agent.run_sync(
                user_input,
                message_history=messages if messages else None,
                deps=deps
            )
            
            # Update messages
            messages = result.all_messages()
            
            # Display response
            output = result.output
            print(f"{Colors.BOLD}{Colors.BLUE}Agent:{Colors.END} {output.message}")
            
            # Display URLs
            if output.urls:
                print_urls(output.urls, auto_open)
            
            print_separator()
            
            # Auto-save after each interaction
            save_history(messages)
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Interrupted. Saving conversation...{Colors.END}")
            save_history(messages)
            print(f"{Colors.GREEN}Goodbye!{Colors.END}\n")
            break
        
        except Exception as e:
            print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}")
            print(f"{Colors.YELLOW}Type /help for available commands{Colors.END}\n")


if __name__ == "__main__":
    main()

