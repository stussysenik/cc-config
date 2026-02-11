#!/bin/bash
set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║                   🚀 cc-config Installation                    ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

CC_CONFIG_DIR="$HOME/Desktop/cc-config"

# 1. Install slash commands
echo "📝 Installing slash commands..."
COMMANDS_DIR="$HOME/.claude/commands"
mkdir -p "$COMMANDS_DIR"

cp "$CC_CONFIG_DIR/commands/"*.md "$COMMANDS_DIR/"
echo "✅ Slash commands installed: /summary, /summary-pick, /summary-range, /summary-quick, /summary-history"
echo ""

# 2. Install activity logger hook
echo "🔧 Installing activity logger hook..."
python3 "$CC_CONFIG_DIR/merge-settings.py"
echo ""

# 3. Run backfill if needed
if [ -f "$HOME/.claude/history.jsonl" ]; then
    LOG_COUNT=$(ls "$CC_CONFIG_DIR/logs/"*.jsonl 2>/dev/null | wc -l | tr -d ' ')

    if [ "$LOG_COUNT" -lt 5 ]; then
        echo "📚 Backfilling history from ~/.claude/history.jsonl..."
        echo ""
        python3 "$CC_CONFIG_DIR/backfill-history.py"
        echo ""
    else
        echo "✅ Log files already populated ($LOG_COUNT files)"
        echo ""
    fi
else
    echo "⚠️  No ~/.claude/history.jsonl found - skipping backfill"
    echo "   Logs will be created as you use Claude Code"
    echo ""
fi

# 4. Verification
echo "🔍 Verifying installation..."
echo ""

# Check slash commands
CMD_COUNT=$(ls "$COMMANDS_DIR/summary"*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$CMD_COUNT" -ge 4 ]; then
    echo "✅ Slash commands: $CMD_COUNT installed"
else
    echo "⚠️  Only $CMD_COUNT slash commands found (expected 5+)"
fi

# Check hook
if grep -q "activity-logger" "$HOME/.claude/settings.json" 2>/dev/null; then
    echo "✅ Activity logger hook: configured"
else
    echo "⚠️  Activity logger hook: not found in settings.json"
fi

# Check logs
LOG_COUNT=$(ls "$CC_CONFIG_DIR/logs/"*.jsonl 2>/dev/null | wc -l | tr -d ' ')
echo "✅ Log files: $LOG_COUNT days of history"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ Installation Complete!                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "💡 Try these commands in any Claude Code session:"
echo ""
echo "   /summary          - Today's work"
echo "   /summary-pick     - Browse all $LOG_COUNT days"
echo "   /summary-range    - View date ranges (e.g. 'last week')"
echo "   /summary-quick    - Quick glance at today"
echo ""
echo "🎉 cc-config is now active globally for all projects!"
echo ""
