#!/usr/bin/env python3
"""
⚡ LongCat Video Avatar 1.5 — Automatic Audio Library Watcher Daemon
Automatically detects when you drop or save any audio file into:
  📂 /Volumes/Partition 2/LongCat Video Avatar 1.5/audio_library/
and uploads it to the remote GPU server in the background.

Guarantees:
1. 100% Genuine Raw Audio (Bit-for-bit identical binary copy, NO re-encoding, NO compression).
2. Smart Copy Detection (Waits until file copy finishes before uploading).
3. Delta Sync (Skips already synced files).
4. Auto-reconnect & Persistent background execution.
"""

import os
import sys
import time
import json
import socket
import urllib.parse
import urllib.request
from pathlib import Path

LOCAL_DIR = Path(__file__).resolve().parent / "audio_library"
SERVER_HOST = os.environ.get("LONGCAT_SERVER_HOST", "122.51.254.66")
SERVER_PORT = int(os.environ.get("LONGCAT_SERVER_PORT", "4094"))
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
LOG_FILE = Path(__file__).resolve().parent / "audio_watcher.log"

def log(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {msg}", flush=True)

def get_remote_library():
    try:
        url = f"http://{SERVER_HOST}:{SERVER_PORT}/api/audio_library"
        req = urllib.request.Request(url, headers={"User-Agent": "LongCat-Watcher/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            audios = data.get("audios", [])
            rem_map = {a["filename"]: a for a in audios}
            sync_completed_manifest(rem_map)
            return rem_map
    except Exception as e:
        log(f"⚠️ Remote check warning: {e}")
        return None

def sync_completed_manifest(remote_map):
    """Checks which remote files have 100% exact byte size matching local, and writes completed_audios.json."""
    try:
        if not LOCAL_DIR.exists() or not remote_map:
            return
        import subprocess
        local_sizes = {p.name: p.stat().st_size for p in LOCAL_DIR.iterdir() if p.is_file() and not p.name.startswith(".")}
        completed = {}
        for fn, r_item in remote_map.items():
            loc_size = local_sizes.get(fn)
            if loc_size is not None and r_item.get("size_bytes") == loc_size:
                completed[fn] = True
        
        json_str = json.dumps(completed, indent=2)
        cmd = [
            "ssh", "-p", "4101", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
            f"root@{SERVER_HOST}",
            f"cat << 'EOF' > /workspace/LongCat-Video/audio_library/completed_audios.json\n{json_str}\nEOF"
        ]
        subprocess.run(cmd, capture_output=True, timeout=8)
    except Exception:
        pass

def upload_raw_binary(file_path):
    """Streams exact raw bytes to server with per-chunk timeout. 100% lossless 1:1 binary transfer."""
    filename = file_path.name
    file_size = file_path.stat().st_size
    size_mb = file_size / (1024 * 1024)

    log(f"🚀 [AUTO-SYNC START] '{filename}' ({size_mb:.2f} MB) -> GPU Server")
    t0 = time.time()

    try:
        s = socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=20)
        s.settimeout(60)  # 60s per chunk

        encoded_fn = urllib.parse.quote(filename)
        headers = (
            f"POST /api/audio_library/upload?filename={encoded_fn} HTTP/1.1\r\n"
            f"Host: {SERVER_HOST}:{SERVER_PORT}\r\n"
            f"Content-Length: {file_size}\r\n"
            f"Content-Type: application/octet-stream\r\n"
            f"Connection: close\r\n\r\n"
        ).encode("utf-8")

        s.sendall(headers)

        sent = 0
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(32768)
                if not chunk:
                    break
                s.sendall(chunk)
                sent += len(chunk)

        # Read HTTP response
        resp = b""
        while True:
            try:
                data = s.recv(4096)
                if not data:
                    break
                resp += data
            except Exception:
                break
        s.close()

        resp_str = resp.decode("utf-8", errors="ignore")
        if "HTTP/1.1 200 OK" in resp_str or '"success": true' in resp_str or '"success":true' in resp_str:
            elapsed = time.time() - t0
            speed = size_mb / elapsed if elapsed > 0 else 0
            log(f"✅ [AUTO-SYNC DONE] '{filename}' (100% Raw Binary · {size_mb:.2f} MB in {elapsed:.1f}s · {speed:.2f} MB/s)")
            return True
        else:
            log(f"❌ [AUTO-SYNC FAIL] Server response: {resp_str[:200]}")
            return False
    except Exception as e:
        log(f"❌ [AUTO-SYNC ERROR] Failed to upload '{filename}': {e}")
        return False

def watch_loop():
    log("=" * 64)
    log("⚡ LongCat Audio Library Auto-Watcher DAEMON STARTED")
    log(f"📂 Monitoring Folder: {LOCAL_DIR}")
    log(f"🌐 Server Target:     http://{SERVER_HOST}:{SERVER_PORT}")
    log("=" * 64)

    if not LOCAL_DIR.exists():
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    file_stable_tracker = {}  # {filename: (size, first_seen_time)}
    currently_uploading = set()

    while True:
        try:
            if not LOCAL_DIR.exists():
                time.sleep(3)
                continue

            current_files = [
                p for p in LOCAL_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in AUDIO_EXTS and not p.name.startswith(".")
            ]

            if current_files:
                remote_map = get_remote_library()
                if remote_map is not None:
                    for p in current_files:
                        fn = p.name
                        if fn in currently_uploading:
                            continue

                        current_size = p.stat().st_size
                        if current_size == 0:
                            continue

                        # Check stability (ensure copy/download is finished)
                        if fn not in file_stable_tracker:
                            file_stable_tracker[fn] = (current_size, time.time())
                            continue

                        prev_size, first_seen = file_stable_tracker[fn]
                        if current_size != prev_size:
                            # File still growing
                            file_stable_tracker[fn] = (current_size, time.time())
                            continue

                        # Wait at least 2 seconds of stable size
                        if time.time() - first_seen < 2.0:
                            continue

                        # Check if remote already has identical exact size
                        if fn in remote_map:
                            rem_bytes = remote_map[fn].get("size_bytes", 0)
                            if rem_bytes == current_size:
                                continue

                        # Trigger auto upload
                        currently_uploading.add(fn)
                        try:
                            success = upload_raw_binary(p)
                            if success:
                                file_stable_tracker[fn] = (current_size, time.time())
                        finally:
                            currently_uploading.discard(fn)

            time.sleep(2)
        except KeyboardInterrupt:
            log("🛑 Watcher stopped by user.")
            break
        except Exception as e:
            log(f"⚠️ Watcher loop error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    watch_loop()
