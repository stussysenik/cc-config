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
        # Narrative fields
        "user_intents": [],
        "plans": [],
        "completion_count": 0,
        "branches": set(),
        "sessions": set(),
        "web_research_count": 0,
        "research_count": 0,
    })

    for e in events:
        project = e.get("project", "unknown")
        action = e.get("action", "")
        ts = e.get("ts", "")
        source = e.get("source", "")

        # Track session and branch
        if e.get("session"):
            projects[project]["sessions"].add(e["session"])
        if e.get("branch") and e["branch"] != "HEAD":
            projects[project]["branches"].add(e["branch"])

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

        # User prompts — extract real intents
        if action == "user_prompt":
            prompt = e.get("prompt", "")
            # Filter out system/command noise
            noise = ['<command-', '<local-command-', '<task-notification>',
                     'This session is being continued', 'Caveat: The messages']
            if not any(skip in prompt for skip in noise):
                projects[project]["user_intents"].append({
                    "prompt": prompt,
                    "time": ts,
                })
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

        # Task planning — from both old TodoWrite and new TaskCreate
        elif action == "planned_tasks":
            tasks = e.get("tasks", [])
            completed = e.get("completed", [])
            projects[project]["tasks_planned"].extend(tasks)
            projects[project]["tasks_completed"].extend(completed)
        elif action == "task_planned":
            task = e.get("task", "")
            if task:
                projects[project]["plans"].append(task)

        # Task completion — from TaskUpdate
        elif action == "task_completed":
            projects[project]["completion_count"] += 1

        # Commands — from both old activity-logger and new sync
        elif action in ("ran_tests", "built_project", "installed_deps", "committed_code",
                       "git_operation", "infra_operation", "ran_command", "command"):
            projects[project]["commands"].append({
                "action": action,
                "command": e.get("command", ""),
                "description": e.get("description", ""),
                "category": e.get("category", ""),
                "time": ts,
            })
            if e.get("category"):
                projects[project]["categories"].add(e["category"])

        # Research — from both old and new formats
        elif action == "researched":
            projects[project]["research"].append({
                "query": e.get("query", ""),
                "time": ts,
            })
        elif action == "research":
            projects[project]["research_count"] += 1
        elif action == "web_research":
            projects[project]["web_research_count"] += 1

        # Delegated work — from both old and new formats
        elif action == "delegated_task":
            projects[project]["delegated"].append({
                "type": e.get("task_type", ""),
                "description": e.get("task_description", ""),
                "prompt": e.get("task_prompt", ""),
                "time": ts,
            })
        elif action == "delegated":
            projects[project]["delegated"].append({
                "type": e.get("agent", ""),
                "description": e.get("task", ""),
                "prompt": e.get("task", ""),
                "time": ts,
            })

        # Track timeline
        if ts:
            projects[project]["timeline"].append(ts)

    return dict(projects)


# ═══════════════════════════════════════════════════════════════════════════════
# NARRATIVE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def extract_intent(user_intents):
    """Extract the first real user prompt as the session's intent."""
    for intent in user_intents:
        text = intent.get("prompt", "").strip()
        if len(text) > 15:  # Skip very short prompts
            # Clean up: collapse whitespace
            text = " ".join(text.split())
            # Strip file paths at the start to get to the human intent
            if text.startswith("~/") or text.startswith("/"):
                # Try multiple strategies to find the meaningful part
                best = text
                for sep in [' use ', ' apply ', ' and use ', ' is the ', ' - ']:
                    idx = text.lower().find(sep)
                    if 0 < idx < 80:
                        candidate = text[idx + len(sep):]
                        if len(candidate) > 20:
                            best = candidate
                            break
                text = best
                # If still starts with path after cleanup, skip to next intent
                if text.startswith("~/") or text.startswith("/"):
                    continue
            if len(text) > 120:
                text = text[:117] + "..."
            return text
    return None


def extract_arc_description(data):
    """Extract a short, meaningful description for the project arc.
    Prioritizes what was built over raw prompts."""

    # Primary: describe what was delivered (interesting groups first)
    deliverables = group_deliverables(data.get("files_created", []))
    if deliverables:
        # Push generic groups to the end
        generic = {'Documentation', 'Configuration', 'Code'}
        groups = [g for g in deliverables if g not in generic] + \
                 [g for g in deliverables if g in generic]
        if len(groups) == 1:
            desc = groups[0]
        elif len(groups) == 2:
            desc = f"{groups[0]} + {groups[1]}"
        else:
            desc = f"{groups[0]} + {groups[1]} + {len(groups)-2} more"
        if len(desc) > 55:
            desc = desc[:52] + "..."
        return desc

    # Secondary: describe what was modified
    files_modified = data.get("files_modified", [])
    if files_modified:
        unique = list(dict.fromkeys(f["file"] for f in files_modified))
        if len(unique) == 1:
            return f"refined {unique[0]}"
        return f"refined {len(unique)} files"

    # Tertiary: use plans
    if data.get("plans"):
        plan = data["plans"][0]
        if len(plan) > 50:
            return plan[:50].rsplit(" ", 1)[0] + "..."
        return plan

    return "activity"


