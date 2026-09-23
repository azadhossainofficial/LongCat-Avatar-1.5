#!/bin/bash
# ========================================================
# Start Audio Library Background Watcher Daemon
# ========================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.audio_watcher.pid"
LOG_FILE="${SCRIPT_DIR}/audio_watcher.log"

if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if ps -p "$OLD_PID" > /dev/null 2>&1; then
    echo "⚡ Audio Library Watcher is ALREADY running (PID: $OLD_PID)."
    echo "📂 It is actively watching '${SCRIPT_DIR}/audio_library/'"
    exit 0
  fi
fi

echo "🚀 Starting LongCat Audio Library Auto-Watcher in background..."
nohup python3 "${SCRIPT_DIR}/audio_library_watcher.py" >> "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

sleep 1
if ps -p "$NEW_PID" > /dev/null 2>&1; then
  echo "✅ Auto-Watcher successfully started (PID: $NEW_PID)!"
  echo "📂 Monitoring folder: '${SCRIPT_DIR}/audio_library/'"
  echo "📄 Logs: '${LOG_FILE}'"
  echo "💡 যেকোনো অডিও ফাইল এই ফোল্ডারে পেস্ট করলেই তা স্বয়ংক্রিয়ভাবে ব্যাকগ্রাউন্ডে সার্ভারে সিঙ্ক হয়ে যাবে।"
else
  echo "❌ Failed to start watcher. Check logs at: ${LOG_FILE}"
  exit 1
fi
