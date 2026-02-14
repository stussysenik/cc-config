# Claude Code Engineering Journal

> **Track your Claude Code sessions, token usage, and costs — data Claude hides from you!**

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

Claude Code logs everything you do to `~/.claude/projects/` but **never shows you**:
- Token usage per request
- Cost estimates
- Model breakdown (opus/sonnet/haiku)
- Historical activity

This tool extracts that hidden data and gives you:

- **💰 Token & Cost Tracking** — See exactly how much you're spending
- **📊 Usage Statistics** — Breakdown by model, project, and day
- **📁 Project Activity** — Files created, modified, commands run
- **📅 Date Range Analysis** — View weeks, months, or custom periods
- **🔄 Auto-Discovery** — Finds all Claude Code activity across your machine

## Quick Install

**One-liner:**
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/stussysenik/cc-config/main/install.sh)
```

**Or clone and run:**
```bash
git clone https://github.com/stussysenik/cc-config.git ~/Desktop/cc-config
cd ~/Desktop/cc-config && ./install.sh
```

This will:
1. ✅ Install all slash commands (`/summary`, `/stats`, etc.)
2. ✅ Sync all your Claude Code activity (auto-discovers everything)
3. ✅ Show your usage statistics

**No hooks needed!** — Reads directly from Claude's native logs.

## Slash Commands

After installation, use these in any Claude Code session:

| Command | What It Shows |
|---------|---------------|
| `/summary` | Quick dev journal — what shipped, vibes, week chart |
| `/summary --full` | Verbose output — file lists, task details, top prompts, principles |
| `/summary-quick` | Compact quick-glance view |
| `/summary-range 7d` | Last 7 days with period costs |
| `/summary-range 30d` | Last 30 days |
| `/summary-range last-month` | Previous month |
| `/summary-pick` | Browse all available dates |
| `/stats` | Full token/cost/cache breakdown |
| `/stats 7d` | Last 7 days statistics |
| `/stats 30d` | Last 30 days statistics |
| `/stats last-month` | Previous month statistics |

## Sample Output

### `/summary` (default — quick journal)
```
  cc — Sat Feb 14 · 20h · 8 projects · $97

  SHIPPED ═════════════════════════════════════════════

  envelope-exa-experiment               03:05 → 21:24
  [feature/exa-integration]
  Feature Flags & Config, Safety Guardrails
  Storybook Setup, Search Provider Adapter
  DSPy Search Sidecar, Sidechain Enhancement
  → 14/15 tasks · 43 test runs · 14 agents

  senik                                 01:20 → 20:28
  FX Chain presets (4), Track templates (5)
  Session templates, Documentation (2)
  → 8/8 tasks

  + 5 smaller sessions (envelope, cc-config, dspy-search +2)

  VIBES ═══════════════════════════════════════════════

  Energy    ████████████████████░░  marathon (20h span)
  Focus     scattered across 8 projects, high completion
  Highlight envelope-exa-experiment — Test suites + API layer
  Method    research-first (675 reads), TDD (43 test runs)
  Cost      $97 · opus $92 / haiku $25

  WEEK ═════════════════════════════════════════════════

    Fri │███████░░░░░░░░░░░░░│  47
  → Sat │████████████████████│ 249
  🔥 2-day streak
```

### `/summary --full` (verbose)
```
┌────────────────────────────────────────────────────────────────────────────┐
│                             ☕ TODAY'S SESSION                              │
├────────────────────────────────────────────────────────────────────────────┤
│  01:20 → 04:20 · 3h of focused work                                        │
│  5 project(s) delivered · 55 files built · 19 tasks completed              │
└────────────────────────────────────────────────────────────────────────────┘

  🎯 DELIVERED:
      FX Chain presets — 4 files (Vocal Chain, Sidechain Pump, Lo-Fi Texture, Space)
      Track templates — 5 files

  ✅ ALL 8 TASKS COMPLETED
  🔬 Research-driven — 211 investigations before building

  🧬 TOP ENGINEERING PRINCIPLES APPLIED
  1. Parallel Agent Delegation
     PRINCIPLE: Decompose large tasks into independent subtasks
     TODAY:     Delegated 15 tasks — explored, built, validated in parallel
```

### `/summary-range 14d`
```
────────────────────────────────────────────────────────────
💰 Usage Statistics
────────────────────────────────────────────────────────────
  Period: $10.45 (10,871 requests)
  Tokens: 1,045,095 (8 days)
  Daily avg: $1.31/day
  Total: $114.92 | 9,357,862 tokens
  Models: opus: $102.20 | haiku: $10.28 | sonnet: $2.45
  Top: mymind-clone-web: $23.38 | v0-clone: $20.35 | clean-writer: $17.65
```

### `/stats`
```
════════════════════════════════════════════════════════════
  📊 CLAUDE CODE USAGE STATISTICS
════════════════════════════════════════════════════════════

📅 Period: All Time

────────────────────────────────────────────────────────────
  💰 COST SUMMARY
