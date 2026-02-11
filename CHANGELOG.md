# Changelog

## v2.0.0 - Complete History & Zero-Setup (2026-01-17)

### 🎉 Major Features

#### Complete History Access
- **Automatic backfill** from `~/.claude/history.jsonl` giving instant access to all past work
- Converted 4,014 history entries into **38 days of browsable logs** (Oct 2025 → Jan 2026)
- Session-based logs for historical dates show projects and prompts
- Detailed logs for current activity show file edits, commands, tests

#### Date Range Summaries
- **New `/summary-range` command** - Analyze work across time periods
- Relative ranges: `7d`, `this-week`, `last-week`, `this-month`, `last-month`
- Specific date ranges: `2025-12-01 to 2025-12-31`
- Shows aggregated stats, per-project breakdowns, daily activity charts

#### Zero-Setup Installation
- **One-command install** - `~/Desktop/cc-config/install.sh` sets up everything
- Safely merges hook into `~/.claude/settings.json` (preserves MCP servers/permissions)
- Works automatically in **any Claude Code session, any project**
- No per-project configuration needed

### ✨ Enhancements

#### Enhanced Date Picker
- `/summary-pick` now shows **all 38 days** of history (not just recent days)
- **Compact view by default** for quicker scanning
- Shows stats for each date (projects, files created/modified, tasks)

#### Improved Rendering
- Backfilled dates labeled with "(from session history)"
- Session activity displayed as prompts (not missing data)
- Graceful handling of mixed detailed/backfilled data
- Better project categorization

### 🛠️ New Components

#### Scripts
- `backfill-history.py` - Converts history.jsonl to daily logs
- `merge-settings.py` - Safely merges hook into settings.json without clobbering

#### Slash Commands
- `/summary-range` - NEW: Date range summaries

#### Updated Commands
- `/summary-pick` - Enhanced to show all history, defaults to compact view

### 📊 Statistics

From the backfill:
- **4,014 entries** processed from history.jsonl
- **38 days** of activity spanning Oct 1, 2025 → Jan 17, 2026
- **36 new log files** created (preserving 2 existing detailed logs)
- **Zero data loss** - all historical context preserved

### 🔧 Technical Improvements

- Smart date range parsing with relative and absolute formats
- Event analysis handles both backfilled and detailed log formats
- Daily breakdown charts for range summaries
- Preserves existing settings.json structure (MCP servers, permissions, etc.)

### 📝 Documentation

- Comprehensive README updates
- Installation guide with backfill explanation
- Usage examples for all new features
- Clear distinction between backfilled vs. detailed logs

---

## v1.0.0 - Initial Release

- Activity logger hook for real-time tracking
- Daily engineering journal summaries
- Slash commands: `/summary`, `/summary-pick`, `/summary-quick`, `/summary-history`
- Per-project breakdowns
- Weekly activity visualization
- Task completion tracking
