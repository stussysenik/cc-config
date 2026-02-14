# Claude Code Engineering Journal - Documentation

## Overview

This tool extracts hidden usage data from Claude Code's native logs and presents it as:
- **Dev-first journal** — quick, scannable summary of what shipped (default mode)
- **Vibes dashboard** — energy, focus, highlight, method, cost at a glance
- **Full narrative mode** — verbose output with file lists, task details, top prompts, engineering principles (`--full`)
- **Deliverable grouping** — files organized by purpose (FX presets, API layer, Test suites)
- **Prompt impact leaderboard** — top 5 most productive prompts with NLP keyword analysis
- **Token & cost tracking** — usage estimates, model breakdown, cache savings
- **Subscription value comparison** — how much value you're getting vs API pricing

## Architecture

```
~/.claude/projects/           ~/Desktop/cc-config/
├── -Users-s3nik-Desktop-*/
│   └── *.jsonl               ──sync──>  logs/
│       (Claude's native logs)            ├── 2026-02-11.jsonl
│                                         ├── 2026-02-10.jsonl
│                                         └── .stats.json
```

## Pricing Model

### Anthropic API Pricing (per 1M tokens)

| Model | Input | Output | Cache Read | Cache Write |
|-------|-------|--------|------------|-------------|
| Opus | $15.00 | $75.00 | $1.50 (90% off) | $18.75 (+25%) |
| Sonnet | $3.00 | $15.00 | $0.30 (90% off) | $3.75 (+25%) |
| Haiku | $0.80 | $4.00 | $0.08 (90% off) | $1.00 (+25%) |

### Cache Savings

- **Cache reads** are 90% cheaper than regular input tokens
- **Cache writes** are 25% more expensive (caching premium)
- Most requests heavily benefit from caching, saving 80-90% of costs

### Subscription Value

Compare your API-equivalent usage to subscription tiers:
- **Claude Pro**: $20/mo
- **Claude Max 5x**: $100/mo
- **Claude Max 20x**: $200/mo

## Commands Reference

### `/summary` (default — quick journal)
Dev-first journal focused on what shipped.

Output includes:
- **Header** — date, duration, project count, cost (one line)
- **SHIPPED** — top projects with product descriptions and metrics (tasks, test runs, agents, commits)
- **VIBES** — energy bar, focus level, highlight, method keywords, cost breakdown
- **WEEK** — slim activity bar chart with streak tracking

### `/summary --full` (verbose)
Full narrative output with all details.

Output includes:
- **TODAY'S SESSION** — time span, project count, total files + tasks
- **THE ARC** — timeline of projects with deliverable descriptions
- **Per-project narratives** — intent quote, grouped deliverables, task completion, engineering patterns
- **TOP PROMPTS BY IMPACT** — top 5 prompts scored by files×3 + tasks×5 + commands + delegated×4
- **MOST EXPENSIVE PROMPT** — callout of the #1 highest-impact prompt
- **FRICTION & SLUMPS** — zero-output prompts categorized (exploration/setup/other) + time gaps
- **ENGINEERING PRINCIPLES** — auto-extracted concepts with PRINCIPLE → TODAY → EXTEND format
- **THIS WEEK** — activity bar chart with streak tracking
- **Usage Statistics** — token costs and model breakdown

### `/summary-quick`
Compact one-line view of today's activity.

### `/summary-range [range]`
View activity over a date range.

Ranges:
- `7d` - Last 7 days
- `30d` - Last 30 days
- `last-month` - Previous calendar month
- `this-month` - Current month
- `YYYY-MM-DD` - Specific date

### `/summary-pick`
Browse all available dates interactively.

### `/stats [range]`
Full token/cost statistics.

Features:
- **Cost Summary**: Actual cost, cost without caching, cache savings
- **Token Breakdown**: Input, output, cache read, cache write
- **Subscription Value**: How much value you're getting vs subscription price
- **By Model**: Breakdown by opus/sonnet/haiku
- **Top Projects**: Highest-cost projects
- **Recent Activity**: Last 10 days of usage

