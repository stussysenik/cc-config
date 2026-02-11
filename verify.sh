#!/bin/bash
# Verifies cc-config setup is working

echo "🔍 Checking cc-config setup..."
echo ""

# Check hook
if grep -q "activity-logger.py" ~/.claude/settings.json 2>/dev/null; then
  echo "✅ Activity logger hook: PRESENT"
else
  echo "❌ Activity logger hook: MISSING"
  echo "   Fix: Re-run 'nix develop' from cc-setup"
fi

# Check slash commands
CMD_COUNT=$(ls ~/.claude/commands/summary*.md 2>/dev/null | wc -l)
if [ "$CMD_COUNT" -eq 4 ]; then
  echo "✅ Slash commands: ALL 4 PRESENT"
else
  echo "⚠️  Slash commands: Only $CMD_COUNT/4 found"
  echo "   Fix: Run ~/Desktop/cc-config/install.sh"
fi

# Check today's log
TODAY=$(date +%Y-%m-%d)
if [ -f ~/Desktop/cc-config/logs/$TODAY.jsonl ]; then
  EVENTS=$(wc -l < ~/Desktop/cc-config/logs/$TODAY.jsonl)
  echo "✅ Today's log: $EVENTS events logged"
else
  echo "⚠️  Today's log: Not created yet (normal if you haven't used Claude today)"
fi

echo ""
echo "📊 Available summaries: /summary, /summary-pick, /summary-quick, /summary-history"
