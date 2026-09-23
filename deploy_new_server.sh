#!/usr/bin/env bash
# ==============================================================================
# LongCat-Avatar-1.5 Studio Master — 1-Click Server Deployer & Launcher
# Works on any Ubuntu/Debian GPU server (Vast.ai, RunPod, Lambda, AutoDL, etc.)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "===================================================================="
echo "🚀 Setting up LongCat-Video-Avatar 1.5 Studio Master on GPU Server..."
echo "===================================================================="

# 1. Detect Python / Virtual Environment
PYTHON_BIN=""
if [ -x "/venv/main/bin/python" ]; then
    PYTHON_BIN="/venv/main/bin/python"
    PIP_BIN="/venv/main/bin/pip"
elif [ -x "/opt/conda/bin/python" ]; then
    PYTHON_BIN="/opt/conda/bin/python"
    PIP_BIN="/opt/conda/bin/pip"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="$(command -v python3)"
    PIP_BIN="$(command -v pip3 || command -v pip)"
else
    echo "❌ Python 3 not found! Please install Python 3.10+."
    exit 1
fi

echo "🐍 Using Python: $PYTHON_BIN"

# 2. System dependencies
echo "📦 Installing system packages (FFmpeg, Libsndfile, Git-LFS)..."
if command -v apt-get &>/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        git \
        git-lfs \
        curl \
        wget \
        procps \
        net-tools \
        psmisc
fi

# 3. Python dependencies
echo "⚡ Upgrading pip and installing Python dependencies..."
$PIP_BIN install --upgrade pip setuptools wheel
$PIP_BIN install huggingface_hub

if [ -f "requirements.txt" ]; then
    echo "Installing core requirements..."
    $PIP_BIN install -r requirements.txt
fi

if [ -f "requirements_avatar.txt" ]; then
    echo "Installing avatar pipeline requirements..."
    $PIP_BIN install -r requirements_avatar.txt
fi

if [ -f "requirements_ui.txt" ]; then
    echo "Installing UI requirements..."
    $PIP_BIN install -r requirements_ui.txt
fi

# 4. Prepare Directories
echo "📁 Setting up runtime folders..."
mkdir -p uploads outputs audio_library web weights avatar_presets

# Initialize empty tasks registry if not present
if [ ! -f "active_tasks.json" ]; then
    echo "{}" > active_tasks.json
fi

# 5. Download Model Weights if missing
WEIGHTS_SUBDIR="$SCRIPT_DIR/weights/LongCat-Video-Avatar-1.5"
if [ ! -d "$WEIGHTS_SUBDIR" ] || [ -z "$(ls -A "$WEIGHTS_SUBDIR" 2>/dev/null)" ]; then
    echo "⬇️ Downloading LongCat-Video-Avatar-1.5 Model Weights from HuggingFace..."
    WEIGHTS_DIR="$SCRIPT_DIR/weights" $PYTHON_BIN download_avatar_models.py
else
    echo "✅ Model weights already present in $WEIGHTS_SUBDIR!"
fi

# 6. Start Studio Server
echo "===================================================================="
echo "🎉 Starting LongCat-Avatar-1.5 Studio Master on Port 20100..."
echo "===================================================================="
exec $PYTHON_BIN server.py 20100