def get_duration_str(timeline):
    """Convert timeline to human-friendly duration string."""
    if not timeline or len(timeline) < 2:
        return None
    times = sorted(timeline)
    start, end = times[0], times[-1]
    try:
        # Handle HH:MM and HH:MM:SS formats
        start_parts = start.split(":")
        end_parts = end.split(":")
        start_mins = int(start_parts[0]) * 60 + int(start_parts[1])
        end_mins = int(end_parts[0]) * 60 + int(end_parts[1])
        total = end_mins - start_mins
        if total < 0:
            total += 24 * 60
        if total < 60:
            return f"{total}m"
        hours = total // 60
        mins = total % 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"
    except:
        return None


def get_time_range_short(timeline):
    """Get start → end time in short format."""
    if not timeline:
        return "no activity", "", ""
    times = sorted(timeline)
    start, end = times[0], times[-1]
    # Truncate to HH:MM
    return f"{start[:5]} → {end[:5]}", start[:5], end[:5]


def group_deliverables(files_created):
    """Group created files into meaningful deliverables by purpose."""
    groups = defaultdict(list)

    # Skip temp/noise files
    skip_patterns = ['.tmp.', 'package.tmp', '.bak', '.keep']

    for f in files_created:
        path = f.get("path", "")
        filename = f.get("file", "")
        category = f.get("category", "")

        if not filename:
            continue
        if any(s in filename.lower() for s in skip_patterns):
            continue

        # Group by patterns in path and filename
        path_lower = path.lower()

        if '.storybook' in path_lower:
            groups["Storybook setup"].append(filename)
        elif '__tests__' in path_lower or '__test__' in path_lower:
            groups["Test suites"].append(filename)
        elif '__stories__' in path_lower or filename.endswith('.stories.js'):
            groups["Component stories"].append(filename)
        elif '/openspec/' in path_lower:
            groups["OpenSpec artifacts"].append(filename)
        elif '/services/' in path_lower:
            parts = path.split('/')
            try:
                idx = [p.lower() for p in parts].index('services')
                svc = parts[idx + 1] if idx + 1 < len(parts) else "service"
                groups[f"Service: {svc}"].append(filename)
            except ValueError:
                groups["Services"].append(filename)
        elif '/docs/' in path_lower:
            groups["Documentation"].append(filename)
        elif '/composables/' in path_lower:
            groups["Frontend composables"].append(filename)
        elif '/api/' in path_lower and category in ('route', 'code', 'test'):
            groups["API layer"].append(filename)
        elif filename.endswith('.RfxChain'):
            groups["FX Chain presets"].append(filename.replace('.RfxChain', ''))
        elif filename.endswith('.RTrackTemplate'):
            groups["Track templates"].append(filename.replace('.RTrackTemplate', ''))
        elif filename.endswith('.RPP'):
            groups["Session templates"].append(filename)
        elif filename.endswith('.ini'):
            groups["Configuration"].append(filename)
        elif filename == '.env.local':
            groups["Configuration"].append(filename)
        elif category == 'test' and not filename.endswith('.md'):
            groups["Test suites"].append(filename)
        elif category == 'config':
            groups["Configuration"].append(filename)
        elif category == 'component':
            groups["Components"].append(filename)
        elif category == 'docs' or filename.endswith('.md'):
            groups["Documentation"].append(filename)
        else:
            groups["Code"].append(filename)

    # Deduplicate files within groups
    return {k: list(dict.fromkeys(v)) for k, v in groups.items()}


