#!/bin/bash

# Quick build test for AutoOstromag
echo "🔨 Testing build..."

cd "$(dirname "$0")"

if swift build; then
    echo "✅ Build successful!"
    echo ""
    echo "📝 Summary of changes:"
    echo "- Fixed await compilation error"
    echo "- Added parsing for health updates from various messages"
    echo "- Added parsing for energy updates and potions"
    echo "- Added level up detection"
    echo "- Added battle reward tracking"
    echo "- Added logging for state changes"
    echo "- Ignores 'not in battle' messages"
    echo ""
    echo "🆕 NEW: Action reporting to reporting channel:"
    echo "- Reports all player actions with current stats"
    echo "- Tracks battles, item findings, exploration events"
    echo "- Shows health/energy status and wait times"
    echo "- Logs level ups, damage taken, potions used"
    echo "- Includes player name and formatted status"
    echo ""
    echo "🆕 NEW: Technical action logging:"
    echo "- Bot startup with session name"
    echo "- Authentication success"
    echo "- Initial character status check"
    echo "- State changes (exploring → battle → waiting)"
    echo "- Energy restoration after waiting"
    echo "- Health recovery notifications"
    echo ""
    echo "🆕 NEW: Control commands:"
    echo "- /start - Start bot automation"
    echo "- /stop - Stop bot automation"
    echo "- /log all - Show all notifications (default)"
    echo "- /log important - Show only important actions"
    echo ""
    echo "🚀 Ready to run: ./starter.sh"
else
    echo "❌ Build failed!"
    exit 1
fi
