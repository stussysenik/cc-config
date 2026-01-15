#!/usr/bin/env python3
"""
Parse Claude Code history.jsonl to generate historical activity summaries.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import sys

HISTORY_FILE = Path.home() / ".claude" / "history.jsonl"

def load_history():
    """Load all history entries."""
    entries = []
    with open(HISTORY_FILE) as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    if "timestamp" in entry:
                        entries.append(entry)
                except:
                    pass
    return entries

def extract_project_name(path):
    """Extract meaningful project name."""
    if not path:
        return "unknown"
    parts = Path(path).parts
    skip = {'Users', 'home', 'Desktop', 'Documents', 'Projects', 'Code', 'dev', 's3nik', 'dev playground'}
    meaningful = [p for p in parts if p not in skip and not p.startswith('.')]
    return meaningful[-1] if meaningful else Path(path).name

def analyze_prompt(text):
    """Categorize what kind of work a prompt represents."""
    text_lower = text.lower() if text else ""

    if any(x in text_lower for x in ['fix', 'bug', 'error', 'issue', 'broken', 'not working']):
        return "debugging"
    elif any(x in text_lower for x in ['add', 'create', 'build', 'implement', 'new feature']):
        return "building"
    elif any(x in text_lower for x in ['refactor', 'clean', 'improve', 'optimize']):
        return "refactoring"
    elif any(x in text_lower for x in ['test', 'spec', 'coverage']):
        return "testing"
    elif any(x in text_lower for x in ['review', 'explain', 'understand', 'how does']):
        return "learning"
    elif any(x in text_lower for x in ['deploy', 'release', 'publish']):
        return "deploying"
    elif '/clear' in text_lower or len(text_lower) < 10:
        return "command"
    else:
        return "coding"

def group_by_date(entries):
    """Group entries by date."""
    by_date = defaultdict(list)
    for e in entries:
        ts = e.get("timestamp", 0)
        if ts:
            # Timestamp is in milliseconds
            dt = datetime.fromtimestamp(ts / 1000)
            date_str = dt.strftime("%Y-%m-%d")
            by_date[date_str].append({
                "time": dt.strftime("%H:%M"),
                "project": extract_project_name(e.get("project", "")),
                "prompt": e.get("display", "")[:200],
                "category": analyze_prompt(e.get("display", "")),
            })
    return dict(by_date)

def render_day(date_str, entries):
    """Render a single day's summary."""
    lines = []

    # Parse date for display
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_display = dt.strftime("%A, %B %d")
    except:
        date_display = date_str

    # Group by project
    projects = defaultdict(lambda: {"prompts": [], "categories": set(), "times": []})
    for e in entries:
        if e["category"] != "command":  # Skip /clear etc
            proj = e["project"]
            projects[proj]["prompts"].append(e["prompt"])
            projects[proj]["categories"].add(e["category"])
            projects[proj]["times"].append(e["time"])

    if not projects:
        return None

    # Calculate stats
    total_prompts = sum(len(p["prompts"]) for p in projects.values())
    all_categories = set()
    for p in projects.values():
        all_categories.update(p["categories"])

    # Header
    lines.append("")
    lines.append(f"┌{'─' * 76}┐")
    lines.append(f"│  📆 {date_display:<70} │")
    lines.append(f"├{'─' * 76}┤")
    lines.append(f"│  {len(projects)} project(s)  •  {total_prompts} prompts  •  {', '.join(sorted(all_categories)):<40} │")
    lines.append(f"└{'─' * 76}┘")

    # Per project
    for proj_name, data in sorted(projects.items(), key=lambda x: -len(x[1]["prompts"])):
        times = data["times"]
        time_range = f"{min(times)} → {max(times)}" if times else ""

        lines.append(f"")
        lines.append(f"  📁 {proj_name}  [{time_range}]")

        # Show category breakdown
        cats = data["categories"]
        cat_icons = {
            "building": "🏗️ Building",
            "debugging": "🔧 Debugging",
            "refactoring": "♻️ Refactoring",
            "testing": "🧪 Testing",
            "learning": "📚 Learning",
            "deploying": "🚀 Deploying",
            "coding": "💻 Coding",
        }
        cat_display = [cat_icons.get(c, c) for c in cats]
        lines.append(f"     {' • '.join(cat_display)}")

        # Show sample prompts (first 3, truncated)
        prompts = data["prompts"]
        lines.append(f"     Prompts: {len(prompts)}")
        for p in prompts[:3]:
            # Clean and truncate
            clean = p.replace('\n', ' ').strip()[:60]
            if clean and len(clean) > 5:
                lines.append(f"       • {clean}...")

    return "\n".join(lines)

