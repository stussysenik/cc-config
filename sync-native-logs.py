#!/usr/bin/env python3
"""
Claude Code Native Log Sync

Syncs Claude's native activity logs (~/.claude/projects/) to cc-config format.
No hooks needed - reads directly from Claude's own logs.

Usage:
    python3 sync-native-logs.py           # Full sync
    python3 sync-native-logs.py --quiet   # Quiet mode (for cron)
    python3 sync-native-logs.py --reset   # Reset sync state and resync all
"""

import json
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Paths
CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
CONFIG_DIR = Path.home() / "Desktop" / "cc-config"
LOGS_DIR = CONFIG_DIR / "logs"
STATE_FILE = CONFIG_DIR / ".sync-state.json"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def extract_project_name(cwd: str) -> str:
    """Extract meaningful project name from path."""
    if not cwd:
        return "unknown"
    parts = Path(cwd).parts
    # Skip common prefixes
    skip = {'Users', 'home', 'Desktop', 'Documents', 'Projects', 'Code', 'dev', 'Volumes'}
    for part in reversed(parts):
        if part and part not in skip and not part.startswith('.'):
            return part
    return parts[-1] if parts else "unknown"


def parse_timestamp(ts: str) -> tuple[str, str]:
    """Parse ISO timestamp to (date, time) tuple."""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M:%S')
    except:
        return None, None


def categorize_file(filepath: str) -> str:
    """Categorize a file by its path/extension."""
    fp = filepath.lower()
    if any(x in fp for x in ['test', 'spec', '__test__']):
        return 'test'
    if any(x in fp for x in ['.md', 'readme', 'docs/']):
        return 'docs'
    if any(x in fp for x in ['.json', '.yaml', '.yml', '.toml', 'config']):
        return 'config'
    if any(x in fp for x in ['.css', '.scss', '.less', 'style']):
        return 'style'
    if any(x in fp for x in ['.svelte', '.vue', '.jsx', '.tsx', 'component']):
        return 'component'
    if any(x in fp for x in ['route', 'page', 'endpoint', 'api/']):
        return 'route'
    if any(x in fp for x in ['schema', 'model', 'db/', 'database']):
        return 'database'
    return 'code'


# ═══════════════════════════════════════════════════════════════════════════════
# LOG PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def load_sync_state() -> dict:
    """Load sync state (tracks last processed position per file)."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"files": {}}


def save_sync_state(state: dict):
    """Save sync state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def find_all_log_files() -> list[Path]:
    """Find all Claude native log files."""
    if not PROJECTS_DIR.exists():
        return []
    return list(PROJECTS_DIR.glob("**/*.jsonl"))


def parse_native_log(log_file: Path, start_pos: int = 0) -> tuple[list[dict], int]:
    """
    Parse a Claude native log file, starting from position.
    Returns (events, new_position).
    """
    events = []

    try:
        with open(log_file, 'r') as f:
            f.seek(start_pos)
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    parsed = parse_log_entry(data)
                    if parsed:
                        events.extend(parsed)
                except json.JSONDecodeError:
                    continue
            new_pos = f.tell()
    except Exception as e:
        return [], start_pos

    return events, new_pos


def parse_log_entry(data: dict) -> list[dict]:
    """Parse a single log entry into cc-config format events."""
    events = []

    entry_type = data.get('type')
    timestamp = data.get('timestamp', '')
    cwd = data.get('cwd', '')
    date, time = parse_timestamp(timestamp)

    if not date:
        return []

    project = extract_project_name(cwd)
    base = {
        "project": project,
        "ts": time,
        "date": date,
        "cwd": cwd,
    }

    # User message
    if entry_type == 'user':
        msg = data.get('message', {})
        content = msg.get('content', '')
        if isinstance(content, str) and content.strip():
            events.append({
                **base,
                "action": "user_prompt",
                "prompt": content[:500],  # Truncate long prompts
            })

    # Assistant message with tool use
    elif entry_type == 'assistant':
        msg = data.get('message', {})
        content = msg.get('content', [])

        for item in content:
            if not isinstance(item, dict):
                continue

            if item.get('type') == 'tool_use':
                tool_events = parse_tool_use(item, base)
                events.extend(tool_events)

    return events


