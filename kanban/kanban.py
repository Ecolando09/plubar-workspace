#!/usr/bin/env python3
"""
Kanban Board Manager for Discord Projects Channel

Usage:
    python kanban.py add-project "Name" "Description"
    python kanban.py add-task "Project" "Task name" --status todo --priority high --assignee Landon
    python kanban.py update-task "Project" "Task name" --status done
    python kanban.py show
    python kanban.py show-project "Project"
    python kanban.py post-discord --channel 1469859869602353396
"""

import yaml
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse

KANBAN_FILE = Path(__file__).parent / "kanban.yaml"

def load_kanban():
    """Load kanban data from YAML file."""
    if KANBAN_FILE.exists():
        with open(KANBAN_FILE, 'r') as f:
            return yaml.safe_load(f) or {'projects': []}
    return {'projects': []}

def save_kanban(data):
    """Save kanban data to YAML file."""
    with open(KANBAN_FILE, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def find_project(data, project_name):
    """Find a project by name (case-insensitive)."""
    for project in data.get('projects', []):
        if project.get('name', '').lower() == project_name.lower():
            return project
    return None

def find_task(project, task_title):
    """Find a task in a project by title (case-insensitive)."""
    for task in project.get('tasks', []):
        if task.get('title', '').lower() == task_title.lower():
            return task
    return None

def add_project(name, description=''):
    """Add a new project."""
    data = load_kanban()
    
    if find_project(data, name):
        print(f"❌ Project '{name}' already exists!")
        return False
    
    data['projects'].append({
        'name': name,
        'description': description,
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'tasks': []
    })
    
    save_kanban(data)
    print(f"✅ Added project: {name}")
    return True

def add_task(project_name, title, status='todo', priority='medium', assignee='', due_date='', notes=''):
    """Add a task to a project."""
    data = load_kanban()
    project = find_project(data, project_name)
    
    if not project:
        print(f"❌ Project '{project_name}' not found!")
        return False
    
    task = {
        'title': title,
        'status': status,
        'priority': priority,
        'assignee': assignee,
        'due_date': due_date,
        'notes': notes,
        'created_at': datetime.now().isoformat()
    }
    
    project['tasks'].append(task)
    save_kanban(data)
    print(f"✅ Added task to {project_name}: {title}")
    return True

def update_task(project_name, task_title, **kwargs):
    """Update a task's status or other fields."""
    data = load_kanban()
    project = find_project(data, project_name)
    
    if not project:
        print(f"❌ Project '{project_name}' not found!")
        return False
    
    task = find_task(project, task_title)
    if not task:
        print(f"❌ Task '{task_title}' not found in {project_name}!")
        return False
    
    old_status = task.get('status', 'todo')
    new_status = kwargs.get('status', old_status)
    
    for key, value in kwargs.items():
        task[key] = value
    task['updated_at'] = datetime.now().isoformat()
    
    save_kanban(data)
    print(f"✅ Updated task: {task_title}")
    
    # Auto-post to Discord if task was marked done
    if new_status == 'done' and old_status != 'done':
        discord_channel_id = os.environ.get('KANBAN_DISCORD_CHANNEL', '')
        if discord_channel_id:
            post_to_discord(project['name'], task_title, task.get('assignee', 'Unknown'))
    
    return True

def post_to_discord(project_name, task_title, assignee):
    """Post task completion to Discord."""
    import subprocess
    message = f"✅ **Task Completed!**\n\n📋 **{project_name}**\n🎯 {task_title}\n👤 Completed by: {assignee}"
    
    discord_channel = os.environ.get('KANBAN_DISCORD_CHANNEL', '')
    if not discord_channel:
        print("⚠️ KANBAN_DISCORD_CHANNEL not set")
        return
    
    try:
        result = subprocess.run([
            '/usr/bin/openclaw', 'message', 'send',
            '--channel', 'discord',
            '--target', f'channel:{discord_channel}',
            '--message', message
        ], capture_output=True, text=True, cwd='/root')
        
        if result.returncode == 0:
            print("📢 Posted to Discord!")
        else:
            print(f"⚠️ Discord post failed: {result.stderr}")
    except FileNotFoundError:
        print("⚠️ openclaw command not found")
    except Exception as e:
        print(f"⚠️ Could not post to Discord: {e}")

def format_status_emoji(status):
    """Get emoji for task status."""
    status_emojis = {
        'todo': '⬜',
        'in-progress': '🔄',
        'done': '✅',
        'blocked': '🚫',
        'active': '🟢',
        'on-hold': '🟡',
        'completed': '✅'
    }
    return status_emojis.get(status, '⬜')

def format_priority_emoji(priority):
    """Get emoji for priority."""
    priority_emojis = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }
    return priority_emojis.get(priority, '🟢')

