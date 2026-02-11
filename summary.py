#!/usr/bin/env python3
"""
Claude Code Engineering Journal
Generates narrative summaries of what you actually built.
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import argparse

CONFIG_DIR = Path.home() / "Desktop" / "cc-config"
LOGS_DIR = CONFIG_DIR / "logs"
SUMMARIES_DIR = CONFIG_DIR / "summaries"
SYNC_SCRIPT = CONFIG_DIR / "sync-native-logs.py"


STATS_FILE = CONFIG_DIR / "logs" / ".stats.json"


def auto_sync_native_logs():
    """Auto-sync native logs before generating summary."""
    if SYNC_SCRIPT.exists():
        try:
            subprocess.run(
                ["python3", str(SYNC_SCRIPT), "--quiet"],
                capture_output=True,
                timeout=30
            )
        except:
            pass  # Silently fail if sync has issues


def load_usage_stats() -> dict:
    """Load usage stats from sync script."""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def render_usage_stats(date_str: str = None, start_date: str = None, end_date: str = None) -> str:
    """Render usage statistics section. Supports single date or date range."""
    stats = load_usage_stats()
    if not stats:
        return ""

    lines = []
    lines.append("\n" + "─" * 60)
    lines.append("💰 Usage Statistics")
    lines.append("─" * 60)

    by_date = stats.get('by_date', {})

    # Date range stats
    if start_date and end_date:
        range_cost = 0.0
        range_requests = 0
        range_input = 0
        range_output = 0
        days_with_activity = 0

        for d, d_stats in by_date.items():
            if start_date <= d <= end_date:
                range_cost += d_stats.get('cost', 0)
                range_requests += d_stats.get('requests', 0)
                range_input += d_stats.get('input', 0)
                range_output += d_stats.get('output', 0)
                days_with_activity += 1

        lines.append(f"  Period: ${range_cost:.2f} ({range_requests:,} requests)")
        lines.append(f"  Tokens: {(range_input + range_output):,} ({days_with_activity} days)")

        # Daily average
        if days_with_activity > 0:
            avg_cost = range_cost / days_with_activity
            lines.append(f"  Daily avg: ${avg_cost:.2f}/day")

    # Single date stats
    elif date_str and date_str in by_date:
        day_stats = by_date[date_str]
        lines.append(f"  Today: ${day_stats['cost']:.2f} ({day_stats['requests']:,} requests)")

    # Total stats
    total_cost = stats.get('total_cost', 0)
    total_tokens = stats.get('total_tokens', {})
    input_t = total_tokens.get('input', 0)
    output_t = total_tokens.get('output', 0)

    lines.append(f"  Total: ${total_cost:.2f} | {(input_t + output_t):,} tokens")

    # Model breakdown (compact)
    by_model = stats.get('by_model', {})
    if by_model:
        model_parts = []
        for model, data in sorted(by_model.items(), key=lambda x: -x[1]['cost']):
            model_parts.append(f"{model}: ${data['cost']:.2f}")
        lines.append(f"  Models: {' | '.join(model_parts)}")

    # Top projects (for range view)
    if start_date and end_date:
        by_project = stats.get('by_project', {})
        if by_project:
            top_projects = sorted(by_project.items(), key=lambda x: -x[1]['cost'])[:5]
            proj_parts = [f"{p}: ${d['cost']:.2f}" for p, d in top_projects]
            lines.append(f"  Top: {' | '.join(proj_parts[:3])}")
    else:
        # Recent days (last 3) for single day view
        if by_date:
            recent = sorted(by_date.keys(), reverse=True)[:3]
            day_parts = [f"{d[-5:]}: ${by_date[d]['cost']:.2f}" for d in recent]
            lines.append(f"  Recent: {' | '.join(day_parts)}")

    lines.append("")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# ASCII ART
# ═══════════════════════════════════════════════════════════════════════════════

HEADER = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███████╗███╗   ██╗ ██████╗      ██╗ ██████╗ ██╗   ██╗██████╗ ███╗   ██╗    ║
║   ██╔════╝████╗  ██║██╔════╝      ██║██╔═══██╗██║   ██║██╔══██╗████╗  ██║    ║
║   █████╗  ██╔██╗ ██║██║  ███╗     ██║██║   ██║██║   ██║██████╔╝██╔██╗ ██║    ║
║   ██╔══╝  ██║╚██╗██║██║   ██║██   ██║██║   ██║██║   ██║██╔══██╗██║╚██╗██║    ║
║   ███████╗██║ ╚████║╚██████╔╝╚█████╔╝╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║    ║
║   ╚══════╝╚═╝  ╚═══╝ ╚═════╝  ╚════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

def load_logs(date_str):
    """Load logs for a specific date."""
    log_file = LOGS_DIR / f"{date_str}.jsonl"
    if not log_file.exists():
        return []
    events = []
    with open(log_file) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except:
                    pass
    return events

def get_available_dates():
    """Get all dates with logs."""
    if not LOGS_DIR.exists():
        return []
    return sorted([f.stem for f in LOGS_DIR.glob("*.jsonl")], reverse=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_events(events):
    """Analyze events into meaningful work summaries."""

    projects = defaultdict(lambda: {
        "files_created": [],
        "files_modified": [],
        "tasks_planned": [],
        "tasks_completed": [],
        "commands": [],
        "research": [],
        "delegated": [],
        "prompts": [],  # For backfilled data
        "timeline": [],
        "categories": set(),
        "has_backfill": False,
    })

    for e in events:
        project = e.get("project", "unknown")
        action = e.get("action", "")
        ts = e.get("ts", "")
        source = e.get("source", "")

        # Handle backfilled events (from history.jsonl)
        if source == "backfill" and action == "user_prompt":
            projects[project]["prompts"].append({
                "prompt": e.get("prompt", ""),
                "time": ts,
            })
            projects[project]["has_backfill"] = True
            if ts:
                projects[project]["timeline"].append(ts)
            continue

        if action == "created_file":
            projects[project]["files_created"].append({
                "file": e.get("file", ""),
                "path": e.get("path", ""),
                "category": e.get("category", ""),
                "time": ts,
            })
            if e.get("category"):
                projects[project]["categories"].add(e["category"])

        elif action == "modified_file":
            projects[project]["files_modified"].append({
                "file": e.get("file", ""),
                "path": e.get("path", ""),
                "time": ts,
            })

        elif action == "planned_tasks":
            tasks = e.get("tasks", [])
            completed = e.get("completed", [])
            projects[project]["tasks_planned"].extend(tasks)
            projects[project]["tasks_completed"].extend(completed)

        elif action in ("ran_tests", "built_project", "installed_deps", "committed_code",
                       "git_operation", "infra_operation", "ran_command"):
            projects[project]["commands"].append({
                "action": action,
                "command": e.get("command", ""),
                "description": e.get("description", ""),
                "category": e.get("category", ""),
                "time": ts,
            })
            if e.get("category"):
                projects[project]["categories"].add(e["category"])

        elif action == "researched":
            projects[project]["research"].append({
                "query": e.get("query", ""),
                "time": ts,
            })

        elif action == "delegated_task":
            projects[project]["delegated"].append({
                "type": e.get("task_type", ""),
                "description": e.get("task_description", ""),
                "prompt": e.get("task_prompt", ""),
                "time": ts,
            })

        # Track timeline
        if ts:
            projects[project]["timeline"].append(ts)

    return dict(projects)

# ═══════════════════════════════════════════════════════════════════════════════
# RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def render_project_summary(name, data):
    """Render a single project's summary."""
    lines = []

    # Project header with work time
    timeline = data["timeline"]
    if timeline:
        start = min(timeline)
        end = max(timeline)
        time_span = f"{start} → {end}"
    else:
        time_span = "no activity"

    # Show backfill indicator
    source_label = " (from session history)" if data.get("has_backfill") else ""

    lines.append(f"")
    lines.append(f"┌{'─' * 76}┐")
    lines.append(f"│  📁 {name:<50} [{time_span:>17}] │")
    if source_label:
        lines.append(f"│  {source_label:<74} │")
    lines.append(f"└{'─' * 76}┘")

    # For backfilled data, show prompts instead of detailed tool usage
    if data.get("has_backfill"):
        prompts = data["prompts"]
        if prompts:
            lines.append(f"")
            lines.append(f"  📝 SESSION ACTIVITY:")
            for p in prompts[:8]:
                prompt_text = p["prompt"][:65] + "..." if len(p["prompt"]) > 65 else p["prompt"]
                if prompt_text:
                    lines.append(f"      • {prompt_text}")
            if len(prompts) > 8:
                lines.append(f"      ... and {len(prompts) - 8} more sessions")
        return "\n".join(lines)

    # What was built
    files_created = data["files_created"]
    if files_created:
        lines.append(f"")
        lines.append(f"  🏗️  BUILT:")
        for f in files_created[:10]:
            category_icon = {
                "code": "💻",
                "frontend": "🎨",
                "config": "⚙️",
                "docs": "📝",
            }.get(f.get("category", ""), "📄")
            lines.append(f"      {category_icon} {f['file']}")
        if len(files_created) > 10:
            lines.append(f"      ... and {len(files_created) - 10} more files")

    # What was modified
    files_modified = data["files_modified"]
    if files_modified:
        lines.append(f"")
        lines.append(f"  ✏️  MODIFIED:")
        unique_files = list(set(f["file"] for f in files_modified))[:8]
        for f in unique_files:
            lines.append(f"      • {f}")
        if len(files_modified) > 8:
            lines.append(f"      ... and {len(set(f['file'] for f in files_modified)) - 8} more files")

    # Key operations
    commands = data["commands"]
    if commands:
        lines.append(f"")
        lines.append(f"  ⚡ OPERATIONS:")

        # Group by type
        by_type = defaultdict(list)
        for c in commands:
            by_type[c["action"]].append(c)

        action_labels = {
            "ran_tests": ("🧪", "Ran tests"),
            "built_project": ("🔨", "Built project"),
            "installed_deps": ("📦", "Installed dependencies"),
            "committed_code": ("💾", "Committed code"),
            "git_operation": ("🌿", "Git operations"),
            "infra_operation": ("☁️", "Infrastructure"),
            "ran_command": ("▶️", "Commands"),
        }

        for action, items in by_type.items():
            icon, label = action_labels.get(action, ("•", action))
            if action == "ran_command":
                # Show interesting commands
                for item in items[:3]:
                    desc = item.get("description", "") or item.get("command", "")[:50]
                    if desc:
                        lines.append(f"      {icon} {desc}")
            else:
                lines.append(f"      {icon} {label} ({len(items)}x)")

    # Research conducted
    research = data["research"]
    if research:
        lines.append(f"")
        lines.append(f"  🔍 RESEARCHED:")
        for r in research[:5]:
            query = r["query"][:60] + "..." if len(r["query"]) > 60 else r["query"]
            lines.append(f"      • {query}")

    # Tasks from todo list
    tasks_completed = list(set(data["tasks_completed"]))
    tasks_planned = list(set(data["tasks_planned"]))

    if tasks_completed:
        lines.append(f"")
        lines.append(f"  ✅ COMPLETED:")
        for t in tasks_completed[:8]:
            lines.append(f"      ✓ {t}")

    # Delegated work (agent tasks)
    delegated = data["delegated"]
    if delegated:
        lines.append(f"")
        lines.append(f"  🤖 DELEGATED:")
        for d in delegated[:5]:
            desc = d.get("description", "") or d.get("type", "task")
            lines.append(f"      → {desc}")

    return "\n".join(lines)

