#!/bin/bash
# =========================================================================
# LongCat Audio Library — Start Automated Background Sync (macOS LaunchAgent)
# =========================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="${HOME}/Library/LaunchAgents/com.longcat.audio_watcher.plist"
LOG_FILE="${SCRIPT_DIR}/audio_watcher.log"

echo "====================================================================="
echo "⚡ LongCat Audio Library Auto-Sync — Starting Background Service..."
echo "====================================================================="

# Ensure LaunchAgents directory exists
mkdir -p "${HOME}/Library/LaunchAgents"

# Install / update plist
cat << 'EOF' > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.longcat.audio_watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Volumes/Partition 2/LongCat Video Avatar 1.5/audio_library_watcher.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Volumes/Partition 2/LongCat Video Avatar 1.5</string>
    <key>StandardOutPath</key>
    <string>/Volumes/Partition 2/LongCat Video Avatar 1.5/audio_watcher.log</string>
    <key>StandardErrorPath</key>
    <string>/Volumes/Partition 2/LongCat Video Avatar 1.5/audio_watcher_err.log</string>
</dict>
</plist>
EOF

# Unload previous instance if any
launchctl unload "$PLIST_FILE" 2>/dev/null
pkill -f "audio_library_watcher.py" 2>/dev/null
sleep 1

# Load and start via launchd
launchctl load -w "$PLIST_FILE"

sleep 1.5

if pgrep -f "audio_library_watcher.py" > /dev/null; then
    PID=$(pgrep -f "audio_library_watcher.py" | head -n 1)
    echo "✅ অটো-সিঙ্ক সার্ভিস সফলভাবে চালু হয়েছে (PID: $PID)!"
    echo "📂 মনিটরিং ফোল্ডার: ${SCRIPT_DIR}/audio_library/"
    echo "🛡️ সুবিধা:"
    echo "   ১. ম্যাকবুক শাটডাউন বা রিস্টার্ট দিলেও সার্ভিস স্বয়ংক্রিয়ভাবে চালু থাকবে।"
    echo "   ২. কোনো অডিও ফোল্ডারে রাখলেই সার্ভার অন থাকলে সঙ্গে সঙ্গে সিঙ্ক শুরু হবে।"
    echo "   ৩. মাঝপথে নেট বা ম্যাকবুক বন্ধ হলেও অগ্রগতি হারিয়ে যাবে না (রিস্যুমেবল সিঙ্ক)।"
    echo "📄 লগ দেখার নিয়ম: tail -f \"${LOG_FILE}\""
else
    echo "⚠️ সরাসরি ব্যাকগ্রাউন্ডে চালু করা হচ্ছে..."
    nohup /usr/bin/python3 "${SCRIPT_DIR}/audio_library_watcher.py" >> "$LOG_FILE" 2>&1 &
    sleep 1
    if pgrep -f "audio_library_watcher.py" > /dev/null; then
        echo "✅ ব্যাকগ্রাউন্ড ওয়াচার সফলভাবে চালু হয়েছে!"
    else
        echo "❌ চালু হতে সমস্যা হয়েছে। লগ পরীক্ষা করুন: ${LOG_FILE}"
    fi
fi
echo "====================================================================="
