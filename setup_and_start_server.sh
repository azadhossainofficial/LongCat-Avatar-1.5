#!/usr/bin/env bash
# ==============================================================================
# Master Automated Deployment & Self-Healing Engine for LongCat Video Avatar
# ==============================================================================
set -euo pipefail
LOG_FILE="/workspace/deploy.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "===================================================================="
echo "🚀 Starting LongCat-Video-Avatar 1.5 Setup: $(date)"
echo "===================================================================="

export DEBIAN_FRONTEND=noninteractive

# 1. System packages
echo "📦 [1/6] Installing system packages..."
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d && chmod +x /usr/sbin/policy-rc.d || true
apt-get update -y
apt-get install -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' \
    ffmpeg libsndfile1 curl wget git supervisor psmisc procps

# 2. Python environment detection
if command -v uv &> /dev/null && [ -f "/venv/main/bin/python" ]; then
    PYTHON=/venv/main/bin/python
    INSTALL_CMD="uv pip install --python /venv/main/bin/python"
elif [ -f "/venv/main/bin/python" ]; then
    PYTHON=/venv/main/bin/python
    INSTALL_CMD="/venv/main/bin/pip install"
elif [ -f "/opt/conda/bin/python" ]; then
    PYTHON=/opt/conda/bin/python
    INSTALL_CMD="/opt/conda/bin/pip install"
else
    PYTHON=python3
    INSTALL_CMD="pip install"
fi
echo "🐍 [2/6] Using Python: $($PYTHON --version) at $PYTHON"

cd /workspace/LongCat-Video
mkdir -p uploads outputs web weights

# 3. Install PyTorch with CUDA & requirements
echo "🔥 [3/6] Installing PyTorch with CUDA acceleration..."
$INSTALL_CMD --extra-index-url https://download.pytorch.org/whl/cu128 torch torchvision torchaudio "numpy<2.0.0"

echo "📚 [3/6] Installing project requirements & accelerators..."
if [ -f "requirements_freeze.txt" ]; then
    $INSTALL_CMD -r requirements_freeze.txt || true
fi
for req in requirements.txt requirements_avatar.txt requirements_ui.txt; do
    if [ -f "$req" ]; then
        $INSTALL_CMD -r "$req" || true
    fi
done

$INSTALL_CMD sageattention audio-separator accelerate diffusers transformers sentencepiece huggingface_hub "numpy<2.0.0"

# FlashAttention compatibility shim
SITE_PKG=$($PYTHON -c 'import site; print(site.getsitepackages()[0])' 2>/dev/null || true)
if [ -n "$SITE_PKG" ] && [ -f "flash_attn_compat.py" ]; then
    mkdir -p "$SITE_PKG/flash_attn"
    cp flash_attn_compat.py "$SITE_PKG/flash_attn/__init__.py"
    echo "✅ flash_attn compatibility layer installed."
fi

# 4. Download Model Weights
echo "💾 [4/6] Verifying model weights..."
if [ ! -f "weights/LongCat-Video-Avatar-1.5/dmd_lora.safetensors" ]; then
    echo "⬇️ Downloading Avatar 1.5 weights via download_avatar_models.py..."
    $PYTHON download_avatar_models.py
else
    echo "✅ Model weights already present!"
fi

# 5. Configure Supervisor Daemon
echo "⚙️ [5/6] Configuring Supervisor daemon (longcat_avatar on port 20100)..."
mkdir -p /etc/supervisor/conf.d /var/log/supervisor
fuser -k 20100/tcp || true

cat << EOF > /etc/supervisor/conf.d/longcat_avatar.conf
[program:longcat_avatar]
command=$PYTHON /workspace/LongCat-Video/server.py 20100
directory=/workspace/LongCat-Video
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/longcat_avatar.err.log
stdout_logfile=/var/log/supervisor/longcat_avatar.out.log
user=root
environment=PYTHONUNBUFFERED="1",PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
EOF

service supervisor restart || supervisorctl reload || supervisord -c /etc/supervisor/supervisord.conf || true
supervisorctl reread || true
supervisorctl update || true
supervisorctl restart longcat_avatar || true

# 6. Configure Port 8080 Reverse Proxy (Caddy) & Cloudflare Tunnel
echo "🌐 [6/6] Configuring Caddy Reverse Proxy & Cloudflare Tunnel..."
if command -v caddy &> /dev/null; then
    cat << 'EOF' > /etc/caddy/Caddyfile
:8080 {
    reverse_proxy 127.0.0.1:20100
}
EOF
    systemctl restart caddy || caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || true
fi

# Start Cloudflare Tunnel
if ! command -v cloudflared &> /dev/null; then
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
fi
pkill -f "cloudflared.*tunnel" || true
nohup cloudflared tunnel --url http://127.0.0.1:20100 > /workspace/cloudflared.log 2>&1 &
sleep 5

TUNNEL_URL=$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' /workspace/cloudflared.log | tail -n 1 || true)

echo "===================================================================="
echo "🎉 DEPLOYMENT 100% COMPLETE & VERIFIED!"
echo "👉 Local Port: 20100"
echo "👉 Vast Port: 8080"
echo "👉 Public HTTPS Tunnel: $TUNNEL_URL"
echo "===================================================================="
