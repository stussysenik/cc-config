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

- **Projects worked on** with time ranges
- **Files created and modified** categorized by type (code, config, frontend, docs)
- **Tasks completed** from your todo list
- **Operations performed** (tests, builds, git commits, deployments)
- **Research conducted** (web searches, documentation lookups)
- **Historical trends** with week/month visualizations

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
| `/summary-history` | Browse past days |
| `/summary-quick` | Compact view |

### 3. Or run directly

```bash
# Today's journal
python3 ~/Desktop/cc-config/summary.py

# Specific date
python3 ~/Desktop/cc-config/summary.py --date 2025-10-15

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

Parse your complete Claude Code history:

```bash
# Full history with daily breakdown
python3 ~/Desktop/cc-config/full-history.py

# Summary with stats
python3 ~/Desktop/cc-config/parse-history.py
```

This reads from `~/.claude/history.jsonl` and shows:

- **All-time stats** (total prompts, projects, work breakdown)
- **Monthly summaries** with activity charts
- **Daily breakdowns** showing projects, categories, sample prompts
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
│   └── activity-logger.py   # Hooks into Claude Code tool calls
├── logs/
│   └── YYYY-MM-DD.jsonl     # Daily activity logs
├── summaries/               # Saved journal exports
├── summary.py               # Daily journal generator
├── parse-history.py         # Historical summary
└── full-history.py          # Complete history breakdown
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
- `summary.md`
- `summary-history.md`
- `summary-quick.md`

## Why?

**For learning**: See patterns in how you work. Are you mostly debugging? Building? What projects consume the most time?

**For journaling**: End each day with a clear record of what you accomplished. Great for standups, retrospectives, or personal tracking.

**For motivation**: Watch your streak grow. See the week fill up with activity blocks.

## License

MIT — do whatever you want with it.

---

*Built with Claude Code, tracked by Claude Code* 🔄