def detect_patterns(data):
    """Detect engineering patterns worth highlighting."""
    patterns = []

    files_created = data.get("files_created", [])
    commands = data.get("commands", [])
    plans = data.get("plans", [])
    completion_count = data.get("completion_count", 0)
    research_count = data.get("research_count", 0)
    web_research_count = data.get("web_research_count", 0)
    delegated = data.get("delegated", [])

    # TDD: tests created + test commands present
    test_files = [f for f in files_created if 'spec' in f.get("file", "").lower()
                  or 'test' in f.get("file", "").lower()]
    test_commands = [c for c in commands if 'test' in c.get("command", "").lower()
                     or 'vitest' in c.get("command", "").lower()
                     or 'jest' in c.get("command", "").lower()]
    if test_files and test_commands:
        patterns.append(("test_driven", f"TDD approach — {len(test_files)} test files, verified with {len(test_commands)} test runs"))

    # Spec-driven: design/proposal doc files created (not test .spec.js files)
    spec_names = set()
    for f in files_created:
        fname = f.get("file", "").lower()
        fpath = f.get("path", "").lower()
        # Only count actual design docs, not test spec files
        is_doc = fname.endswith('.md') or '/openspec/' in fpath
        is_design = any(s in fname for s in ['spec', 'design', 'proposal', 'playbook'])
        if is_doc and is_design:
            spec_names.add(fname)
    if len(spec_names) >= 3:
        patterns.append(("spec_driven", f"Spec-driven — designed before building ({len(spec_names)} spec artifacts)"))

    # Research-heavy
    total_research = research_count + web_research_count + len(data.get("research", []))
    if total_research > 20:
        patterns.append(("research_driven", f"Research-driven — {total_research} investigations before building"))

    # Safety-conscious — must have actual safety tooling, not just specs
    safety_files = [f for f in files_created if any(s in f.get("file", "").lower()
                    for s in ['pre-commit', '.github/workflows'])]
    safety_commands = [c for c in commands if any(s in c.get("command", "").lower()
                       for s in ['detect-secrets', 'trufflehog', 'pre-commit'])]
    if safety_files or safety_commands:
        patterns.append(("safety_first", "Safety-first — secret scanning, CI pipeline, env validation"))

    # Parallel delegation
    if len(delegated) >= 3:
        agent_types = set(d.get("type", "") for d in delegated)
        patterns.append(("parallel_work", f"Parallelized work — delegated to {len(delegated)} agents ({', '.join(filter(None, agent_types))})"))

    # Full completion
    if plans and completion_count > 0:
        if completion_count >= len(plans):
            patterns.append(("all_shipped", f"All {completion_count} planned tasks shipped"))
        else:
            patterns.append(("progress", f"{completion_count}/{len(plans)} planned tasks completed"))

    return patterns

# ═══════════════════════════════════════════════════════════════════════════════
# RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def render_project_summary(name, data):
    """Render a single project's narrative summary."""
    lines = []

    # Project header with work time and branch
    timeline = data["timeline"]
    time_span, start_time, end_time = get_time_range_short(timeline)
    duration = get_duration_str(timeline)
    branches = data.get("branches", set())

    # Show backfill indicator
    source_label = " (from session history)" if data.get("has_backfill") else ""

    lines.append(f"")
    lines.append(f"┌{'─' * 76}┐")
    lines.append(f"│  📁 {name:<50} [{time_span:>17}] │")
    if branches:
        branch_str = ", ".join(branches)
        duration_str = f"⏱️  {duration}" if duration else ""
        lines.append(f"│  🌿 {branch_str:<48} {duration_str:>21} │")
    elif duration:
        lines.append(f"│  {'':54} ⏱️  {duration:>15} │")
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

    # Intent — what the user set out to do
    intent = extract_intent(data.get("user_intents", []))
    if intent:
        # Word-wrap the intent at ~60 chars for display
        words = intent.split()
        intent_lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 > 62:
                intent_lines.append(current_line)
                current_line = word
            else:
                current_line = f"{current_line} {word}" if current_line else word
        if current_line:
            intent_lines.append(current_line)
        lines.append(f"")
        lines.append(f"  💬 \"{intent_lines[0]}")
        for il in intent_lines[1:]:
            lines.append(f"      {il}")
        if len(intent_lines) > 1:
            lines[-1] += "\""
        else:
            lines[-1] += "\""

    # Deliverables — grouped by purpose, interesting work first
    files_created = data["files_created"]
    if files_created:
        deliverables = group_deliverables(files_created)
        # Reorder: interesting/unique groups first, generic last
        generic = {'Documentation', 'Configuration', 'Code'}
        sorted_groups = [(k, v) for k, v in deliverables.items() if k not in generic] + \
                        [(k, v) for k, v in deliverables.items() if k in generic]
        lines.append(f"")
        lines.append(f"  🎯 DELIVERED:")
        for group_name, files in sorted_groups:
            if len(files) == 1:
                lines.append(f"      {group_name} — {files[0]}")
            elif len(files) <= 4:
                file_list = ", ".join(files)
                lines.append(f"      {group_name} — {len(files)} files ({file_list})")
            else:
                preview = ", ".join(files[:3])
                lines.append(f"      {group_name} — {len(files)} files ({preview}, ...)")

    # Modified files — compact
    files_modified = data["files_modified"]
    if files_modified:
        unique_files = list(dict.fromkeys(f["file"] for f in files_modified))
        lines.append(f"")
        if len(unique_files) <= 6:
            file_list = ", ".join(unique_files)
            lines.append(f"  ✏️  REFINED: {file_list}")
        else:
            preview = ", ".join(unique_files[:5])
            lines.append(f"  ✏️  REFINED: {preview}")
            lines.append(f"      +{len(unique_files) - 5} more files touched")

    # Task completion — the achievement story
    plans = data.get("plans", [])
    completion_count = data.get("completion_count", 0)
    # Also check old-style tasks
    old_completed = list(set(data.get("tasks_completed", [])))
    old_planned = list(set(data.get("tasks_planned", [])))

    if plans and completion_count > 0:
        if completion_count >= len(plans):
            lines.append(f"")
            lines.append(f"  ✅ ALL {completion_count} TASKS COMPLETED:")
        else:
            lines.append(f"")
            lines.append(f"  ✅ {completion_count}/{len(plans)} TASKS COMPLETED:")
        for p in plans:
            lines.append(f"      ✓ {p}")
    elif old_completed:
        lines.append(f"")
        lines.append(f"  ✅ COMPLETED:")
        for t in old_completed[:8]:
            lines.append(f"      ✓ {t}")

    # Engineering patterns — the interesting bits
    patterns = detect_patterns(data)
    if patterns:
        lines.append(f"")
        pattern_icons = {
            "test_driven": "🧪",
            "spec_driven": "📐",
            "research_driven": "🔬",
            "safety_first": "🔒",
            "parallel_work": "⚡",
            "all_shipped": "🚀",
            "progress": "📊",
        }
        for pattern_key, description in patterns:
            if pattern_key not in ("all_shipped", "progress"):  # Skip — already shown in tasks
                icon = pattern_icons.get(pattern_key, "✨")
                lines.append(f"  {icon} {description}")

    return "\n".join(lines)

