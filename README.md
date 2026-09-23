# LongCat-Avatar-1.5 Studio Master 🎬✨

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

## 🚀 1-Click Automated Setup (Vast.ai, RunPod, Lambda, etc.)

Whenever you spin up a new GPU server instance, run the following single command in terminal:

```bash
git clone https://github.com/azadhossainofficial/LongCat-Avatar-1.5.git /workspace/LongCat-Video && cd /workspace/LongCat-Video && bash install.sh
```

### What `install.sh` does automatically:
1. Installs system audio/video libraries (`ffmpeg`, `libsndfile1`, `git-lfs`, `curl`).
2. Configures Python virtual environment and installs all dependencies (`requirements.txt`, `requirements_avatar.txt`, `requirements_ui.txt`).
3. Automatically downloads official LongCat-Video-Avatar-1.5 and Wan VAE model weights from HuggingFace to `./weights/`.
4. Sets up directory structure and initial state registries.
5. Generates `start_studio.sh` for easy one-line service management.

---

## 🖥️ Launching the Studio Server

To start the studio server manually:
```bash
cd /workspace/LongCat-Video
./start_studio.sh
```

The Web UI will be live at:
```
http://<SERVER_IP>:20100
```

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
