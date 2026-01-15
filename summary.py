#!/usr/bin/env python3
"""
Claude Code Engineering Journal
Generates narrative summaries of what you actually built.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import argparse

CONFIG_DIR = Path.home() / "Desktop" / "cc-config"
LOGS_DIR = CONFIG_DIR / "logs"
SUMMARIES_DIR = CONFIG_DIR / "summaries"

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
        "timeline": [],
        "categories": set(),
    })

    for e in events:
        project = e.get("project", "unknown")
        action = e.get("action", "")
        ts = e.get("ts", "")

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

    lines.append(f"")
    lines.append(f"┌{'─' * 76}┐")
    lines.append(f"│  📁 {name:<50} [{time_span:>17}] │")
    lines.append(f"└{'─' * 76}┘")

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


def main():
    parser = argparse.ArgumentParser(description="Claude Code Engineering Journal")
    parser.add_argument("--date", "-d", help="Date to summarize (YYYY-MM-DD)")
    parser.add_argument("--list", "-l", action="store_true", help="List available dates")
    parser.add_argument("--save", "-s", action="store_true", help="Save summary to file")
    parser.add_argument("--raw", "-r", action="store_true", help="Show raw log data")
    parser.add_argument("--compact", "-c", action="store_true", help="Compact quick-glance view")

    args = parser.parse_args()

    if args.list:
        dates = get_available_dates()
        print("\n  📅 Available engineering journals:\n")
        for d in dates:
            events = load_logs(d)
            projects = len(set(e.get("project", "") for e in events if e.get("project")))
            print(f"    {d}: {len(events)} events across {projects} project(s)")
        print()
        return

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    events = load_logs(date_str)

    if args.raw:
        for e in events[-20:]:
            print(json.dumps(e, indent=2))
        return

    if args.compact:
        print(render_compact_summary(events, date_str))
        return

    summary = render_engineering_summary(events, date_str)
    print(summary)

    if args.save:
        SUMMARIES_DIR.mkdir(exist_ok=True)
        save_path = SUMMARIES_DIR / f"{date_str}-journal.txt"
        with open(save_path, "w") as f:
            f.write(summary)
        print(f"  💾 Saved to: {save_path}")

if __name__ == "__main__":
    main()
