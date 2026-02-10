#!/usr/bin/env python3
"""
Hourly Memory Summarizer
Summarizes activity and appends to daily memory file.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
MEMORY_DIR = f"{WORKSPACE}/memory"
SESSION_DIR = f"{WORKSPACE}/agents/main/sessions"
HOURLY_DIR = f"{MEMORY_DIR}/hourly"

def get_session_files():
    """Get recent session files."""
    if not os.path.exists(SESSION_DIR):
        return []
    
    files = []
    for f in os.listdir(SESSION_DIR):
        if f.endswith('.jsonl'):
            filepath = os.path.join(SESSION_DIR, f)
            files.append((filepath, os.path.getmtime(filepath)))
    
    # Sort by modification time, newest first
    files.sort(key=lambda x: x[1], reverse=True)
    return [f[0] for f in files[:3]]  # Last 3 sessions

def extract_recent_messages(session_files, max_messages=50):
    """Extract recent messages from session files."""
    messages = []
    
    for session_file in session_files:
        try:
            with open(session_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if 'content' in data and data.get('role') in ['user', 'assistant']:
                            messages.append({
                                'role': data['role'],
                                'content': data['content'][:500],  # Truncate long messages
                                'timestamp': data.get('created_at', '')
                            })
        except Exception as e:
            print(f"Error reading {session_file}: {e}")
    
    return messages[-max_messages:]

def summarize_hour(messages):
    """Generate a summary of the hour's activity."""
    if not messages:
        return "No activity recorded."
    
    user_msgs = [m for m in messages if m['role'] == 'user']
    assistant_msgs = [m for m in messages if m['role'] == 'assistant']
    
    summary_parts = []
    
    # Count message types
    summary_parts.append(f"Total interactions: {len(messages)} ({len(user_msgs)} user, {len(assistant_msgs)} assistant)")
    
    # Extract key topics
    topics = set()
    for msg in user_msgs:
        content = msg['content'].lower()
        if 'app' in content or 'build' in content or 'create' in content:
            topics.add('app development')
        if 'memory' in content or 'remember' in content:
            topics.add('memory system')
        if 'journal' in content or 'email' in content:
            topics.add('family journaling')
        if 'literacy' in content or 'reading' in content or 'game' in content:
            topics.add('educational apps')
        if 'google' in content or 'drive' in content:
            topics.add('google integration')
    
    if topics:
        summary_parts.append(f"Key areas: {', '.join(topics)}")
    
    # Recent accomplishments
    accomplishments = []
    for msg in assistant_msgs[-5:]:
        content = msg['content']
        if any(kw in content.lower() for kw in ['created', 'built', 'implemented', 'fixed', 'added']):
            accomplishments.append(content[:100])
    
    if accomplishments:
        summary_parts.append(f"Recent work: {accomplishments[0]}...")
    
    return ' | '.join(summary_parts)

def append_to_daily_memory(summary):
    """Append summary to today's memory file."""
    today = datetime.now().strftime('%Y-%m-%d')
    daily_file = os.path.join(MEMORY_DIR, f"{today}.md")
    now = datetime.now().strftime('%H:%M')
    
    entry = f"\n### {now} - Hourly Summary\n{summary}\n"
    
    with open(daily_file, 'a') as f:
        f.write(entry)
    
    return daily_file

def main():
    """Run hourly summarization."""
    now = datetime.now()
    print(f"Running hourly memory summarizer at {now.isoformat()}")
    
    # Get recent session files
    session_files = get_session_files()
    print(f"Found {len(session_files)} recent session files")
    
    # Extract messages
    messages = extract_recent_messages(session_files)
    print(f"Extracted {len(messages)} messages")
    
    # Generate summary
    summary = summarize_hour(messages)
    print(f"Summary: {summary[:100]}...")
    
    # Save to daily memory
    daily_file = append_to_daily_memory(summary)
    print(f"Appended to {daily_file}")
    
    return summary

if __name__ == '__main__':
    main()
