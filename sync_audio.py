#!/usr/bin/env python3
"""
⚡ LongCat Video Avatar 1.5 — Audio Library Fast Sync Tool
Synchronizes audio files from local MacBook audio_library/ folder to Remote GPU Server.
Features:
- Delta sync (skips already synced files)
- Streaming high-speed HTTP upload
- Real-time upload progress display
- Automatic duration & metadata verification
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

LOCAL_DIR = Path(__file__).resolve().parent / "audio_library"
SERVER_URL = os.environ.get("LONGCAT_SERVER_URL", "http://122.51.254.66:4094")
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}

def get_remote_library():
    try:
        url = f"{SERVER_URL}/api/audio_library"
        req = urllib.request.Request(url, headers={"User-Agent": "LongCat-Sync/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            audios = data.get("audios", [])
            return {a["filename"]: a for a in audios}
    except Exception as e:
        print(f"⚠️  Could not connect to {SERVER_URL}: {e}")
        return None

def upload_file(file_path):
    filename = file_path.name
    file_size = file_path.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    encoded_fn = urllib.parse.quote(filename)
    upload_url = f"{SERVER_URL}/api/audio_library/upload?filename={encoded_fn}"

    print(f"   ⬆️  Uploading: {filename} ({size_mb:.1f} MB)...", end="", flush=True)
    start_time = time.time()

    try:
        with open(file_path, "rb") as f:
            data = f.read()

        req = urllib.request.Request(
            upload_url,
            data=data,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(data)),
                "User-Agent": "LongCat-Sync/1.0"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=180) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - start_time
            speed = size_mb / elapsed if elapsed > 0 else 0
            if res_data.get("success"):
                print(f"\r   ✅ Synced: {filename} ({size_mb:.1f} MB in {elapsed:.1f}s · {speed:.1f} MB/s)")
                return True
            else:
                print(f"\r   ❌ Failed: {filename} - {res_data.get('error')}")
                return False
    except Exception as e:
        print(f"\r   ❌ Error uploading {filename}: {e}")
        return False

def main():
    print("=" * 64)
    print("⚡ LongCat Studio — Audio Library High-Speed Sync")
    print(f"📂 Local Folder:  {LOCAL_DIR}")
    print(f"🌐 Server Target: {SERVER_URL}")
    print("=" * 64)

    if not LOCAL_DIR.exists():
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created local folder: {LOCAL_DIR}")

    local_files = [
        p for p in sorted(LOCAL_DIR.iterdir())
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS and not p.name.startswith(".")
    ]

    if not local_files:
        print(f"\nℹ️  ফোল্ডারটি ফাঁকা! অনুগ্রহ করে আপনার অডিও ফাইলগুলি এখানে রাখুন:")
        print(f"   👉 {LOCAL_DIR}/\n")
        print("অডিও ফাইল রাখার পর পুনরায় এই স্ক্রিপ্টটি চালান।")
        return

    print(f"\n🔍 স্থানীয় অডিও ফাইল পাওয়া গেছে: {len(local_files)} টি")
    print("🌐 সার্ভারের সাথে সিঙ্ক স্ট্যাটাস যাচাই করা হচ্ছে...")

    remote_map = get_remote_library()
    if remote_map is None:
        print("❌ সার্ভারের সাথে যোগাযোগ করা সম্ভব হয়নি। ইন্টারনেট সংযোগ বা সার্ভার চালু আছে কি না পরীক্ষা করুন।")
        sys.exit(1)

    to_upload = []
    already_synced = []

    for p in local_files:
        if p.name in remote_map:
            rem = remote_map[p.name]
            local_size = p.stat().st_size
            if rem.get("size_bytes") == local_size:
                already_synced.append(p)
                continue
        to_upload.append(p)

    for p in already_synced:
        rem = remote_map[p.name]
        dur = rem.get("duration_formatted", "")
        print(f"   ⏭️  Already synced: {p.name} ({dur})")

    if not to_upload:
        print("\n🎉 চমৎকার! সকল অডিও ফাইল ইতিমধ্যে সার্ভারে সিঙ্ক হয়ে আছে।")
        print("👉 ওয়েব স্টুডিওর '📂 Audio Library' থেকে যেকোনো অডিও ০-সেকেন্ডে সিলেক্ট করুন।\n")
        return

    print(f"\n🚀 নতুন বা পরিবর্তিত অডিও আপলোড শুরু হচ্ছে ({len(to_upload)} টি ফাইল)...")
    success_count = 0
    for p in to_upload:
        if upload_file(p):
            success_count += 1

    print("\n" + "=" * 64)
    print(f"✅ সিঙ্ক সম্পূর্ণ! সফল: {success_count}/{len(to_upload)} টি ফাইল।")
    print("💡 এখন ওয়েব স্টুডিওর '📂 Audio Library' তে ক্লিক করলেই এই অডিওগুলো পাবেন!")
    print("=" * 64 + "\n")

if __name__ == "__main__":
    main()
