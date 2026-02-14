# Progress Log

## 2026-02-14: Dev-First Journal Redesign

### Problem
The default `/summary` output was ~250 lines for a heavy day — ASCII art banner, box-drawn sections, full file lists, full task lists, academic "Engineering Principles" explanations, and "Friction & Slumps" framing. Too verbose for a quick end-of-day scan.

### Solution
New default journal mode (~45 lines) focused on product value, dev happiness, and DX:
- **One-line header**: date, duration, projects, cost
- **SHIPPED section**: product descriptions per project (smart task-name cleaning strips procedural prefixes, falls through to deliverable groups when tasks are too granular)
- **VIBES section**: energy bar, focus level, highlight, method keywords, cost
- **WEEK chart**: slim bars + streak, no box header
- **Project ranking**: top 4 expanded, rest collapsed into one line

### New functions
- `render_journal()` — new default renderer
- `generate_product_description()` — turns tasks/deliverables into prose
- `compute_vibes()` — energy, focus, highlight, method, cost analysis
- `rank_projects()` — substance scoring and expand/collapse
- `generate_metrics_line()` — compact per-project metrics
- `render_week_slim()` — slim week chart without box header
- `_clean_task_name()` — strips Implement/Create/Verify prefixes, task number suffixes
- `_truncate_word()` — word-boundary-aware truncation

### Old output preserved
- `render_engineering_summary()` renamed to `render_full_summary()`
- Available via `--full` flag
- All existing modes (--compact, --range, --prompt, --pick) unchanged

## 2026-02-14: Narrative Journal + Prompt Analytics + Engineering Principles

### Narrative Engine
- Rewrote `analyze_events()` to handle all sync script action types (user_prompt, task_planned, task_completed, command, research, web_research, delegated)
- Added `extract_intent()` — extracts first meaningful user prompt, strips file paths
- Added `group_deliverables()` — groups files by purpose (FX Chain presets, Test suites, API layer, Storybook setup, etc.) with temp file filtering and deduplication
- Added `detect_patterns()` — TDD, spec-driven, research-heavy, safety-first, parallel work
- Rewrote `render_project_summary()` — intent quotes, grouped deliverables, task completion story, engineering pattern badges
- Rewrote `render_day_narrative()` — "TODAY'S SESSION" with THE ARC timeline

### Prompt Analytics
- Added `analyze_top_prompts()` — scores by files×3 + tasks×5 + commands + delegated×4
- Added `render_top_prompts()` — leaderboard with keyword extraction and prompt style detection
- Added `render_prompt_detail()` — `--prompt N` flag for full text, impact breakdown, keywords, stats
- Most expensive prompt callout with comparison to average

### Session Insights
- Added `analyze_slumps()` — zero-output prompts categorized (exploration/setup/other)
- Added `analyze_time_gaps()` — biggest pauses between events
- Added `extract_engineering_concepts()` — auto-extracts up to 5 principles:
  - Parallel Agent Delegation, Research-First Development, Structured Task Decomposition
  - Version Control Discipline, Tight Test Feedback Loops, Spec-Driven Development, Iterative Refinement
- Each principle rendered as: PRINCIPLE → TODAY (concrete example) → EXTEND (generalization)

### Key Design Decisions
- Pure Python heuristics, no LLM/DSPy — deterministic, fast, zero cost
- Interesting deliverable groups sort first, generic (Documentation, Configuration, Code) last
- Spec-driven detection restricted to `.md` files only (not `.spec.js` test files)
- Safety pattern restricted to actual safety tooling files/commands only

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