def render_day_narrative(projects, date_str):
    """Generate a narrative summary of the day — the story arc."""
    lines = []

    total_files_created = sum(len(p["files_created"]) for p in projects.values())
    total_files_modified = sum(len(p["files_modified"]) for p in projects.values())
    total_completed = sum(p.get("completion_count", 0) for p in projects.values())
    total_completed += sum(len(set(p.get("tasks_completed", []))) for p in projects.values())

    # Compute overall time span
    all_times = []
    for p in projects.values():
        all_times.extend(p["timeline"])
    overall_duration = get_duration_str(all_times) if all_times else None
    time_range, start_t, end_t = get_time_range_short(all_times)

    # Count projects with real activity
    active_projects = sum(1 for p in projects.values()
                         if p["files_created"] or p["files_modified"] or p["plans"])

    lines.append("")
    lines.append("┌" + "─" * 76 + "┐")
    lines.append("│" + " " * 29 + "☕ TODAY'S SESSION" + " " * 30 + "│")
    lines.append("├" + "─" * 76 + "┤")

    # Time and overall stats
    time_line = f"│  {time_range}"
    if overall_duration:
        time_line += f" · {overall_duration} of focused work"
    time_line += " " * (77 - len(time_line)) + "│"
    lines.append(time_line)

    stats = f"│  {active_projects} project(s) delivered · {total_files_created} files built · {total_completed} tasks completed"
    stats = stats + " " * (77 - len(stats)) + "│"
    lines.append(stats)

    lines.append("└" + "─" * 76 + "┘")

    # Story arc — timeline of projects
    sorted_projects = sorted(
        ((name, data) for name, data in projects.items()
         if data["timeline"] and (data["files_created"] or data["files_modified"]
                                  or data.get("plans") or data.get("user_intents"))),
        key=lambda x: min(x[1]["timeline"])
    )

    if sorted_projects:
        lines.append("")
        lines.append("  📖 THE ARC:")

        for name, data in sorted_projects:
            _, proj_start, _ = get_time_range_short(data["timeline"])
            desc = extract_arc_description(data)
            lines.append(f"  {proj_start}  {name} — {desc}")

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

def analyze_top_prompts(events):
    """Find the most impactful user prompts by output generated."""
    NOISE = ['<command-', '<local-command-', '<task-notification>',
             'This session is being continued', 'Caveat: The messages']

    prompts_with_impact = []
    current_prompt = None
    current_impact = {"files": 0, "tasks": 0, "commands": 0, "delegated": 0}

    # Sort events by timestamp for chronological analysis
    sorted_events = sorted(events, key=lambda e: (e.get("session", ""), e.get("ts", "")))

    for e in sorted_events:
        action = e.get("action", "")

        if action == "user_prompt":
            # Save previous prompt's impact
            if current_prompt:
                total = current_impact["files"] * 3 + current_impact["tasks"] * 5 + \
                        current_impact["commands"] + current_impact["delegated"] * 4
                if total > 0:
                    prompts_with_impact.append((current_prompt, dict(current_impact), total))

            prompt_text = e.get("prompt", "")
            if any(s in prompt_text for s in NOISE):
                current_prompt = None
                continue

            current_prompt = {
                "text": prompt_text,
                "time": e.get("ts", ""),
                "project": e.get("project", ""),
            }
            current_impact = {"files": 0, "tasks": 0, "commands": 0, "delegated": 0}

        elif current_prompt:
            if action in ("created_file", "modified_file"):
                current_impact["files"] += 1
            elif action in ("task_completed", "task_planned"):
                current_impact["tasks"] += 1
            elif action in ("command", "ran_tests", "built_project", "ran_command",
                           "git_operation", "installed_deps"):
                current_impact["commands"] += 1
            elif action in ("delegated", "delegated_task"):
                current_impact["delegated"] += 1

    # Don't forget last prompt
    if current_prompt:
        total = current_impact["files"] * 3 + current_impact["tasks"] * 5 + \
                current_impact["commands"] + current_impact["delegated"] * 4
        if total > 0:
            prompts_with_impact.append((current_prompt, dict(current_impact), total))

    # Sort by impact score
    prompts_with_impact.sort(key=lambda x: -x[2])
    return prompts_with_impact[:5]


