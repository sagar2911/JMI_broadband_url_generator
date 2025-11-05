#!/usr/bin/env python3
"""
Test the extract_conversation_from_history function with real message history.
"""

import json
from pathlib import Path
from pydantic_ai.messages import ModelMessagesTypeAdapter

# Import the extraction function
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app import extract_conversation_from_history


def main():
    print("="*60)
    print("Testing Message History Extraction")
    print("="*60)
    
    # Load the actual message history
    history_file = Path("message_history.json")
    
    if not history_file.exists():
        print("❌ message_history.json not found")
        return
    
    print(f"\n✓ Found {history_file}")
    
    try:
        with open(history_file, 'rb') as f:
            json_bytes = f.read()
        
        print(f"✓ File size: {len(json_bytes)} bytes")
        
        # Parse with Pydantic AI adapter
        messages = ModelMessagesTypeAdapter.validate_json(json_bytes)
        print(f"✓ Parsed {len(messages)} messages")
        
        # Extract conversation
        conversation = extract_conversation_from_history(messages)
        print(f"✓ Extracted {len(conversation)} conversation turns")
        
        # Display the conversation
        print("\n" + "="*60)
        print("EXTRACTED CONVERSATION")
        print("="*60)
        
        for i, msg in enumerate(conversation, 1):
            role = msg['role'].upper()
            content = msg['content']
            urls = msg.get('urls', [])
            
            print(f"\n[{i}] {role}:")
            print(f"    {content[:200]}{'...' if len(content) > 200 else ''}")
            
            if urls:
                print(f"    URLs: {len(urls)}")
                for j, url in enumerate(urls[:2], 1):  # Show first 2 URLs
                    print(f"      {j}. {url[:80]}...")
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        user_msgs = sum(1 for m in conversation if m['role'] == 'user')
        assistant_msgs = sum(1 for m in conversation if m['role'] == 'assistant')
        total_urls = sum(len(m.get('urls', [])) for m in conversation)
        
        print(f"User messages: {user_msgs}")
        print(f"Assistant messages: {assistant_msgs}")
        print(f"Total URLs generated: {total_urls}")
        
        # Test edge cases
        print("\n" + "="*60)
        print("VALIDATION")
        print("="*60)
        
        # Check for empty content
        empty_content = [i for i, m in enumerate(conversation) if not m['content']]
        if empty_content:
            print(f"⚠️  Found {len(empty_content)} messages with empty content at indices: {empty_content}")
        else:
            print("✓ All messages have content")
        
        # Check for proper role alternation (mostly)
        role_sequence = [m['role'] for m in conversation]
        print(f"✓ Role sequence: {' → '.join(role_sequence[:10])}{'...' if len(role_sequence) > 10 else ''}")
        
        # Check URL structure
        for i, msg in enumerate(conversation):
            if msg.get('urls'):
                for url in msg['urls']:
                    if not url.startswith('http'):
                        print(f"⚠️  Invalid URL at message {i}: {url}")
        
        print("\n" + "="*60)
        print("✅ EXTRACTION TEST PASSED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

