#!/usr/bin/env python3
"""
⚡ LongCat Video Avatar 1.5 — Automatic Audio Library Watcher Daemon (MacBook -> Remote GPU Server)
------------------------------------------------------------------------------------------------
Monitors local MacBook folder:
  📂 /Volumes/Partition 2/LongCat Video Avatar 1.5/audio_library/
and automatically synchronizes any audio files (.mp3, .wav, .m4a, .aac, .ogg, .flac)
to the remote GPU server over high-speed resumable rsync.

Features:
- Native macOS launchd persistence (runs automatically on MacBook boot, login, wake from sleep).
- Resumable transfers (--partial --inplace): If MacBook is closed or rebooted mid-transfer,
  progress is NOT lost; it automatically resumes exactly where it stopped!
- Health-checked: Waits patiently when the remote server is offline and resumes the moment it comes online.
- Bit-for-bit lossless binary sync with zero audio re-encoding.
- Automatic manifest update: Registers completed audios so Web UI marks them '✓ Uploaded' with 0s latency.
"""

import os
import sys
import time
import json
import socket
import signal
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

# Paths & Target Server Configuration
WORKSPACE_DIR = Path(__file__).resolve().parent
LOCAL_DIR = WORKSPACE_DIR / "audio_library"
LOG_FILE = WORKSPACE_DIR / "audio_watcher.log"

SERVER_HOST = os.environ.get("LONGCAT_SERVER_HOST", "122.51.254.66")
SERVER_SSH_PORT = int(os.environ.get("LONGCAT_SERVER_SSH_PORT", "4101"))
SERVER_HTTP_PORT = int(os.environ.get("LONGCAT_SERVER_PORT", "4094"))
REMOTE_DIR = "/workspace/LongCat-Video/audio_library"

AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
CHECK_INTERVAL_SEC = 5
OFFLINE_RETRY_SEC = 15

running = True

def handle_signal(sig, frame):
    global running
    log(f"🛑 Received signal {sig}. Gracefully shutting down audio watcher...")
    running = False

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def log(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)

def is_server_reachable():
    """Checks if the remote server SSH port is reachable within 4 seconds."""
    try:
        s = socket.create_connection((SERVER_HOST, SERVER_SSH_PORT), timeout=4)
        s.close()
        return True
    except Exception:
        return False

