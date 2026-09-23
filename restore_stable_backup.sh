#!/usr/bin/env bash
# 1-Click Restore Script for LongCat Avatar
set -e
echo "=== Restoring stable backup from /Volumes/Partition 2/LongCat Video Avatar 1.5/backups/backup_stable_state_20260828_205208 ==="
cp -rf "/Volumes/Partition 2/LongCat Video Avatar 1.5/backups/backup_stable_state_20260828_205208/"* "/Volumes/Partition 2/LongCat Video Avatar 1.5/"
echo "=== Local restore completed successfully! ==="
