#!/usr/bin/env python3
"""
Backfills cc-config daily logs from Claude Code history.jsonl
Creates synthetic activity logs for dates without detailed tracking.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Paths
HISTORY_FILE = Path.home() / ".claude" / "history.jsonl"
LOGS_DIR = Path.home() / "Desktop" / "cc-config" / "logs"


def parse_history():
    """Parse history.jsonl and group by date."""
    if not HISTORY_FILE.exists():
        print(f"❌ History file not found: {HISTORY_FILE}")
        return {}

    print(f"📚 Reading history from {HISTORY_FILE}")

    entries_by_date = defaultdict(list)
    total_entries = 0

    with open(HISTORY_FILE) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                timestamp = entry.get("timestamp")
                if not timestamp:
                    continue

                # Convert timestamp (milliseconds) to datetime
                dt = datetime.fromtimestamp(timestamp / 1000)
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M")

                # Extract project from path
                project_path = entry.get("project", "")
                project_name = Path(project_path).name if project_path else "unknown"

                # Get prompt display text
                prompt_text = entry.get("display", "")

                # Create synthetic log entry
                log_entry = {
                    "ts": time_str,
                    "source": "backfill",
                    "action": "user_prompt",
                    "project": project_name,
                    "cwd": project_path,
                    "prompt": prompt_text[:200],  # Truncate long prompts
                    "description": "Session activity"
                }

                entries_by_date[date_str].append(log_entry)
                total_entries += 1

            except Exception as e:
                print(f"⚠️  Skipping malformed entry: {e}")
                continue

    print(f"✅ Parsed {total_entries} entries across {len(entries_by_date)} dates")
    return entries_by_date


def write_daily_logs(entries_by_date, force=False):
    """Write daily log files, skipping dates that already exist."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    new_files = 0
    skipped_files = 0

    for date_str, entries in sorted(entries_by_date.items()):
        log_file = LOGS_DIR / f"{date_str}.jsonl"

        # Skip if file already exists (preserve detailed logs)
        if log_file.exists() and not force:
            skipped_files += 1
            continue

        # Write entries to daily log file
        with open(log_file, "w") as f:
            for entry in sorted(entries, key=lambda e: e["ts"]):
                f.write(json.dumps(entry) + "\n")

        new_files += 1
        print(f"  📝 Created {date_str}.jsonl ({len(entries)} entries)")

    print(f"\n✅ Created {new_files} new log files")
    if skipped_files > 0:
        print(f"⏭️  Skipped {skipped_files} existing files (preserving detailed logs)")


def main():
    print("\n🔄 Backfilling cc-config logs from Claude Code history\n")
    print("=" * 60)

    # Parse history
    entries_by_date = parse_history()

    if not entries_by_date:
        print("\n❌ No history entries found to backfill")
        return 1

    # Show date range
    all_dates = sorted(entries_by_date.keys())
    print(f"\n📅 Date range: {all_dates[0]} → {all_dates[-1]}")
    print(f"   Total days: {len(all_dates)}")

    # Write logs
    print(f"\n💾 Writing daily log files to {LOGS_DIR}\n")
    write_daily_logs(entries_by_date)

    print("\n" + "=" * 60)
    print("✅ Backfill complete!")
    print(f"\n💡 Tip: Run /summary-pick to browse all {len(all_dates)} days of history\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
