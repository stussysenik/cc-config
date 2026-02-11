#!/usr/bin/env python3
"""
Claude Code Native Log Sync v2

Syncs Claude's native activity logs (~/.claude/projects/) to cc-config format.
No hooks needed - reads directly from Claude's own logs.

Now captures:
- Token usage & cost estimates
- Model used (opus, sonnet, haiku)
- Git branch
- Session tracking
- Full conversation context

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
STATS_FILE = CONFIG_DIR / "logs" / ".stats.json"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Cost estimates per 1M tokens (as of 2024)
COST_PER_1M = {
    "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-haiku-3-5-20241022": {"input": 0.80, "output": 4.00},
    # Fallback for unknown models
    "default": {"input": 3.00, "output": 15.00},
}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def extract_project_name(cwd: str) -> str:
    """Extract meaningful project name from path."""
    if not cwd:
        return "unknown"
    parts = Path(cwd).parts
    skip = {'Users', 'home', 'Desktop', 'Documents', 'Projects', 'Code', 'dev', 'Volumes'}
    for part in reversed(parts):
        if part and part not in skip and not part.startswith('.'):
            return part
    return parts[-1] if parts else "unknown"


def parse_timestamp(ts: str) -> tuple[str, str, str]:
    """Parse ISO timestamp to (date, time, iso) tuple."""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M:%S'), ts
    except:
        return None, None, None


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


def extract_model_name(model: str) -> str:
    """Extract short model name."""
    if not model:
        return "unknown"
    if "opus" in model.lower():
        return "opus"
    if "sonnet" in model.lower():
        return "sonnet"
    if "haiku" in model.lower():
        return "haiku"
    return model.split("-")[0] if "-" in model else model


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost in USD."""
    costs = COST_PER_1M.get(model, COST_PER_1M["default"])
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 4)


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
    return {"files": {}, "sessions": {}}