def render_top_prompts(events):
    """Render the most impactful prompts with keyword analysis."""
    top = analyze_top_prompts(events)
    if not top:
        return ""

    lines = []
    lines.append("")
    lines.append("┌" + "─" * 76 + "┐")
    lines.append("│" + " " * 22 + "🧠 TOP PROMPTS BY IMPACT" + " " * 30 + "│")
    lines.append("└" + "─" * 76 + "┘")

    for i, (prompt, impact, score) in enumerate(top, 1):
        text = " ".join(prompt["text"].split())
        # Clean up paths for display
        if text.startswith("~/") or text.startswith("/"):
            for sep in [' use ', ' apply ', ' is the ', ' and ']:
                idx = text.lower().find(sep)
                if 0 < idx < 80:
                    text = text[idx + len(sep):]
                    break
        if len(text) > 90:
            text = text[:87] + "..."
        lines.append(f"")
        lines.append(f"  #{i}  [{prompt['time'][:5]}] {prompt['project']}")
        lines.append(f"      \"{text}\"")

        parts = []
        if impact["files"]:
            parts.append(f"{impact['files']} files")
        if impact["tasks"]:
            parts.append(f"{impact['tasks']} tasks")
        if impact["commands"]:
            parts.append(f"{impact['commands']} actions")
        if impact["delegated"]:
            parts.append(f"{impact['delegated']} delegated")
        lines.append(f"      → {' · '.join(parts)}  (impact: {score})")

    # Keyword analysis across top prompts
    stop_words = {
        'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'will',
        'been', 'are', 'was', 'were', 'has', 'had', 'not', 'but', 'all',
        'can', 'you', 'your', 'our', 'what', 'when', 'how', 'which', 'into',
        'also', 'just', 'like', 'them', 'than', 'then', 'each', 'make',
        'way', 'use', 'using', 'about', 'it\'s', 'don\'t', 'i\'m',
        'should', 'could', 'would', 'does', 'there', 'here', 'need',
    }
    all_words = []
    for prompt, _, _ in top:
        text = prompt["text"].lower()
        for word in text.split():
            word = word.strip(".,!?\"'()[]{}:/~")
            if len(word) > 3 and word not in stop_words and not word.startswith('/'):
                all_words.append(word)

    from collections import Counter
    word_counts = Counter(all_words)
    top_keywords = word_counts.most_common(10)

    if top_keywords:
        lines.append(f"")
        lines.append(f"  🔑 PROMPT PATTERNS:")
        kw_parts = [f"{word} ({count}x)" for word, count in top_keywords if count > 1]
        if kw_parts:
            lines.append(f"      Recurring: {' · '.join(kw_parts[:6])}")

        # Detect prompt engineering patterns
        patterns = []
        all_text = " ".join(p["text"].lower() for p, _, _ in top)
        if any(w in all_text for w in ['test', 'spec', 'vitest', 'jest']):
            patterns.append("test-oriented")
        if any(w in all_text for w in ['systematic', 'methodical', 'step']):
            patterns.append("systematic")
        if any(w in all_text for w in ['setup', 'install', 'configure']):
            patterns.append("environment-focused")
        if any(w in all_text for w in ['explain', 'walk', 'understand']):
            patterns.append("learning-oriented")
        if any(w in all_text for w in ['safe', 'security', 'guard']):
            patterns.append("safety-conscious")
        if any(w in all_text for w in ['reusable', 're-usable', 'pattern']):
            patterns.append("pattern-thinking")

        if patterns:
            lines.append(f"      Style: {' · '.join(patterns)}")

    lines.append(f"")
    lines.append(f"  💡 Expand a prompt: python3 summary.py --prompt 1")

    return "\n".join(lines)