def render_day_narrative(projects, date_str):
    """Generate a narrative summary of the day."""
    lines = []

    total_files_created = sum(len(p["files_created"]) for p in projects.values())
    total_files_modified = sum(len(p["files_modified"]) for p in projects.values())
    total_commands = sum(len(p["commands"]) for p in projects.values())
    total_completed = sum(len(set(p["tasks_completed"])) for p in projects.values())

    # All categories worked on
    all_categories = set()
    for p in projects.values():
        all_categories.update(p["categories"])

    lines.append("")
    lines.append("┌" + "─" * 76 + "┐")
    lines.append("│" + " " * 28 + "📊 DAY AT A GLANCE" + " " * 30 + "│")
    lines.append("├" + "─" * 76 + "┤")

    # Stats row
    stats = f"│  {len(projects)} project(s)  •  {total_files_created} created  •  {total_files_modified} modified  •  {total_completed} tasks done"
    stats = stats + " " * (77 - len(stats)) + "│"
    lines.append(stats)

    lines.append("└" + "─" * 76 + "┘")

    # Work type indicators
    if all_categories:
        category_icons = {
            "code": "💻 Coding",
            "frontend": "🎨 Frontend",
            "config": "⚙️ Config",
            "docs": "📝 Docs",
            "testing": "🧪 Testing",
            "build": "🔨 Building",
            "git": "🌿 Git",
            "infrastructure": "☁️ Infra",
            "dependencies": "📦 Deps",
        }
        work_types = [category_icons.get(c, c) for c in all_categories if c in category_icons]
        if work_types:
            lines.append("")
            lines.append("  Work types: " + "  ".join(work_types))

    return "\n".join(lines)