def sync_completed_manifest():
    """Updates completed_audios.json on remote server so Web UI recognizes uploaded files."""
    try:
        if not LOCAL_DIR.exists():
            return
        local_sizes = {
            p.name: p.stat().st_size
            for p in LOCAL_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in AUDIO_EXTS and not p.name.startswith(".")
        }
        if not local_sizes:
            return

        completed = {fn: True for fn in local_sizes.keys()}
        json_str = json.dumps(completed, indent=2)

        ssh_cmd = [
            "ssh", "-p", str(SERVER_SSH_PORT),
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=8",
            f"root@{SERVER_HOST}",
            f"cat << 'EOF' > {REMOTE_DIR}/completed_audios.json\n{json_str}\nEOF"
        ]
        subprocess.run(ssh_cmd, capture_output=True, timeout=12)

        # Notify HTTP API to refresh metadata cache if HTTP port is open
        try:
            req = urllib.request.Request(f"http://{SERVER_HOST}:{SERVER_HTTP_PORT}/api/audio_library", headers={"User-Agent": "LongCat-Watcher/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception:
            pass
    except Exception as e:
        log(f"⚠️ Warning updating remote manifest: {e}")

def run_resilient_rsync():
    """Executes rsync with keepalive, partial resume, and timeout safeguards."""
    ssh_opts = (
        f"ssh -p {SERVER_SSH_PORT} "
        "-o BatchMode=yes "
        "-o StrictHostKeyChecking=no "
        "-o ConnectTimeout=15 "
        "-o ServerAliveInterval=15 "
        "-o ServerAliveCountMax=6 "
        "-o TCPKeepAlive=yes "
        "-o IPQoS=throughput"
    )

    cmd = [
        "rsync",
        "-av",
        "--partial",
        "--inplace",
        "--timeout=120",
        "-e", ssh_opts,
        "--exclude=.DS_Store",
        "--exclude=.*",
        "--exclude=*.tmp",
        "--exclude=*.crdownload",
        f"{LOCAL_DIR}/",
        f"root@{SERVER_HOST}:{REMOTE_DIR}/"
    ]

    log("🚀 [AUTO-SYNC START] Syncing audio library to remote server via resilient rsync...")
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        elapsed = time.time() - t0
        if proc.returncode == 0:
            log(f"✅ [AUTO-SYNC DONE] Audio files successfully synchronized in {elapsed:.1f}s!")
            sync_completed_manifest()
            return True
        else:
            err_snippet = (proc.stderr or proc.stdout or "")[-300:].strip()
            log(f"⚠️ [AUTO-SYNC RETRY] rsync interrupted (code {proc.returncode}). Resuming partial transfer on next cycle...")
            return False
    except subprocess.TimeoutExpired:
        log("⚠️ [AUTO-SYNC TIMEOUT] rsync process timed out. Will resume on next cycle.")
        return False
    except Exception as e:
        log(f"❌ [AUTO-SYNC ERROR] rsync execution error: {e}")
        return False

def watch_loop():
    log("=" * 68)
    log("⚡ LongCat Audio Library Auto-Watcher DAEMON STARTED (Resilient Engine)")
    log(f"📂 Local Folder:  {LOCAL_DIR}")
    log(f"🌐 Server Target: root@{SERVER_HOST}:{REMOTE_DIR} (SSH Port: {SERVER_SSH_PORT})")
    log("🔄 Resumable:     Active (--partial --inplace)")
    log("=" * 68)

    if not LOCAL_DIR.exists():
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    file_stable_tracker = {}
    was_offline = False

    while running:
        try:
            if not LOCAL_DIR.exists():
                time.sleep(CHECK_INTERVAL_SEC)
                continue

            current_files = [
                p for p in LOCAL_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in AUDIO_EXTS and not p.name.startswith(".")
            ]

            if not current_files:
                time.sleep(CHECK_INTERVAL_SEC)
                continue

            # Verify file stability (avoid uploading while user is still copying or saving)
            stable_files = []
            for p in current_files:
                fn = p.name
                sz = p.stat().st_size
                if sz == 0:
                    continue
                if fn not in file_stable_tracker:
                    file_stable_tracker[fn] = (sz, time.time())
                    continue
                prev_sz, first_seen = file_stable_tracker[fn]
                if sz != prev_sz:
                    file_stable_tracker[fn] = (sz, time.time())
                    continue
                if time.time() - first_seen >= 2.0:
                    stable_files.append(p)

            if not stable_files:
                time.sleep(CHECK_INTERVAL_SEC)
                continue

            # Check if server is online before attempting sync
            if not is_server_reachable():
                if not was_offline:
                    log(f"⏳ Remote GPU server ({SERVER_HOST}:{SERVER_SSH_PORT}) is currently OFFLINE or unreachable.")
                    log("   The watcher is standing by and will automatically resume sync the moment the server turns on.")
                    was_offline = True
                time.sleep(OFFLINE_RETRY_SEC)
                continue

            if was_offline:
                log(f"🌐 Remote GPU server ({SERVER_HOST}) is now ONLINE! Resuming automatic sync...")
                was_offline = False

            # Run resilient rsync
            run_resilient_rsync()

            # Wait before next inspection cycle
            time.sleep(CHECK_INTERVAL_SEC)

        except Exception as e:
            log(f"⚠️ Watcher loop exception: {e}")
            time.sleep(CHECK_INTERVAL_SEC)

    log("🛑 Audio Library Auto-Watcher stopped.")

if __name__ == "__main__":
    watch_loop()
