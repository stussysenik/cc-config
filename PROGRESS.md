# Progress Log

## 2026-02-11: Enhanced Stats & Cache Tracking

### Completed
- Added cache-aware pricing to cost calculations
  - Cache reads are 90% cheaper than input tokens
  - Cache writes are 25% more expensive
- Updated `calculate_cost()` to return actual cost, cost without cache, and savings
- Enhanced `/stats` command with:
  - Date range filtering (7d, 30d, last-month, this-month, custom)
  - Cache savings display
  - Subscription value comparison (Pro, Max 5x, Max 20x)
  - Token breakdown with cache read/write stats
  - Daily average for date ranges
- Updated `update_stats()` to track cache savings per date/model/project
- Reset and resynced all logs with new calculations

### Stats
- Total discovered: $7,766.91 actual cost
- Without caching: $45,758.96
- Cache savings: $37,992.02 (83%)
- Subscription value: 2,287x at $20/mo tier

## 2026-02-11: Native Log Sync v2

### Completed
- Created `sync-native-logs.py` to read Claude's native logs
- No hooks needed - reads directly from `~/.claude/projects/`
- Extracts hidden token usage and cost data
- Synced 23,189 events from 684 log files
- Recovered 2+ weeks of missed activity (Jan 27 - Feb 11)
- Added `/summary`, `/summary-quick`, `/summary-range`, `/stats` commands
- Created one-click installer (`install.sh`)

### Key Discovery
Claude logs detailed token usage for every request but hides it from users:
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

## Previous: Hook-Based Logger (Deprecated)

The previous approach used Claude Code hooks (`hooks/activity-logger.py`) which was fragile:
- Depended on `settings.json` configuration
- Settings got reset, breaking the logger silently
- Missed 2+ weeks of activity

The native log sync approach is more reliable and captures MORE data.