def show_kanban(project_name=None):
    """Display the kanban board."""
    data = load_kanban()
    
    if project_name:
        project = find_project(data, project_name)
        if not project:
            print(f"❌ Project '{project_name}' not found!")
            return
        
        print(f"\n📋 {project.get('name', 'Unknown')}")
        print(f"   {project.get('description', '')}")
        print(f"   Status: {project.get('status', 'unknown')}")
        print(f"\n   Tasks:")
        
        for task in project.get('tasks', []):
            status_emoji = format_status_emoji(task.get('status', 'todo'))
            priority_emoji = format_priority_emoji(task.get('priority', 'medium'))
            assignee = task.get('assignee', 'Unassigned')
            print(f"   {status_emoji} {priority_emoji} {task.get('title', 'Unknown')}")
            print(f"      → {task.get('status', 'todo')} | {assignee}")
        return
    
    print("\n📊 KANBAN BOARD")
    print("=" * 50)
    
    for project in data.get('projects', []):
        status_emoji = format_status_emoji(project.get('status', 'active'))
        task_count = len(project.get('tasks', []))
        done_count = sum(1 for t in project.get('tasks', []) if t.get('status') == 'done')
        
        print(f"\n{status_emoji} **{project.get('name', 'Unknown')}**")
        print(f"   {project.get('description', '')}")
        print(f"   Tasks: {done_count}/{task_count} done")
        
        # Group tasks by status
        for status in ['todo', 'in-progress', 'done', 'blocked']:
            tasks = [t for t in project.get('tasks', []) if t.get('status') == status]
            if tasks:
                print(f"\n   {format_status_emoji(status)} {status.upper()}:")
                for task in tasks:
                    priority_emoji = format_priority_emoji(task.get('priority', 'medium'))
                    assignee = task.get('assignee', 'Unassigned')
                    print(f"      {priority_emoji} {task.get('title', 'Unknown')} ({assignee})")

def generate_discord_message():
    """Generate a Discord-ready kanban message."""
    data = load_kanban()
    
    message = "📊 **PROJECT KANBAN BOARD** 📊\n"
    message += "=" * 50 + "\n\n"
    
    for project in data.get('projects', []):
        status_emoji = format_status_emoji(project.get('status', 'active'))
        task_count = len(project.get('tasks', []))
        done_count = sum(1 for t in project.get('tasks', []) if t.get('status') == 'done')
        
        message += f"{status_emoji} **{project.get('name', 'Unknown')}**\n"
        message += f"📝 {project.get('description', '')}\n"
        message += f"✅ Progress: {done_count}/{task_count} tasks complete\n\n"
        
        # Quick status by priority
        high = [t for t in project.get('tasks', []) if t.get('priority') == 'high' and t.get('status') != 'done']
        if high:
            message += f"🔴 **High Priority:**\n"
            for task in high:
                assignee = task.get('assignee', 'Unassigned')
                message += f"  • {task.get('title', 'Unknown')} ({assignee})\n"
            message += "\n"
    
    message += f"\n_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_"
    return message

def main():
    parser = argparse.ArgumentParser(description='Kanban Board Manager')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add project
    cmd = subparsers.add_parser('add-project', help='Add a new project')
    cmd.add_argument('name', help='Project name')
    cmd.add_argument('description', nargs='?', default='', help='Project description')
    
    # Add task
    cmd = subparsers.add_parser('add-task', help='Add a task to a project')
    cmd.add_argument('project', help='Project name')
    cmd.add_argument('title', help='Task title')
    cmd.add_argument('--status', default='todo', choices=['todo', 'in-progress', 'done', 'blocked'])
    cmd.add_argument('--priority', default='medium', choices=['high', 'medium', 'low'])
    cmd.add_argument('--assignee', default='')
    cmd.add_argument('--due', default='', help='Due date (YYYY-MM-DD)')
    cmd.add_argument('--notes', default='')
    
    # Update task
    cmd = subparsers.add_parser('update-task', help='Update a task')
    cmd.add_argument('project', help='Project name')
    cmd.add_argument('task', help='Task title')
    cmd.add_argument('--status', choices=['todo', 'in-progress', 'done', 'blocked'])
    cmd.add_argument('--priority', choices=['high', 'medium', 'low'])
    cmd.add_argument('--assignee')
    
    # Show
    cmd = subparsers.add_parser('show', help='Show kanban board')
    cmd.add_argument('project', nargs='?', help='Show specific project')
    
    # Discord
    cmd = subparsers.add_parser('post-discord', help='Generate Discord message')
    cmd.add_argument('--channel', required=True, help='Discord channel ID')
    
    args = parser.parse_args()
    
    if args.command == 'add-project':
        add_project(args.name, args.description)
    elif args.command == 'add-task':
        add_task(args.project, args.title, args.status, args.priority, args.assignee, args.due, args.notes)
    elif args.command == 'update-task':
        kwargs = {}
        if args.status:
            kwargs['status'] = args.status
        if args.priority:
            kwargs['priority'] = args.priority
        if args.assignee:
            kwargs['assignee'] = args.assignee
        update_task(args.project, args.task, **kwargs)
    elif args.command == 'show':
        show_kanban(args.project)
    elif args.command == 'post-discord':
        print(generate_discord_message())
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