def render_week_activity(days=7):
    """Show activity across the week."""
    lines = []
    today = datetime.now()

    lines.append("")
    lines.append("┌" + "─" * 76 + "┐")
    lines.append("│" + " " * 30 + "📅 THIS WEEK" + " " * 34 + "│")
    lines.append("└" + "─" * 76 + "┘")
    lines.append("")

    week_data = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        day_name = day.strftime("%a")
        events = load_logs(date_str)

        # Count meaningful events
        meaningful = [e for e in events if e.get("action") in
                     ("created_file", "modified_file", "committed_code", "ran_tests", "built_project")]
        week_data.append((day_name, date_str, len(meaningful), len(events)))

    max_events = max(d[2] for d in week_data) if week_data else 1

    # Render each day
    for day_name, date_str, meaningful, total in week_data:
        bar_len = int((meaningful / max(max_events, 1)) * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)

        is_today = date_str == today.strftime("%Y-%m-%d")
        marker = "→" if is_today else " "

        lines.append(f"  {marker} {day_name} │{bar}│ {meaningful:3} actions")

    # Streak
    streak = 0
    for _, _, meaningful, _ in reversed(week_data):
        if meaningful > 0:
            streak += 1
        else:
            break

    if streak > 1:
        lines.append("")
        lines.append(f"  🔥 {streak}-day streak!")

    return "\n".join(lines)

