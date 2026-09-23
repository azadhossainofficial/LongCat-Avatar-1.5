#!/usr/bin/env python3
"""
LongCat Video Avatar 1.5 - Automatic Background Output Downloader / Sync
------------------------------------------------------------------------
Watches Server 2 for completed 1080P videos and automatically downloads
them into your local `/outputs` directory at high multi-stream speed!
"""

import os
import sys
import time
import json
import urllib.parse
import urllib.request
import urllib.error
import threading
import concurrent.futures
from pathlib import Path

# Configuration
SERVER_HOST = "175.155.64.164"
SERVER_PORT = "19757"
SERVER_TOKEN = "10ae61f5b98d35e3547d5082aabb02bec2af1aa17cd2c299e397826835d29720"
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
LOCAL_OUTPUTS_DIR = Path(__file__).resolve().parent / "outputs"
PARALLEL_THREADS = 20
CHUNK_SIZE_MB = 10
CHECK_INTERVAL_SEC = 10


def format_bytes(b):
    if b >= 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024 * 1024):.2f} GB"
    elif b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.2f} MB"
    elif b >= 1024:
        return f"{b / 1024:.2f} KB"
    return f"{b} B"


def fetch_server_gallery():
    url = f"{BASE_URL}/api/gallery?token={SERVER_TOKEN}"
    req = urllib.request.Request(url, headers={"User-Agent": "LongCat-AutoSync/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                return data.get("videos", [])
    except Exception as e:
        print(f"[AutoSync] Warning: Failed to query server gallery: {e}", flush=True)
    return []


def download_video_multithreaded(video_meta):
    filename = video_meta.get("filename")
    if not filename or not filename.endswith(".mp4") or "_720p.mp4" in filename:
        return False

    LOCAL_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    dest_file = LOCAL_OUTPUTS_DIR / filename
    part_file = LOCAL_OUTPUTS_DIR / f"{filename}.part"

    quoted_fn = urllib.parse.quote(filename)
    video_url = f"{BASE_URL}/outputs/{quoted_fn}?token={SERVER_TOKEN}"

    # Get exact file size
    head_req = urllib.request.Request(video_url, method="HEAD", headers={"User-Agent": "LongCat-AutoSync/1.0"})
    try:
        with urllib.request.urlopen(head_req, timeout=10) as r:
            total_size = int(r.headers.get("Content-Length", 0))
    except Exception as e:
        print(f"[AutoSync] Error probing file size for {filename}: {e}", flush=True)
        return False

    if total_size == 0:
        return False

    # Check if already fully downloaded
    if dest_file.exists() and dest_file.stat().st_size == total_size:
        return False

    print(f"\n==================================================", flush=True)
    print(f"🚀 [Auto-Download] Starting: {filename}", flush=True)
    print(f"📦 Total Size: {format_bytes(total_size)} | Parallel Streams: {PARALLEL_THREADS}", flush=True)
    print(f"📂 Destination: {dest_file}", flush=True)
    print(f"==================================================", flush=True)

    # Pre-allocate part file
    with open(part_file, "wb") as f:
        f.truncate(total_size)

    chunk_bytes = max(2 * 1024 * 1024, CHUNK_SIZE_MB * 1024 * 1024)
    ranges = []
    offset = 0
    while offset < total_size:
        end = min(total_size - 1, offset + chunk_bytes - 1)
        ranges.append((offset, end))
        offset = end + 1

    start_time = time.time()
    downloaded_lock = threading.Lock()
    downloaded_bytes = 0
    file_lock = threading.Lock()

    def fetch_worker(r_range):
        nonlocal downloaded_bytes
        s, e = r_range
        cur_pos = s
        max_retries = 5

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(video_url, headers={
                    "Range": f"bytes={cur_pos}-{e}",
                    "User-Agent": "LongCat-AutoSync/1.0"
                })
                with urllib.request.urlopen(req, timeout=45) as resp:
                    while cur_pos <= e:
                        buf = resp.read(256 * 1024)
                        if not buf:
                            break
                        with file_lock:
                            with open(part_file, "r+b") as pf:
                                pf.seek(cur_pos)
                                pf.write(buf)
                        cur_pos += len(buf)
                        with downloaded_lock:
                            downloaded_bytes += len(buf)
                            elapsed = max(0.1, time.time() - start_time)
                            speed = (downloaded_bytes / (1024 * 1024)) / elapsed
                            pct = min(100.0, (downloaded_bytes / total_size) * 100)
                            sys.stdout.write(f"\r⚡ Progress: {pct:.1f}% ({format_bytes(downloaded_bytes)}/{format_bytes(total_size)}) @ {speed:.2f} MB/s ")
                            sys.stdout.flush()

                if cur_pos > e:
                    return  # Chunk completed successfully
            except Exception as ex:
                if attempt == max_retries - 1:
                    raise ex
                time.sleep(1 + attempt)

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_THREADS) as executor:
            list(executor.map(fetch_worker, ranges))

        # Atomic finalize
        if dest_file.exists():
            dest_file.unlink()
        part_file.rename(dest_file)

        total_elapsed = max(0.1, time.time() - start_time)
        avg_speed = (total_size / (1024 * 1024)) / total_elapsed
        print(f"\n✅ [Done!] Successfully saved to {dest_file.name}", flush=True)
        print(f"⏱️ Time Taken: {total_elapsed:.1f}s | Avg Speed: {avg_speed:.2f} MB/s\n", flush=True)
        return True

    except Exception as e:
        print(f"\n❌ Error during auto-download of {filename}: {e}", flush=True)
        return False


def run_sync_loop(once=False):
    print("==========================================================", flush=True)
    print("✨ LongCat Video Avatar 1.5 - Local Auto-Sync Daemon", flush=True)
    print(f"🎯 Target Server: {BASE_URL}", flush=True)
    print(f"📁 Local Outputs: {LOCAL_OUTPUTS_DIR}", flush=True)
    print("==========================================================", flush=True)

    LOCAL_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            videos = fetch_server_gallery()
            for v in videos:
                filename = v.get("filename")
                if not filename or "_720p.mp4" in filename:
                    continue
                dest = LOCAL_OUTPUTS_DIR / filename
                if not dest.exists():
                    download_video_multithreaded(v)
        except KeyboardInterrupt:
            print("\n[AutoSync] Exiting...", flush=True)
            break
        except Exception as e:
            print(f"[AutoSync] Error: {e}", flush=True)

        if once:
            break
        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    is_once = "--once" in sys.argv
    run_sync_loop(once=is_once)
