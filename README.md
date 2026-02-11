# Claude Code Engineering Journal

> **Turn your Claude Code sessions into a daily engineering journal with ASCII visualizations.**

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║   ███████╗███╗   ██╗ ██████╗      ██╗ ██████╗ ██╗   ██╗██████╗ ███╗   ██╗    ║
║   ██╔════╝████╗  ██║██╔════╝      ██║██╔═══██╗██║   ██║██╔══██╗████╗  ██║    ║
║   █████╗  ██╔██╗ ██║██║  ███╗     ██║██║   ██║██║   ██║██████╔╝██╔██╗ ██║    ║
║   ██╔══╝  ██║╚██╗██║██║   ██║██   ██║██║   ██║██║   ██║██╔══██╗██║╚██╗██║    ║
║   ███████╗██║ ╚████║╚██████╔╝╚█████╔╝╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║    ║
║   ╚══════╝╚═╝  ╚═══╝ ╚═════╝  ╚════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## What It Does

This system hooks into Claude Code to automatically track **what you're actually building** — not just tool calls, but meaningful engineering work:

- **Complete history access** — Automatically backfills from `~/.claude/history.jsonl` to give you access to all your past work
- **Projects worked on** with time ranges
- **Files created and modified** categorized by type (code, config, frontend, docs)
- **Tasks completed** from your todo list
- **Operations performed** (tests, builds, git commits, deployments)
- **Research conducted** (web searches, documentation lookups)
- **Date range summaries** — View work across weeks, months, or custom ranges
- **Zero-setup** — Works automatically in any Claude Code session after one-time install

## Setup

### One-Time Installation

Run the installer to set up everything automatically:

```bash
~/Desktop/cc-config/install.sh
```

This will:

1. **Install slash commands** — Adds `/summary`, `/summary-pick`, `/summary-range`, `/summary-quick`, `/summary-history` to `~/.claude/commands/`
2. **Configure activity logger hook** — Safely merges into `~/.claude/settings.json` (preserves existing MCP servers/settings)
3. **Backfill complete history** — Converts `~/.claude/history.jsonl` into daily logs (all your past work becomes browsable)
4. **Verify installation** — Checks that everything is working correctly

After installation, cc-config works **automatically in any Claude Code session, in any project**.

### What Gets Backfilled

When you run install.sh, it parses your complete `~/.claude/history.jsonl` and creates daily log files for all past activity:

- **Session-based logs** for historical dates (shows prompts and projects worked on)
- **Detailed logs** for current activity (shows file edits, commands, tests, etc.)
- **Preserves existing logs** — Won't overwrite detailed logs with backfilled data

This means you instantly get access to weeks or months of past work history.

## Quick Start

### 1. The hooks are already configured

Your `~/.claude/settings.json` includes:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "/Users/YOU/Desktop/cc-config/hooks/activity-logger.py"
      }]
    }]
  }
}
```

### 2. Use the slash commands

| Command | Description |
|---------|-------------|
| `/summary` | Today's engineering journal |
| `/summary-pick` | Browse ALL days with stats, choose one to expand (compact by default) |
| `/summary-range` | View work across date ranges (e.g., "last week", "Dec 1 to Dec 15") |
| `/summary-history` | Browse past days (basic list) |
| `/summary-quick` | Compact view of today |

**New in v2:** `/summary-range` lets you analyze work across time periods:
- Natural language: "last 7 days", "this week", "last month"
- Specific dates: "2025-12-01 to 2025-12-15"
- Shows aggregated stats, per-project breakdowns, daily activity charts

### 3. Or run directly

```bash
# Today's journal
python3 ~/Desktop/cc-config/summary.py

# Compact view of today
python3 ~/Desktop/cc-config/summary.py --compact

# Interactive date picker (choose by number)
python3 ~/Desktop/cc-config/summary.py --pick

# Non-interactive date picker list (for slash commands)
python3 ~/Desktop/cc-config/summary.py --pick-list

# Specific date
python3 ~/Desktop/cc-config/summary.py --date 2025-10-15

# Specific date, compact view
python3 ~/Desktop/cc-config/summary.py --date 2025-10-15 --compact

# Date range (specific dates)
python3 ~/Desktop/cc-config/summary.py --range 2025-12-01 2025-12-31

# Date range (relative)
python3 ~/Desktop/cc-config/summary.py --range-relative 7d        # Last 7 days
python3 ~/Desktop/cc-config/summary.py --range-relative this-week  # This week
python3 ~/Desktop/cc-config/summary.py --range-relative last-month # Last month

# List all available dates
python3 ~/Desktop/cc-config/summary.py --list