────────────────────────────────────────────────────────────
  Actual Cost:      $    114.90
  Without Caching:  $    745.82
  Cache Savings:    $    630.92  💚 (85% saved)

────────────────────────────────────────────────────────────
  📝 TOKEN BREAKDOWN
────────────────────────────────────────────────────────────
  Total Tokens:        9,358,700
    Input:             8,614,499
    Output:              744,201
  Cache:
    Read:          3,687,882,565  (90% cheaper)
    Write:           273,748,132  (25% premium)

────────────────────────────────────────────────────────────
  🎯 SUBSCRIPTION VALUE COMPARISON
────────────────────────────────────────────────────────────
  Claude Pro ($20/mo):
    API Value:  $745.82 for $20/mo = 37.3x value ✨
  Claude Max 5x ($100/mo):
    API Value:  $745.82 for $100/mo = 7.5x value ✨

────────────────────────────────────────────────────────────
  📈 BY MODEL (all-time)
────────────────────────────────────────────────────────────
  opus         $  102.18  (35,152 reqs) (saved $512.87)
  haiku        $   10.28  (7,562 reqs) (saved $77.37)
  sonnet       $    2.45  (4,886 reqs) (saved $40.68)
```

## How It Works

Claude Code writes detailed logs to `~/.claude/projects/` including hidden usage data:

```json
{
  "message": {
    "model": "claude-opus-4-5-20251101",
    "usage": {
      "input_tokens": 17483,
      "output_tokens": 5,
      "cache_read_input_tokens": 3671035677
    }
  }
}
```

This tool:
1. **Scans** all `~/.claude/projects/**/*.jsonl` files
2. **Extracts** token usage, costs, file operations, commands
3. **Aggregates** by date, project, and model
4. **Displays** in a readable format

**No hooks, no configuration** — it just reads what Claude already logs.

## CLI Usage

```bash
# Today's journal (quick dev-first format)
python3 ~/Desktop/cc-config/summary.py

# Full verbose output (file lists, tasks, prompts, principles)
python3 ~/Desktop/cc-config/summary.py --full

# Compact view
python3 ~/Desktop/cc-config/summary.py --compact

# Deep-dive into a top prompt (by rank 1-5 or 'all')
python3 ~/Desktop/cc-config/summary.py --prompt 1
python3 ~/Desktop/cc-config/summary.py --prompt all

# Date range
python3 ~/Desktop/cc-config/summary.py --range-relative 7d
python3 ~/Desktop/cc-config/summary.py --range-relative last-month
python3 ~/Desktop/cc-config/summary.py --range 2026-01-01 2026-01-31

# Specific date
python3 ~/Desktop/cc-config/summary.py --date 2026-02-10

# Usage statistics
python3 ~/Desktop/cc-config/sync-native-logs.py --stats

# Manual sync (usually auto-runs)
python3 ~/Desktop/cc-config/sync-native-logs.py

# Full resync
python3 ~/Desktop/cc-config/sync-native-logs.py --reset
```

## Directory Structure

```
~/Desktop/cc-config/
├── commands/                   # Slash command definitions
│   ├── summary.md
│   ├── summary-quick.md
│   ├── summary-range.md
│   ├── summary-pick.md
│   ├── summary-history.md
│   └── stats.md
├── logs/
│   ├── YYYY-MM-DD.jsonl        # Daily activity logs
│   └── .stats.json             # Aggregated usage statistics
├── sync-native-logs.py         # Syncs from ~/.claude/projects/
├── summary.py                  # Generates journal summaries
└── install.sh                  # One-click installer
```

## Works On Any Device

This tool works on any machine with Claude Code activity:

1. Clone the repo
2. Run `./install.sh`
3. All your Claude Code history is instantly available

The sync script auto-discovers all projects in `~/.claude/projects/`.

## Cache Savings & Pricing

### How Much You Save

Claude Code uses **prompt caching** aggressively. Cache reads are **90% cheaper** than regular input tokens:

| Model | Input | Output | Cache Read | Cache Write |
|-------|-------|--------|------------|-------------|
| Opus | $15/1M | $75/1M | $1.50/1M | $18.75/1M |
| Sonnet | $3/1M | $15/1M | $0.30/1M | $3.75/1M |
| Haiku | $0.80/1M | $4/1M | $0.08/1M | $1.00/1M |

Most users save **80-90%** compared to non-cached API pricing.

### Subscription Value

See how much value you're getting from your subscription:

```
🎯 SUBSCRIPTION VALUE COMPARISON
────────────────────────────────────────
Claude Pro ($20/mo):
  API Value: $745.82 for $20/mo = 37.3x value ✨
```

The "API Value" is what your usage would cost at API rates (without caching). This shows the value of your subscription.

## Why Claude Hides This

Claude Code logs detailed token usage for every request but doesn't expose it in the UI. This data includes:
- Input/output token counts
- Cache hit/miss ratios (the big money saver)
- Which model handled each request
- Request IDs for debugging

Now you can see it all.

## License

MIT — do whatever you want with it.

---

*Built with Claude Code, tracking Claude Code* 🔄