def render_week_chart(by_date, days=7):
    """Render week activity chart."""
    lines = []
    today = datetime.now()

    lines.append("")
    lines.append("┌" + "─" * 76 + "┐")
    lines.append("│" + " " * 25 + "📊 ACTIVITY LAST 7 DAYS" + " " * 28 + "│")
    lines.append("└" + "─" * 76 + "┘")
    lines.append("")

    week_data = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        day_name = day.strftime("%a")
        entries = by_date.get(date_str, [])
        meaningful = [e for e in entries if e.get("category") != "command"]
        week_data.append((day_name, date_str, len(meaningful)))

    max_count = max(d[2] for d in week_data) if week_data else 1

    for day_name, date_str, count in week_data:
        bar_len = int((count / max(max_count, 1)) * 45)
        bar = "█" * bar_len + "░" * (45 - bar_len)
        is_today = date_str == today.strftime("%Y-%m-%d")
        marker = "→" if is_today else " "
        lines.append(f"  {marker} {day_name} │{bar}│ {count:3}")

    return "\n".join(lines)

def render_month_chart(by_date):
    """Render month activity chart."""
    lines = []
    today = datetime.now()

    lines.append("")
    lines.append("┌" + "─" * 76 + "┐")
    lines.append("│" + " " * 25 + "📅 ACTIVITY THIS MONTH" + " " * 29 + "│")
    lines.append("└" + "─" * 76 + "┘")
    lines.append("")

    # Get all days this month
    first_day = today.replace(day=1)
    month_data = []

    current = first_day
    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        entries = by_date.get(date_str, [])
        meaningful = [e for e in entries if e.get("category") != "command"]
        if meaningful:
            month_data.append((current.strftime("%d"), date_str, len(meaningful)))
        current += timedelta(days=1)

    if not month_data:
        lines.append("  No activity this month yet.")
        return "\n".join(lines)

    # Calendar-style grid
    max_count = max(d[2] for d in month_data)

    # Show days with activity
    lines.append(f"  Days with activity: {len(month_data)}")
    lines.append(f"  Total prompts: {sum(d[2] for d in month_data)}")
    lines.append("")

    # Mini chart per day
    for day_num, date_str, count in month_data:
        intensity = int((count / max(max_count, 1)) * 4)
        block = ["░", "▒", "▓", "█", "█"][intensity]
        lines.append(f"    {date_str}: {block * min(count, 30)} ({count})")

    return "\n".join(lines)

def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗  ██╗██╗███████╗████████╗ ██████╗ ██████╗ ██╗   ██╗                      ║
║   ██║  ██║██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝                      ║
║   ███████║██║███████╗   ██║   ██║   ██║██████╔╝ ╚████╔╝                       ║
║   ██╔══██║██║╚════██║   ██║   ██║   ██║██╔══██╗  ╚██╔╝                        ║
║   ██║  ██║██║███████║   ██║   ╚██████╔╝██║  ██║   ██║                         ║
║   ╚═╝  ╚═╝╚═╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝                         ║
║                                                                               ║
║                    CLAUDE CODE ENGINEERING HISTORY                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")

    entries = load_history()
    print(f"  📊 Loaded {len(entries)} history entries")

    by_date = group_by_date(entries)
    dates = sorted(by_date.keys())

    if dates:
        print(f"  📆 Date range: {dates[0]} → {dates[-1]}")
        print(f"  📁 Days with activity: {len(dates)}")

    # Week chart
    print(render_week_chart(by_date))

    # Month chart
    print(render_month_chart(by_date))

    # Per-day breakdown for last 7 days
    print("")
    print("═" * 78)
    print("                         DAILY BREAKDOWN (LAST 7 DAYS)")
    print("═" * 78)

    today = datetime.now()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        if date_str in by_date:
            day_summary = render_day(date_str, by_date[date_str])
            if day_summary:
                print(day_summary)

    # All time stats
    print("")
    print("═" * 78)
    print("                              ALL TIME STATS")
    print("═" * 78)

    all_projects = set()
    all_categories = defaultdict(int)
    for date_str, day_entries in by_date.items():
        for e in day_entries:
            if e["category"] != "command":
                all_projects.add(e["project"])
                all_categories[e["category"]] += 1

    print(f"""
  📁 Total projects worked on: {len(all_projects)}
  📝 Total meaningful prompts: {sum(all_categories.values())}

  Work breakdown:
""")

    cat_icons = {
        "building": "🏗️",
        "debugging": "🔧",
        "refactoring": "♻️",
        "testing": "🧪",
        "learning": "📚",
        "deploying": "🚀",
        "coding": "💻",
    }

    total = sum(all_categories.values())
    for cat, count in sorted(all_categories.items(), key=lambda x: -x[1]):
        icon = cat_icons.get(cat, "•")
        pct = int((count / total) * 100) if total > 0 else 0
        bar = "█" * (pct // 2) + "░" * (50 - pct // 2)
        print(f"    {icon} {cat:12} {bar} {pct:3}% ({count})")

    print(f"""
  Projects:
""")
    for proj in sorted(all_projects)[:15]:
        print(f"    • {proj}")
    if len(all_projects) > 15:
        print(f"    ... and {len(all_projects) - 15} more")

    print("")

if __name__ == "__main__":
    main()