# Save to file
python3 ~/Desktop/cc-config/summary.py --save
```

## Sample Output

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            📊 DAY AT A GLANCE                              │
├────────────────────────────────────────────────────────────────────────────┤
│  3 project(s)  •  12 created  •  8 modified  •  5 tasks done               │
└────────────────────────────────────────────────────────────────────────────┘

  Work types: 💻 Coding  🧪 Testing  🔨 Building  🌿 Git

┌────────────────────────────────────────────────────────────────────────────┐
│  📁 my-awesome-app                                     [09:30 → 17:45]    │
└────────────────────────────────────────────────────────────────────────────┘

  🏗️  BUILT:
      💻 api-handler.ts
      💻 auth-middleware.ts
      ⚙️ config.json
      🎨 dashboard.css

  ✏️  MODIFIED:
      • App.tsx
      • routes.ts
      • package.json

  ✅ COMPLETED:
      ✓ Set up authentication flow
      ✓ Add user dashboard
      ✓ Fix pagination bug

  ⚡ OPERATIONS:
      🧪 Ran tests (3x)
      🔨 Built project (2x)
      💾 Committed code (1x)

┌────────────────────────────────────────────────────────────────────────────┐
│                              📅 THIS WEEK                                  │
└────────────────────────────────────────────────────────────────────────────┘

    Mon │████████████████████░░░░░░░░░░░░░░░░░░░░│  15 actions
    Tue │██████████████████████████████░░░░░░░░░░│  22 actions
    Wed │████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   9 actions
    Thu │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   0 actions
  → Fri │██████████████████████████████████████░░│  28 actions

  🔥 3-day streak!
```

## Historical Analysis

### Automatic Backfill

Your complete history is automatically backfilled on first install:

```bash
# Manual backfill (if needed)
python3 ~/Desktop/cc-config/backfill-history.py
```

This reads from `~/.claude/history.jsonl` and creates daily log files showing:

- **All your past projects** organized by date
- **Session activity** (what you worked on each day)
- **Time ranges** (when you were active)
- **Project context** (which codebases you touched)

Backfilled logs show session-level activity, while current logs (from the activity hook) show detailed tool usage.

### Standalone History Parsers

For advanced analysis, use the standalone parsers:

```bash
# Full history with daily breakdown
python3 ~/Desktop/cc-config/full-history.py

# Summary with stats
python3 ~/Desktop/cc-config/parse-history.py
```

These provide:
- **All-time stats** (total prompts, projects, work breakdown)
- **Monthly summaries** with activity charts
- **Work type analysis** (debugging vs building vs testing, etc.)

## What Gets Logged

The activity logger captures **meaningful engineering context**, not raw tool calls:

| Activity | What's Captured |
|----------|-----------------|
| **File Creation** | File name, path, type (code/config/docs/frontend) |
| **File Editing** | File name, project context |
| **Commands** | Categorized as: tests, builds, deps, git, infra |
| **Task Delegation** | Full task description + prompt context |
| **Todo Completion** | Task names from your todo list |
| **Research** | Search queries, documentation lookups |

Noisy events (file reads, grep searches) are filtered out to keep logs meaningful.

## Directory Structure

```
~/Desktop/cc-config/
├── hooks/
│   └── activity-logger.py      # Hooks into Claude Code tool calls
├── logs/
│   └── YYYY-MM-DD.jsonl        # Daily activity logs (backfilled + current)
├── summaries/                  # Saved journal exports
├── commands/                   # Slash command definitions
│   ├── summary.md
│   ├── summary-pick.md
│   ├── summary-range.md        # NEW: Date range summaries
│   ├── summary-quick.md
│   └── summary-history.md
├── summary.py                  # Daily journal generator (enhanced with date ranges)
├── backfill-history.py         # NEW: Backfills from history.jsonl
├── merge-settings.py           # NEW: Safely merges hook into settings.json
├── install.sh                  # Complete installation script
├── parse-history.py            # Historical summary
└── full-history.py             # Complete history breakdown
```

## Configuration

The hooks are defined in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "..." }] }],
    "PostToolUse": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "..." }] }],
    "Stop": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "..." }] }]
  }
}
```

Slash commands are in `~/.claude/commands/`:
- `summary.md` — full journal for today
- `summary-pick.md` — browse ALL days with stats (compact by default)
- `summary-range.md` — **NEW:** date range summaries (weeks, months, custom ranges)
- `summary-history.md` — basic date list
- `summary-quick.md` — compact view

## Why?

**For learning**: See patterns in how you work. Are you mostly debugging? Building? What projects consume the most time?

**For journaling**: End each day with a clear record of what you accomplished. Great for standups, retrospectives, or personal tracking.

**For motivation**: Watch your streak grow. See the week fill up with activity blocks.

## License

MIT — do whatever you want with it.

---

*Built with Claude Code, tracked by Claude Code* 🔄