def render_engineering_summary(events, date_str):
    """Generate the full engineering journal summary."""
    output = []

    # Header
    output.append(HEADER)

    # Date
    date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %B %d, %Y")
    output.append(f"  📆 {date_display}")
    output.append(f"  🕐 Generated at {datetime.now().strftime('%H:%M')}")

    if not events:
        output.append("")
        output.append("  ⚠️  No engineering activity logged for this day.")
        output.append("")
        output.append("  Available dates:")
        for d in get_available_dates()[:5]:
            output.append(f"    • {d}")
        return "\n".join(output)

    # Analyze
    projects = analyze_events(events)

    # Day narrative
    output.append(render_day_narrative(projects, date_str))

    # Per-project summaries
    for name, data in sorted(projects.items(), key=lambda x: -len(x[1]["timeline"])):
        if data["timeline"]:  # Only show projects with activity
            output.append(render_project_summary(name, data))

    # Week view
    output.append(render_week_activity())

    # Footer
    output.append("")
    output.append("═" * 78)
    output.append("  📁 Logs: ~/Desktop/cc-config/logs/")
    output.append("  💡 Tip: Run /summary at end of day for your engineering journal")
    output.append("")

    return "\n".join(output)

# ═══════════════════════════════════════════════════════════════════════════════
# DATE RANGE SUPPORT
# ═══════════════════════════════════════════════════════════════════════════════