def render_prompt_detail(events, rank):
    """Render full detail for a specific prompt from the leaderboard."""
    top = analyze_top_prompts(events)
    if not top:
        return "\n  No prompts found for this day.\n"

    if rank == "all":
        indices = range(len(top))
    else:
        try:
            idx = int(rank) - 1
            if idx < 0 or idx >= len(top):
                return f"\n  Invalid rank #{rank}. Available: 1–{len(top)}\n"
            indices = [idx]
        except ValueError:
            return f"\n  Usage: --prompt 1  or  --prompt all\n"

    output = []
    output.append("")
    output.append("┌" + "─" * 76 + "┐")
    output.append("│" + " " * 22 + "🔍 PROMPT DEEP DIVE" + " " * 35 + "│")
    output.append("└" + "─" * 76 + "┘")

    for idx in indices:
        prompt, impact, score = top[idx]
        text = prompt["text"].strip()

        output.append("")
        output.append(f"  ━━━ #{idx + 1} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        output.append(f"  📁 {prompt['project']}  ·  🕐 {prompt['time'][:5]}  ·  Impact: {score}")
        output.append("")

        # Full prompt text, word-wrapped at ~72 chars
        output.append("  PROMPT:")
        words = text.split()
        current_line = "    "
        for word in words:
            if len(current_line) + len(word) + 1 > 74:
                output.append(current_line)
                current_line = "    " + word
            else:
                current_line = current_line + " " + word if current_line.strip() else "    " + word
        if current_line.strip():
            output.append(current_line)

        # Impact breakdown
        output.append("")
        output.append("  IMPACT:")
        if impact["files"]:
            output.append(f"    📄 {impact['files']} file(s) created or modified  (×3 = {impact['files'] * 3})")
        if impact["tasks"]:
            output.append(f"    ✅ {impact['tasks']} task(s) planned or completed  (×5 = {impact['tasks'] * 5})")
        if impact["commands"]:
            output.append(f"    ▶️  {impact['commands']} command(s) executed         (×1 = {impact['commands']})")
        if impact["delegated"]:
            output.append(f"    ⚡ {impact['delegated']} agent(s) delegated          (×4 = {impact['delegated'] * 4})")
        output.append(f"    ─────────────────────────────────")
        output.append(f"    Total impact score: {score}")

        # Keyword extraction for this individual prompt
        stop_words = {
            'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'will',
            'been', 'are', 'was', 'were', 'has', 'had', 'not', 'but', 'all',
            'can', 'you', 'your', 'our', 'what', 'when', 'how', 'which', 'into',
            'also', 'just', 'like', 'them', 'than', 'then', 'each', 'make',
            'way', 'use', 'using', 'about', "it's", "don't", "i'm",
            'should', 'could', 'would', 'does', 'there', 'here', 'need',
        }
        from collections import Counter
        words_clean = []
        for w in text.lower().split():
            w = w.strip(".,!?\"'()[]{}:/~")
            if len(w) > 3 and w not in stop_words and not w.startswith('/'):
                words_clean.append(w)
        word_counts = Counter(words_clean)
        top_kw = word_counts.most_common(8)
        if top_kw:
            output.append("")
            output.append("  KEYWORDS:")
            kw_str = " · ".join(f"{w} ({c}x)" if c > 1 else w for w, c in top_kw)
            output.append(f"    {kw_str}")

        # Prompt character analysis
        output.append("")
        output.append("  STATS:")
        char_count = len(text)
        word_count = len(text.split())
        output.append(f"    {word_count} words · {char_count} chars")

    output.append("")
    return "\n".join(output)


def analyze_slumps(events):
    """Find periods where prompts produced zero or minimal output — the slumps."""
    NOISE = ['<command-', '<local-command-', '<task-notification>',
             'This session is being continued', 'Caveat: The messages',
             'Your task is to create a detailed summary']

    sorted_events = sorted(events, key=lambda e: (e.get("session", ""), e.get("ts", "")))
    slumps = []
    current_prompt = None
    impact = 0

    for e in sorted_events:
        action = e.get("action", "")

        if action == "user_prompt":
            if current_prompt and impact == 0:
                slumps.append(current_prompt)
            text = e.get("prompt", "")
            if not any(s in text for s in NOISE) and len(text.strip()) > 20:
                current_prompt = {
                    "text": text,
                    "time": e.get("ts", ""),
                    "project": e.get("project", ""),
                }
                impact = 0
            else:
                current_prompt = None
        elif current_prompt:
            if action in ("created_file", "modified_file", "task_completed", "task_planned"):
                impact += 1

    # Last one
    if current_prompt and impact == 0:
        slumps.append(current_prompt)

    return slumps


def analyze_time_gaps(events):
    """Find the biggest time gaps (potential context-switching or thinking pauses)."""
    times = sorted(set(e.get("ts", "") for e in events if e.get("ts", "")))

    def to_secs(t):
        parts = t.split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + (int(parts[2]) if len(parts) > 2 else 0)

    gaps = []
    for i in range(1, len(times)):
        try:
            gap = to_secs(times[i]) - to_secs(times[i - 1])
            if gap > 120:  # >2 min
                gaps.append((times[i - 1], times[i], gap))
        except:
            pass

    gaps.sort(key=lambda x: -x[2])
    return gaps[:5]


def extract_engineering_concepts(events):
    """Extract top engineering concepts/principles demonstrated in today's session."""
    from collections import Counter

    concepts = []

    # Gather data
    delegated = [e for e in events if e.get("action") in ("delegated", "delegated_task")]
    commands = [e for e in events if e.get("action") in ("command", "ran_command", "ran_tests",
                                                          "built_project", "git_operation")]
    research = [e for e in events if e.get("action") in ("research", "web_research")]
    planned = [e for e in events if e.get("action") == "task_planned"]
    completed = [e for e in events if e.get("action") == "task_completed"]
    created = [e for e in events if e.get("action") == "created_file"]
    git_ops = [c for c in commands if "git" in c.get("command", "").lower()]
    test_ops = [c for c in commands if any(t in c.get("command", "").lower()
                for t in ["test", "jest", "vitest", "pytest"])]

    # 1. Parallel Delegation pattern
    if len(delegated) >= 3:
        agent_types = Counter(d.get("agent", d.get("task_type", "")) for d in delegated)
        top_agent = agent_types.most_common(1)[0][0] if agent_types else "agents"
        concepts.append({
            "name": "Parallel Agent Delegation",
            "principle": "Decompose large tasks into independent subtasks, run them concurrently via specialized agents",
            "example": f"Delegated {len(delegated)} tasks (mostly to {top_agent}) — explored, built, and validated in parallel",
            "generalize": "Any time you have N independent subtasks, spawn N workers. Applies to: CI pipelines, microservices, MapReduce, even human team coordination.",
        })

    # 2. Research-before-build
    if len(research) > 15 and len(created) > 5:
        concepts.append({
            "name": "Research-First Development",
            "principle": "Invest upfront in understanding the problem space before writing code",
            "example": f"{len(research)} research events preceded {len(created)} files created — studied before building",
            "generalize": "For any unfamiliar domain: read docs → prototype → build. The research:code ratio should be at least 2:1 for novel problems.",
        })

    # 3. Task decomposition & completion
    if len(planned) >= 5 and len(completed) >= 5:
        ratio = len(completed) / max(len(planned), 1)
        concepts.append({
            "name": "Structured Task Decomposition",
            "principle": "Break work into explicit, trackable tasks with clear completion criteria",
            "example": f"Planned {len(planned)} tasks, completed {len(completed)} ({ratio:.0%} completion rate)",
            "generalize": "Every project benefits from explicit task lists. The act of decomposing reveals hidden complexity and prevents scope creep.",
        })

    # 4. Iterative refinement
    modified = [e for e in events if e.get("action") == "modified_file"]
    if len(modified) > len(created) * 2 and len(modified) > 10:
        concepts.append({
            "name": "Iterative Refinement Over Perfection",
            "principle": "Ship a working version first, then refine through multiple passes",
            "example": f"Created {len(created)} files but made {len(modified)} modifications — refined 2x+ per file on average",
            "generalize": "First drafts are never final. Build the skeleton, then flesh it out. Applies to code, writing, design, and architecture.",
        })

    # 5. Git discipline
    commits = [c for c in git_ops if "commit" in c.get("command", "").lower()]
    branches = [c for c in git_ops if any(b in c.get("command", "").lower()
                for b in ["checkout", "branch", "worktree"])]
    if len(commits) >= 3 or len(branches) >= 2:
        concepts.append({
            "name": "Version Control Discipline",
            "principle": "Commit frequently in logical units, use branches for isolation",
            "example": f"{len(commits)} commits and {len(branches)} branch operations — kept changes atomic and reversible",
            "generalize": "Small, frequent commits > large monolithic ones. Each commit should be a complete, working state. Branch per feature, not per day.",
        })

    # 6. Test feedback loops
    if len(test_ops) >= 3:
        concepts.append({
            "name": "Tight Test Feedback Loops",
            "principle": "Run tests frequently to catch regressions early and build confidence",
            "example": f"Ran {len(test_ops)} test cycles during the session — verified continuously, not just at the end",
            "generalize": "Automated tests are your safety net. Run after every meaningful change. The cost of a late-caught bug is 10x the cost of early detection.",
        })

    # 7. Spec-driven development
    spec_files = [e for e in created if any(s in e.get("file", "").lower()
                  for s in ["spec", "design", "proposal", "playbook"])
                  and e.get("file", "").lower().endswith(".md")]
    if len(spec_files) >= 2:
        concepts.append({
            "name": "Spec-Driven Development",
            "principle": "Write the specification before the implementation — design the interface before the internals",
            "example": f"Created {len(spec_files)} spec/design docs before building implementation code",
            "generalize": "Specs force you to think about the 'what' before the 'how'. They serve as documentation, test plan, and contract all at once.",
        })

    # Sort by relevance (concepts with more evidence first)
    return concepts[:5]


def render_session_insights(events):
    """Render slumps, most expensive prompt callout, and engineering concepts."""
    output = []

    # ── MOST EXPENSIVE PROMPT ──
    top = analyze_top_prompts(events)
    if top:
        prompt, impact, score = top[0]
        text = " ".join(prompt["text"].split())
        if len(text) > 120:
            text = text[:117] + "..."

        output.append("")
        output.append("┌" + "─" * 76 + "┐")
        output.append("│" + " " * 19 + "💎 MOST EXPENSIVE PROMPT" + " " * 33 + "│")
        output.append("└" + "─" * 76 + "┘")
        output.append(f"")
        output.append(f"  Impact score: {score}  ({impact['files']} files × 3 + {impact['tasks']} tasks × 5 + {impact['commands']} cmds + {impact['delegated']} delegated × 4)")
        output.append(f"  📁 {prompt['project']}  ·  🕐 {prompt['time'][:5]}")
        output.append(f"")

        # Word-wrap the prompt text
        words = text.split()
        current = "  \""
        for word in words:
            if len(current) + len(word) + 1 > 74:
                output.append(current)
                current = "   " + word
            else:
                current = current + " " + word if len(current) > 3 else current + word
        if current.strip():
            output.append(current + "\"")
        output.append("")

        # Compare to average
        if len(top) > 1:
            avg_score = sum(s for _, _, s in top) / len(top)
            ratio = score / max(avg_score, 1)
            output.append(f"  {ratio:.1f}x the average top-5 prompt impact")

    # ── SLUMPS ──
    slumps = analyze_slumps(events)
    gaps = analyze_time_gaps(events)

    if slumps or gaps:
        output.append("")
        output.append("┌" + "─" * 76 + "┐")
        output.append("│" + " " * 23 + "📉 FRICTION & SLUMPS" + " " * 33 + "│")
        output.append("└" + "─" * 76 + "┘")

    if slumps:
        output.append(f"")
        output.append(f"  {len(slumps)} prompt(s) produced zero file/task output:")
        # Show top 5 most interesting slumps (longest prompts = most effort wasted)
        sorted_slumps = sorted(slumps, key=lambda s: -len(s["text"]))[:5]
        for s in sorted_slumps:
            text = " ".join(s["text"].split())
            if len(text) > 70:
                text = text[:67] + "..."
            output.append(f"    {s['time'][:5]}  [{s['project']}] {text}")

        # Categorize the slumps
        exploration = sum(1 for s in slumps if any(w in s["text"].lower()
                         for w in ["check", "explore", "research", "what is", "how to", "tell me"]))
        setup = sum(1 for s in slumps if any(w in s["text"].lower()
                    for w in ["setup", "install", "configure", "open"]))
        other = len(slumps) - exploration - setup
        output.append(f"")
        parts = []
        if exploration:
            parts.append(f"{exploration} exploration/research")
        if setup:
            parts.append(f"{setup} setup/config")
        if other:
            parts.append(f"{other} other")
        output.append(f"  Breakdown: {' · '.join(parts)}")
        output.append(f"  💡 Not all slumps are bad — exploration and research build understanding")

    if gaps:
        output.append(f"")
        output.append(f"  Biggest pauses:")
        for t1, t2, gap_secs in gaps[:3]:
            mins = gap_secs // 60
            output.append(f"    {t1[:5]} → {t2[:5]}  ({mins}m pause)")

    # ── ENGINEERING CONCEPTS ──
    concepts = extract_engineering_concepts(events)
    if concepts:
        output.append("")
        output.append("┌" + "─" * 76 + "┐")
        output.append("│" + " " * 16 + "🧬 TOP ENGINEERING PRINCIPLES APPLIED" + " " * 23 + "│")
        output.append("└" + "─" * 76 + "┘")

        for i, c in enumerate(concepts, 1):
            output.append(f"")
            output.append(f"  {i}. {c['name']}")
            output.append(f"     PRINCIPLE: {c['principle']}")
            output.append(f"     TODAY:     {c['example']}")
            # Word-wrap the generalize text
            gen_text = c["generalize"]
            words = gen_text.split()
            current = "     EXTEND:    "
            for word in words:
                if len(current) + len(word) + 1 > 76:
                    output.append(current)
                    current = "                " + word
                else:
                    current = current + " " + word if current.strip() else "                " + word
            if current.strip():
                output.append(current)

    return "\n".join(output)


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

    # Per-project summaries — skip projects with minimal activity
    for name, data in sorted(projects.items(), key=lambda x: -len(x[1]["timeline"])):
        has_substance = (data["files_created"] or data["files_modified"]
                        or data.get("plans") or data.get("user_intents")
                        or data.get("completion_count", 0) > 0)
        if data["timeline"] and has_substance:
            output.append(render_project_summary(name, data))

    # Top prompts analysis
    output.append(render_top_prompts(events))

    # Session insights: most expensive prompt, slumps, engineering concepts
    output.append(render_session_insights(events))

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
    parser.add_argument("--prompt", "-P", type=str, help="Expand a top prompt by rank (1-5) or 'all'")

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

    # Prompt deep dive
    if args.prompt:
        print(render_prompt_detail(events, args.prompt))
        return

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
