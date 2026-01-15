#!/usr/bin/env python3
"""
Claude Code Activity Logger v2
Captures meaningful engineering context for daily journals.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path.home() / "Desktop" / "cc-config"
LOGS_DIR = CONFIG_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_log_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return LOGS_DIR / f"{today}.jsonl"

def log_event(event_data):
    log_file = get_log_file()
    with open(log_file, "a") as f:
        f.write(json.dumps(event_data) + "\n")

def extract_project_name(cwd):
    """Extract meaningful project name from path."""
    parts = Path(cwd).parts
    # Skip common prefixes
    skip = {'Users', 'home', 'Desktop', 'Documents', 'Projects', 'Code', 'dev'}
    meaningful = [p for p in parts if p not in skip and not p.startswith('.')]
    return meaningful[-1] if meaningful else Path(cwd).name

def main():
    stdin_data = {}
    try:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
            if content.strip():
                stdin_data = json.loads(content)
    except:
        pass

    cwd = os.getcwd()
    event = {
        "ts": datetime.now().strftime("%H:%M"),
        "project": extract_project_name(cwd),
        "cwd": cwd,
    }

    if not stdin_data:
        return  # Skip empty events

    tool_name = stdin_data.get("tool_name", "")
    tool_input = stdin_data.get("tool_input", {})
    hook_event = stdin_data.get("hook_event", "")

    # Only log meaningful events
    if hook_event == "PreToolUse":
        return  # Skip pre-events, we'll capture post

    event["tool"] = tool_name

    # Capture high-level context based on tool
    if tool_name == "Write":
        filepath = tool_input.get("file_path", "")
        event["action"] = "created_file"
        event["file"] = Path(filepath).name
        event["path"] = filepath
        # Infer what kind of file
        ext = Path(filepath).suffix
        if ext in ('.py', '.js', '.ts', '.tsx', '.jsx'):
            event["category"] = "code"
        elif ext in ('.md', '.txt', '.rst'):
            event["category"] = "docs"
        elif ext in ('.json', '.yaml', '.yml', '.toml'):
            event["category"] = "config"
        elif ext in ('.css', '.scss', '.html'):
            event["category"] = "frontend"

    elif tool_name == "Edit":
        filepath = tool_input.get("file_path", "")
        event["action"] = "modified_file"
        event["file"] = Path(filepath).name
        event["path"] = filepath

    elif tool_name == "Bash":
        cmd = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        event["command"] = cmd[:200]
        event["description"] = desc

        # Categorize command intent
        cmd_lower = cmd.lower()
        if any(x in cmd_lower for x in ['test', 'jest', 'pytest', 'vitest', 'spec']):
            event["action"] = "ran_tests"
            event["category"] = "testing"
        elif any(x in cmd_lower for x in ['build', 'compile', 'webpack', 'vite', 'tsc']):
            event["action"] = "built_project"
            event["category"] = "build"
        elif any(x in cmd_lower for x in ['npm install', 'yarn add', 'pip install', 'cargo add']):
            event["action"] = "installed_deps"
            event["category"] = "dependencies"
        elif any(x in cmd_lower for x in ['git commit', 'git push']):
            event["action"] = "committed_code"
            event["category"] = "git"
        elif any(x in cmd_lower for x in ['git checkout', 'git branch', 'git merge']):
            event["action"] = "git_operation"
            event["category"] = "git"
        elif 'mkdir' in cmd_lower:
            event["action"] = "created_directory"
            event["category"] = "setup"
        elif any(x in cmd_lower for x in ['docker', 'kubectl', 'terraform']):
            event["action"] = "infra_operation"
            event["category"] = "infrastructure"
        else:
            event["action"] = "ran_command"

    elif tool_name == "Task":
        event["action"] = "delegated_task"
        event["task_type"] = tool_input.get("subagent_type", "")
        event["task_description"] = tool_input.get("description", "")
        event["task_prompt"] = tool_input.get("prompt", "")[:500]  # Capture what was asked

    elif tool_name == "TodoWrite":
        todos = tool_input.get("todos", [])
        event["action"] = "planned_tasks"
        event["tasks"] = [t.get("content", "") for t in todos if t.get("status") != "completed"]
        event["completed"] = [t.get("content", "") for t in todos if t.get("status") == "completed"]

    elif tool_name in ("WebSearch", "WebFetch"):
        event["action"] = "researched"
        event["query"] = tool_input.get("query", tool_input.get("prompt", ""))[:200]

    elif tool_name == "Read":
        # Only log reads if they seem significant (not just checking files)
        filepath = tool_input.get("file_path", "")
        event["action"] = "read_file"
        event["file"] = Path(filepath).name
        # Don't log every read - they're too noisy
        return

    elif tool_name in ("Grep", "Glob"):
        event["action"] = "searched_code"
        event["pattern"] = tool_input.get("pattern", "")
        # Skip logging searches - too noisy
        return

    else:
        # Skip unknown/noisy tools
        return

    log_event(event)

if __name__ == "__main__":
    main()
