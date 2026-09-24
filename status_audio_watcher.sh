#!/bin/bash
# =========================================================================
# LongCat Audio Library — Check Background Sync Status
# =========================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="${HOME}/Library/LaunchAgents/com.longcat.audio_watcher.plist"
LOG_FILE="${SCRIPT_DIR}/audio_watcher.log"

echo "====================================================================="
echo "📊 LongCat Audio Library Auto-Sync Status"
echo "====================================================================="

# 1. Check process
if pgrep -f "audio_library_watcher.py" > /dev/null; then
    PID=$(pgrep -f "audio_library_watcher.py" | head -n 1)
    echo "🟢 Service Status:    RUNNING (PID: $PID)"
else
    echo "🔴 Service Status:    STOPPED"
fi

# 2. Check LaunchAgent registration
if launchctl list | grep "com.longcat.audio_watcher" > /dev/null 2>&1; then
    echo "🛡️ Auto-Start (Boot): ENABLED (macOS LaunchAgent active)"
else
    echo "⚠️ Auto-Start (Boot): NOT REGISTERED (Run ./start_audio_watcher.sh to enable)"
fi

# 3. Check active rsync transfer
if pgrep -f "rsync.*audio_library" > /dev/null; then
    RSYNC_PID=$(pgrep -f "rsync.*audio_library" | head -n 1)
    echo "🚀 Active Transfer:   SYNCING NOW (PID: $RSYNC_PID)"
else
    echo "💤 Active Transfer:   IDLE (Waiting for new/modified files)"
fi

# 4. Check local audio library files
echo ""
echo "📂 Local Files in 'audio_library/':"
if [ -d "${SCRIPT_DIR}/audio_library" ]; then
    find "${SCRIPT_DIR}/audio_library" -maxdepth 1 -type f ! -name ".*" -exec ls -lh {} + | awk '{print "   • " $9 " (" $5 ")"}'
else
    echo "   (Folder not created yet)"
fi

# 5. Show recent logs
echo ""
echo "📄 Recent Activity (Last 10 Log Lines):"
echo "---------------------------------------------------------------------"
if [ -f "$LOG_FILE" ]; then
    tail -n 10 "$LOG_FILE"
else
    echo "   (No log file found)"
fi
echo "====================================================================="
