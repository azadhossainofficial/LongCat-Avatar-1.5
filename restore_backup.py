#!/usr/bin/env python3
"""
LongCat Video Avatar 1.5 - Instant 1-Click Restore Tool
Usage:
  python3 restore_backup.py             # Restores the latest available backup
  python3 restore_backup.py --list      # Lists all available backups by date
  python3 restore_backup.py YYYY-MM-DD  # Restores a specific day's backup
"""

import os
import sys
import tarfile
import json
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
BACKUP_ROOT = WORKSPACE_ROOT / "backups"
INDEX_FILE = BACKUP_ROOT / "backup_index.json"

def get_backups():
    if not INDEX_FILE.exists():
        return []
    try:
        with open(INDEX_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def list_backups():
    backups = get_backups()
    if not backups:
        print("❌ No backups recorded in backup_index.json yet.")
        return
    print("\n📅 Available LongCat Video Avatar Backups:")
    print("-" * 75)
    print(f"{'No.':<4} {'Date & Time':<22} {'Year/Month':<20} {'Size':<10} {'Archive File'}")
    print("-" * 75)
    for idx, b in enumerate(backups, 1):
        ym = f"{b.get('year', '')}/{b.get('month', '')}"
        created = b.get('created_at', b.get('timestamp', ''))
        size = f"{b.get('archive_size_mb', 0)} MB"
        arch = Path(b.get('archive_path', '')).name
        print(f"[{idx:<2}] {created:<22} {ym:<20} {size:<10} {arch}")
    print("-" * 75)

def restore_backup(target_archive_path: Path):
    if not target_archive_path.exists():
        print(f"❌ Backup archive not found: {target_archive_path}")
        return False
        
    print(f"\n🔄 Restoring LongCat Video Avatar from: {target_archive_path}")
    print("   Extracting to:", WORKSPACE_ROOT)
    
    with tarfile.open(target_archive_path, "r:gz") as tar:
        tar.extractall(path=WORKSPACE_ROOT)
        
    print("✅ Restore completed successfully! All code and studio files restored.")
    return True

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--list", "-l", "list"):
        list_backups()
        return

    backups = get_backups()
    if not backups:
        # Check if legacy backup exists
        legacy_tar = BACKUP_ROOT / "backup_stable_state_20260828_205208.tar.gz"
        if legacy_tar.exists():
            restore_backup(legacy_tar)
            return
        print("❌ No backups found to restore.")
        return

    target_b = None
    if len(sys.argv) > 1:
        query = sys.argv[1]
        for b in reversed(backups):
            if query in b.get('date', '') or query in b.get('timestamp', '') or query in b.get('archive_path', ''):
                target_b = b
                break
        if not target_b:
            print(f"❌ Could not find a backup matching '{query}'. Run with --list to see all available dates.")
            return
    else:
        target_b = backups[-1] # latest

    archive_full_path = WORKSPACE_ROOT / target_b['archive_path']
    restore_backup(archive_full_path)

if __name__ == "__main__":
    main()