def parse_relative_range(relative_str):
    """Parse relative date ranges like '7d', 'this-week', 'last-month'."""
    today = datetime.now()

    if relative_str.endswith('d'):
        # Last N days
        days = int(relative_str[:-1])
        start = today - timedelta(days=days-1)
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    elif relative_str in ('this-week', 'week'):
        # This week (Mon-Sun)
        start = today - timedelta(days=today.weekday())
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    elif relative_str in ('last-week',):
        # Last week
        end = today - timedelta(days=today.weekday()+1)
        start = end - timedelta(days=6)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    elif relative_str in ('this-month', 'month'):
        # This month
        start = today.replace(day=1)
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    elif relative_str in ('last-month',):
        # Last month
        first_of_month = today.replace(day=1)
        end = first_of_month - timedelta(days=1)
        start = end.replace(day=1)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    else:
        raise ValueError(f"Unknown relative range: {relative_str}")


def load_date_range(start_date, end_date):
    """Load all events in a date range."""
    all_events = []

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    current = start
    dates_loaded = []

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        events = load_logs(date_str)
        if events:
            all_events.extend(events)
            dates_loaded.append(date_str)
        current += timedelta(days=1)

    return all_events, dates_loaded


def render_range_summary(start_date, end_date):
    """Generate a summary for a date range."""
    output = []

    # Load all events in range
    all_events, dates_loaded = load_date_range(start_date, end_date)

    if not all_events:
        output.append(f"\n  ⚠️  No activity logged between {start_date} and {end_date}\n")
        return "\n".join(output)

    # Calculate span
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    days_span = (end_dt - start_dt).days + 1

    # Format header
    start_display = start_dt.strftime("%b %d")
    end_display = end_dt.strftime("%b %d, %Y")

    output.append("")
    output.append("┌" + "─" * 76 + "┐")
    title = f"📊 WORK SUMMARY: {start_display.upper()} → {end_display.upper()} ({days_span} DAYS)"
    padding = (78 - len(title)) // 2
    output.append("│" + " " * padding + title + " " * (78 - padding - len(title)) + "│")
    output.append("├" + "─" * 76 + "┤")

    # Analyze all events
    projects = analyze_events(all_events)

    # Overall stats
    total_projects = len(projects)
    days_active = len(dates_loaded)
    total_sessions = len(all_events)

    stats = f"│  {total_projects} project(s)  •  {days_active} days active  •  {total_sessions} sessions"
    stats = stats + " " * (77 - len(stats)) + "│"
    output.append(stats)
    output.append("└" + "─" * 76 + "┘")

    # Per-project summaries
    for name, data in sorted(projects.items(), key=lambda x: -len(x[1]["timeline"])):
        if not data["timeline"]:
            continue

        output.append("")
        output.append(f"  📁 {name:<60} [{len(set([t[:10] for t in data['timeline']]))} days active]")

        # Show work done (adapt to backfilled vs detailed)
        if data.get("has_backfill"):
            prompts = data["prompts"]
            if prompts and len(prompts) <= 5:
                for p in prompts[:5]:
                    prompt_text = p["prompt"][:60] + "..." if len(p["prompt"]) > 60 else p["prompt"]
                    if prompt_text:
                        output.append(f"      📝 {prompt_text}")
            elif prompts:
                output.append(f"      📝 {len(prompts)} sessions")
        else:
            # Detailed stats
            if data["files_created"]:
                output.append(f"      🏗️  Created {len(data['files_created'])} files")
            if data["files_modified"]:
                unique_modified = len(set(f["file"] for f in data["files_modified"]))
                output.append(f"      ✏️  Modified {unique_modified} files")
            if data["commands"]:
                # Group commands by type
                cmd_types = defaultdict(int)
                for c in data["commands"]:
                    cmd_types[c["action"]] += 1

                for action, count in cmd_types.items():
                    icon = {"ran_tests": "🧪", "built_project": "🔨", "committed_code": "💾"}.get(action, "▶️")
                    label = action.replace("_", " ").title()
                    output.append(f"      {icon} {label} ({count}x)")

    # Daily breakdown
    if days_active > 1:
        output.append("")
        output.append("  Daily breakdown:")

        # Count events per date
        events_by_date = defaultdict(int)
        for e in all_events:
            # Extract date from various timestamp formats
            ts = e.get("ts", "")
            if ts and len(ts) >= 5:  # HH:MM format
                # We need to track which log file this came from
                # For now, count all events
                pass

        # Load each date individually for accurate counts
        for date_str in dates_loaded[:10]:  # Show max 10 days
            events = load_logs(date_str)
            count = len(events)

            # Format date
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            date_display = dt.strftime("%b %d")

            # Activity bar
            max_count = max(len(load_logs(d)) for d in dates_loaded)
            bar_len = int((count / max(max_count, 1)) * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)

            output.append(f"    {date_display} │{bar}│ {count:3} sessions")

        if len(dates_loaded) > 10:
            output.append(f"    ... and {len(dates_loaded) - 10} more days")

    return "\n".join(output)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def render_compact_summary(events, date_str):
    """Generate a compact quick-glance summary."""
    output = []

    date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a %b %d")

    if not events:
        output.append(f"📊 {date_display} — No activity logged")
        return "\n".join(output)

    projects = analyze_events(events)

    total_created = sum(len(p["files_created"]) for p in projects.values())
    total_modified = sum(len(p["files_modified"]) for p in projects.values())
    total_completed = sum(len(set(p["tasks_completed"])) for p in projects.values())

    # Header line
    output.append(f"📊 {date_display} — {len(projects)} project(s) | {total_created} created | {total_modified} modified | {total_completed} tasks")
    output.append("")

    # Per-project one-liners
    for name, data in sorted(projects.items(), key=lambda x: -len(x[1]["timeline"])):
        if not data["timeline"]:
            continue

        start = min(data["timeline"])
        end = max(data["timeline"])

        # Build a brief description
        parts = []
        if data["files_created"]:
            parts.append(f"{len(data['files_created'])} files")
        if data["tasks_completed"]:
            parts.append(f"{len(set(data['tasks_completed']))} tasks")
        if data["commands"]:
            cmd_types = set(c["action"] for c in data["commands"])
            if "ran_tests" in cmd_types:
                parts.append("tests")
            if "built_project" in cmd_types:
                parts.append("build")

        desc = ", ".join(parts) if parts else "activity"
        output.append(f"  📁 {name} [{start}→{end}]: {desc}")

    return "\n".join(output)


