#!/bin/bash
#
# Claude Code Config Installer
# Sets up /summary commands and syncs activity logs
#
# Usage (one-liner):
#   bash <(curl -fsSL https://raw.githubusercontent.com/stussysenik/cc-config/main/install.sh)
#
# Or after cloning:
#   cd ~/Desktop/cc-config && ./install.sh
#

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║              🚀 Claude Code Config Installer                   ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Determine install location
CC_CONFIG_DIR="$HOME/Desktop/cc-config"

# Clone if running from curl (not already in repo)
if [ ! -f "./sync-native-logs.py" ]; then
    if [ ! -d "$CC_CONFIG_DIR" ]; then
        echo "📦 Cloning cc-config..."
        git clone https://github.com/stussysenik/cc-config.git "$CC_CONFIG_DIR"
    else
        echo "📦 Updating cc-config..."
        cd "$CC_CONFIG_DIR" && git pull --ff-only || true
    fi
    cd "$CC_CONFIG_DIR"
else
    CC_CONFIG_DIR="$(pwd)"
fi

echo ""

# 1. Install slash commands
echo "📝 Installing slash commands to ~/.claude/commands/..."
COMMANDS_DIR="$HOME/.claude/commands"
mkdir -p "$COMMANDS_DIR"

for cmd in "$CC_CONFIG_DIR/commands/"*.md; do
    if [ -f "$cmd" ]; then
        name=$(basename "$cmd" .md)
        cp "$cmd" "$COMMANDS_DIR/"
        echo "   ✓ /$name"
    fi
done

echo ""

# 2. Sync native logs (no hooks needed!)
echo "🔄 Syncing Claude Code activity logs..."
echo "   (This reads directly from ~/.claude/projects/ - no hooks needed)"
echo ""

python3 "$CC_CONFIG_DIR/sync-native-logs.py" --reset

echo ""

# 3. Show usage stats
echo "📊 Your Claude Code usage:"
python3 "$CC_CONFIG_DIR/sync-native-logs.py" --stats

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ Installation Complete!                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "💡 Available slash commands:"
echo ""
echo "   /summary            Today's engineering journal + costs"
echo "   /summary-quick      Compact quick-glance view"
echo "   /summary-range 7d   Last 7 days with period costs"
echo "   /summary-range 30d  Last 30 days"
echo "   /summary-pick       Browse all available dates"
echo "   /summary-history    View historical summaries"
echo "   /stats              Token usage & cost breakdown"
echo ""
echo "🔄 To update logs anytime:"
echo "   python3 $CC_CONFIG_DIR/sync-native-logs.py"
echo ""
echo "💰 Your token usage is extracted from Claude's hidden logs!"
echo "   Claude tracks everything but doesn't show you - now you can see it."
echo ""
