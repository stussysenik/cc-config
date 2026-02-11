Show all available Claude Code activity log dates with detailed stats and let the user choose which to view.

First, show the available dates with stats:
```bash
python3 ~/Desktop/cc-config/summary.py --pick-list
```

Display the list to the user and ask which date they'd like to see (they can give the number or the date).

When they choose, run the **compact view by default**:
```bash
python3 ~/Desktop/cc-config/summary.py --date YYYY-MM-DD --compact
```

If the user explicitly asks for "full" or "detailed" view, run without the --compact flag:
```bash
python3 ~/Desktop/cc-config/summary.py --date YYYY-MM-DD
```

Note: The default should be compact view for quicker scanning unless the user specifically requests full details.
