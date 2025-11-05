"""
Streamlit Demo App for Broadband Comparison Agent

Features:
- Proper message history management in Pydantic AI format
- Conversation display with URLs
- Auto-open links option
- Session persistence to JSON
- Clean, demo-friendly UI
"""

import json
from pathlib import Path
from typing import List, Optional

import streamlit as st
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from agent import chat_with_agent, get_agent, reset_agent
from config import create_default_dependencies, AgentDependencies


# Configuration
HISTORY_FILE = "app_session_history.json"
SESSION_KEY_MESSAGES = "messages"
SESSION_KEY_DEPS = "dependencies"
SESSION_KEY_AUTO_OPEN = "auto_open_urls"


def init_session_state():
    """Initialize Streamlit session state."""
    if SESSION_KEY_MESSAGES not in st.session_state:
        # Auto-load history on first render
        loaded_history = load_history_from_file()
        st.session_state[SESSION_KEY_MESSAGES] = loaded_history
        if loaded_history:
            st.success(f"Loaded {len(loaded_history)} messages from previous session")
    
    if SESSION_KEY_DEPS not in st.session_state:
        # Create dependencies once per session
        st.session_state[SESSION_KEY_DEPS] = create_default_dependencies()
    
    if SESSION_KEY_AUTO_OPEN not in st.session_state:
        st.session_state[SESSION_KEY_AUTO_OPEN] = False


def save_history_to_file(messages: List[ModelMessage], filepath: str = HISTORY_FILE):
    """
    Save message history to JSON file in Pydantic AI format.
    
    Args:
        messages: List of ModelMessage objects
        filepath: Path to save JSON file
    """
    try:
        # Serialize messages using Pydantic AI's adapter with mode='json'
        # This properly handles datetime and other special types
        json_str = ModelMessagesTypeAdapter.dump_json(messages)
        
        with open(filepath, 'wb') as f:
            f.write(json_str)
        
        return True
    except Exception as e:
        st.error(f"Failed to save history: {e}")
        return False


def load_history_from_file(filepath: str = HISTORY_FILE) -> List[ModelMessage]:
    """
    Load message history from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of ModelMessage objects, empty list if file doesn't exist
    """
    try:
        if not Path(filepath).exists():
            return []
        
        with open(filepath, 'rb') as f:
            json_bytes = f.read()
        
        # Deserialize using Pydantic AI's adapter
        messages = ModelMessagesTypeAdapter.validate_json(json_bytes)
        return messages
    
    except Exception as e:
        st.error(f"Failed to load history: {e}")
        return []


def clear_history():
    """Clear conversation history."""
    st.session_state[SESSION_KEY_MESSAGES] = []
    
    # Delete history file
    if Path(HISTORY_FILE).exists():
        Path(HISTORY_FILE).unlink()
    
    # Reset agent to clear any internal state
    reset_agent()


def render_message(role: str, content: str, urls: Optional[List[str]] = None, message_key: str = ""):
    """
    Render a single message in the chat.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
        urls: Optional list of URLs to display
        message_key: Unique key for this message to avoid duplicate keys
    """
    with st.chat_message(role):
        st.markdown(content)
        
        if urls:
            st.markdown("---")
            st.markdown("**🔗 Generated Comparison URLs:**")
            
            for i, url in enumerate(urls, 1):
                # Use link_button which opens in new tab by default
                st.link_button(
                    f"🔗 Open Deal #{i}",
                    url,
                    use_container_width=True,
                    type="secondary"
                )
                # Also show the URL text for reference
                st.caption(f"{url[:80]}..." if len(url) > 80 else url)


