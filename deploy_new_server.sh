#!/usr/bin/env bash
# ==============================================================================
# LongCat-Video-Avatar 1.5 Studio — 1-Click Server Deployer & Setup Script
# Works on any Ubuntu/Debian GPU server (Vast.ai, RunPod, Lambda, AutoDL, etc.)
# ==============================================================================
set -e

echo "===================================================================="
echo "🚀 Setting up LongCat-Video-Avatar 1.5 Studio on New GPU Server..."
echo "===================================================================="

# Step 1: System packages
echo "📦 Installing system audio/video dependencies..."
apt-get update -y && apt-get install -y ffmpeg libsndfile1 git git-lfs curl wget

# Step 2: Python packages
echo "🐍 Installing Python packages..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then pip install -r requirements.txt; fi
if [ -f "requirements_avatar.txt" ]; then pip install -r requirements_avatar.txt; fi
if [ -f "requirements_ui.txt" ]; then pip install -r requirements_ui.txt; fi

# Step 3: Weights verification / download
echo "💾 Verifying model weights..."
if [ ! -d "weights/LongCat-Video-Avatar-1.5" ]; then
    echo "⬇️ Downloading LongCat-Video-Avatar-1.5 weights..."
    python3 download_avatar_models.py
else
    echo "✅ Weights already present!"
fi

# Step 4: Ensure output and upload directories
mkdir -p uploads outputs web

# Step 5: Start Studio Server
echo "===================================================================="
echo "🎉 Starting LongCat-Video-Avatar 1.5 Studio on Port 20100..."
echo "===================================================================="
python3 server.py --host 0.0.0.0 --port 20100
