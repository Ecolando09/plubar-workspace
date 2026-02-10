#!/usr/bin/env python3
"""
Pre-Compaction Dump
Saves recent conversation state before compaction for later injection.
"""

import os
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
SESSION_DIR = f"{WORKSPACE}/agents/main/sessions"
PRECOMPACT_DIR = f"{WORKSPACE}/memory/precompact"

def get_recent_sessions(max_hours=2):
    """Get session files from last N hours."""
    if not os.path.exists(SESSION_DIR):
        return []
    
    cutoff = datetime.now().timestamp() - (2 * 3600)  # 2 hours ago
    recent = []
    
    for f in os.listdir(SESSION_DIR):
        if f.endswith('.jsonl'):
            filepath = os.path.join(SESSION_DIR, f)
            mtime = os.path.getmtime(filepath)
            if mtime > cutoff:
                recent.append((filepath, mtime))
    
    recent.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in recent]

def extract_precompact_state(session_files):
    """Extract state for pre-compaction dump."""
    state = {
        'dump_time': datetime.now().isoformat(),
        'sessions': [],
        'key_context': {
            'user_preferences': [],
            'active_projects': [],
            'recent_decisions': [],
            'pending_tasks': [],
            'open_loops': []
        }
    }
    
    for session_file in session_files:
        session_data = {
            'file': os.path.basename(session_file),
            'messages': [],
            'think_blocks': []
        }
        
        try:
            with open(session_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        
                        # Extract messages
                        if 'content' in data and data.get('role') in ['user', 'assistant']:
                            msg = {
                                'role': data['role'],
                                'content': data['content'][:1000],
                                'timestamp': data.get('created_at', '')
                            }
                            session_data['messages'].append(msg)
                        
                        # Extract thinking blocks
                        if data.get('type') == 'think':
                            session_data['think_blocks'].append({
                                'content': data.get('content', '')[:500],
                                'timestamp': data.get('created_at', '')
                            })
                        
                        # Look for key context markers
                        content = data.get('content', '').lower()
                        
                        # Project indicators
                        if any(kw in content for kw in ['building', 'working on', 'implementing', 'creating']):
                            if content not in state['key_context']['active_projects'][-3:]:
                                state['key_context']['active_projects'].append(content[:200])
                        
                        # Decision indicators
                        if any(kw in content for kw in ['decided', 'chose', 'agreed', 'settled on']):
                            state['key_context']['recent_decisions'].append(content[:200])
                        
                        # Task indicators
                        if any(kw in content for kw in ['need to', 'want to', 'should', 'have to']):
                            if content not in state['key_context']['pending_tasks'][-3:]:
                                state['key_context']['pending_tasks'].append(content[:200])
                        
                        # User preferences
                        if any(kw in content for kw in ['prefer', 'like', 'dislike', 'want', 'don\'t want']):
                            if content not in state['key_context']['user_preferences'][-5:]:
                                state['key_context']['user_preferences'].append(content[:200])
            
            state['sessions'].append(session_data)
            
        except Exception as e:
            print(f"Error processing {session_file}: {e}")
    
    return state

def save_precompact_dump(state):
    """Save pre-compaction dump."""
    os.makedirs(PRECOMPACT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filepath = os.path.join(PRECOMPACT_DIR, f"precompact_{timestamp}.json")
    
    with open(filepath, 'w') as f:
        json.dump(state, f, indent=2)
    
    # Also save latest as symlink
    latest_link = os.path.join(PRECOMPACT_DIR, "latest.json")
    if os.path.exists(latest_link):
        os.remove(latest_link)
    os.symlink(filepath, latest_link)
    
    return filepath

def generate_compact_summary(state):
    """Generate a compact summary for injection after compaction."""
    summary = {
        'dump_time': state['dump_time'],
        'session_count': len(state['sessions']),
        'message_count': sum(len(s['messages']) for s in state['sessions']),
        'active_projects': state['key_context']['active_projects'][-3:],
        'recent_decisions': state['key_context']['recent_decisions'][-2:],
        'pending_tasks': state['key_context']['pending_tasks'][-3:],
        'key_preferences': state['key_context']['user_preferences'][-5:],
        'last_user_message': '',
        'last_assistant_response': ''
    }
    
    # Get last messages
    all_msgs = []
    for session in state['sessions']:
        all_msgs.extend(session['messages'])
    
    user_msgs = [m for m in all_msgs if m['role'] == 'user']
    assistant_msgs = [m for m in all_msgs if m['role'] == 'assistant']
    
    if user_msgs:
        summary['last_user_message'] = user_msgs[-1]['content'][:300]
    if assistant_msgs:
        summary['last_assistant_response'] = assistant_msgs[-1]['content'][:300]
    
    return summary

def main():
    """Run pre-compaction dump."""
    print("Running pre-compaction dump...")
    
    # Get recent sessions
    session_files = get_recent_sessions()
    print(f"Found {len(session_files)} recent session files")
    
    # Extract state
    state = extract_precompact_state(session_files)
    print(f"Extracted {sum(len(s['messages']) for s in state['sessions'])} messages")
    
    # Save dump
    filepath = save_precompact_dump(state)
    print(f"Saved pre-compaction dump to {filepath}")
    
    # Generate compact summary
    summary = generate_compact_summary(state)
    print(f"Compact summary: {summary['message_count']} messages, {len(summary['active_projects'])} projects")
    
    return filepath, summary

if __name__ == '__main__':
    main()
