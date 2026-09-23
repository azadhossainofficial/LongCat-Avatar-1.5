#!/bin/bash
# ========================================================
# Stop Audio Library Background Watcher Daemon
# ========================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.audio_watcher.pid"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if ps -p "$PID" > /dev/null 2>&1; then
    kill "$PID"
    echo "🛑 Stopped Audio Library Watcher (PID: $PID)."
  else
    echo "ℹ️  Watcher was not running."
  fi
  rm -f "$PID_FILE"
else
  pkill -f "audio_library_watcher.py" 2>/dev/null && echo "🛑 Stopped background watcher." || echo "ℹ️  No watcher process found."
fi
