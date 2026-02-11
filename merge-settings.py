#!/usr/bin/env python3
"""
Safely merges cc-config activity logger hook into ~/.claude/settings.json
Preserves existing MCP servers, permissions, and other settings.
"""

import json
import os
import sys
from pathlib import Path

SETTINGS_FILE = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = str(Path.home() / "Desktop" / "cc-config" / "hooks" / "activity-logger.py")


def merge_hook_into_settings():
    """Add activity logger hook to settings.json, preserving existing config."""

    # Load existing settings or create new
    if SETTINGS_FILE.exists():
        print(f"📖 Reading existing settings from {SETTINGS_FILE}")
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)
    else:
        print(f"📝 Creating new settings file at {SETTINGS_FILE}")
        settings = {"model": "sonnet"}

    # Initialize hooks structure if needed
    if "hooks" not in settings:
        settings["hooks"] = {}

    if "PostToolUse" not in settings["hooks"]:
        settings["hooks"]["PostToolUse"] = []

    # Check if hook already exists
    existing_hooks = settings["hooks"]["PostToolUse"]
    hook_exists = False

    for hook_entry in existing_hooks:
        if isinstance(hook_entry, dict) and "hooks" in hook_entry:
            for hook in hook_entry["hooks"]:
                if isinstance(hook, dict) and hook.get("command") == HOOK_COMMAND:
                    hook_exists = True
                    break

    if hook_exists:
        print(f"✅ Activity logger hook already configured")
        return True

    # Add our hook
    hook_config = {
        "matcher": "*",
        "hooks": [{
            "type": "command",
            "command": HOOK_COMMAND
        }]
    }

    settings["hooks"]["PostToolUse"].append(hook_config)

    # Write back to file
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")  # Add trailing newline

    print(f"✅ Activity logger hook added to settings.json")
    return True


def main():
    try:
        merge_hook_into_settings()
        return 0
    except Exception as e:
        print(f"❌ Error merging settings: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