def render_date_picker():
    """Show an interactive date picker with compact summaries."""
    dates = get_available_dates()

    if not dates:
        print("\n  ⚠️  No logs found. Start coding with Claude Code to generate activity logs!\n")
        return None

    print("\n  📅 Available Engineering Journals\n")
    print("  ─" * 38)

    for i, date_str in enumerate(dates[:15], 1):
        events = load_logs(date_str)
        if not events:
            continue

        projects = analyze_events(events)
        total_created = sum(len(p["files_created"]) for p in projects.values())
        total_modified = sum(len(p["files_modified"]) for p in projects.values())
        total_tasks = sum(len(set(p["tasks_completed"])) for p in projects.values())

        date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a %b %d")
        project_names = ", ".join(list(projects.keys())[:3])
        if len(projects) > 3:
            project_names += f" +{len(projects)-3}"

        # Highlight today
        is_today = date_str == datetime.now().strftime("%Y-%m-%d")
        marker = "→" if is_today else " "
        today_label = " (today)" if is_today else ""

        print(f"  {marker} [{i:2}] {date_display}{today_label}")
        print(f"        {len(projects)} project(s) | {total_created} created | {total_modified} modified | {total_tasks} tasks")
        print(f"        {project_names}")
        print()

    if len(dates) > 15:
        print(f"       ... and {len(dates) - 15} more dates (use --list to see all)\n")

    print("  ─" * 38)
    print("  Enter number to expand, or press Enter for today: ", end="")

    try:
        choice = input().strip()
        if not choice:
            return dates[0] if dates else None

        idx = int(choice) - 1
        if 0 <= idx < min(len(dates), 15):
            return dates[idx]
        else:
            print("  Invalid selection.")
            return None
    except (ValueError, EOFError, KeyboardInterrupt):
        print()
        return None


