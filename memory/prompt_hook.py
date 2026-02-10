#!/usr/bin/env python3
"""
Prompt Hook for Memory Injection
Injects relevant memories before processing user prompts.
"""

import os
import sys
import json
from datetime import datetime

WORKSPACE = "/root/.openclaw/workspace"
MEMORY_DIR = f"{WORKSPACE}/memory"

def load_user_prompt():
    """Load prompt from stdin or file."""
    if len(sys.argv) > 1:
        # First argument is prompt file
        with open(sys.argv[1], 'r') as f:
            return f.read()
    else:
        # Read from stdin
        return sys.stdin.read()

def get_recent_summary():
    """Get last 24 hours of hourly summaries."""
    today = datetime.now().strftime('%Y-%m-%d')
    daily_file = os.path.join(MEMORY_DIR, f"{today}.md")
    
    if not os.path.exists(daily_file):
        return ""
    
    with open(daily_file, 'r') as f:
        content = f.read()
    
    # Get last 5000 chars (recent summaries)
    return content[-5000:] if len(content) > 5000 else content

def get_precompact_dump():
    """Get latest pre-compaction dump."""
    latest_link = os.path.join(MEMORY_DIR, 'precompact', 'latest.json')
    
    if not os.path.exists(latest_link):
        return ""
    
    try:
        with open(latest_link, 'r') as f:
            data = json.load(f)
            return json.dumps(data.get('key_context', {}), indent=2)
    except:
        return ""

def get_vector_memories(query):
    """Get semantically similar memories."""
    try:
        sys.path.insert(0, MEMORY_DIR)
        from vector_search import inject_memories_into_context
        return inject_memories_into_context(query)
    except ImportError:
        return ""

def build_injected_context(prompt):
    """Build context to inject before prompt."""
    context_parts = []
    
    # Recent activity summary
    summary = get_recent_summary()
    if summary:
        context_parts.append(f"=== RECENT ACTIVITY (Last 24h) ===\n{summary}\n")
    
    # Pre-compaction context
    precompact = get_precompact_dump()
    if precompact:
        context_parts.append(f"=== PRE-COMPACTION STATE ===\n{precompact}\n")
    
    # Relevant vector memories
    vector_memories = get_vector_memories(prompt)
    if vector_memories:
        context_parts.append(vector_memories)
    
    return "\n".join(context_parts)

def main():
    """Main entry point - inject memories into prompt."""
    prompt = load_user_prompt()
    
    if not prompt:
        print(prompt)
        return
    
    injected_context = build_injected_context(prompt)
    
    if injected_context:
        full_prompt = f"{injected_context}\n\n=== CURRENT USER PROMPT ===\n{prompt}"
    else:
        full_prompt = prompt
    
    # Output modified prompt
    print(full_prompt)

if __name__ == '__main__':
    main()
