#!/usr/bin/env python3
"""
Complete Claude Code history - all days with activity.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

HISTORY_FILE = Path.home() / ".claude" / "history.jsonl"

def load_history():
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
    if not path:
        return "unknown"
    parts = Path(path).parts
    skip = {'Users', 'home', 'Desktop', 'Documents', 'Projects', 'Code', 'dev', 's3nik', 'dev playground'}
    meaningful = [p for p in parts if p not in skip and not p.startswith('.')]
    return meaningful[-1] if meaningful else Path(path).name

def analyze_prompt(text):
    text_lower = text.lower() if text else ""
    if any(x in text_lower for x in ['fix', 'bug', 'error', 'issue', 'broken', 'not working']):
        return "🔧 debug"
    elif any(x in text_lower for x in ['add', 'create', 'build', 'implement', 'new feature']):
        return "🏗️ build"
    elif any(x in text_lower for x in ['refactor', 'clean', 'improve', 'optimize']):
        return "♻️ refactor"
    elif any(x in text_lower for x in ['test', 'spec', 'coverage']):
        return "🧪 test"
    elif any(x in text_lower for x in ['review', 'explain', 'understand', 'how does']):
        return "📚 learn"
    elif '/clear' in text_lower or len(text_lower) < 10:
        return None
    else:
        return "💻 code"

def main():
    entries = load_history()

    # Group by date
    by_date = defaultdict(lambda: {"projects": defaultdict(list), "count": 0})

    for e in entries:
        ts = e.get("timestamp", 0)
        if ts:
            dt = datetime.fromtimestamp(ts / 1000)
            date_str = dt.strftime("%Y-%m-%d")
            project = extract_project_name(e.get("project", ""))
            prompt = e.get("display", "")
            category = analyze_prompt(prompt)

            if category:  # Skip /clear etc
                by_date[date_str]["projects"][project].append({
                    "time": dt.strftime("%H:%M"),
                    "prompt": prompt[:80],
                    "category": category,
                })
                by_date[date_str]["count"] += 1

    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║    ██████╗ ██████╗ ███╗   ███╗██████╗ ██╗     ███████╗████████╗███████╗       ║
║   ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██║     ██╔════╝╚══██╔══╝██╔════╝       ║
║   ██║     ██║   ██║██╔████╔██║██████╔╝██║     █████╗     ██║   █████╗         ║
║   ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██║     ██╔══╝     ██║   ██╔══╝         ║
║   ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ███████╗███████╗   ██║   ███████╗       ║
║    ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝   ╚═╝   ╚══════╝       ║
║                                                                               ║
║                    CLAUDE CODE HISTORY - ALL TIME                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")

    # Sort dates
    sorted_dates = sorted(by_date.keys())

    if not sorted_dates:
        print("  No activity found.")
        return

    print(f"  📆 First activity: {sorted_dates[0]}")
    print(f"  📆 Last activity: {sorted_dates[-1]}")
    print(f"  📊 Total days: {len(sorted_dates)}")
    print(f"  📝 Total prompts: {sum(d['count'] for d in by_date.values())}")
    print()

    # Month grouping
    by_month = defaultdict(list)
    for date_str in sorted_dates:
        month = date_str[:7]
        by_month[month].append(date_str)

    for month in sorted(by_month.keys()):
        month_dates = by_month[month]
        month_prompts = sum(by_date[d]["count"] for d in month_dates)

        # Parse month for display
        try:
            month_dt = datetime.strptime(month, "%Y-%m")
            month_display = month_dt.strftime("%B %Y")
        except:
            month_display = month

        print()
        print(f"{'═' * 78}")
        print(f"  📅 {month_display}")
        print(f"     {len(month_dates)} days active • {month_prompts} prompts")
        print(f"{'═' * 78}")

        for date_str in month_dates:
            day_data = by_date[date_str]

            # Parse for day name
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                day_display = dt.strftime("%a %d")
            except:
                day_display = date_str

            # Projects for this day
            projects = day_data["projects"]

            # Activity bar
            count = day_data["count"]
            bar_len = min(count, 30)
            bar = "█" * bar_len

            print()
            print(f"  ┌{'─' * 74}┐")
            print(f"  │  {day_display}  {bar:<30}  {count:>3} prompts{' ' * 24}│")
            print(f"  └{'─' * 74}┘")

            for proj_name, proj_entries in sorted(projects.items(), key=lambda x: -len(x[1])):
                times = [e["time"] for e in proj_entries]
                categories = set(e["category"] for e in proj_entries)

                print(f"      📁 {proj_name}  [{min(times)} → {max(times)}]")
                print(f"         {' '.join(categories)}  ({len(proj_entries)} prompts)")

                # Sample prompts
                for entry in proj_entries[:2]:
                    prompt = entry["prompt"].replace('\n', ' ').strip()[:55]
                    if len(prompt) > 5:
                        print(f"           • {prompt}...")

    print()
    print("═" * 78)
    print("  📁 Logs stored at: ~/Desktop/cc-config/")
    print("  💡 Run /summary for today's engineering journal")
    print()

if __name__ == "__main__":
    main()