Ranges (optional):
- `7d` - Last 7 days
- `30d` - Last 30 days
- `last-month` - Previous month
- `this-month` - Current month
- (none) - All time

## Files

### `sync-native-logs.py`
Main sync script that reads Claude's native logs.

```bash
python3 sync-native-logs.py           # Incremental sync
python3 sync-native-logs.py --reset   # Full resync
python3 sync-native-logs.py --stats   # Show statistics
python3 sync-native-logs.py --stats 7d  # 7-day stats
```

### `summary.py`
Generates narrative engineering journals from synced logs.

```bash
python3 summary.py                    # Quick dev journal (default)
python3 summary.py --full             # Verbose output (file lists, prompts, principles)
python3 summary.py --date 2026-02-10  # Specific date
python3 summary.py --range-relative 7d  # Date range
python3 summary.py --compact          # Quick view
python3 summary.py --prompt 1         # Deep-dive into top prompt #1
python3 summary.py --prompt all       # Expand all top 5 prompts
```

Key analysis functions:
- `analyze_events()` — Parses all action types into per-project narratives
- `generate_product_description()` — Turns deliverables/tasks into human-readable prose
- `compute_vibes()` — Energy, focus, highlight, method, cost analysis
- `rank_projects()` — Scores projects by substance, splits into expanded/collapsed
- `group_deliverables()` — Groups files by purpose (pattern matching on paths)
- `detect_patterns()` — Detects TDD, spec-driven, research-heavy, safety-first, parallel work
- `analyze_top_prompts()` — Scores prompts by downstream impact
- `extract_engineering_concepts()` — Auto-extracts engineering principles from session data

### `install.sh`
One-click installer.

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/stussysenik/cc-config/main/install.sh)
```

What it does:
1. Clones/updates the repo
2. Copies commands to `~/.claude/commands/`
3. Runs initial sync
4. Shows your usage stats

### `logs/*.jsonl`
Daily activity logs in JSONL format.

Event types:
- `user_prompt` - User input
- `created_file` - File created (Write tool)
- `modified_file` - File modified (Edit tool)
- `command` - Bash command executed
- `git_operation` - Git commits/pushes
- `task_planned` - TaskCreate
- `task_completed` - TaskUpdate (completed)
- `research` - Read/Glob/Grep
- `web_research` - WebFetch/WebSearch
- `delegated` - Task tool (agent delegation)

### `logs/.stats.json`
Aggregated statistics.

Structure:
```json
{
  "total_tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
  "total_cost": 0.0,
  "total_cost_without_cache": 0.0,
  "total_cache_savings": 0.0,
  "by_date": {},
  "by_model": {},
  "by_project": {}
}
```

## Troubleshooting

### "No log files found"
Make sure Claude Code has been used on this machine. Logs are stored in `~/.claude/projects/`.

### Stats show $0
Run a full resync: `python3 sync-native-logs.py --reset`

### Slash commands not working
1. Check `~/.claude/commands/` has the `.md` files
2. Restart Claude Code
3. Re-run `install.sh`

### Missing recent activity
Run sync: `python3 ~/Desktop/cc-config/sync-native-logs.py`

## Technical Details

### How Claude Logs Work

Claude Code writes JSONL files to `~/.claude/projects/{encoded-path}/` with each line being a JSON object:

```json
{
  "type": "assistant",
  "timestamp": "2026-02-11T20:18:40.123Z",
  "cwd": "/Users/s3nik/Desktop/project",
  "sessionId": "abc123...",
  "message": {
    "model": "claude-opus-4-5-20251101",
    "usage": {
      "input_tokens": 17483,
      "output_tokens": 5,
      "cache_read_input_tokens": 3671035677,
      "cache_creation_input_tokens": 0
    },
    "content": [
      {"type": "tool_use", "name": "Write", "input": {"file_path": "..."}}
    ]
  }
}
```

### Incremental Sync

The sync script tracks file positions in `.sync-state.json`:
```json
{
  "files": {
    "/path/to/log.jsonl": 12345
  }
}
```

Each sync continues from the last position, making it fast for frequent syncs.