def extract_conversation_from_history(messages: List[ModelMessage]) -> List[dict]:
    """
    Extract user-assistant conversation pairs from Pydantic AI message history.
    
    Args:
        messages: List of ModelMessage objects from Pydantic AI
        
    Returns:
        List of dicts with 'role', 'content', and optionally 'urls'
    """
    conversation = []
    
    for idx, msg in enumerate(messages):
        # All Pydantic AI messages have 'kind' and 'parts'
        msg_kind = str(msg.kind)
        
        # Request messages contain user input
        if msg_kind == 'request':
            for part in msg.parts:
                part_kind = str(part.part_kind)
                
                if part_kind == 'user-prompt' and part.content:
                    content = part.content.strip()
                    if content:
                        conversation.append({
                            'role': 'user',
                            'content': content,
                            'key': f"user_{idx}_{len(conversation)}"
                        })
        
        # Response messages contain model output
        elif msg_kind == 'response':
            for part in msg.parts:
                part_kind = str(part.part_kind)
                
                # Tool call with final_result contains our AgentOutput
                if part_kind == 'tool-call' and part.tool_name == 'final_result':
                    args = part.args
                    message = args.get('message', '')
                    urls = args.get('urls', [])
                    
                    if message:
                        conversation.append({
                            'role': 'assistant',
                            'content': message,
                            'urls': urls if urls else None,
                            'key': f"assistant_{idx}_{len(conversation)}"
                        })
    
    return conversation


def main():
    """Main Streamlit app."""
    
    # Page config
    st.set_page_config(
        page_title="Broadband Comparison Agent",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.title("📡 Broadband Comparison Agent")
    st.markdown(
        "Find the best broadband deals by chatting with our AI agent. "
        "Just provide your postcode and preferences!"
    )
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Auto-open URLs option
        auto_open = st.checkbox(
            "Auto-open first URL",
            value=st.session_state[SESSION_KEY_AUTO_OPEN],
            help="Automatically open the first generated URL in a new tab"
        )
        st.session_state[SESSION_KEY_AUTO_OPEN] = auto_open
        
        st.markdown("---")
        
        # Session management
        st.header("💾 Session")
        
        if st.button("🗑️ Clear History", help="Clear conversation and start fresh", use_container_width=True):
            clear_history()
            st.success("History cleared!")
            st.rerun()
        
        st.caption("💡 Conversation auto-saves after each message")
        
        st.markdown("---")
        
        # Stats
        st.header("📊 Stats")
        st.metric("Messages", len(st.session_state[SESSION_KEY_MESSAGES]))
        
        # Example queries
        st.markdown("---")
        st.header("💡 Example Queries")
        st.markdown("""
        - "I need broadband in E14 9WB"
        - "Find deals in SW10 9PA with 100Mb speed"
        - "Show me BT and Sky deals for 12 months"
        - "I want the cheapest broadband with phone line"
        """)
    
    # Main chat area
    st.markdown("---")
    
    # Display conversation history
    if st.session_state[SESSION_KEY_MESSAGES]:
        conversation = extract_conversation_from_history(st.session_state[SESSION_KEY_MESSAGES])
        
        for msg in conversation:
            render_message(
                role=msg['role'],
                content=msg['content'],
                urls=msg.get('urls'),
                message_key=msg.get('key', '')
            )
    else:
        # Welcome message
        with st.chat_message("assistant"):
            st.markdown("""
            👋 Hello! I'm your broadband comparison assistant.
            
            I can help you find the best broadband deals based on your location and preferences.
            
            **To get started, tell me:**
            - Your UK postcode (required)
            - Desired speed (optional)
            - Contract length preference (optional)
            - Preferred providers (optional)
            
            For example: *"I need broadband in E14 9WB with at least 55Mb speed"*
            """)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Get agent response
        with st.spinner("🤔 Thinking..."):
            try:
                # Get agent with session dependencies
                agent = get_agent(st.session_state[SESSION_KEY_DEPS])
                
                # Run agent with message history
                result = agent.run_sync(
                    user_input,
                    message_history=st.session_state[SESSION_KEY_MESSAGES] if st.session_state[SESSION_KEY_MESSAGES] else None,
                    deps=st.session_state[SESSION_KEY_DEPS]
                )
                
                # Update message history with all messages from the run
                st.session_state[SESSION_KEY_MESSAGES] = result.all_messages()
                
                # Auto-save after each interaction
                save_history_to_file(st.session_state[SESSION_KEY_MESSAGES])
                
                # Rerun to display the updated conversation
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.exception(e)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Powered by Pydantic AI | Built with Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