def save_sync_state(state: dict):
    """Save sync state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def load_stats() -> dict:
    """Load cumulative stats."""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        "total_tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
        "total_cost": 0.0,
        "by_date": {},
        "by_model": {},
        "by_project": {},
    }


def save_stats(stats: dict):
    """Save cumulative stats."""
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)


def find_all_log_files() -> list[Path]:
    """Find all Claude native log files."""
    if not PROJECTS_DIR.exists():
        return []
    return list(PROJECTS_DIR.glob("**/*.jsonl"))


def parse_native_log(log_file: Path, start_pos: int = 0) -> tuple[list[dict], list[dict], int]:
    """
    Parse a Claude native log file, starting from position.
    Returns (events, token_records, new_position).
    """
    events = []
    token_records = []

    try:
        with open(log_file, 'r') as f:
            f.seek(start_pos)
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    parsed_events, parsed_tokens = parse_log_entry(data)
                    events.extend(parsed_events)
                    if parsed_tokens:
                        token_records.append(parsed_tokens)
                except json.JSONDecodeError:
                    continue
            new_pos = f.tell()
    except Exception as e:
        return [], [], start_pos

    return events, token_records, new_pos


def parse_log_entry(data: dict) -> tuple[list[dict], dict]:
    """Parse a single log entry into cc-config format events and token data."""
    events = []
    token_data = None

    entry_type = data.get('type')
    timestamp = data.get('timestamp', '')
    cwd = data.get('cwd', '')
    date, time, iso = parse_timestamp(timestamp)

    if not date:
        return [], None

    project = extract_project_name(cwd)
    session_id = data.get('sessionId', '')
    git_branch = data.get('gitBranch', '')

    base = {
        "project": project,
        "ts": time,
        "date": date,
        "cwd": cwd,
        "session": session_id[:8] if session_id else "",
        "branch": git_branch,
    }

    # User message
    if entry_type == 'user':
        msg = data.get('message', {})
        content = msg.get('content', '')
        if isinstance(content, str) and content.strip():
            events.append({
                **base,
                "action": "user_prompt",
                "prompt": content[:500],
            })

    # Assistant message with tool use and token tracking
    elif entry_type == 'assistant':
        msg = data.get('message', {})
        content = msg.get('content', [])
        model = msg.get('model', '')
        usage = msg.get('usage', {})

        # Extract token usage
        if usage:
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cache_read = usage.get('cache_read_input_tokens', 0)
            cache_write = usage.get('cache_creation_input_tokens', 0)

            if input_tokens or output_tokens:
                token_data = {
                    "date": date,
                    "project": project,
                    "model": model,
                    "model_short": extract_model_name(model),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_read": cache_read,
                    "cache_write": cache_write,
                    "cost": calculate_cost(model, input_tokens, output_tokens),
                }

        # Parse tool uses
        for item in content:
            if not isinstance(item, dict):
                continue

            if item.get('type') == 'tool_use':
                tool_events = parse_tool_use(item, base, extract_model_name(model))
                events.extend(tool_events)

    return events, token_data


def parse_tool_use(tool_data: dict, base: dict, model: str = "") -> list[dict]:
    """Parse a tool_use into events."""
    events = []
    tool_name = tool_data.get('name', '')
    inputs = tool_data.get('input', {})

    # Add model to base
    extended_base = {**base, "model": model}

    # File write = created
    if tool_name == 'Write':
        filepath = inputs.get('file_path', '')
        if filepath:
            events.append({
                **extended_base,
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
                **extended_base,
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
            # Detect git commits
            is_commit = 'git commit' in command or 'git push' in command
            events.append({
                **extended_base,
                "action": "git_operation" if is_commit else "command",
                "command": command[:200],
                "description": description,
            })

    # Task tool = delegation
    elif tool_name == 'Task':
        prompt = inputs.get('prompt', '')
        subagent = inputs.get('subagent_type', '')
        events.append({
            **extended_base,
            "action": "delegated",
            "agent": subagent,
            "task": prompt[:200],
        })

    # TaskCreate/TaskUpdate = task tracking
    elif tool_name == 'TaskCreate':
        subject = inputs.get('subject', '')
        events.append({
            **extended_base,
            "action": "task_planned",
            "task": subject,
        })

    elif tool_name == 'TaskUpdate':
        status = inputs.get('status', '')
        if status == 'completed':
            events.append({
                **extended_base,
                "action": "task_completed",
                "task_id": inputs.get('taskId', ''),
            })

    # Read/Glob/Grep = research
    elif tool_name in ['Read', 'Glob', 'Grep']:
        events.append({
            **extended_base,
            "action": "research",
            "tool": tool_name,
            "target": inputs.get('file_path') or inputs.get('pattern', ''),
        })

    # Web operations
    elif tool_name in ['WebFetch', 'WebSearch']:
        events.append({
            **extended_base,
            "action": "web_research",
            "tool": tool_name,
            "target": inputs.get('url') or inputs.get('query', ''),
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
        with open(log_file, 'a') as f:
            for event in date_events:
                f.write(json.dumps(event) + '\n')

    return dict(by_date)


def update_stats(stats: dict, token_records: list[dict]):
    """Update cumulative stats with new token data."""
    for record in token_records:
        date = record['date']
        project = record['project']
        model = record['model_short']

        # Total tokens
        stats['total_tokens']['input'] += record['input_tokens']
        stats['total_tokens']['output'] += record['output_tokens']
        stats['total_tokens']['cache_read'] += record['cache_read']
        stats['total_tokens']['cache_write'] += record['cache_write']
        stats['total_cost'] += record['cost']

        # By date
        if date not in stats['by_date']:
            stats['by_date'][date] = {
                'input': 0, 'output': 0, 'cost': 0.0, 'requests': 0
            }
        stats['by_date'][date]['input'] += record['input_tokens']
        stats['by_date'][date]['output'] += record['output_tokens']
        stats['by_date'][date]['cost'] += record['cost']
        stats['by_date'][date]['requests'] += 1

        # By model
        if model not in stats['by_model']:
            stats['by_model'][model] = {
                'input': 0, 'output': 0, 'cost': 0.0, 'requests': 0
            }
        stats['by_model'][model]['input'] += record['input_tokens']
        stats['by_model'][model]['output'] += record['output_tokens']
        stats['by_model'][model]['cost'] += record['cost']
        stats['by_model'][model]['requests'] += 1

        # By project
        if project not in stats['by_project']:
            stats['by_project'][project] = {
                'input': 0, 'output': 0, 'cost': 0.0, 'requests': 0
            }
        stats['by_project'][project]['input'] += record['input_tokens']
        stats['by_project'][project]['output'] += record['output_tokens']
        stats['by_project'][project]['cost'] += record['cost']
        stats['by_project'][project]['requests'] += 1

    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Sync Claude native logs to cc-config format')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
    parser.add_argument('--reset', action='store_true', help='Reset sync state and resync all')
    parser.add_argument('--stats', action='store_true', help='Show token/cost stats')
    args = parser.parse_args()

    log = lambda *a: None if args.quiet else print(*a)

    # Stats only mode
    if args.stats:
        stats = load_stats()
        print("\n📊 Claude Code Usage Statistics")
        print("=" * 50)
        print(f"\n💰 Total Cost: ${stats['total_cost']:.2f}")
        print(f"📝 Total Tokens: {stats['total_tokens']['input'] + stats['total_tokens']['output']:,}")
        print(f"   Input:  {stats['total_tokens']['input']:,}")
        print(f"   Output: {stats['total_tokens']['output']:,}")
        print(f"   Cache:  {stats['total_tokens']['cache_read']:,} read / {stats['total_tokens']['cache_write']:,} write")

        print(f"\n📈 By Model:")
        for model, data in sorted(stats.get('by_model', {}).items(), key=lambda x: -x[1]['cost']):
            print(f"   {model}: ${data['cost']:.2f} ({data['requests']} requests)")

        print(f"\n📁 Top Projects by Cost:")
        for project, data in sorted(stats.get('by_project', {}).items(), key=lambda x: -x[1]['cost'])[:10]:
            print(f"   {project}: ${data['cost']:.2f}")

        print(f"\n📅 Recent Days:")
        for date in sorted(stats.get('by_date', {}).keys(), reverse=True)[:7]:
            data = stats['by_date'][date]
            print(f"   {date}: ${data['cost']:.2f} ({data['requests']} requests)")
        return

    log("🔄 Claude Code Native Log Sync v2")
    log("=" * 50)

    # Load or reset state
    if args.reset:
        state = {"files": {}, "sessions": {}}
        stats = {
            "total_tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
            "total_cost": 0.0,
            "by_date": {},
            "by_model": {},
            "by_project": {},
        }
        # Clear existing logs for clean resync
        for f in LOGS_DIR.glob("*.jsonl"):
            f.unlink()
        log("♻️  Reset sync state and cleared logs")
    else:
        state = load_sync_state()
        stats = load_stats()

    # Find all log files
    log_files = find_all_log_files()
    log(f"📁 Found {len(log_files)} log files in ~/.claude/projects/")

    if not log_files:
        log("⚠️  No log files found")
        return

    # Process each file
    all_events = []
    all_tokens = []
    files_processed = 0

    for log_file in log_files:
        file_key = str(log_file)
        start_pos = state["files"].get(file_key, 0)

        events, tokens, new_pos = parse_native_log(log_file, start_pos)

        if events or tokens:
            all_events.extend(events)
            all_tokens.extend(tokens)
            files_processed += 1

        state["files"][file_key] = new_pos

    # Write events
    if all_events:
        by_date = write_events_by_date(all_events)
        log(f"\n✅ Synced {len(all_events)} events from {files_processed} files")
        for date, events in sorted(by_date.items()):
            log(f"   {date}: {len(events)} events")
    else:
        log("\n✅ Events already up to date")

    # Update stats
    if all_tokens:
        stats = update_stats(stats, all_tokens)
        new_cost = sum(t['cost'] for t in all_tokens)
        log(f"\n💰 New token usage: ${new_cost:.4f}")
        log(f"   Total to date: ${stats['total_cost']:.2f}")
        save_stats(stats)

    # Save state
    save_sync_state(state)
    log(f"\n💾 State saved")


if __name__ == '__main__':
    main()
