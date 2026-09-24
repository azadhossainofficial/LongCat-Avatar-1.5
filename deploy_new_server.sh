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

# 3. Python dependencies & PyTorch with CUDA
echo "⚡ Upgrading pip and installing Python dependencies..."
if command -v uv &>/dev/null; then
    echo "⚡ Fast Package Installer (uv) detected!"
    INSTALL_CMD="uv pip install --python $PYTHON_BIN"
else
    $PIP_BIN install --upgrade pip setuptools wheel
    INSTALL_CMD="$PIP_BIN install"
fi

# Verify / Install PyTorch with CUDA
if ! $PYTHON_BIN -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    echo "🔥 Installing PyTorch with CUDA 12.8 acceleration..."
    $INSTALL_CMD --extra-index-url https://download.pytorch.org/whl/cu128 torch torchvision torchaudio "numpy<2.0.0"
fi

$INSTALL_CMD huggingface_hub audioread

if [ -f "requirements.txt" ]; then
    echo "Installing core requirements..."
    $INSTALL_CMD -r requirements.txt || true
fi

if [ -f "requirements_avatar.txt" ]; then
    echo "Installing avatar pipeline requirements..."
    $INSTALL_CMD -r requirements_avatar.txt || true
fi

if [ -f "requirements_ui.txt" ]; then
    echo "Installing UI requirements..."
    $INSTALL_CMD -r requirements_ui.txt || true
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

# 6. Ensure Port 8080 and 20100 are completely clear
echo "🧹 Ensuring Port 8080 and 20100 are clear..."
if command -v supervisorctl &>/dev/null; then
    supervisorctl stop jupyter 2>/dev/null || true
    if [ -f "/etc/supervisor/conf.d/jupyter.conf" ]; then
        sed -i 's/autostart=true/autostart=false/g' /etc/supervisor/conf.d/jupyter.conf
        supervisorctl reread 2>/dev/null || true
        supervisorctl update 2>/dev/null || true
    fi
fi
pkill -9 -f "jupyter-notebook" 2>/dev/null || true
fuser -k 8080/tcp 2>/dev/null || true
fuser -k 20100/tcp 2>/dev/null || true

# 7. Start Studio Server
echo "===================================================================="
echo "🎉 Starting LongCat-Avatar-1.5 Studio Master (Ports 8080, 20100, 7860)..."
echo "===================================================================="
exec $PYTHON_BIN server.py 8080

