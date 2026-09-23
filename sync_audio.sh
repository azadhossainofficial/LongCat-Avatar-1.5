#!/bin/bash
# ========================================================
# LongCat Audio Library Sync Launcher (MacBook -> Remote GPU Server)
# ========================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 &>/dev/null; then
  python3 sync_audio.py "$@"
else
  echo "❌ Error: python3 not found. Please install Python 3 on your MacBook."
  exit 1
fi