def parse_tool_use(tool_data: dict, base: dict) -> list[dict]:
    """Parse a tool_use into events."""
    events = []
    tool_name = tool_data.get('name', '')
    inputs = tool_data.get('input', {})

    # File write = created
    if tool_name == 'Write':
        filepath = inputs.get('file_path', '')
        if filepath:
            events.append({
                **base,
                "action": "created_file",
                "file": Path(filepath).name,
                "path": filepath,
                "category": categorize_file(filepath),
            })

    # File edit = modified
    elif tool_name == 'Edit':
        filepath = inputs.get('file_path', '')
        if filepath:
            events.append({
                **base,
                "action": "modified_file",
                "file": Path(filepath).name,
                "path": filepath,
                "category": categorize_file(filepath),
            })

    # Bash command
    elif tool_name == 'Bash':
        command = inputs.get('command', '')
        description = inputs.get('description', '')
        if command:
            events.append({
                **base,
                "action": "command",
                "command": command[:200],  # Truncate long commands
                "description": description,
            })

    # Task tool = delegation
    elif tool_name == 'Task':
        prompt = inputs.get('prompt', '')
        subagent = inputs.get('subagent_type', '')
        events.append({
            **base,
            "action": "delegated",
            "agent": subagent,
            "task": prompt[:200],
        })

    # TaskCreate/TaskUpdate = task tracking
    elif tool_name == 'TaskCreate':
        subject = inputs.get('subject', '')
        events.append({
            **base,
            "action": "task_planned",
            "task": subject,
        })

    elif tool_name == 'TaskUpdate':
        status = inputs.get('status', '')
        if status == 'completed':
            events.append({
                **base,
                "action": "task_completed",
                "task_id": inputs.get('taskId', ''),
            })

    # Read/Glob/Grep = research
    elif tool_name in ['Read', 'Glob', 'Grep', 'WebFetch', 'WebSearch']:
        events.append({
            **base,
            "action": "research",
            "tool": tool_name,
            "target": inputs.get('file_path') or inputs.get('pattern') or inputs.get('url', ''),
        })

    return events


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

def write_events_by_date(events: list[dict]):
    """Write events grouped by date to log files."""
    by_date = defaultdict(list)

    for event in events:
        date = event.pop('date', None)
        if date:
            by_date[date].append(event)

    for date, date_events in by_date.items():
        log_file = LOGS_DIR / f"{date}.jsonl"

        # Append to existing log file
        with open(log_file, 'a') as f:
            for event in date_events:
                f.write(json.dumps(event) + '\n')

    return dict(by_date)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Sync Claude native logs to cc-config format')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
    parser.add_argument('--reset', action='store_true', help='Reset sync state and resync all')
    args = parser.parse_args()

    log = lambda *a: None if args.quiet else print(*a)

    log("🔄 Claude Code Native Log Sync")
    log("=" * 50)

    # Load or reset state
    if args.reset:
        state = {"files": {}}
        log("♻️  Reset sync state")
    else:
        state = load_sync_state()

    # Find all log files
    log_files = find_all_log_files()
    log(f"📁 Found {len(log_files)} log files in ~/.claude/projects/")

    if not log_files:
        log("⚠️  No log files found")
        return

    # Process each file
    all_events = []
    files_processed = 0

    for log_file in log_files:
        file_key = str(log_file)
        start_pos = state["files"].get(file_key, 0)

        events, new_pos = parse_native_log(log_file, start_pos)

        if events:
            all_events.extend(events)
            files_processed += 1

        state["files"][file_key] = new_pos

    # Write events
    if all_events:
        by_date = write_events_by_date(all_events)
        log(f"\n✅ Synced {len(all_events)} events from {files_processed} files")
        for date, events in sorted(by_date.items()):
            log(f"   {date}: {len(events)} events")
    else:
        log("\n✅ Already up to date")

    # Save state
    save_sync_state(state)
    log(f"\n💾 State saved to {STATE_FILE}")


if __name__ == '__main__':
    main()
