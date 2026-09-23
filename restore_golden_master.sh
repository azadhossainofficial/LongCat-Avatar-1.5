#!/usr/bin/env bash
# ==============================================================================
# LongCat Video Avatar 1.5 - 1-Click Restore Golden Master State (2026-09-20)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups/backup_golden_master_stable_state_20260920"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup folder not found: $BACKUP_DIR"
    exit 1
fi

echo "===================================================================="
echo "🔄 Restoring LongCat Video Avatar 1.5 Golden Master State..."
echo "   Source: $BACKUP_DIR"
echo "   Target: $SCRIPT_DIR"
echo "===================================================================="

cp -rf "$BACKUP_DIR/"* "$SCRIPT_DIR/"

echo ""
echo "✅ Golden Master state successfully restored!"
echo "   All codes, models scripts, web assets, and configs are 100% up to date."
echo "===================================================================="
