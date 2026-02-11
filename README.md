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
| `/summary` | Today's engineering journal + costs |
| `/summary-quick` | Compact quick-glance view |
| `/summary-range 7d` | Last 7 days with period costs |
| `/summary-range 30d` | Last 30 days |
| `/summary-range last-month` | Previous month |
| `/summary-pick` | Browse all available dates |
| `/stats` | Full token/cost breakdown |

## Sample Output

### `/summary`
```
📊 Wed Feb 11 — 1 project(s) | 22 created | 10 modified | 0 tasks

  📁 hype-commerce-swiss-tool [20:18:40→22:12:51]: 22 files

────────────────────────────────────────────────────────────
💰 Usage Statistics
────────────────────────────────────────────────────────────
  Today: $0.29 (824 requests)
  Total: $114.92 | 9,357,862 tokens
  Models: opus: $102.20 | haiku: $10.28 | sonnet: $2.45
  Recent: 02-11: $0.29 | 02-10: $2.58 | 02-08: $0.19
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
📊 Claude Code Usage Statistics
==================================================

💰 Total Cost: $114.90
📝 Total Tokens: 9,357,145
   Input:  8,613,301
   Output: 743,844
   Cache:  3,671,035,677 read / 272,818,421 write

📈 By Model:
   opus: $102.18 (35152 requests)
   haiku: $10.28 (7562 requests)
   sonnet: $2.45 (4886 requests)

📁 Top Projects by Cost:
   mymind-clone-web: $23.38
   v0-clone: $20.35
   clean-writer: $17.65
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
# Today's journal
python3 ~/Desktop/cc-config/summary.py

# Compact view
python3 ~/Desktop/cc-config/summary.py --compact

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

## Why Claude Hides This

Claude Code logs detailed token usage for every request but doesn't expose it in the UI. This data includes:
- Input/output token counts
- Cache hit/miss ratios
- Which model handled each request
- Request IDs for debugging

Now you can see it all.

## License

MIT — do whatever you want with it.

---

*Built with Claude Code, tracking Claude Code* 🔄
