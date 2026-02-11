Show all available Claude Code activity log dates and let the user choose which to view.

First, list available dates:
```bash
python3 ~/Desktop/cc-config/summary.py --list
```

Show the user the available dates and ask which date they'd like to see a detailed summary for.

When they provide a date, run:
```bash
python3 ~/Desktop/cc-config/summary.py --date YYYY-MM-DD --history
```

Replace YYYY-MM-DD with the user's chosen date.
