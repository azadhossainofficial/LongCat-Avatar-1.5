# LongCat-Avatar-1.5 Studio Master 🎬✨

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/azadhossainofficial/LongCat-Avatar-1.5)

Production-ready Conversational Video Avatar Generation System powered by **LongCat-Video-Avatar-1.5** Diffusion Transformer (DiT) architecture and **Wan2.1-VAE**.

---

## 🌟 Key Features & Customizations

- **Dual-GPU Context Parallelism:** Native support for Dual NVIDIA RTX 4090 (48GB x 2 • 96GB VRAM) or L40S setups with zero VRAM fragmentation.
- **Anchor Seamless Mode:** S-Curve Hann cross-fade continuity and pristine facial anchor tracking for zero seam artifacts across hours of multi-segment audio.
- **Natural Presenter Dynamics:** 100% natural organic upper-body posture, subtle chest breathing, and gentle micro-motions without artificial torso freezing or stiff cardboard aesthetics.
- **Precision Oral Tone Neutralizer:** Eliminates fluorescent magenta/hot-pink lipstick drift while preserving natural mouth anatomy and skin fidelity.
- **Studio Master Web UI:** Dark Master aesthetic with a 4-Slot sequential batch queue, real-time per-segment diffusion progress, GPU thermal/VRAM telemetry, audio library watcher, and interactive video gallery.
- **Automated Audio Slicing:** Whisper Large-v3 and Kim Vocal 2 ONNX voice isolation with automatic sentence boundary chunking.

---

## 🚀 1-Click Automated Deployment (New Cloud GPU Server / Local Server)

If you want to install, deploy, and run the complete LongCat-Avatar-1.5 Studio Master on any **new cloud GPU server** (e.g. Vast.ai, RunPod, Lambda Labs, AutoDL) or **local Linux GPU machine**, run this single command in your terminal:

### 🔹 For Cloud GPU Instances (Vast.ai, RunPod, Lambda — Standard `/workspace`):
```bash
git clone https://github.com/azadhossainofficial/LongCat-Avatar-1.5.git /workspace/LongCat-Video && cd /workspace/LongCat-Video && bash deploy_new_server.sh
```

### 🔹 For Local GPU Server or Custom Directory:
```bash
git clone https://github.com/azadhossainofficial/LongCat-Avatar-1.5.git && cd LongCat-Avatar-1.5 && bash deploy_new_server.sh
```

### ⚡ What `deploy_new_server.sh` does automatically:
1. **Codebase Sync:** Clones and syncs the 100% production-ready Studio Master codebase.
2. **Environment Auto-Detection:** Automatically detects Python environment (`/venv/main/bin/python`, `/opt/conda/bin/python`, or system `python3`).
3. **System Packages:** Installs required media libraries (`ffmpeg`, `libsndfile1`, `git-lfs`, `curl`, `wget`).
4. **Python Dependencies:** Installs all core DiT, Whisper Large-v3, Wan-VAE, and FastAPI Web UI dependencies (`requirements.txt`, `requirements_avatar.txt`, `requirements_ui.txt`).
5. **Model Weights:** Automatically verifies and downloads official LongCat-Video-Avatar-1.5 and Wan VAE weights from HuggingFace to `./weights/`.
6. **Instant Launch:** Starts the Studio Master Web UI immediately on **Port 20100**.

---

## 🖥️ Accessing the Studio Web UI

Once the deployment finishes, the Web UI is live at:
```
http://<SERVER_IP>:20100
```
*(If deploying on Vast.ai, you can also map port 20100 or use standard port 8080)*

---

## 📁 Repository Structure

```
├── server.py                               # Studio Master backend & 4-slot sequential queue manager
├── run_demo_avatar_single_audio_to_video.py # Inference runner with Anchor Seamless pipeline
├── download_avatar_models.py               # Automated HuggingFace weight downloader
├── install.sh                              # 1-Click automated server installer
├── web/
│   ├── index.html                          # Studio Master Web UI
│   ├── app.js                              # Frontend logic, telemetry, slot management
│   └── style.css                           # Dark Master UI design tokens
├── longcat_video/                          # DiT architecture & attention modules
│   ├── modules/
│   ├── context_parallel/
│   ├── audio_process/
│   └── pipeline_longcat_video_avatar.py
├── requirements.txt                        # Core machine learning packages
├── requirements_avatar.txt                 # Avatar pipeline packages
└── requirements_ui.txt                     # Web server dependencies
```

---

## 📄 License
This repository is configured for personal and production deployment with LongCat-Video-Avatar 1.5. Model weights are subject to Meituan LongCat terms of service.