def main():
    parser = argparse.ArgumentParser(description="Claude Code Engineering Journal")
    parser.add_argument("--date", "-d", help="Date to summarize (YYYY-MM-DD)")
    parser.add_argument("--list", "-l", action="store_true", help="List available dates")
    parser.add_argument("--save", "-s", action="store_true", help="Save summary to file")
    parser.add_argument("--raw", "-r", action="store_true", help="Show raw log data")
    parser.add_argument("--compact", "-c", action="store_true", help="Compact quick-glance view")
    parser.add_argument("--pick", "-p", action="store_true", help="Interactive date picker")
    parser.add_argument("--pick-list", action="store_true", help="Show date picker list (non-interactive)")
    parser.add_argument("--range", nargs=2, metavar=("START", "END"), help="Date range (YYYY-MM-DD YYYY-MM-DD)")
    parser.add_argument("--range-relative", help="Relative range (7d, this-week, last-month)")

    args = parser.parse_args()

    # Auto-sync native logs before any operation
    auto_sync_native_logs()

    if args.list:
        dates = get_available_dates()
        print("\n  📅 Available engineering journals:\n")
        for d in dates:
            events = load_logs(d)
            projects = len(set(e.get("project", "") for e in events if e.get("project")))
            print(f"    {d}: {len(events)} events across {projects} project(s)")
        print()
        return

    # Interactive date picker
    if args.pick:
        date_str = render_date_picker()
        if not date_str:
            return
        events = load_logs(date_str)
        if args.compact:
            print()
            print(render_compact_summary(events, date_str))
        else:
            print(render_engineering_summary(events, date_str))
        return

    # Non-interactive date picker list (for slash commands)
    if args.pick_list:
        dates = get_available_dates()
        if not dates:
            print("\n  No logs found yet.\n")
            return
        print("\n  📅 Available Engineering Journals\n")
        for i, date_str in enumerate(dates[:15], 1):
            events = load_logs(date_str)
            if not events:
                continue
            projects = analyze_events(events)
            total_created = sum(len(p["files_created"]) for p in projects.values())
            total_modified = sum(len(p["files_modified"]) for p in projects.values())
            total_tasks = sum(len(set(p["tasks_completed"])) for p in projects.values())
            date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a %b %d")
            project_names = ", ".join(list(projects.keys())[:3])
            if len(projects) > 3:
                project_names += f" +{len(projects)-3}"
            is_today = date_str == datetime.now().strftime("%Y-%m-%d")
            marker = "→" if is_today else " "
            today_label = " (today)" if is_today else ""
            print(f"  {marker} [{i:2}] {date_str} — {date_display}{today_label}")
            print(f"        {len(projects)} project(s) | {total_created} created | {total_modified} modified | {total_tasks} tasks")
            print(f"        {project_names}")
            print()
        if len(dates) > 15:
            print(f"       ... and {len(dates) - 15} more dates\n")
        return

    # Date range summary
    if args.range or args.range_relative:
        if args.range_relative:
            try:
                start_date, end_date = parse_relative_range(args.range_relative)
            except ValueError as e:
                print(f"\n  ❌ Error: {e}\n")
                return
        else:
            start_date, end_date = args.range

        print(render_range_summary(start_date, end_date))
        print(render_usage_stats(start_date=start_date, end_date=end_date))
        return

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    events = load_logs(date_str)

    if args.raw:
        for e in events[-20:]:
            print(json.dumps(e, indent=2))
        return

    if args.compact:
        print(render_compact_summary(events, date_str))
        print(render_usage_stats(date_str))
        return

    summary = render_engineering_summary(events, date_str)
    print(summary)
    print(render_usage_stats(date_str))

    if args.save:
        SUMMARIES_DIR.mkdir(exist_ok=True)
        save_path = SUMMARIES_DIR / f"{date_str}-journal.txt"
        with open(save_path, "w") as f:
            f.write(summary)
        print(f"  💾 Saved to: {save_path}")

if __name__ == "__main__":
    main()
