View Claude Code work summaries across a date range.

Usage examples:
1. Specific date range: "Dec 1 to Dec 15" or "2025-12-01 to 2025-12-15"
2. Relative ranges: "last 7 days", "this week", "last month"
3. Natural language: "past week", "last 2 weeks"

The assistant will:
1. Parse the date range from your request
2. Run the appropriate command:
   - For relative ranges: `python3 ~/Desktop/cc-config/summary.py --range-relative RANGE`
     - Examples: `7d`, `this-week`, `last-month`
   - For specific dates: `python3 ~/Desktop/cc-config/summary.py --range START END`
     - Format: YYYY-MM-DD YYYY-MM-DD
3. Display aggregated work summary across those dates

Common relative ranges:
- `7d` - Last 7 days
- `this-week` - This week (Mon-Sun)
- `last-week` - Last week
- `this-month` - This month
- `last-month` - Last month

The summary will show:
- Total projects worked on
- Days active in the range
- Per-project breakdowns
- Daily activity chart
