#!/usr/bin/env python3
"""
LongCat Video Avatar 1.5 - Automated Hierarchical Daily Backup System
Organizes backups by: backups/YEAR/MONTH/backup_YYYY-MM-DD_HHMMSS.tar.gz
"""

import os
import sys
import time
import tarfile
import json
import shutil
from datetime import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
BACKUP_ROOT = WORKSPACE_ROOT / "backups"

# Exclude large binary weights, videos, uploads, caches
EXCLUDE_NAMES = {
    ".git",
    "weights",
    "uploads",
    "outputs",
    "audio_temp_file",
    "__pycache__",
    ".DS_Store",
    "backups",
    ".idea",
    ".vscode"
}

def is_excluded(path_str: str) -> bool:
    parts = Path(path_str).parts
    for p in parts:
        if p in EXCLUDE_NAMES:
            return True
        if p.endswith('.mp4') or p.endswith('.wav') or p.endswith('.tar.gz'):
            return True
    return False

def run_backup():
    now = datetime.now()
    year_str = now.strftime("%Y")
    month_str = now.strftime("%B") # e.g. 'August', 'September'
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    
    target_dir = BACKUP_ROOT / year_str / month_str
    target_dir.mkdir(parents=True, exist_ok=True)
    
    archive_name = f"backup_{date_str}_{now.strftime('%H%M%S')}.tar.gz"
    archive_path = target_dir / archive_name
    snapshot_dir = target_dir / f"snapshot_{date_str}_{now.strftime('%H%M%S')}"
    
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 📦 Starting Automated Backup for LongCat Video Avatar...")
    print(f"   Target Folder: {target_dir}")
    print(f"   Archive File: {archive_name}")
    
    # 1. Create tar.gz archive
    file_count = 0
    total_bytes = 0
    
    with tarfile.open(archive_path, "w:gz") as tar:
        for item in WORKSPACE_ROOT.iterdir():
            if item.name in EXCLUDE_NAMES:
                continue
            if item.is_file():
                if not is_excluded(item.name):
                    tar.add(item, arcname=item.name)
                    file_count += 1
                    total_bytes += item.stat().st_size
            elif item.is_dir():
                for root, dirs, files in os.walk(item):
                    # filter out excluded dirs in-place
                    dirs[:] = [d for d in dirs if not is_excluded(d)]
                    for file in files:
                        full_p = Path(root) / file
                        rel_p = full_p.relative_to(WORKSPACE_ROOT)
                        if not is_excluded(str(rel_p)):
                            tar.add(full_p, arcname=str(rel_p))
                            file_count += 1
                            total_bytes += full_p.stat().st_size

    # 2. Extract quick folder snapshot for direct browsing/diffing
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=snapshot_dir)

    # 3. Create clean zip archive
    zip_name = f"backup_{date_str}_{now.strftime('%H%M%S')}.zip"
    zip_path = target_dir / zip_name
    import zipfile
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_f:
        for root, dirs, files in os.walk(snapshot_dir):
            for file in files:
                full_p = Path(root) / file
                rel_p = full_p.relative_to(snapshot_dir)
                zip_f.write(full_p, arcname=str(rel_p))
        
    archive_size_mb = archive_path.stat().st_size / (1024 * 1024)
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    
    # 3. Update backup index
    index_file = BACKUP_ROOT / "backup_index.json"
    index_data = []
    if index_file.exists():
        try:
            with open(index_file, "r") as f:
                index_data = json.load(f)
        except Exception:
            index_data = []
            
    index_data.append({
        "timestamp": timestamp_str,
        "date": date_str,
        "year": year_str,
        "month": month_str,
        "archive_path": str(archive_path.relative_to(WORKSPACE_ROOT)),
        "snapshot_path": str(snapshot_dir.relative_to(WORKSPACE_ROOT)),
        "file_count": file_count,
        "archive_size_mb": round(archive_size_mb, 2),
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(index_file, "w") as f:
        json.dump(index_data, f, indent=2)
        
    # 4. Create / update latest symlink or pointer
    latest_pointer = BACKUP_ROOT / "LATEST_BACKUP.json"
    with open(latest_pointer, "w") as f:
        json.dump(index_data[-1], f, indent=2)

    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] ✅ Backup successfully created!")
    print(f"   Files Saved: {file_count} files ({archive_size_mb:.2f} MB)")
    print(f"   Stored at: {archive_path}")
    return str(archive_path)

if __name__ == "__main__":
    run_backup()
