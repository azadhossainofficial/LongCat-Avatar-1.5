#!/bin/bash
# =========================================================================
# LongCat Audio Library — Stop Automated Background Sync
# =========================================================================

PLIST_FILE="${HOME}/Library/LaunchAgents/com.longcat.audio_watcher.plist"

echo "🛑 Stopping LongCat Audio Library Auto-Sync Service..."

if [ -f "$PLIST_FILE" ]; then
    launchctl unload -w "$PLIST_FILE" 2>/dev/null
fi

pkill -f "audio_library_watcher.py" 2>/dev/null
pkill -f "rsync.*audio_library" 2>/dev/null

sleep 1

if ! pgrep -f "audio_library_watcher.py" > /dev/null; then
    echo "✅ অটো-সিঙ্ক সার্ভিস সফলভাবে বন্ধ করা হয়েছে।"
else
    pkill -9 -f "audio_library_watcher.py" 2>/dev/null
    echo "✅ ফোর্স স্টপ সম্পন্ন হয়েছে।"
fi
