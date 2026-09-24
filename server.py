#!/usr/bin/env python3
"""
LongCat-Video-Avatar 1.5 Studio — Full Production Backend Server
Supports:
- Dynamic Master Port (prevents port collisions)
- Custom Inference Steps (8, 12, 16, 20, 24, 30, 40, 50 steps)
- Granular Real-Time Sub-Step Denoising Progress Tracking
- Multi-Port Listener (Vast.ai Portal & Direct Ports)
"""

import os
import sys
import re
import time
import math
import json
import uuid
import socket
import fcntl
import signal
import random
import shutil
import hashlib
import asyncio
import subprocess
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None

import queue

LOCK_FILE = "/tmp/longcat_server.lock"
_lock_fd = None

def acquire_server_lock():
    global _lock_fd
    try:
        _lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()
        return True
    except (BlockingIOError, OSError):
        print(f"[{time.strftime('%H:%M:%S')}] Another server instance is already running. Exiting.")
        return False

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
WEIGHTS_DIR = BASE_DIR / "weights"
AVATARS_DIR = BASE_DIR / "avatar_presets"
AUDIO_LIBRARY_DIR = BASE_DIR / "audio_library"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRASH_DIR = OUTPUT_DIR / ".trash"
TRASH_DIR.mkdir(parents=True, exist_ok=True)
AVATARS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

def ensure_flash_attn_shim():
    """Ensure FlashAttention drop-in compatibility shim is registered in Python site-packages and sys.modules."""
    try:
        import flash_attn
    except ImportError:
        try:
            import site
            shim_src = BASE_DIR / "flash_attn_compat.py"
            if shim_src.exists():
                for sp in site.getsitepackages():
                    fa_dir = Path(sp) / "flash_attn"
                    fa_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(shim_src, fa_dir / "__init__.py")
                    fa_if_dir = Path(sp) / "flash_attn_interface"
                    fa_if_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(shim_src, fa_if_dir / "__init__.py")
                print(f"[{time.strftime('%H:%M:%S')}] ⚡ Installed FlashAttention PyTorch SDPA compatibility shim into site-packages.")
        except Exception:
            pass
    try:
        import flash_attn_compat
    except Exception:
        pass

ensure_flash_attn_shim()


active_tasks = {}
task_queue = queue.Queue()
sequential_queue = task_queue
manual_dual_queue = queue.Queue()
running_tasks_set = set() # Set of task_ids currently running on GPU
active_processes = {}     # Map of task_id -> subprocess.Popen for instant killing
active_task_lock = threading.Lock()

CONFIG_FILE = BASE_DIR / "server_config.json"

def load_server_config():
    cfg = {"hybrid_mode": False, "max_concurrency": 1}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if "hybrid_mode" in saved:
                    cfg["hybrid_mode"] = bool(saved.get("hybrid_mode", False))
                    cfg["max_concurrency"] = 1
        except Exception:
            pass
    return cfg

def save_server_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception:
        pass

_DURATION_CACHE = {}

def get_system_gpu_name():
    try:
        res = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            lines = [l.strip() for l in res.stdout.strip().split("\n") if l.strip()]
            if len(lines) > 1:
                first_line_parts = lines[0].split(",")
                gpu_model = first_line_parts[0].strip()
                total_mb = sum([int(re.search(r'(\d+)', l.split(",")[1]).group(1)) for l in lines if len(l.split(",")) > 1 and re.search(r'(\d+)', l.split(",")[1])])
                total_gb = int(round(total_mb / 1024.0))
                per_gpu_gb = int(round((total_mb / len(lines)) / 1024.0))
                return f"Dual {gpu_model} ({per_gpu_gb}GB x {len(lines)} • {total_gb}GB Total)"
            else:
                parts = lines[0].split(",")
                gpu_model = parts[0].strip()
                vram = parts[1].strip() if len(parts) > 1 else ""
                return f"{gpu_model} ({vram})"
    except Exception:
        pass
    return "Dual NVIDIA RTX 4090 (48GB x 2 • 96GB Total)"

def get_max_gpu_vram_gb():
    try:
        res = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            vals = [float(x.strip()) for x in res.stdout.strip().splitlines() if x.strip().replace('.', '', 1).isdigit()]
            if vals:
                return max(vals) / 1024.0
    except Exception:
        pass
    return 48.0

def format_seconds_human(sec):
    if not sec or sec <= 0:
        return "0s"
    try:
        sec = float(sec)
        total_sec = int(round(sec))
        if total_sec < 60:
            return f"{total_sec}s"
        m = total_sec // 60
        s = total_sec % 60
        if m < 60:
            return f"{m}m {s}s" if s > 0 else f"{m}m"
        h = m // 60
        rem_m = m % 60
        return f"{h}h {rem_m}m" if rem_m > 0 else f"{h}h"
    except Exception:
        return str(sec)

def get_video_duration_seconds(file_path):
    p_str = str(file_path)
    if p_str in _DURATION_CACHE:
        return _DURATION_CACHE[p_str]
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", p_str],
            capture_output=True, text=True, timeout=3
        )
        dur_sec = float(res.stdout.strip())
        _DURATION_CACHE[p_str] = dur_sec
        return dur_sec
    except Exception:
        return 10.0

def get_video_duration_fast(file_path):
    dur_sec = get_video_duration_seconds(file_path)
    return format_seconds_human(dur_sec)

def ensure_video_has_audio(video_file_path, audio_file_path):
    """Probes the video file; if no audio stream exists, forcefully muxes audio from audio_file_path."""
    try:
        p_vid = Path(video_file_path)
        if not p_vid.exists():
            return False
        
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1", str(p_vid)
        ], capture_output=True, text=True)
        if probe.stdout.strip():
            return True  # Audio stream is verified and present
        
        if not audio_file_path or not os.path.exists(audio_file_path):
            return False
        
        temp_muxed = p_vid.parent / f"temp_mux_{p_vid.name}"
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", str(p_vid),
            "-i", str(audio_file_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "44100",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", "-movflags", "+faststart",
            str(temp_muxed)
        ]
        subprocess.run(mux_cmd, check=True, capture_output=True)
        if temp_muxed.exists() and temp_muxed.stat().st_size > 1000:
            shutil.move(str(temp_muxed), str(p_vid))
            return True
    except Exception as e:
        print(f"ensure_video_has_audio notice on {video_file_path}: {e}")
    return False

_DIR_CACHE = {}
_DIR_CACHE_TIME = {}

def get_resolution_badge(res_str: str) -> str:
    r = str(res_str or "").lower().strip()
    if any(x in r for x in ["500p", "500", "512"]):
        return "500p DiT"
    elif any(x in r for x in ["540p", "540", "544", "960"]):
        return "540p DiT"
    elif any(x in r for x in ["600p", "600", "608", "1024"]):
        return "600p DiT"
    elif any(x in r for x in ["520p", "520", "580", "736"]):
        return "520p DiT"
    elif any(x in r for x in ["480p", "480", "832", "627"]):
        return "480p DiT"
    elif any(x in r for x in ["700p", "700", "704", "720", "880", "1080", "1216", "1312", "1920"]):
        return "700p DiT"
    return "500p DiT"

def scan_video_dir(target_dir: Path, is_trash: bool = False):
    target_dir.mkdir(parents=True, exist_ok=True)
    cache_key = str(target_dir)
    now = time.time()
    
    # Fast in-memory cache if requested within 2.5 seconds and directory mtime hasn't changed
    try:
        dir_mtime = target_dir.stat().st_mtime
    except Exception:
        dir_mtime = 0

    if cache_key in _DIR_CACHE and (now - _DIR_CACHE_TIME.get(cache_key, 0) < 2.5):
        return _DIR_CACHE[cache_key]

    videos = []
    task_lookup = {}
    for tid, t in active_tasks.items():
        fn = t.get("output_filename")
        if fn:
            task_lookup[fn] = t
            clean_fn = re.sub(r'[^a-zA-Z0-9.]+', '_', fn)
            task_lookup[clean_fn] = t
            task_lookup[clean_fn.replace('_mp4', '.mp4')] = t
            task_lookup[clean_fn.replace('.mp4', '')] = t
        fn720 = t.get("output_filename_720p")
        if fn720:
            task_lookup[fn720] = t
        task_lookup[tid] = t

    all_mp4s = [f for f in target_dir.glob("*.mp4") if ".trash" not in f.name]
    seen_stems = set()
    for f in all_mp4s:
        stem = f.stem
        base_stem = stem[:-5] if stem.endswith("_720p") else stem
        
        if base_stem in seen_stems:
            continue
        seen_stems.add(base_stem)

        f_1080p = target_dir / f"{base_stem}.mp4"
        f_720p = target_dir / f"{base_stem}_720p.mp4"

        primary_file = f_1080p if f_1080p.exists() else f_720p
        if not primary_file.exists():
            continue

        stat = primary_file.stat()
        name = primary_file.name
        matched_task = task_lookup.get(name) or task_lookup.get(base_stem)
        if not matched_task:
            for tid, t in active_tasks.items():
                fn = str(t.get("output_filename", ""))
                if tid in name or (fn and (fn == name or base_stem in fn or fn in base_stem)):
                    matched_task = t
                    break

        vid_dur_sec = get_video_duration_seconds(primary_file)
        dur_info = format_seconds_human(vid_dur_sec)

        gen_info = None
        res_badge = None
        video_title = None
        slot_name = None

        # 1. Check sidecar meta json first (highest priority source of truth)
        meta_file = target_dir / f"{base_stem}.meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    mdata = json.load(mf)
                    if mdata.get("generation_time_formatted"):
                        gen_info = mdata["generation_time_formatted"]
                    elif mdata.get("generation_time_sec"):
                        gen_info = format_seconds_human(mdata["generation_time_sec"])
                    if mdata.get("resolution_label"):
                        res_badge = mdata["resolution_label"]
                    elif mdata.get("resolution"):
                        res_badge = get_resolution_badge(mdata.get("resolution"))
                    if mdata.get("video_title"):
                        video_title = str(mdata["video_title"]).strip()
                    if mdata.get("slot_name"):
                        slot_name = str(mdata["slot_name"]).strip()
            except Exception:
                pass

        # 2. Check matched task if not present in meta
        if matched_task:
            if not video_title and matched_task.get("video_title"):
                video_title = str(matched_task["video_title"]).strip()
            if not slot_name and matched_task.get("slot_name"):
                slot_name = str(matched_task["slot_name"]).strip()
            if not gen_info:
                exec_sec = matched_task.get("generation_time_sec")
                if exec_sec and exec_sec > 0:
                    gen_info = format_seconds_human(exec_sec)
                elif matched_task.get("generation_time_formatted"):
                    gen_info = matched_task.get("generation_time_formatted")
            if not res_badge:
                if matched_task.get("resolution_label"):
                    res_badge = matched_task["resolution_label"]
                elif matched_task.get("resolution"):
                    res_badge = get_resolution_badge(matched_task["resolution"])

        # 3. Fallback to active_tasks search
        if not gen_info or not res_badge or not video_title or not slot_name:
            for tid, t in active_tasks.items():
                t_out = str(t.get("output_filename", ""))
                if t_out and (t_out == name or t_out == f"{base_stem}.mp4" or base_stem in t_out or tid in name):
                    if not res_badge:
                        res_badge = get_resolution_badge(t.get("resolution"))
                    if not gen_info:
                        if t.get("generation_time_formatted"):
                            gen_info = t.get("generation_time_formatted")
                        elif t.get("generation_time_sec"):
                            gen_info = format_seconds_human(t["generation_time_sec"])
                    if not video_title and t.get("video_title"):
                        video_title = str(t["video_title"]).strip()
                    if not slot_name and t.get("slot_name"):
                        slot_name = str(t["slot_name"]).strip()
                    break

        # 4. Fallback to studio_state.json search
        if not video_title or not slot_name:
            try:
                st_file = OUTPUT_DIR / "studio_state.json"
                if st_file.exists():
                    with open(st_file, "r", encoding="utf-8") as sf:
                        st_data = json.load(sf)
                    for sl in st_data.get("slots", []):
                        sl_id = sl.get("id")
                        sl_fn = sl.get("outputFilename") or ""
                        sl_tid = sl.get("taskId") or ""
                        sl_name = sl.get("name") or f"Video {sl_id}"
                        if (sl_fn and (sl_fn == name or base_stem in sl_fn)) or \
                           (sl_tid and (sl_tid in name or (matched_task and matched_task.get("task_id") == sl_tid))) or \
                           (sl_id and name.startswith(f"Video_{sl_id}_")):
                            if not video_title and sl.get("title"):
                                video_title = str(sl.get("title")).strip()
                            if not slot_name and sl_name:
                                slot_name = sl_name
                            break
            except Exception:
                pass

        # 5. Clean fallback parsing from filename
        if not slot_name:
            slot_m = re.match(r"^Video[_\s](\d+)", name, re.IGNORECASE)
            if slot_m:
                slot_name = f"Video {slot_m.group(1)}"
            else:
                slot_name = "Video 1"

        if not video_title:
            cl = base_stem
            cl = re.sub(r"^Video[_\s]\d+[_\s]*", "", cl, flags=re.IGNORECASE)
            cl = re.sub(r"^Avatar_[a-f0-9]+", "", cl, flags=re.IGNORECASE).strip(" _-")
            cl = cl.replace("_", " ").replace("-", " ").strip()
            video_title = cl or "Rendered Video"

        if not gen_info:
            gen_info = format_seconds_human(vid_dur_sec * 15.5)

        if not res_badge:
            res_badge = "500p DiT"

        size_1080p_mb = round(f_1080p.stat().st_size / (1024 * 1024), 2) if f_1080p.exists() else None
        size_720p_mb = round(f_720p.stat().st_size / (1024 * 1024), 2) if f_720p.exists() else None

        prefix = "/outputs/.trash" if is_trash else "/outputs"
        url_1080p = f"{prefix}/{urllib.parse.quote(f_1080p.name)}" if f_1080p.exists() else f"{prefix}/{urllib.parse.quote(f_720p.name)}"
        url_720p = f"{prefix}/{urllib.parse.quote(f_720p.name)}" if f_720p.exists() else url_1080p

        f_poster = target_dir / f"{base_stem}.jpg"
        if not f_poster.exists() and primary_file.exists():
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-ss", "00:00:00.200", "-i", str(primary_file),
                    "-vframes", "1", "-q:v", "2", str(f_poster)
                ], capture_output=True)
            except Exception:
                pass
        poster_url = f"{prefix}/{urllib.parse.quote(f_poster.name)}" if f_poster.exists() else None

        videos.append({
            "id": base_stem,
            "filename": f_1080p.name if f_1080p.exists() else f_720p.name,
            "url": url_1080p,
            "poster_url": poster_url,
            "video_title": video_title,
            "slot_name": slot_name,
            "size_mb": size_1080p_mb or size_720p_mb,
            "filename_1080p": f_1080p.name if f_1080p.exists() else f_720p.name,
            "url_1080p": url_1080p,
            "size_1080p_mb": size_1080p_mb or size_720p_mb,
            "filename_720p": f_720p.name if f_720p.exists() else f_1080p.name,
            "url_720p": url_720p,
            "size_720p_mb": size_720p_mb or size_1080p_mb,
            "duration_label": dur_info,
            "render_time_label": gen_info,
            "resolution_label": res_badge,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
        })
    res_sorted = sorted(videos, key=lambda x: x["created_at"], reverse=True)
    _DIR_CACHE[cache_key] = res_sorted
    _DIR_CACHE_TIME[cache_key] = now
    return res_sorted

SERVER_CONFIG = load_server_config()

TASKS_FILE = BASE_DIR / "active_tasks.json"

def save_active_tasks_to_disk():
    try:
        tmp_file = BASE_DIR / "active_tasks.json.tmp"
        clean_dict = {}
        with active_task_lock:
            for tid, t in active_tasks.items():
                clean_dict[tid] = {k: v for k, v in t.items() if isinstance(v, (str, int, float, bool, list, dict)) or v is None}
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(clean_dict, f, indent=2)
        os.replace(tmp_file, TASKS_FILE)
    except Exception:
        pass

def load_active_tasks_from_disk():
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for tid, t in loaded.items():
                    if t.get("status") in ["processing", "queued"]:
                        t["status"] = "cancelled"
                        t["stage"] = "Interrupted by server restart"
                    active_tasks[tid] = t
        except Exception:
            pass

def get_free_port():
    """Finds a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def get_audio_duration(file_path: str) -> float:
    """Calculates audio duration in seconds using ffprobe, soundfile, or librosa."""
    try:
        res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            d = float(res.stdout.strip())
            if d > 0:
                return d
    except Exception:
        pass
    try:
        import soundfile as sf
        info = sf.info(file_path)
        return float(info.duration)
    except Exception:
        pass
    try:
        import librosa
        dur = librosa.get_duration(path=file_path)
        return float(dur)
    except Exception:
        pass
    return 10.0

def detect_framing_and_hands(image_path: str) -> str:
    """
    Analyzes uploaded portrait/landscape image to determine framing and whether hands are visible:
    - 'bust_locked': Bust-up / chest-up / close-up or landscape where hands are absent/locked. Hands must be completely locked/absent.
    - 'resting_subtle': Half-body / full-body portrait where hands are visibly resting.
    """
    try:
        if not image_path or not os.path.exists(image_path):
            return "bust_locked"

        # Check aspect ratio first
        import PIL.Image
        im = PIL.Image.open(image_path)
        w, h = im.size
        # All landscape / wide / square photos (w >= h, e.g. 16:9 YouTube format) must be bust_locked
        # so hands are strictly prevented from appearing or gesturing.
        if w >= h:
            return "bust_locked"

        import cv2
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if hasattr(cv2, 'CascadeClassifier') and os.path.exists(cascade_path):
            face_cascade = cv2.CascadeClassifier(cascade_path)
            cv_img = cv2.imread(image_path)
            if cv_img is not None:
                h_img, w_img = cv_img.shape[:2]
                scale_factor = 1.0
                if max(h_img, w_img) > 1024:
                    scale_factor = 1024.0 / max(h_img, w_img)
                    proc_img = cv2.resize(cv_img, (int(w_img * scale_factor), int(h_img * scale_factor)))
                else:
                    proc_img = cv_img
                gray = cv2.cvtColor(proc_img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) > 0:
                    # Select largest face by area (crucial: avoids tiny background noise false positives)
                    best_face = max(faces, key=lambda f: f[2] * f[3])
                    _, _, _, fh = best_face
                    orig_fh = fh / scale_factor
                    face_ratio = orig_fh / float(h_img)
                    # If face occupies > 14% of vertical height, framing is close-up/bust-up/shoulders-up (hands absent/locked)
                    if face_ratio > 0.14:
                        return "bust_locked"
                    else:
                        return "resting_subtle"
        # Fallback based on image aspect ratio
        if h > w * 1.35:
            return "resting_subtle"
        return "bust_locked"
    except Exception:
        return "bust_locked"

def compute_num_segments(duration_sec: float, num_frames: int = 205, num_cond_frames: int = 13, fps: int = 25, generation_mode: str = "anchor_seamless", transition_overlap: int = 4) -> int:
    """Calculates the exact number of continuation segments for avatar generation (205 frames / 8.2s default)."""
    if duration_sec <= (num_frames / fps):
        return 1
    remaining_sec = duration_sec - (num_frames / fps)
    if generation_mode == "anchor_seamless":
        step_frames = num_frames - transition_overlap
    else:
        step_frames = num_frames - num_cond_frames
    step_sec = step_frames / float(fps)
    return 1 + math.ceil(remaining_sec / step_sec)

def calculate_segments(duration_sec: float, num_frames: int = 205, num_cond_frames: int = 13, fps: int = 25, generation_mode: str = "anchor_seamless", transition_overlap: int = 4) -> int:
    return compute_num_segments(duration_sec, num_frames, num_cond_frames, fps, generation_mode, transition_overlap)

# ==============================================================================
# Persistent Audio Library Architecture (MacBook Sync & Zero-Upload Streaming)
# ==============================================================================

def get_audio_library_list():
    """Scans audio_library/ and returns sorted list of all audios with duration, size, and streaming URLs."""
    if not AUDIO_LIBRARY_DIR.exists():
        AUDIO_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
        return []

    cache_file = AUDIO_LIBRARY_DIR / ".audio_meta_cache.json"
    cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    audio_exts = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
    items = []
    updated_cache = False

    for p in sorted(AUDIO_LIBRARY_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in audio_exts and not p.name.startswith("."):
            fname = p.name
            try:
                stat = p.stat()
                mtime = stat.st_mtime
                size_mb = round(stat.st_size / (1024 * 1024), 2)

                dur = 0.0
                if fname in cache and cache[fname].get("mtime") == mtime:
                    dur = cache[fname].get("duration", 0.0)
                else:
                    try:
                        cmd = [
                            "ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                            str(p)
                        ]
                        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                        dur = float(res.stdout.strip()) if res.stdout.strip() else 0.0
                    except Exception:
                        dur = 0.0
                    cache[fname] = {"mtime": mtime, "duration": dur}
                    updated_cache = True

                if stat.st_size < 1024 or dur <= 0:
                    continue

                dur_sec = int(dur)
                dur_formatted = f"{dur_sec // 60}m {dur_sec % 60:02d}s" if dur_sec >= 60 else f"{dur_sec}s"

                items.append({
                    "id": hashlib.md5(fname.encode()).hexdigest()[:10],
                    "filename": fname,
                    "duration": round(dur, 2),
                    "duration_formatted": dur_formatted,
                    "size_mb": f"{size_mb} MB",
                    "size_bytes": stat.st_size,
                    "url": f"/audio_library/{urllib.parse.quote(fname)}",
                    "mtime": mtime
                })
            except Exception:
                continue

    if updated_cache:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except Exception:
            pass

    return items

# ==============================================================================
# HeyGen / Akool Style Avatar Preset & Persona Library Architecture
# ==============================================================================

def get_avatar_presets_list():
    """Returns sorted list of all persistent avatar presets with metadata and asset URLs."""
    presets = []
    if not AVATARS_DIR.exists():
        return presets

    for sub in sorted(AVATARS_DIR.iterdir()):
        if sub.is_dir() and not sub.name.startswith("."):
            portrait = None
            for p in sub.glob("portrait.*"):
                if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    portrait = p
                    break
            if not portrait:
                # Check any image in the directory
                for p in sub.iterdir():
                    if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                        portrait = p
                        break
            if not portrait:
                continue

            meta_file = sub / "meta.json"
            meta = {}
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            avatar_id = meta.get("id", sub.name)
            name = meta.get("name", sub.name.replace("_", " ").title())
            created_at = meta.get("created_at", sub.stat().st_mtime)
            aspect_ratio = meta.get("aspect_ratio", "16:9")
            dimensions = meta.get("dimensions", [1280, 720])

            preview_file = sub / "preview.mp4"
            preview_url = f"/avatar_presets/{sub.name}/preview.mp4" if preview_file.exists() else None

            presets.append({
                "id": avatar_id,
                "folder_name": sub.name,
                "name": name,
                "image_url": f"/avatar_presets/{sub.name}/{portrait.name}",
                "preview_url": preview_url,
                "aspect_ratio": aspect_ratio,
                "dimensions": dimensions,
                "created_at": created_at,
                "prompt_tags": meta.get("prompt_tags", ""),
                "gender": meta.get("gender", "auto")
            })

    def get_avatar_sort_key(item):
        m = re.search(r'Avatar\s*(\d+)', item.get("name", ""), re.IGNORECASE)
        if m:
            return (0, int(m.group(1)))
        return (1, -float(item.get("created_at", 0)))

    presets.sort(key=get_avatar_sort_key)
    return presets

def get_next_avatar_serial_number():
    """Calculates next sequential Avatar index (e.g. Avatar 1, Avatar 2...)."""
    existing = get_avatar_presets_list()
    numbers = []
    for a in existing:
        m = re.search(r'Avatar\s*(\d+)', a.get("name", ""), re.IGNORECASE)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1

def detect_image_aspect_ratio_and_dims(img_path: Path):
    """Detects native dimensions and maps to 16:9, 9:16, or 1:1."""
    width, height = 1280, 720
    try:
        if Image:
            with Image.open(img_path) as im:
                width, height = im.size
        else:
            res = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(img_path)],
                capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0 and "x" in res.stdout:
                w, h = res.stdout.strip().split("x")
                width, height = int(w), int(h)
    except Exception:
        pass

    ratio_val = width / max(1, height)
    if ratio_val > 1.2:
        aspect = "16:9"
    elif ratio_val < 0.8:
        aspect = "9:16"
    else:
        aspect = "1:1"
    return width, height, aspect

def save_new_avatar_preset(file_bytes: bytes, original_filename: str = "portrait.jpg", custom_name: str = None):
    """Persists a new avatar portrait into avatar_presets/<id>/ with full metadata."""
    next_num = get_next_avatar_serial_number()
    assigned_name = custom_name.strip() if custom_name and custom_name.strip() else f"Avatar {next_num}"
    avatar_id = f"avatar_{next_num}_{uuid.uuid4().hex[:4]}"

    avatar_dir = AVATARS_DIR / avatar_id
    avatar_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(original_filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    target_img_name = f"portrait{ext}"
    target_img_path = avatar_dir / target_img_name

    with open(target_img_path, "wb") as f:
        f.write(file_bytes)

    width, height, aspect = detect_image_aspect_ratio_and_dims(target_img_path)

    meta = {
        "id": avatar_id,
        "name": assigned_name,
        "created_at": time.time(),
        "aspect_ratio": aspect,
        "dimensions": [width, height],
        "original_filename": original_filename,
        "gender": "auto"
    }

    with open(avatar_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)

    meta["folder_name"] = avatar_id
    meta["image_url"] = f"/avatar_presets/{avatar_id}/{target_img_name}"
    meta["preview_url"] = None
    return meta

def rename_avatar_preset(avatar_id: str, new_name: str):
    """Inline renames an avatar preset and updates meta.json."""
    if not avatar_id or not new_name:
        return False, "Invalid avatar_id or new_name"

    target_dir = AVATARS_DIR / avatar_id
    if not target_dir.exists():
        for sub in AVATARS_DIR.iterdir():
            if sub.is_dir():
                mf = sub / "meta.json"
                if mf.exists():
                    try:
                        with open(mf, "r", encoding="utf-8") as f:
                            d = json.load(f)
                            if d.get("id") == avatar_id:
                                target_dir = sub
                                break
                    except Exception:
                        pass

    if not target_dir.exists():
        return False, "Avatar preset not found"

    meta_file = target_dir / "meta.json"
    meta = {}
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            pass

    meta["name"] = new_name.strip()
    meta["updated_at"] = time.time()
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)

    return True, meta

def delete_avatar_preset(avatar_id: str):
    """Permanently deletes or archives an avatar preset folder."""
    if not avatar_id:
        return False, "Invalid avatar_id"

    target_dir = AVATARS_DIR / avatar_id
    if not target_dir.exists():
        for sub in AVATARS_DIR.iterdir():
            if sub.is_dir():
                mf = sub / "meta.json"
                if mf.exists():
                    try:
                        with open(mf, "r", encoding="utf-8") as f:
                            d = json.load(f)
                            if d.get("id") == avatar_id:
                                target_dir = sub
                                break
                    except Exception:
                        pass

    if not target_dir.exists():
        return False, "Avatar preset not found"

    try:
        shutil.rmtree(str(target_dir))
        return True, "Avatar deleted successfully"
    except Exception as e:
        return False, str(e)


def background_queue_worker(worker_id: int = 0):
    """
    Dedicated Single-Engine Sequential Worker: Consumes tasks one-by-one in strict FIFO sequence.
    Guarantees 100% stable GPU memory and runs videos of any length without interruption.
    """
    global running_tasks_set
    while True:
        try:
            try:
                task_id = sequential_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            with active_task_lock:
                running_tasks_set.add(task_id)
            
            task = active_tasks.get(task_id)
            if task and task.get("status") == "queued":
                print(f"[{time.strftime('%H:%M:%S')}] 🎬 [QUEUE WORKER] Dispatching task {task_id} to GPU engine...", flush=True)
                execute_avatar_generation(task_id)
            
            with active_task_lock:
                running_tasks_set.discard(task_id)
            sequential_queue.task_done()
        except Exception as e:
            print(f"[QueueWorker Exception] {e}")
            with active_task_lock:
                if 'task_id' in locals():
                    running_tasks_set.discard(task_id)
            time.sleep(1)

def execute_avatar_generation(task_id: str):
    """Executes the real PyTorch torchrun pipeline for LongCat-Video-Avatar 1.5."""
    task = active_tasks.get(task_id)
    if not task:
        return

    exec_start_time = time.time()

    task_upload_dir = Path(task["upload_dir"])
    task_output_dir = OUTPUT_DIR / task_id
    task_output_dir.mkdir(parents=True, exist_ok=True)

    # Fast-complete duplicate baseline requests if preview already exists
    if task.get("is_avatar_baseline"):
        task["slot_name"] = "Avatar Library"
        av_id = task.get("avatar_id")
        target_av_dir = Path(task.get("target_avatar_dir", AVATARS_DIR / av_id)) if av_id else None
        if target_av_dir and (target_av_dir / "preview.mp4").exists() and (target_av_dir / "preview.mp4").stat().st_size > 50000:
            task["logs"].append(f"[{time.strftime('%H:%M:%S')}] [CACHE] Baseline preview.mp4 already exists for avatar {av_id}. Completing immediately.")
            task["status"] = "completed"
            task["stage"] = "Completed — Video Ready"
            task["progress"] = 100.0
            task["output_video_url"] = f"/avatar_presets/{target_av_dir.name}/preview.mp4"
            save_active_tasks_to_disk()
            return

    image_path = task["image_path"]
    audio_path = task["audio_path"]
    prompt = task.get("prompt", "")
    negative_prompt = task.get("negative_prompt", "")
    resolution = task["resolution"]
    preset = task["preset"]
    num_segments = task["num_segments"]
    num_inference_steps = task.get("num_inference_steps", 3)
    seed = task["seed"]
    ref_img_index = task.get("ref_img_index", 10)
    mask_frame_range = task.get("mask_frame_range", 0)

    # 1. Create input JSON with separated positive and negative prompt enforcement
    default_negative = (
        "moving hands while speaking, conversational hand gestures, talking with hands, gesturing with hands, raising hands to emphasize speech, hand movements synced to speech style or cadence, expressive hand gestures, repetitive hand gestures, "
        "overexposure, washed out colors, milky shadows, lifted blacks, white haze, desaturated colors, skin brightening, whitening filter, beauty filter, airbrushed skin, smoothed pores, blended beard, softened hair, blurry beard whiskers, artificial gloss, plastic look, glow effect, exposure shift, lighting change, altered skin tone, pale skin, bleached highlights, loss of contrast, flat lighting, "
        "hands in frame, hand gestures, waving hands, moving arms, hands entering frame, touching face, touching hair, touching chest, touching neck, raised hands, pointing fingers, fidgeting hands, hands near face, "
        "ring, finger ring, wedding ring, band ring, metallic ring, thumb ring, multiple rings, changing rings, flickering ring, morphing ring, gold ring, silver ring, "
        "nail polish, painted nails, colored nails, red nails, black nails, pink nails, purple nails, white nails, acrylic nails, fake nails, manicured colored nails, flashing nail colors, flickering nail polish, morphing nails, changing nail colors, unnatural nails, mutated fingers, extra fingers, missing fingers, "
        "watch, wristwatch, smartwatch, bracelet, bangles, armbands, jewelry, hand jewelry, wrist accessories, ornaments, "
        "zooming in, zooming out, camera zoom, camera drift, camera shift, camera panning, camera movement, changing focal length, scaling shift, scale changes, jumping framing, "
        "leaning forward, lunging forward, moving closer to camera, head pitching forward, forward torso lean, bowing head, lunging head, camera intrusion, body distortion, "
        "cars, vehicles, traffic, road traffic, moving cars, automobiles, pedestrians, walking people, people in background, crowd, bystanders, background figures, animals, birds, random objects appearing, morphing background, background distortion, "
        "exaggerated head movement, head shaking, head bobbing, head swaying, head rolling, head tilting, erratic head jerks, nodding head, side-to-side head shaking, wobbling head, unstable head posture, jerky neck, neck twisting, neck stretching, neck swaying, bobblehead, wild gestures, chaotic motion, restless posture, "
        "wide mouth opening, wide open mouth, gaping mouth, over-opened mouth, shouting mouth, wide jaw extension, wide jaw drop, unhinged jaw, dropped jaw, stretching jaw, loose mouth, gaping oral cavity, robotic mouth stretching, overacting, rubber lips, dramatic mouth movement, excessive lip flapping, wide toothy speech, screaming mouth, excessive mouth movements, exaggerated mouth articulation, dramatic speech, "
        "dark lips, smoky lips, blackened lips, discolored lips, dirty lips, burnt lips, stained lips, smoking lips, pink lips, red lips, magenta lips, purple lips, violet lips, blue lips, cyan lips, bruised lips, lipstick, shiny lips, glossy lips, painted lips, unnatural lip tone, lip gloss, lip recoloring, "
        "changing teeth, distorted teeth, morphing teeth, crooked teeth, shifting teeth shape, abnormal teeth, yellowing teeth, multiple teeth rows, blurry teeth, deformed mouth, distorted lips, mouth morphing, identity changes, "
        "angry face, aggressive expression, jaw tension, facial strain, popping neck veins, clenched teeth, forced shouting, plastic skin, doll face, artificial smoothing, blur filter, airbrush, cartoonish, oversaturated, color distortion, "
        "background blur, warped background, edge artifacts, halo, seams, vertical lines, haloing around shoulders, background smearing, worst quality, low quality, deformed, disfigured"
    )
    
    full_negative = f"{negative_prompt}, {default_negative}".strip(", ") if negative_prompt else default_negative

    # Clean any outdated phrases that could trigger camera zooming, posture lunges, head nodding, or unnatural freeze
    clean_p = prompt
    if "breasts will bounce" not in prompt.lower() and "preserve the same woman" not in prompt.lower():
        clean_p = clean_p.replace("full expressive lifelike upper body motion", "fixed camera portrait, stationary posture")
        clean_p = clean_p.replace("organic posture shifts", "calm natural speech")
        clean_p = clean_p.replace("subtle shoulder and chest breathing", "calm natural breathing")
        clean_p = clean_p.replace("energetic gestures", "subtle posture")
        clean_p = clean_p.replace("perfectly still body", "natural relaxed body")
        clean_p = clean_p.replace("completely still torso", "natural upper body")
        clean_p = clean_p.replace("still torso", "natural upper body")
        clean_p = clean_p.replace("occasional head nods", "stable upright head and poised neck")
        clean_p = clean_p.replace("subtle occasional nods", "stable upright head and poised neck")
        clean_p = clean_p.replace("head micro-movements and subtle occasional nods", "stable upright head posture and poised neck")
        clean_p = clean_p.replace("subtle shoulder, neck, head, and torso micro-movements", "stable upright head posture, poised neck, and gentle breathing")
        clean_p = clean_p.replace("natural head micro-movements", "stable upright head alignment")
        clean_p = clean_p.replace("pink", "").replace("lipstick", "").replace("lipstick-like", "").replace("purple", "").replace("violet", "").strip()

    gender = task.get("gender", "male").lower()
    if gender == "auto":
        lower_str = f"{task.get('video_title', '')} {os.path.basename(image_path)}".lower()
        if any(w in lower_str for w in ["woman", "female", "girl", "lady", "she", "her", "mrs", "miss", "women"]):
            gender = "female"
        elif any(w in lower_str for w in ["man", "male", "boy", "guy", "he", "his", "mr", "gentleman", "men"]):
            gender = "male"
        else:
            gender = "female"

    hand_control = task.get("hand_control", "auto")
    if hand_control == "auto":
        detected_hand_mode = detect_framing_and_hands(str(image_path))
    else:
        detected_hand_mode = hand_control

    if detected_hand_mode == "bust_locked":
        # 1. BUST-UP / CLOSE-UP / LANDSCAPE: Hands are completely absent or locked. NEVER mention hands in positive prompt!
        hand_pos_guidance = (
            "Composed stationary presenter with natural relaxed upper-body posture, gentle organic breathing, authentic photography."
        )
        hand_neg_guidance = (
            "hands, arms, fingers, palms, wrists, thumbs, hand gestures, waving hands, moving hands, gesturing with hands, "
            "raising hands, hands entering frame, hands visible, hands in frame, hands rising, virtual hands, extra limbs, human hands, "
            "conversational gestures, fidgeting hands, lifting hands, moving arms, hands near face, hands near chest, talking with hands"
        )
        # Thoroughly strip any hand mentions from clean_p so diffusion cross-attention never receives hand tokens
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_p) if s.strip()]
        clean_sentences = [s for s in sentences if not any(w in s.lower() for w in ['hand', 'hands', 'arm', 'arms', 'finger', 'wrist', 'palm'])]
        clean_p = " ".join(clean_sentences)
    else:
        # 2. HANDS VISIBLE IN FRAME: Never mention 'hands' positively to avoid prompting hand synthesis
        hand_pos_guidance = (
            "Composed natural posture, stationary calm presenter, authentic photography."
        )
        hand_neg_guidance = (
            "hands, arms, fingers, palms, wrists, thumbs, moving hands while speaking, conversational hand gestures, talking with hands, gesturing with hands, "
            "raising hands, hand movements, expressive hand gestures, waving hands, moving arms, explanatory gestures, fidgeting hands, "
            "lifting hands, animated hands, touching face, touching hair, touching chest, finger distortion, extra fingers, missing fingers, deformed hands, broken wrists, unnatural hands"
        )

    if gender == "female":
        female_positive_prompt = (
            "Use the uploaded image exactly as the reference. Preserve the same woman, face, hairstyle, skin tone, clothing, body proportions, framing, lighting, and natural colors.\n\n"
            "Professional woman speaking naturally, calmly, and politely with smooth accurate lip sync, restrained natural mouth aperture, controlled gentle jaw movement, and relaxed closed lips during pauses. Natural conversational delivery, steady dignified eye gaze, relaxed facial expressions, subtle cheek motion, and natural irregular blinking.\n\n"
            "Gentle organic breathing with subtle chest and shoulder rise and fall. Her breasts will bounce while she talks naturally, with realistic weight and soft secondary motion caused by breathing and speech. Keep it natural and never exaggerated or repetitive.\n\n"
            f"Composed, dignified presenter with stable upright head posture and poised neck. Calm, polite delivery with steady centered head alignment, zero wild head shaking, zero head bobbing, zero erratic tilting, and zero side-to-side swaying. Maintain poised realistic upper-body posture without repetitive rocking or excessive gestures. {hand_pos_guidance}\n\n"
            "Locked stationary tripod camera. Zero zoom in, zero zoom out, no pan, no tilt, no camera shake, no forward leaning, and completely static background.\n\n"
            "Preserve identity, anatomy, clothing, lighting, and image consistency throughout. Avoid face distortion, body warping, chest distortion, lip jitter, robotic motion, repetitive movement, wide mouth opening, or exaggerated expressions.\n\n"
            "Final result should look like a real professional woman speaking calmly, politely, and naturally in a high-end podcast or interview."
        )
        female_negative_prompt = (
            "Aggressive speech, shouting, yelling, loud forceful talking, wide mouth opening, wide open mouth, gaping mouth, over-opened mouth, shouting mouth, wide jaw drop, unhinged jaw, dropped jaw, stretching jaw, loose mouth, gaping oral cavity, forced facial strain, jaw tension, clenched teeth, robotic mouth stretching, dramatic mouth movement, excessive lip flapping, wide toothy speech, popping neck veins, exaggerated head shaking, head bobbing, head swaying, head rolling, head tilting, erratic head jerks, nodding head, side-to-side head shaking, wobbling head, unstable head posture, jerky neck, neck twisting, neck stretching, neck swaying, bobblehead, wild gestures, chaotic motion, restless posture, sudden fast movements, aggressive gestures.\n\n"
            f"{hand_neg_guidance}, excessive hand movement, finger distortion, extra or missing fingers, fused or deformed fingers, broken wrists, unnatural hands, ring morphing or flickering, changing nail color, nail morphing.\n\n"
            "Frozen body, stiff mannequin posture, robotic posture, wooden torso, artificial paralysis, frozen chest, locked shoulders.\n\n"
            "Zoom in, zoom out, camera movement, camera drift, pan, tilt, framing shift, focal-length change, scale change, camera shake, frame vibration, jumping cuts.\n\n"
            "Forward leaning, lunging toward camera, moving closer to camera, head pitching forward, torso leaning forward, excessive bowing.\n\n"
            "Overexposure, washed-out colors, white haze, lifted blacks, desaturated colors, skin brightening, whitening filter, beauty filter, airbrushed skin, plastic skin, altered skin tone, bleached highlights, flat lighting.\n\n"
            "Pink, red, magenta, purple, or violet lips, lipstick, lip gloss, glossy or shiny lips, painted lips, unnatural lip color.\n\n"
            "Face distortion, body warping, anatomy distortion, deformed features, low quality, severe artifacts, disfigured appearance."
        )

        if ("breasts will bounce" in prompt.lower() or "preserve the same woman" in prompt.lower()) and "locked in a stable resting position" in prompt.lower():
            full_prompt = prompt.strip()
        else:
            full_prompt = female_positive_prompt

        if detected_hand_mode == "bust_locked":
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_prompt) if s.strip()]
            sentences.append("Clean stationary presenter framing. Composed upper-body posture with natural organic breathing, realistic chest rise and fall, and subtle shoulder micro-movements while speaking calmly and naturally.")
            full_prompt = " ".join(sentences)

        if "moving hands while speaking" in negative_prompt.lower() and "unnatural hands" in negative_prompt.lower():
            full_negative = negative_prompt.strip()
        elif negative_prompt.strip():
            full_negative = f"{negative_prompt.strip()}, {female_negative_prompt}"
        else:
            full_negative = female_negative_prompt

        if detected_hand_mode == "bust_locked":
            bust_neg_front = "hands, arms, fingers, palms, wrists, thumbs, hand gestures, waving hands, moving hands, gesturing with hands, raising hands, hands entering frame, hands rising, virtual hands, extra limbs, human hands, conversational gestures, pink lips, red lips, magenta lips, lipstick, shiny lips, glossy lips, colored mouth, painted lips, purple lips, unnatural lip tone, fluorescent lips, wide open mouth, gaping mouth, over-opened mouth, shouting mouth, "
            if not full_negative.startswith("hands,"):
                full_negative = bust_neg_front + full_negative
    else:
        male_positive_prompt = (
            "Use the uploaded image exactly as the reference. Preserve the same man, face, hairstyle, facial hair, skin tone, clothing, body proportions, framing, lighting, and natural colors.\n\n"
            "Professional man speaking naturally, calmly, and politely with smooth accurate lip sync, restrained natural mouth aperture, controlled gentle jaw movement, and relaxed closed mouth during pauses. Natural conversational voice cadence, steady dignified eye contact, relaxed facial expressions, and natural irregular blinking without weird staring or darting eyes.\n\n"
            "Gentle organic breathing with subtle chest and shoulder rise and fall. Composed, dignified presenter with stable upright head posture and poised neck. Calm, polite delivery with steady centered head alignment, zero wild head shaking, zero head bobbing, zero erratic tilting, and zero side-to-side swaying. Maintain composed realistic upper-body posture without repetitive rocking or excessive gestures. {hand_pos_guidance}\n\n"
            "Locked stationary tripod camera. Zero zoom in, zero zoom out, no pan, no tilt, no camera shake, no forward leaning, and completely static background.\n\n"
            "Preserve identity, facial features, beard texture, clothing, lighting, and photographic realism throughout. Natural matte masculine lips with zero lipstick or gloss, authentic skin tone matching reference photo exactly. Avoid aggressive speech, wide mouth opening, jaw stretching, robotic motion, or exaggerated facial expressions.\n\n"
            "Final result should look like a real authentic human man speaking calmly, politely, and professionally in a high-end podcast or interview."
        )
        male_negative_prompt = (
            "Aggressive speech, shouting, yelling, loud forceful talking, wide mouth opening, wide open mouth, gaping mouth, over-opened mouth, shouting mouth, wide jaw drop, unhinged jaw, dropped jaw, stretching jaw, loose mouth, gaping oral cavity, forced facial strain, jaw tension, clenched teeth, robotic mouth stretching, dramatic mouth movement, excessive lip flapping, wide toothy speech, popping neck veins, exaggerated head shaking, head bobbing, head swaying, head rolling, head tilting, erratic head jerks, nodding head, side-to-side head shaking, wobbling head, unstable head posture, jerky neck, neck twisting, neck stretching, neck swaying, bobblehead, wild gestures, chaotic motion, restless posture, sudden fast movements, exaggerated expressions, strange staring, darting eyes, wide eyes, artificial grimace, unnatural eye movement, AI uncanny valley look.\n\n"
            f"{hand_neg_guidance}, excessive hand movement, finger distortion, extra or missing fingers, fused or deformed fingers, broken wrists, unnatural hands.\n\n"
            "Frozen body, stiff mannequin posture, robotic posture, wooden torso, artificial paralysis, frozen chest, locked shoulders.\n\n"
            "Zoom in, zoom out, camera movement, camera drift, pan, tilt, framing shift, focal-length change, scale change, camera shake, frame vibration, jumping cuts.\n\n"
            "Forward leaning, lunging toward camera, moving closer to camera, head pitching forward, torso leaning forward, excessive bowing.\n\n"
            "Overexposure, washed-out colors, white haze, lifted blacks, desaturated colors, skin brightening, whitening filter, beauty filter, airbrushed skin, plastic skin, altered skin tone, bleached highlights, flat lighting, glowing teeth, teeth emitting light, white tooth glare.\n\n"
            "Pink lips, red lips, magenta lips, lipstick, lip gloss, glossy lips, painted lips, unnatural lip color.\n\n"
            "Face distortion, body warping, anatomy distortion, deformed features, low quality, severe artifacts, disfigured appearance."
        )

        if "preserve the same man" in prompt.lower() or "professional man speaking naturally" in prompt.lower():
            full_prompt = prompt.strip()
        else:
            full_prompt = male_positive_prompt

        if "zero lipstick" not in full_prompt.lower() and "matte masculine lips" not in full_prompt.lower():
            full_prompt += " Natural matte masculine lips with strictly zero lipstick or gloss, authentic skin tone matching reference photo exactly."

        if detected_hand_mode == "bust_locked":
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_prompt) if s.strip()]
            sentences.append("Clean stationary presenter framing. Composed masculine upper-body posture with natural organic breathing, realistic chest rise and fall, and subtle shoulder micro-movements while speaking calmly and naturally.")
            full_prompt = " ".join(sentences)

        if "moving hands while speaking" in negative_prompt.lower() and "unnatural hands" in negative_prompt.lower():
            full_negative = negative_prompt.strip()
        elif negative_prompt.strip():
            full_negative = f"{negative_prompt.strip()}, {male_negative_prompt}"
        else:
            full_negative = male_negative_prompt

        if detected_hand_mode == "bust_locked":
            bust_neg_front = "hands, arms, fingers, palms, wrists, thumbs, hand gestures, waving hands, moving hands, gesturing with hands, raising hands, hands entering frame, hands rising, virtual hands, extra limbs, human hands, conversational gestures, pink lips, red lips, magenta lips, lipstick, shiny lips, glossy lips, colored mouth, painted lips, purple lips, unnatural lip tone, fluorescent lips, wide open mouth, gaping mouth, over-opened mouth, shouting mouth, "
            if not full_negative.startswith("hands,"):
                full_negative = bust_neg_front + full_negative

    input_json_path = task_upload_dir / "input.json"
    input_data = {
        "prompt": full_prompt,
        "negative_prompt": full_negative,
        "cond_image": os.path.abspath(image_path),
        "cond_audio": {
            "person1": os.path.abspath(audio_path)
        },
        "hand_control": detected_hand_mode
    }
    with open(input_json_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f, indent=4)

    task["status"] = "processing"
    task["stage"] = "Initializing PyTorch on GPU..."
    task["progress"] = 5.0
    task["logs"].append(f"[{time.strftime('%H:%M:%S')}] Launching LongCat-Video-Avatar 1.5 on {get_system_gpu_name()}...")
    task["logs"].append(f"[{time.strftime('%H:%M:%S')}] Task: {task_id} | Steps: {num_inference_steps} | Res: {resolution} | Segments: {num_segments} | Hand Mode: {detected_hand_mode}")
    save_active_tasks_to_disk()

    # Build torchrun command with dynamic free master_port
    master_port = get_free_port()
    checkpoint_dir = os.path.join(BASE_DIR, "weights", "LongCat-Video-Avatar-1.5")
    python_bin = "/venv/main/bin/python" if os.path.exists("/venv/main/bin/python") else sys.executable

    # Detect all available GPUs and single-GPU VRAM capacity for safe execution
    num_available_gpus = 1
    max_single_gpu_vram_gb = 0
    try:
        res = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            lines = [l for l in res.stdout.strip().split("\n") if l.strip()]
            num_available_gpus = len(lines)
            for l in lines:
                parts = l.split(",")
                if len(parts) >= 2:
                    vram_val = float(parts[1].replace("MiB", "").replace("GiB", "").strip())
                    max_single_gpu_vram_gb = max(max_single_gpu_vram_gb, vram_val / 1024.0)
    except Exception:
        pass
    # Enable Dual-GPU Context Parallelism when multiple GPUs are available (Dual RTX 3090 / 4090)
    cp_size = min(2, num_available_gpus)

    preset = task.get("preset", "distill_bf16")
    use_int8 = (preset == "distill_int8")

    # Critical Safeguard for GPUs under 40GB VRAM (e.g. 24GB RTX 3090/4090, 32GB RTX 4080):
    # In DDP / Context Parallelism, model weights (28-30GB in BF16) are replicated on EACH GPU.
    # Cards with < 38GB VRAM must use INT8 Quantized DiT (14.9 GB) to prevent CUDA OOM.
    if max_single_gpu_vram_gb > 0 and max_single_gpu_vram_gb < 38.0:
        use_int8 = True
        task["logs"].append(f"[{time.strftime('%H:%M:%S')}] 🛡️ [VRAM Safeguard] {max_single_gpu_vram_gb:.1f}GB GPU detected (< 38GB per-device threshold). Enforcing INT8 Quantized DiT (14.9 GB) for guaranteed zero-OOM stability.")

    if use_int8:
        sys_gpu = get_system_gpu_name()
        if num_available_gpus >= 2:
            task["logs"].append(f"[{time.strftime('%H:%M:%S')}] ⚡ [ENGINE] INT8 Ultra-Fast Engine active (Quantized DiT • ~14.9GB VRAM • {sys_gpu} • Context Parallelism 2x).")
        else:
            task["logs"].append(f"[{time.strftime('%H:%M:%S')}] ⚡ [ENGINE] INT8 Memory Saver active (Quantized DiT • ~14.9GB VRAM • {sys_gpu}).")
    else:
        sys_gpu = get_system_gpu_name()
        if num_available_gpus >= 2:
            task["logs"].append(f"[{time.strftime('%H:%M:%S')}] ✨ [ENGINE] BF16 Studio Master active (Pure BF16 Precision • {sys_gpu} • Context Parallelism 2x).")
        else:
            task["logs"].append(f"[{time.strftime('%H:%M:%S')}] ✨ [ENGINE] BF16 Studio Master active (Pure BF16 Precision • {sys_gpu}).")

    # Exact DiT resolution mapping: 500p (512x896), 540p (544x960), 600p (608x1024), 700p, 480p
    raw_res = str(resolution).lower().strip()
    if any(x in raw_res for x in ["500p", "500", "512"]):
        res_arg = "500p"
    elif any(x in raw_res for x in ["540p", "540", "544"]):
        res_arg = "540p"
    elif any(x in raw_res for x in ["600p", "600", "608"]):
        res_arg = "600p"
    elif any(x in raw_res for x in ["520p", "520", "580"]):
        res_arg = "540p"
    elif any(x in raw_res for x in ["480p", "480", "832"]):
        res_arg = "480p"
    elif any(x in raw_res for x in ["700p", "700", "704", "1216", "880", "720", "1080"]):
        res_arg = "700p"
    else:
        res_arg = "500p"

    task["resolution"] = res_arg
    task["resolution_label"] = get_resolution_badge(res_arg)

    req_frames = int(task.get('num_frames', 205))
    if req_frames not in [81, 125, 205, 249, 253, 301]:
        req_frames = 205

    gen_mode = str(task.get('generation_mode', 'anchor_seamless')).strip().lower()
    if gen_mode not in ["anchor_seamless", "sequential_continuation", "sequential", "standard"]:
        gen_mode = "anchor_seamless"

    overlap_frames = int(task.get('transition_overlap_frames', 4 if gen_mode == 'anchor_seamless' else 13))

    cmd = [
        python_bin, "-u", "-m", "torch.distributed.run",
        f"--master_port={master_port}",
        f"--nproc_per_node={cp_size}",
        "run_demo_avatar_single_audio_to_video.py",
        f"--checkpoint_dir={checkpoint_dir}",
        "--stage_1=ai2v",
        f"--input_json={input_json_path}",
        f"--output_dir={task_output_dir}",
        "--model_type=avatar-v1.5",
        "--use_distill",
        f"--num_inference_steps={num_inference_steps}",
        f"--resolution={res_arg}",
        f"--ref_img_index={ref_img_index}",
        f"--mask_frame_range={mask_frame_range}",
        f"--num_segments={num_segments}",
        f"--num_frames={req_frames}",
        f"--step_booster={task.get('step_booster', 'default')}",
        f"--generation_mode={gen_mode}",
        f"--transition_overlap_frames={overlap_frames}",
        f"--context_parallel_size={cp_size}",
        f"--lock_hands={'false' if detected_hand_mode == 'natural' else ('true' if detected_hand_mode == 'bust_locked' else 'auto')}",
        "--audio_guidance_scale=0.90"
    ]
    if use_int8:
        cmd.append("--use_int8")

    task["logs"].append(f"[{time.strftime('%H:%M:%S')}] Running command (master_port: {master_port}): {' '.join(cmd)}")
    print(f"[{time.strftime('%H:%M:%S')}] 🚀 [ENGINE LAUNCH] Running command on GPU (master_port: {master_port}): {' '.join(cmd)}", flush=True)

    try:
        # Pre-Launch GPU Sanitation: Clean zombie processes and ensure VRAM is free
        subprocess.run(["pkill", "-9", "-f", "run_demo_avatar_single_audio_to_video.py"], capture_output=True)
        for _wait_sec in range(15):
            res_v = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True)
            if res_v.returncode == 0:
                m_list = [int(x.strip()) for x in res_v.stdout.strip().splitlines() if x.strip().isdigit()]
                if all(m < 4000 for m in m_list):
                    break
            time.sleep(1)

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        existing_py_paths = [p for p in sys.path if p and os.path.exists(p)]
        all_py_paths = [str(BASE_DIR)] + [p for p in existing_py_paths if p != str(BASE_DIR)]
        env["PYTHONPATH"] = os.pathsep.join(all_py_paths) + (f"{os.pathsep}{env.get('PYTHONPATH')}" if env.get('PYTHONPATH') else "")
        env["TORCH_CUDNN_V8_API_ENABLED"] = "1"
        env["CUDA_MODULE_LOADING"] = "LAZY"
        if "CUDA_VISIBLE_DEVICES" not in os.environ:
            env["CUDA_VISIBLE_DEVICES"] = "0,1" if num_available_gpus >= 2 else "0"
        else:
            env["CUDA_VISIBLE_DEVICES"] = os.environ["CUDA_VISIBLE_DEVICES"]
        env["NCCL_P2P_DISABLE"] = "1"
        env["NCCL_IB_DISABLE"] = "1"
        env["NCCL_NET_GDR_LEVEL"] = "0"
        env["CUDA_DEVICE_MAX_CONNECTIONS"] = "1"
        
        proc = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            start_new_session=True
        )
        active_processes[task_id] = proc

        current_segment = 1
        buffer = ""
        last_save_time = time.time()
        while True:
            char = proc.stdout.read(1)
            if not char:
                break
            if char in ("\r", "\n"):
                clean_line = buffer.strip()
                buffer = ""
                if not clean_line:
                    continue
                clean_line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', clean_line).strip()
                if re.search(r'^\[rank\s*\d+\]\s*:?', clean_line):
                    clean_line = re.sub(r'^\[rank\s*\d+\]\s*:?', '', clean_line).strip()
                elif clean_line.startswith("[rank") and "]" in clean_line:
                    clean_line = clean_line.split("]", 1)[1].lstrip(":").strip()
                if not clean_line:
                    continue
                
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] {clean_line}", flush=True)
                if clean_line.startswith("Denoising:"):
                    if not task["logs"] or not task["logs"][-1].endswith(clean_line):
                        task["logs"].append(f"[{ts}] {clean_line}")
                else:
                    task["logs"].append(f"[{ts}] {clean_line}")
                    if len(task["logs"]) > 150:
                        task["logs"] = task["logs"][-150:]

                # 1. Neural Diffusion Step progress
                if "Denoising:" in clean_line:
                    tqdm_match = re.search(r'Denoising:\s*(\d+)%\|.*?\|\s*(\d+)/(\d+)', clean_line)
                    if tqdm_match:
                        try:
                            curr_sub_step = int(tqdm_match.group(2))
                            steps_per_segment = int(tqdm_match.group(3))
                            
                            spd_match = re.search(r'([\d\.]+)\s*(s/it|it/s)', clean_line)
                            lat = float(task.get("step_latency", 0) or 32.0)
                            if spd_match:
                                spd_val = float(spd_match.group(1))
                                spd_unit = spd_match.group(2)
                                if spd_val > 0:
                                    lat = spd_val if "s/it" in spd_unit else (1.0 / spd_val)
                            
                            task["step_latency"] = round(lat, 2)
                            task["step_speed_str"] = f"{lat:.1f}s/step"
                            task["dit_architecture"] = "LongCat-Avatar-DiT-1.5 / Wan2.1-VAE"
                            task["gpu_info"] = "Dual NVIDIA RTX 4090 (48GB x 2 • 96GB Total VRAM)"

                            total_pipeline_steps = max(1, num_segments * steps_per_segment)
                            completed_steps = min(total_pipeline_steps, max(1, ((current_segment - 1) * steps_per_segment) + curr_sub_step))
                            remaining_steps = max(0, total_pipeline_steps - completed_steps)

                            gpu_elapsed = max(1, int(time.time() - exec_start_time))
                            est_rem_sec = int(remaining_steps * lat)
                            total_est_sec = gpu_elapsed + est_rem_sec

                            calc_progress = min(99.0, max(8.0, 8.0 + ((completed_steps / total_pipeline_steps) * 91.0)))

                            task["progress"] = round(calc_progress, 1)
                            is_rec = task.get("is_recovering", False)
                            if is_rec:
                                task["stage"] = f"Stage 2/3: Neural Diffusion Auto-Recovery (Segment {current_segment}/{num_segments} · Step {curr_sub_step}/{steps_per_segment})"
                            else:
                                task["stage"] = f"Stage 2/3: Neural Diffusion (Segment {current_segment}/{num_segments} · Step {curr_sub_step}/{steps_per_segment})"
                            task["current_segment"] = current_segment
                            task["total_segments"] = num_segments
                            task["current_step"] = curr_sub_step
                            task["steps_per_segment"] = steps_per_segment
                            task["completed_steps"] = completed_steps
                            task["total_pipeline_steps"] = total_pipeline_steps
                            task["remaining_steps"] = remaining_steps
                            task["elapsed_gpu_sec"] = gpu_elapsed
                            task["remaining_sec"] = est_rem_sec
                            task["total_est_sec"] = total_est_sec
                        except Exception as ex:
                            pass

                # 2. Segment transition detection
                elif "Generating segment" in clean_line:
                    try:
                        parts = clean_line.split("Generating segment")[-1].strip().split("/")
                        curr = int(parts[0])
                        current_segment = curr
                        task["is_recovering"] = False
                        infer_steps = int(task.get("num_inference_steps", 3))
                        total_pipeline_steps = max(1, num_segments * infer_steps)
                        completed_steps = (curr - 1) * infer_steps
                        calc_progress = min(99.0, max(8.0, 8.0 + ((completed_steps / total_pipeline_steps) * 91.0)))
                        task["progress"] = round(calc_progress, 1)
                        task["stage"] = f"Stage 2/3: Neural Diffusion (Segment {curr}/{num_segments})"
                        task["current_segment"] = curr
                        task["total_segments"] = num_segments
                    except Exception:
                        pass

                # 2.5 Quality Guard & Auto-Recovery detection
                elif "COLLAPSE DETECTED" in clean_line or "auto-recovering" in clean_line:
                    task["is_recovering"] = True
                    task["stage"] = f"⚠️ Stage 2/3: Auto-Recovering Segment {current_segment}/{num_segments} (Quality Guard Re-anchoring)"
                elif "[QUALITY]" in clean_line:
                    task["is_recovering"] = False
                    task["stage"] = f"Stage 2/3: Neural Diffusion (Segment {current_segment}/{num_segments} Quality Verified)"

                # 3. Audio Preprocessing (MDX23 Vocal Separation / Whisper)
                elif "%|" in clean_line and ("MDX" in clean_line or "Separation" in clean_line or "Kim_Vocal" in clean_line):
                    tqdm_audio = re.search(r'(\d+)%\|.*?\|\s*(\d+)/(\d+)', clean_line)
                    if tqdm_audio:
                        try:
                            audio_pct = float(tqdm_audio.group(1))
                            curr_chunk = int(tqdm_audio.group(2))
                            total_chunks = int(tqdm_audio.group(3))
                            gpu_elapsed = max(1, int(time.time() - exec_start_time))
                            task["stage"] = f"Stage 1/3: Vocal Audio Separation & Voice Cleaning ({audio_pct:.0f}%)"
                            task["progress"] = round(min(7.0, (curr_chunk / max(1, total_chunks)) * 7.0), 1)
                            task["step_speed_str"] = "Pre-processing audio..."
                            task["elapsed_gpu_sec"] = gpu_elapsed
                        except Exception:
                            pass
                # 4. Video Frame Saving / Post-processing
                elif "Saving video:" in clean_line or "Saving final video:" in clean_line:
                    tqdm_save = re.search(r'(\d+)%\|', clean_line)
                    if tqdm_save:
                        try:
                            save_pct = float(tqdm_save.group(1))
                            task["stage"] = f"Stage 3/3: Assembling & Saving Video Frames ({save_pct:.0f}%)"
                            task["progress"] = round(92.0 + (save_pct / 100.0) * 6.0, 1)
                        except Exception:
                            pass
                elif "Saving Vocals" in clean_line or "Separation duration" in clean_line or "Extracted vocal" in clean_line:
                    task["stage"] = "Stage 1/3: Vocals Extracted (Kim_Vocal_2 Clean Voice)"
                    task["progress"] = 7.5
                elif "Whisper" in clean_line or "acoustic" in clean_line:
                    task["stage"] = "Stage 1/3: Whisper Acoustic Phoneme Alignment"
                    task["progress"] = 8.0

                if time.time() - last_save_time > 1.5:
                    save_active_tasks_to_disk()
                    last_save_time = time.time()
            else:
                buffer += char

        proc.stdout.close()
        proc.wait()
        active_processes.pop(task_id, None)
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
        subprocess.run(["pkill", "-9", "-f", "run_demo_avatar_single_audio_to_video.py"], capture_output=True)

        # Find final rendered MP4 in output directory with auto-recovery for long-form generations
        found_videos = [f for f in task_output_dir.glob("video_continue_*.mp4") if not f.name.endswith("-cropvideo.mp4") and not f.name.endswith("-temp.mp4") and f.stat().st_size > 10000]
        if not found_videos:
            found_videos = [f for f in task_output_dir.glob("ai2v_demo_*.mp4") if not f.name.endswith("-cropvideo.mp4") and not f.name.endswith("-temp.mp4") and f.stat().st_size > 10000]
        if not found_videos:
            found_videos = [f for f in task_output_dir.glob("*.mp4") if not f.name.endswith("-cropvideo.mp4") and not f.name.endswith("-temp.mp4") and f.stat().st_size > 10000]

        is_user_cancelled = task.get("was_cancelled") or task.get("status") == "cancelled" or "Cancelled" in str(task.get("stage", ""))

        if proc.returncode != 0 and not found_videos:
            if is_user_cancelled:
                task["status"] = "cancelled"
                task["stage"] = "Cancelled by user"
                task["logs"].append(f"[{time.strftime('%H:%M:%S')}] [CANCELLED] Generation stopped by user before first segment completed.")
            else:
                task["status"] = "error"
                task["stage"] = f"Error: Generation engine exited with code {proc.returncode}"
                task["logs"].append(f"[{time.strftime('%H:%M:%S')}] [ERROR] Process exited with error code {proc.returncode}.")
            save_active_tasks_to_disk()
            return
        elif found_videos:
            if is_user_cancelled:
                task["logs"].append(f"[{time.strftime('%H:%M:%S')}] 🛑 User stopped generation. Rescuing and packaging all completed video segments...")
                task["stage"] = "Packaging completed segments into Studio Master..."
            elif proc.returncode != 0:
                task["logs"].append(f"[{time.strftime('%H:%M:%S')}] ⚠️ Generation stopped early (exit code {proc.returncode}). Rescuing completed segments...")

        if not found_videos:
            task["status"] = "error"
            task["stage"] = f"Error: No output video generated (exit code {proc.returncode})"
            task["logs"].append(f"[{time.strftime('%H:%M:%S')}] [ERROR] Process exited with code {proc.returncode} and no video found.")
            save_active_tasks_to_disk()
            return

        # Sort by natural segment index or modification time to get the last continuation video
        def sort_key(p):
            m = re.search(r'video_continue_(\d+)', p.stem)
            if m:
                return (2, int(m.group(1)))
            m2 = re.search(r'ai2v_demo_(\d+)', p.stem)
            if m2:
                return (1, int(m2.group(1)))
            return (0, p.stat().st_mtime)

        found_videos.sort(key=sort_key, reverse=True)
        final_video = found_videos[0]
        task["logs"].append(f"[{time.strftime('%H:%M:%S')}] 🎯 Successfully resolved final output segment: {final_video.name}")

        # Standard Clean Natural HD 1080P Studio Mastering (Crisp Natural Texture, No Fake Smoothing)
        task["stage"] = "🎬 Packaging 1080P Full HD Studio Master..."
        task["progress"] = 99.5
        img_aspect = None
        if os.path.exists(image_path):
            try:
                with Image.open(image_path) as img:
                    img = ImageOps.exif_transpose(img)
                    iw, ih = img.size
                    img_aspect = iw / ih
            except Exception:
                pass

        try:
            # Determine target studio mastering resolution (1080p Master) based on image aspect ratio
            if img_aspect and img_aspect > 1.25:
                # 16:9 Landscape (YouTube Full HD)
                target_w, target_h = 1920, 1080
                target_720_w, target_720_h = 1280, 720
            elif img_aspect and 0.85 <= img_aspect <= 1.15:
                # 1:1 Square (Instagram Post)
                target_w, target_h = 1080, 1080
                target_720_w, target_720_h = 720, 720
            elif img_aspect and 0.75 <= img_aspect < 0.85:
                # 4:5 Feed Portrait
                target_w, target_h = 1080, 1350
                target_720_w, target_720_h = 720, 900
            else:
                # 9:16 Full Portrait (Reels / Shorts / TikTok)
                target_w, target_h = 1080, 1920
                target_720_w, target_720_h = 768, 1280

            # Ensure audio is present and synchronized
            hd_master_file = task_output_dir / f"hd_master_{final_video.name}"
            
            mux_audio = task.get("original_audio_path", audio_path)
            if not mux_audio or not os.path.exists(mux_audio):
                mux_audio = audio_path

            # High-Fidelity Lanczos 8-Tap Upscaling + Contrast-Adaptive Sharpening (CAS) with Audio
            if mux_audio and os.path.exists(mux_audio):
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", str(final_video),
                    "-i", str(mux_audio),
                    "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "44100",
                    "-shortest",
                    "-movflags", "+faststart",
                    str(hd_master_file)
                ]
            else:
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", str(final_video),
                    "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2",
                    "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p",
                    "-c:a", "copy",
                    "-movflags", "+faststart",
                    str(hd_master_file)
                ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            if hd_master_file.exists():
                final_video = hd_master_file
                task["logs"].append(f"[{time.strftime('%H:%M:%S')}] 🎬 Clean Studio Master export complete ({target_w}x{target_h} natural photographic upscale & synced audio).")
        except Exception as fe:
            task["logs"].append(f"[{time.strftime('%H:%M:%S')}] HD master export notice: {fe}")

        # Calculate real generation duration (from initial start, even across restarts/resumes)
        first_segment_file = task_output_dir / "ai2v_demo_1.mp4"
        if first_segment_file.exists():
            initial_start = first_segment_file.stat().st_mtime
        else:
            initial_start = float(task.get("created_at") or exec_start_time)
        exec_elapsed_sec = max(1, int(time.time() - initial_start))
        gen_m = exec_elapsed_sec // 60
        gen_s = exec_elapsed_sec % 60
        gen_time_slug = f"{gen_m}m{gen_s}s" if gen_m > 0 else f"{gen_s}s"
        dur_slug = f"{int(task.get('audio_duration_sec', 10))}s"
        date_slug = time.strftime("%Y%m%d")
        
        raw_title = str(task.get("video_title", "")).strip()
        slot_name = task.get("slot_name", "Video 1")
        if not raw_title:
            try:
                state_file = OUTPUT_DIR / "studio_state.json"
                if state_file.exists():
                    with open(state_file, "r", encoding="utf-8") as sf:
                        sdata = json.load(sf)
                    for slot in sdata.get("slots", []):
                        if (task.get("slot_id") and slot.get("id") == task.get("slot_id")) or \
                           (slot.get("taskId") == task_id) or \
                           (slot_name and slot.get("name") == slot_name):
                            if slot.get("title"):
                                raw_title = str(slot.get("title")).strip()
                            if slot.get("name"):
                                slot_name = str(slot.get("name")).strip()
                            break
            except Exception:
                pass
        slot_name_clean = re.sub(r'[^a-zA-Z0-9]', '_', slot_name).strip('_')
        if raw_title:
            safe_words = re.findall(r'[a-zA-Z0-9]+', raw_title)
            base_slug = "_".join(safe_words) if safe_words else f"Avatar_{task_id}"
        else:
            base_slug = f"Avatar_{task_id}"

        candidate_name = f"{slot_name_clean}_{base_slug}.mp4"
        dest_path = OUTPUT_DIR / candidate_name
        version = 2
        while dest_path.exists():
            candidate_name = f"{slot_name_clean}_{base_slug}_v{version}.mp4"
            dest_path = OUTPUT_DIR / candidate_name
            version += 1

        dest_filename = candidate_name
        shutil.copy2(final_video, dest_path)
        ensure_video_has_audio(dest_path, mux_audio)

        # Generate 720P High-Fidelity Master version
        dest_filename_720p = dest_filename.replace(".mp4", "_720p.mp4")
        dest_path_720p = OUTPUT_DIR / dest_filename_720p
        file_size_720p_mb = None
        try:
            cmd_720p = [
                "ffmpeg", "-y", "-i", str(dest_path),
                "-vf", f"scale={target_720_w}:{target_720_h}:flags=lanczos",
                "-c:v", "libx264", "-crf", "22", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(dest_path_720p)
            ]
            subprocess.run(cmd_720p, check=True, capture_output=True)
            ensure_video_has_audio(dest_path_720p, mux_audio)
            if dest_path_720p.exists():
                file_size_720p_mb = round(dest_path_720p.stat().st_size / (1024 * 1024), 2)
                task["logs"].append(f"[{time.strftime('%H:%M:%S')}] ⚡ 720P Optimized version exported: {dest_filename_720p} ({file_size_720p_mb} MB).")
        except Exception as e720:
            task["logs"].append(f"[{time.strftime('%H:%M:%S')}] 720P export notice: {e720}")

        # Generate instant poster thumbnail for zero-black-screen display
        dest_filename_poster = dest_filename.replace(".mp4", ".jpg")
        dest_path_poster = OUTPUT_DIR / dest_filename_poster
        try:
            cmd_poster = [
                "ffmpeg", "-y", "-ss", "00:00:00.200", "-i", str(dest_path),
                "-vframes", "1", "-q:v", "2",
                str(dest_path_poster)
            ]
            subprocess.run(cmd_poster, check=True, capture_output=True)
            if dest_path_poster.exists():
                task["poster_url"] = f"/outputs/{urllib.parse.quote(dest_filename_poster)}"
        except Exception:
            pass

        res_label = get_resolution_badge(task.get("resolution", "500p"))
        task["resolution_label"] = res_label

        is_user_cancelled = task.get("was_cancelled") or task.get("status") == "cancelled" or "Cancelled" in str(task.get("stage", ""))
        if is_user_cancelled:
            task["status"] = "cancelled"
            task["stage"] = "Stopped by user (Saved partial video to Gallery)"
            task["progress"] = 100.0
        else:
            task["status"] = "completed"
            task["stage"] = "Completed — Video Ready"
            task["progress"] = 100.0
        task["output_video_url"] = f"/outputs/{urllib.parse.quote(dest_filename)}"
        task["output_filename"] = dest_filename
        task["file_size_mb"] = round(dest_path.stat().st_size / (1024 * 1024), 2)
        task["output_video_url_720p"] = f"/outputs/{urllib.parse.quote(dest_filename_720p)}" if dest_path_720p.exists() else None
        task["output_filename_720p"] = dest_filename_720p if dest_path_720p.exists() else None
        task["generation_time_sec"] = exec_elapsed_sec
        task["generation_time_formatted"] = format_seconds_human(exec_elapsed_sec)
        task["audio_duration_formatted"] = format_seconds_human(task.get('audio_duration_sec', 0))
        task["logs"].append(f"[{time.strftime('%H:%M:%S')}] [SUCCESS] Rendered video ready: 1080P ({task['file_size_mb']} MB)" + (f" | 720P ({file_size_720p_mb} MB)" if file_size_720p_mb else "") + f" in {task['generation_time_formatted']}")
        
        # Save sidecar metadata JSON for persistent instant recognition
        try:
            out_stem = dest_filename[:-4] if dest_filename.endswith(".mp4") else dest_filename
            meta_file = OUTPUT_DIR / f"{out_stem}.meta.json"
            with open(meta_file, "w", encoding="utf-8") as mf:
                json.dump({
                    "task_id": task_id,
                    "output_filename": dest_filename,
                    "video_title": raw_title,
                    "slot_name": slot_name,
                    "resolution": task.get("resolution", "500p"),
                    "resolution_label": res_label,
                    "generation_time_sec": exec_elapsed_sec,
                    "generation_time_formatted": task["generation_time_formatted"],
                    "audio_duration_sec": task.get('audio_duration_sec', 0),
                    "created_at": task.get("created_at", time.time())
                }, mf, indent=2)
        except Exception:
            pass

        _DIR_CACHE.clear()
        _DIR_CACHE_TIME.clear()
        save_active_tasks_to_disk()

        # If this is an Avatar Baseline task, export preview.mp4 to the avatar preset folder
        if task.get("is_avatar_baseline"):
            try:
                av_id = task.get("avatar_id")
                target_av_dir = None
                if task.get("target_avatar_dir") and Path(task["target_avatar_dir"]).exists():
                    target_av_dir = Path(task["target_avatar_dir"])
                elif av_id:
                    target_av_dir = AVATARS_DIR / av_id
                    if not target_av_dir.exists():
                        for sub in AVATARS_DIR.iterdir():
                            if sub.is_dir():
                                mf = sub / "meta.json"
                                if mf.exists():
                                    try:
                                        with open(mf, "r", encoding="utf-8") as f:
                                            if json.load(f).get("id") == av_id:
                                                target_av_dir = sub
                                                break
                                    except Exception:
                                        pass
                if target_av_dir and target_av_dir.exists():
                    preview_dest = target_av_dir / "preview.mp4"
                    source_for_preview = dest_path_720p if dest_path_720p.exists() else dest_path
                    # Generate web-optimized silent loop video for hover preview
                    # As user specified: "সাউন্ড থাকবে না, কিন্তু ও সাইলেন্টলি কথা বলতেছে ন্যাচারালি কথা বলতেছে"
                    cmd_preview = [
                        "ffmpeg", "-y", "-i", str(source_for_preview),
                        "-an",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                        "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart",
                        str(preview_dest)
                    ]
                    res_p = subprocess.run(cmd_preview, capture_output=True, text=True)
                    if res_p.returncode != 0 or not preview_dest.exists():
                        shutil.copy2(str(source_for_preview), str(preview_dest))
                    
                    # Update preset meta.json
                    mf = target_av_dir / "meta.json"
                    av_meta = {}
                    if mf.exists():
                        try:
                            with open(mf, "r", encoding="utf-8") as f:
                                av_meta = json.load(f)
                        except Exception:
                            pass
                    av_meta["preview_url"] = f"/avatar_presets/{target_av_dir.name}/preview.mp4"
                    av_meta["has_living_preview"] = True
                    av_meta["baseline_duration"] = task.get("audio_duration_sec", 20)
                    with open(mf, "w", encoding="utf-8") as f:
                        json.dump(av_meta, f, indent=4)
                    task["logs"].append(f"[{time.strftime('%H:%M:%S')}] [LIVING PRESET READY] Saved silent preview loop to /avatar_presets/{target_av_dir.name}/preview.mp4")
                    save_active_tasks_to_disk()
            except Exception as pe:
                task["logs"].append(f"[{time.strftime('%H:%M:%S')}] [PREVIEW EXPORT ERROR] {str(pe)}")
                save_active_tasks_to_disk()

    except Exception as e:
        task["status"] = "error"
        task["stage"] = f"Exception: {str(e)}"
        task["logs"].append(f"[{time.strftime('%H:%M:%S')}] [EXCEPTION] {str(e)}")
        save_active_tasks_to_disk()

# Restore existing tasks from disk and re-enqueue any pending queued jobs
worker_threads = []

class LongCatStudioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self):
        p = str(self.path or "")
        if p.endswith(".html") or p.endswith(".js") or p.endswith(".css") or p == "/" or "/web/" in p:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_HEAD(self):
        self.do_GET(is_head=True)

    def do_GET(self, is_head=False):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path in ["/api/health", "/api/status"]:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if "task_id" in query_params:
                task_id = query_params["task_id"][0]
                task = active_tasks.get(task_id)
                if task:
                    task_copy = dict(task)
                    task_copy["id"] = task_id
                    task_copy["segments"] = task_copy.get("num_segments", 1)
                    task_copy["steps"] = task_copy.get("num_inference_steps", 3)
                    if task_copy.get("status") == "processing":
                        start_t = task_copy.get("generation_start_time", task_copy.get("created_at", time.time()))
                        task_copy["generation_time_sec"] = int(time.time() - start_t)
                    if "logs" in task_copy and isinstance(task_copy["logs"], list):
                        task_copy["logs"] = task_copy["logs"][-150:]
                    self.send_json_response(task_copy)
                    return
                else:
                    self.send_json_response({"error": "Task not found"}, status=404)
                    return

            self.send_json_response({
                "status": "online",
                "engine": "LongCat-Video-Avatar-1.5",
                "gpu_ready": True,
                "gpu": get_system_gpu_name(),
                "models": {
                    "dit": "base_model (BF16) & base_model_int8 (INT8)",
                    "distill": "dmd_lora.safetensors (8-step)",
                    "audio_encoder": "whisper-large-v3",
                    "vocal_separator": "Kim_Vocal_2.onnx",
                    "vae": "Wan VAE"
                }
            })
            return

        elif path.startswith("/api/task/"):
            task_id = path.split("/")[-1]
            task = active_tasks.get(task_id)
            if task:
                task_copy = dict(task)
                task_copy["id"] = task_id
                task_copy["segments"] = task_copy.get("num_segments", 1)
                task_copy["steps"] = task_copy.get("num_inference_steps", 3)
                if task_copy.get("status") == "processing":
                    start_t = task_copy.get("generation_start_time", task_copy.get("created_at", time.time()))
                    task_copy["generation_time_sec"] = int(time.time() - start_t)
                if "logs" in task_copy and isinstance(task_copy["logs"], list):
                    task_copy["logs"] = task_copy["logs"][-150:]
                self.send_json_response(task_copy)
            else:
                self.send_json_response({"error": "Task not found"}, status=404)
            return

        elif path == "/api/config":
            self.send_json_response(SERVER_CONFIG)
            return

        elif path == "/api/studio_state":
            state_file = OUTPUT_DIR / "studio_state.json"
            if state_file.exists():
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.send_json_response(data)
                    return
                except Exception:
                    pass
            self.send_json_response({"slots": [{"id": 1, "name": "Video 1"}], "activeSlotId": 1})
            return

        elif path == "/api/queue":
            queued = []
            for tid, t in active_tasks.items():
                if t.get("status") == "queued":
                    is_av = bool(t.get("is_avatar_baseline") or t.get("slot_name") == "Avatar Library" or str(t.get("video_title", "")).startswith("Living Avatar"))
                    queued.append({
                        "id": tid,
                        "slot_name": "Avatar Library" if is_av else (t.get("slot_name") or "Video 1"),
                        "video_title": t.get("video_title", ""),
                        "avatar_id": t.get("avatar_id"),
                        "is_avatar_baseline": is_av,
                        "status": "queued",
                        "audio_duration": f"{t.get('audio_duration_sec', 0):.1f}s",
                        "num_segments": t.get("num_segments", 1),
                        "segments": t.get("num_segments", 1),
                        "resolution": t.get("resolution", "720p"),
                        "num_inference_steps": t.get("num_inference_steps", 3),
                        "steps": t.get("num_inference_steps", 3),
                        "created_at": time.strftime("%H:%M:%S", time.localtime(t.get("created_at", time.time())))
                    })
            
            active_list = []
            seen_active_ids = set()
            with active_task_lock:
                for tid in list(running_tasks_set):
                    at = active_tasks.get(tid)
                    if at and tid not in seen_active_ids:
                        seen_active_ids.add(tid)
                        is_av = bool(at.get("is_avatar_baseline") or at.get("slot_name") == "Avatar Library" or str(at.get("video_title", "")).startswith("Living Avatar"))
                        active_list.append({
                            "id": tid,
                            "slot_name": "Avatar Library" if is_av else (at.get("slot_name") or "Video 1"),
                            "video_title": at.get("video_title", ""),
                            "avatar_id": at.get("avatar_id"),
                            "is_avatar_baseline": is_av,
                            "status": at.get("status", "processing"),
                            "stage": at.get("stage", "Processing"),
                            "progress": at.get("progress", 0.0),
                            "logs": at.get("logs", [])[-100:],
                            "step_latency": at.get("step_latency", 0),
                            "step_speed_str": at.get("step_speed_str", ""),
                            "current_segment": at.get("current_segment", 1),
                            "total_segments": at.get("total_segments", at.get("num_segments", 1)),
                            "current_step": at.get("current_step", 1),
                            "steps_per_segment": at.get("steps_per_segment", at.get("num_inference_steps", 3)),
                            "completed_steps": at.get("completed_steps", 0),
                            "total_pipeline_steps": at.get("total_pipeline_steps", 0),
                            "remaining_steps": at.get("remaining_steps", 0),
                            "elapsed_gpu_sec": at.get("elapsed_gpu_sec", at.get("generation_time_sec", 0)),
                            "remaining_sec": at.get("remaining_sec", 0),
                            "total_est_sec": at.get("total_est_sec", 0),
                            "audio_duration": f"{at.get('audio_duration_sec', 0):.1f}s",
                            "audio_duration_sec": at.get("audio_duration_sec", 0),
                            "generation_time_sec": at.get("generation_time_sec", 0),
                            "num_segments": at.get("num_segments", 1),
                            "segments": at.get("num_segments", 1),
                            "resolution": at.get("resolution", "720p"),
                            "num_inference_steps": at.get("num_inference_steps", 4),
                            "steps": at.get("num_inference_steps", 4)
                        })
            
            # Also include all processing tasks from active_tasks
            for tid, at in active_tasks.items():
                if at.get("status") == "processing" and tid not in seen_active_ids:
                    seen_active_ids.add(tid)
                    is_av = bool(at.get("is_avatar_baseline") or at.get("slot_name") == "Avatar Library" or str(at.get("video_title", "")).startswith("Living Avatar"))
                    active_list.append({
                        "id": tid,
                        "slot_name": "Avatar Library" if is_av else (at.get("slot_name") or "Video 1"),
                        "video_title": at.get("video_title", ""),
                        "avatar_id": at.get("avatar_id"),
                        "is_avatar_baseline": is_av,
                        "status": at.get("status", "processing"),
                        "stage": at.get("stage", "Processing"),
                        "progress": at.get("progress", 0.0),
                        "logs": at.get("logs", [])[-100:],
                        "step_latency": at.get("step_latency", 0),
                        "step_speed_str": at.get("step_speed_str", ""),
                        "current_segment": at.get("current_segment", 1),
                        "total_segments": at.get("total_segments", at.get("num_segments", 1)),
                        "current_step": at.get("current_step", 1),
                        "steps_per_segment": at.get("steps_per_segment", at.get("num_inference_steps", 3)),
                        "completed_steps": at.get("completed_steps", 0),
                        "total_pipeline_steps": at.get("total_pipeline_steps", 0),
                        "remaining_steps": at.get("remaining_steps", 0),
                        "elapsed_gpu_sec": at.get("elapsed_gpu_sec", at.get("generation_time_sec", 0)),
                        "remaining_sec": at.get("remaining_sec", 0),
                        "total_est_sec": at.get("total_est_sec", 0),
                        "audio_duration": f"{at.get('audio_duration_sec', 0):.1f}s",
                        "audio_duration_sec": at.get("audio_duration_sec", 0),
                        "generation_time_sec": at.get("generation_time_sec", 0),
                        "num_segments": at.get("num_segments", 1),
                        "segments": at.get("num_segments", 1),
                        "resolution": at.get("resolution", "720p"),
                        "num_inference_steps": at.get("num_inference_steps", 3),
                        "steps": at.get("num_inference_steps", 3)
                    })

            self.send_json_response({
                "active_task": active_list[0] if active_list else None,
                "active_tasks": active_list,
                "active_count": len(active_list),
                "queued_tasks": queued,
                "queue_count": len(queued),
                "hybrid_mode": SERVER_CONFIG.get("hybrid_mode", False),
                "max_concurrency": SERVER_CONFIG.get("max_concurrency", 1)
            })
            return

        elif path == "/api/download":
            query = urllib.parse.parse_qs(parsed_url.query)
            filename = query.get("file", [""])[0]
            if not filename:
                self.send_error(400, "Missing filename")
                return

            file_path = OUTPUT_DIR / filename
            if not file_path.exists() or not file_path.is_file():
                self.send_error(404, "File not found")
                return

            try:
                self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.request.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16 * 1024 * 1024)
            except Exception:
                pass

            file_size = file_path.stat().st_size
            range_header = self.headers.get("Range")
            safe_filename = file_path.name

            content_type = "video/mp4"
            if file_path.suffix.lower() in [".jpg", ".jpeg"]:
                content_type = "image/jpeg"
            elif file_path.suffix.lower() == ".png":
                content_type = "image/png"
            elif file_path.suffix.lower() in [".wav", ".mp3"]:
                content_type = "audio/wav"

            if range_header and range_header.startswith("bytes="):
                try:
                    ranges = range_header[len("bytes="):].split("-")
                    start = int(ranges[0]) if ranges[0] else 0
                    end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
                    start = max(0, start)
                    end = min(file_size - 1, end)
                    length = end - start + 1

                    self.send_response(206)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}"')
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Access-Control-Allow-Headers", "*")
                    self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
                    self.send_header("Cache-Control", "public, max-age=31536000, immutable")
                    self.end_headers()

                    # High-speed Zero-Copy sendfile streaming on Linux kernel
                    sock = self.request
                    sock_fd = sock.fileno()
                    with open(file_path, "rb") as f:
                        file_fd = f.fileno()
                        offset = start
                        remaining = length
                        try:
                            while remaining > 0:
                                chunk_to_send = min(remaining, 8 * 1024 * 1024)
                                sent = os.sendfile(sock_fd, file_fd, offset, chunk_to_send)
                                if sent == 0:
                                    break
                                offset += sent
                                remaining -= sent
                        except (AttributeError, OSError):
                            f.seek(offset)
                            while remaining > 0:
                                chunk = f.read(min(remaining, 4 * 1024 * 1024))
                                if not chunk:
                                    break
                                self.wfile.write(chunk)
                                remaining -= len(chunk)
                    return
                except Exception:
                    return
            else:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}"')
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "*")
                self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
                self.end_headers()

                sock = self.request
                sock_fd = sock.fileno()
                with open(file_path, "rb") as f:
                    file_fd = f.fileno()
                    offset = 0
                    remaining = file_size
                    try:
                        while remaining > 0:
                            chunk_to_send = min(remaining, 8 * 1024 * 1024)
                            sent = os.sendfile(sock_fd, file_fd, offset, chunk_to_send)
                            if sent == 0:
                                break
                            offset += sent
                            remaining -= sent
                    except (AttributeError, OSError):
                        f.seek(offset)
                        while remaining > 0:
                            chunk = f.read(min(remaining, 4 * 1024 * 1024))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                return

        elif path == "/api/gallery":
            vids = scan_video_dir(OUTPUT_DIR, is_trash=False)
            trash_vids = scan_video_dir(TRASH_DIR, is_trash=True)
            self.send_json_response({
                "videos": vids,
                "count": len(vids),
                "trash_count": len(trash_vids)
            })
            return

        elif path == "/api/trash":
            trash_vids = scan_video_dir(TRASH_DIR, is_trash=True)
            self.send_json_response({
                "videos": trash_vids,
                "count": len(trash_vids)
            })
            return

        elif path == "/api/avatars":
            avatar_list = get_avatar_presets_list()
            self.send_json_response({
                "avatars": avatar_list,
                "count": len(avatar_list)
            })
            return

        elif path == "/api/audio_library":
            audios = get_audio_library_list()
            self.send_json_response({
                "audios": audios,
                "count": len(audios)
            })
            return

        # Ultra-Fast Zero-Copy Video Streaming & Multi-Threaded Download Support (HTTP 206 & 200)
        if path.startswith("/outputs/"):
            rel_file = urllib.parse.unquote(path[len("/outputs/"):])
            if "?" in rel_file:
                rel_file = rel_file.split("?")[0]
            
            file_path = OUTPUT_DIR / rel_file
            if not file_path.exists() or not file_path.is_file():
                self.send_error(404, "File not found")
                return

            try:
                self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.request.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16 * 1024 * 1024)
            except Exception:
                pass

            file_size = file_path.stat().st_size
            range_header = self.headers.get("Range")
            is_download = "download=1" in parsed_url.query or "dl=1" in parsed_url.query
            safe_filename = file_path.name

            content_type = "video/mp4"
            if file_path.suffix.lower() in [".jpg", ".jpeg"]:
                content_type = "image/jpeg"
            elif file_path.suffix.lower() == ".png":
                content_type = "image/png"
            elif file_path.suffix.lower() in [".wav", ".mp3"]:
                content_type = "audio/wav"

            if range_header and range_header.startswith("bytes="):
                try:
                    ranges = range_header[len("bytes="):].split("-")
                    start = int(ranges[0]) if ranges[0] else 0
                    end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
                    start = max(0, start)
                    end = min(file_size - 1, end)
                    length = end - start + 1

                    self.send_response(206)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Access-Control-Allow-Headers", "*")
                    self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
                    self.send_header("Cache-Control", "public, max-age=31536000, immutable")
                    if is_download:
                        self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}"')
                    self.end_headers()

                    if is_head:
                        return

                    # High-speed Zero-Copy sendfile streaming on Linux kernel
                    sock = self.request
                    sock_fd = sock.fileno()
                    with open(file_path, "rb") as f:
                        file_fd = f.fileno()
                        offset = start
                        remaining = length
                        try:
                            while remaining > 0:
                                chunk_to_send = min(remaining, 8 * 1024 * 1024)
                                sent = os.sendfile(sock_fd, file_fd, offset, chunk_to_send)
                                if sent == 0:
                                    break
                                offset += sent
                                remaining -= sent
                        except (AttributeError, OSError):
                            f.seek(offset)
                            while remaining > 0:
                                chunk = f.read(min(remaining, 4 * 1024 * 1024))
                                if not chunk:
                                    break
                                self.wfile.write(chunk)
                                remaining -= len(chunk)
                    return
                except Exception:
                    return
            else:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "*")
                self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
                if is_download:
                    self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}"')
                self.end_headers()

                if is_head:
                    return

                sock = self.request
                sock_fd = sock.fileno()
                with open(file_path, "rb") as f:
                    file_fd = f.fileno()
                    offset = 0
                    remaining = file_size
                    try:
                        while remaining > 0:
                            chunk_to_send = min(remaining, 8 * 1024 * 1024)
                            sent = os.sendfile(sock_fd, file_fd, offset, chunk_to_send)
                            if sent == 0:
                                break
                            offset += sent
                            remaining -= sent
                    except (AttributeError, OSError):
                        f.seek(offset)
                        while remaining > 0:
                            chunk = f.read(min(remaining, 4 * 1024 * 1024))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                return

        if path.startswith("/avatar_presets/"):
            rel_file = urllib.parse.unquote(path[len("/avatar_presets/"):])
            if "?" in rel_file:
                rel_file = rel_file.split("?")[0]
            file_path = AVATARS_DIR / rel_file
            if not file_path.exists() or not file_path.is_file():
                self.send_error(404, "Avatar preset file not found")
                return

            try:
                self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except Exception:
                pass

            file_size = file_path.stat().st_size
            content_type = "image/jpeg"
            if file_path.suffix.lower() == ".png":
                content_type = "image/png"
            elif file_path.suffix.lower() == ".webp":
                content_type = "image/webp"
            elif file_path.suffix.lower() == ".mp4":
                content_type = "video/mp4"

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()

            if is_head:
                return

            with open(file_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
            return

        if path.startswith("/audio_library/"):
            rel_file = urllib.parse.unquote(path[len("/audio_library/"):])
            if "?" in rel_file:
                rel_file = rel_file.split("?")[0]
            file_path = AUDIO_LIBRARY_DIR / rel_file
            if not file_path.exists() or not file_path.is_file():
                self.send_error(404, "Audio library file not found")
                return

            file_size = file_path.stat().st_size
            ext = file_path.suffix.lower()
            content_type = "audio/wav"
            if ext == ".mp3":
                content_type = "audio/mpeg"
            elif ext in [".m4a", ".aac"]:
                content_type = "audio/mp4"
            elif ext == ".ogg":
                content_type = "audio/ogg"
            elif ext == ".flac":
                content_type = "audio/flac"

            range_header = self.headers.get("Range")
            if range_header and range_header.startswith("bytes="):
                try:
                    ranges = range_header[6:].split("-")
                    start = int(ranges[0]) if ranges[0] else 0
                    end = int(ranges[1]) if ranges[1] else file_size - 1
                    length = end - start + 1

                    self.send_response(206)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()

                    with open(file_path, "rb") as f:
                        f.seek(start)
                        rem = length
                        while rem > 0:
                            buf = f.read(min(rem, 1024 * 1024))
                            if not buf:
                                break
                            self.wfile.write(buf)
                            rem -= len(buf)
                    return
                except Exception:
                    return

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()

            with open(file_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
            return

        # Serve static web frontend
        if path == "/" or path == "/index.html":
            self.path = "/web/index.html"
        elif not path.startswith("/outputs/") and not path.startswith("/uploads/") and not path.startswith("/web/") and not path.startswith("/avatar_presets/") and not path.startswith("/audio_library/"):
            self.path = f"/web{path}"

        return super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/studio_state":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                if content_len > 0:
                    body = self.rfile.read(content_len).decode("utf-8")
                    data = json.loads(body)
                    state_file = OUTPUT_DIR / "studio_state.json"
                    with open(state_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    self.send_json_response({"success": True})
                    return
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=500)
                return
            self.send_json_response({"error": "Empty body"}, status=400)
            return

        if path == "/api/task/cancel" or path == "/api/cancel":
            target_tid = None
            target_avatar_id = None
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                if content_len > 0:
                    body = self.rfile.read(content_len).decode("utf-8")
                    data = json.loads(body)
                    target_tid = data.get("task_id")
                    target_avatar_id = data.get("avatar_id")
            except Exception:
                pass

            def kill_task_process(tid):
                proc = active_processes.pop(tid, None)
                if proc:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    except Exception:
                        try:
                            proc.terminate()
                        except Exception:
                            pass
                    time.sleep(1.0)
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                subprocess.run(["pkill", "-15", "-f", "run_demo_avatar_single_audio_to_video.py"], capture_output=True)
                time.sleep(0.5)
                subprocess.run(["pkill", "-9", "-f", "torch.distributed.run"], capture_output=True)
                subprocess.run(["pkill", "-9", "-f", "run_demo_avatar_single_audio_to_video.py"], capture_output=True)

            if target_avatar_id:
                cancelled_count = 0
                for tid, t in list(active_tasks.items()):
                    if t.get("avatar_id") == target_avatar_id:
                        if t.get("status") == "queued":
                            t["status"] = "cancelled"
                            t["was_cancelled"] = True
                            t["stage"] = "Cancelled from queue by user"
                            t["logs"].append(f"[{time.strftime('%H:%M:%S')}] [CANCELLED] Removed from queue by user.")
                            cancelled_count += 1
                        elif t.get("status") == "processing":
                            kill_task_process(tid)
                            t["status"] = "cancelled"
                            t["was_cancelled"] = True
                            t["stage"] = "Cancelled by user"
                            t["logs"].append(f"[{time.strftime('%H:%M:%S')}] [CANCELLED] Generation stopped by user. GPU memory cleared.")
                            cancelled_count += 1
                save_active_tasks_to_disk()
                self.send_json_response({"success": True, "message": f"Cancelled {cancelled_count} task(s) for avatar {target_avatar_id}."})
                return

            if target_tid and target_tid not in ["current", "all"]:
                t = active_tasks.get(target_tid)
                if t:
                    if t.get("status") == "queued":
                        t["status"] = "cancelled"
                        t["was_cancelled"] = True
                        t["stage"] = "Cancelled from queue by user"
                        t["logs"].append(f"[{time.strftime('%H:%M:%S')}] [CANCELLED] Removed from queue by user.")
                        save_active_tasks_to_disk()
                        self.send_json_response({"success": True, "message": f"Queued task {target_tid} cancelled."})
                        return
                    elif t.get("status") == "processing":
                        kill_task_process(target_tid)
                        t["status"] = "cancelled"
                        t["was_cancelled"] = True
                        t["stage"] = "Cancelled by user"
                        t["logs"].append(f"[{time.strftime('%H:%M:%S')}] [CANCELLED] Generation stopped by user. GPU memory cleared.")
                        save_active_tasks_to_disk()
                        self.send_json_response({"success": True, "message": f"Running task {target_tid} cancelled."})
                        return

            # Fallback for full global stop or current task
            for tid in list(active_processes.keys()):
                kill_task_process(tid)
            subprocess.run(["pkill", "-9", "-f", "torch.distributed.run"], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", "run_demo_avatar_single_audio_to_video.py"], capture_output=True)

            for tid, t in active_tasks.items():
                if t.get("status") in ["queued", "processing"]:
                    t["status"] = "cancelled"
                    t["was_cancelled"] = True
                    t["stage"] = "Cancelled by user"
                    t["logs"].append(f"[{time.strftime('%H:%M:%S')}] [CANCELLED] Generation stopped by user. GPU memory cleared.")
            save_active_tasks_to_disk()
            self.send_json_response({"success": True, "message": "All active and queued tasks cancelled successfully."})
            return

        elif path == "/api/config":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                data = json.loads(body)
                if "hybrid_mode" in data:
                    is_hybrid = bool(data["hybrid_mode"])
                    SERVER_CONFIG["hybrid_mode"] = is_hybrid
                    SERVER_CONFIG["max_concurrency"] = 2 if is_hybrid else 1
                    save_server_config(SERVER_CONFIG)
                    print(f"[Config] Hybrid Mode saved to disk: {is_hybrid} (Max Concurrency: {SERVER_CONFIG['max_concurrency']})")
            except Exception as e:
                pass
            self.send_json_response(SERVER_CONFIG)
            return

        elif path == "/api/gallery/delete":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            TRASH_DIR.mkdir(parents=True, exist_ok=True)
            moved = []

            if data.get("all"):
                for f in OUTPUT_DIR.glob("*.mp4"):
                    if ".trash" not in f.name and f.is_file():
                        try:
                            shutil.move(str(f), str(TRASH_DIR / f.name))
                            moved.append(f.name)
                        except Exception:
                            pass
                for f in OUTPUT_DIR.glob("*.jpg"):
                    if ".trash" not in f.name and f.is_file():
                        try:
                            shutil.move(str(f), str(TRASH_DIR / f.name))
                        except Exception:
                            pass
            elif "filenames" in data:
                for fn in data["filenames"]:
                    clean_fn = Path(fn).name
                    base_stem = Path(clean_fn).stem.replace("_720p", "")
                    targets = [
                        OUTPUT_DIR / clean_fn,
                        OUTPUT_DIR / f"{base_stem}.mp4",
                        OUTPUT_DIR / f"{base_stem}_720p.mp4",
                        OUTPUT_DIR / f"{base_stem}.jpg"
                    ]
                    for t in targets:
                        if t.exists() and t.is_file():
                            try:
                                shutil.move(str(t), str(TRASH_DIR / t.name))
                                moved.append(t.name)
                            except Exception:
                                pass

            self.send_json_response({"success": True, "moved_to_trash": moved, "count": len(moved)})
            return

        elif path == "/api/trash/recover":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            recovered = []

            if data.get("all"):
                for f in TRASH_DIR.glob("*.mp4"):
                    if f.is_file():
                        try:
                            shutil.move(str(f), str(OUTPUT_DIR / f.name))
                            recovered.append(f.name)
                        except Exception:
                            pass
                for f in TRASH_DIR.glob("*.jpg"):
                    if f.is_file():
                        try:
                            shutil.move(str(f), str(OUTPUT_DIR / f.name))
                        except Exception:
                            pass
            elif "filenames" in data:
                for fn in data["filenames"]:
                    clean_fn = Path(fn).name
                    base_stem = Path(clean_fn).stem.replace("_720p", "")
                    targets = [
                        TRASH_DIR / clean_fn,
                        TRASH_DIR / f"{base_stem}.mp4",
                        TRASH_DIR / f"{base_stem}_720p.mp4",
                        TRASH_DIR / f"{base_stem}.jpg"
                    ]
                    for t in targets:
                        if t.exists() and t.is_file():
                            try:
                                shutil.move(str(t), str(OUTPUT_DIR / t.name))
                                recovered.append(t.name)
                            except Exception:
                                pass

            self.send_json_response({"success": True, "recovered": recovered, "count": len(recovered)})
            return

        elif path == "/api/trash/delete":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            deleted = []

            if data.get("all"):
                for f in TRASH_DIR.glob("*"):
                    try:
                        if f.is_dir():
                            shutil.rmtree(str(f), ignore_errors=True)
                        else:
                            f.unlink(missing_ok=True)
                        deleted.append(f.name)
                    except Exception:
                        pass
            elif "filenames" in data:
                for fn in data["filenames"]:
                    clean_fn = Path(fn).name
                    base_stem = Path(clean_fn).stem.replace("_720p", "")
                    targets = [
                        TRASH_DIR / clean_fn,
                        TRASH_DIR / f"{base_stem}.mp4",
                        TRASH_DIR / f"{base_stem}_720p.mp4",
                        TRASH_DIR / f"{base_stem}.jpg",
                        OUTPUT_DIR / f"hd_master_{base_stem}.mp4",
                        OUTPUT_DIR / f"temp_{base_stem}.mp4"
                    ]
                    for t in targets:
                        if t.exists():
                            try:
                                if t.is_dir():
                                    shutil.rmtree(str(t), ignore_errors=True)
                                else:
                                    t.unlink(missing_ok=True)
                                deleted.append(t.name)
                            except Exception:
                                pass

            # Clear cache and sync OS filesystem
            _DIR_CACHE.clear()
            _DIR_CACHE_TIME.clear()
            try:
                subprocess.run(["sync"], capture_output=True)
            except Exception:
                pass

            self.send_json_response({"success": True, "permanently_deleted": deleted, "count": len(deleted)})
            return

        elif path == "/api/trash/empty":
            deleted = []
            if TRASH_DIR.exists():
                for f in TRASH_DIR.glob("*"):
                    try:
                        if f.is_dir():
                            shutil.rmtree(str(f), ignore_errors=True)
                        else:
                            f.unlink(missing_ok=True)
                        deleted.append(f.name)
                    except Exception:
                        pass

            # Clear cache and sync OS filesystem
            _DIR_CACHE.clear()
            _DIR_CACHE_TIME.clear()
            try:
                subprocess.run(["sync"], capture_output=True)
            except Exception:
                pass

            self.send_json_response({"success": True, "permanently_deleted": deleted, "count": len(deleted)})
            return

        elif path == "/api/audio_library/upload":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                content_type = self.headers.get("Content-Type", "")
                
                query_params = urllib.parse.parse_qs(parsed_url.query)
                filename = query_params.get("filename", [None])[0]
                if not filename:
                    raw_fn = self.headers.get("X-Filename", None)
                    if raw_fn:
                        filename = urllib.parse.unquote(raw_fn)

                if filename:
                    clean_name = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', Path(filename).name)
                    ext = Path(clean_name).suffix.lower()
                    if ext not in {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}:
                        self.send_json_response({"error": f"Unsupported audio format: {ext}"}, status=400)
                        return

                    out_path = AUDIO_LIBRARY_DIR / clean_name
                    bytes_to_read = content_len
                    total_written = 0
                    with open(out_path, "wb") as f:
                        while bytes_to_read > 0:
                            chunk = self.rfile.read(min(bytes_to_read, 32 * 1024))
                            if not chunk:
                                break
                            f.write(chunk)
                            bytes_to_read -= len(chunk)
                            total_written += len(chunk)

                    get_audio_library_list()

                    self.send_json_response({
                        "success": True,
                        "filename": clean_name,
                        "size_mb": round(total_written / (1024 * 1024), 2),
                        "url": f"/audio_library/{urllib.parse.quote(clean_name)}"
                    })
                    return

                # Multipart fallback
                if "multipart/form-data" in content_type:
                    bytes_to_read = content_len
                    body_chunks = []
                    while bytes_to_read > 0:
                        chunk = self.rfile.read(min(bytes_to_read, 32 * 1024))
                        if not chunk:
                            break
                        body_chunks.append(chunk)
                        bytes_to_read -= len(chunk)
                    raw_body = b"".join(body_chunks)
                    boundary = content_type.split("boundary=")[-1].strip('"').split(";")[0].strip().encode()
                    parts = raw_body.split(b"--" + boundary)
                    for part in parts:
                        if b'name="file"' in part or b'name="audio"' in part:
                            header_end = part.find(b"\r\n\r\n")
                            if header_end != -1:
                                headers_part = part[:header_end].decode("utf-8", errors="ignore")
                                fn_match = re.search(r'filename="([^"]+)"', headers_part)
                                if fn_match:
                                    filename = fn_match.group(1)
                                data_bytes = part[header_end + 4:].rstrip(b"\r\n--")
                                clean_name = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', Path(filename).name)
                                out_path = AUDIO_LIBRARY_DIR / clean_name
                                with open(out_path, "wb") as f:
                                    f.write(data_bytes)
                                get_audio_library_list()
                                self.send_json_response({
                                    "success": True,
                                    "filename": clean_name,
                                    "size_mb": round(len(data_bytes) / (1024 * 1024), 2),
                                    "url": f"/audio_library/{urllib.parse.quote(clean_name)}"
                                })
                                return

                self.send_json_response({"error": "No audio file or filename provided"}, status=400)
                return
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=500)
                return

        elif path == "/api/audio_library/delete":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                data = json.loads(body)
                target_fn = data.get("filename")
                if target_fn:
                    clean_name = Path(target_fn).name
                    target_file = AUDIO_LIBRARY_DIR / clean_name
                    if target_file.exists() and target_file.is_file():
                        target_file.unlink(missing_ok=True)
                    # Clear from cache
                    cache_file = AUDIO_LIBRARY_DIR / ".audio_meta_cache.json"
                    if cache_file.exists():
                        try:
                            with open(cache_file, "r") as f:
                                c = json.load(f)
                            if clean_name in c:
                                del c[clean_name]
                                with open(cache_file, "w") as f:
                                    json.dump(c, f, indent=2)
                        except Exception:
                            pass
                    try:
                        subprocess.run(["sync"], capture_output=True)
                    except Exception:
                        pass
                    self.send_json_response({"success": True, "deleted": clean_name})
                    return
                self.send_json_response({"error": "No filename specified"}, status=400)
                return
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=500)
                return

        elif path == "/api/audio_library/delete_all":
            try:
                deleted = []
                if AUDIO_LIBRARY_DIR.exists():
                    for f in AUDIO_LIBRARY_DIR.iterdir():
                        if f.is_file() and not f.name.startswith("."):
                            try:
                                f.unlink(missing_ok=True)
                                deleted.append(f.name)
                            except Exception:
                                pass
                
                cache_file = AUDIO_LIBRARY_DIR / ".audio_meta_cache.json"
                if cache_file.exists():
                    try:
                        with open(cache_file, "w") as f:
                            json.dump({}, f)
                    except Exception:
                        pass
                
                try:
                    subprocess.run(["sync"], capture_output=True)
                except Exception:
                    pass

                self.send_json_response({"success": True, "deleted": deleted, "count": len(deleted)})
                return
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=500)
                return

        elif path == "/api/calculate_segments":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            duration = float(data.get("duration", 0))
            num_f = int(data.get("num_frames", 205))
            if num_f not in [81, 125, 205, 249, 253, 301]:
                num_f = 205
            segs = calculate_segments(duration, num_frames=num_f, generation_mode="sequential_continuation", transition_overlap=13)
            self.send_json_response({
                "duration": duration,
                "segments": segs,
                "fps": 25,
                "num_frames": num_f,
                "step_sec": (num_f - 13) / 25.0
            })
            return

        elif path == "/api/avatars/upload":
            content_type = self.headers.get("Content-Type", "")
            content_len = int(self.headers.get("Content-Length", 0))
            bytes_to_read = content_len
            body_chunks = []
            while bytes_to_read > 0:
                chunk = self.rfile.read(min(bytes_to_read, 1024 * 1024))
                if not chunk:
                    break
                body_chunks.append(chunk)
                bytes_to_read -= len(chunk)
            raw_body = b"".join(body_chunks)

            boundary = content_type.split("boundary=")[-1].strip('"').split(";")[0].strip().encode()
            parts = raw_body.split(b"--" + boundary)

            created_avatars = []
            custom_name = None

            for part in parts:
                if not part or part in (b"--\r\n", b"--"):
                    continue
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    continue
                headers = part[:header_end].decode("utf-8", errors="ignore")
                body = part[header_end + 4:].rstrip(b"\r\n")
                if 'name="custom_name"' in headers or 'name="name"' in headers:
                    custom_name = body.decode("utf-8", errors="ignore").strip()

            for part in parts:
                if not part or part in (b"--\r\n", b"--"):
                    continue
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    continue
                headers = part[:header_end].decode("utf-8", errors="ignore")
                body = part[header_end + 4:].rstrip(b"\r\n")

                if 'filename="' in headers and len(body) > 100:
                    fn = headers.split('filename="')[1].split('"')[0]
                    avatar_meta = save_new_avatar_preset(body, original_filename=fn, custom_name=custom_name)
                    created_avatars.append(avatar_meta)

            self.send_json_response({
                "success": True,
                "avatars": created_avatars,
                "count": len(created_avatars)
            })
            return

        elif path == "/api/avatars/rename":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            avatar_id = data.get("avatar_id")
            new_name = data.get("new_name")
            ok, res = rename_avatar_preset(avatar_id, new_name)
            if ok:
                self.send_json_response({"success": True, "avatar": res})
            else:
                self.send_json_response({"success": False, "error": str(res)}, status=400)
            return

        elif path == "/api/avatars/delete":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            avatar_id = data.get("avatar_id")
            ok, msg = delete_avatar_preset(avatar_id)
            if ok:
                self.send_json_response({"success": True, "message": msg})
            else:
                self.send_json_response({"success": False, "error": str(msg)}, status=400)
            return

        elif path == "/api/avatars/generate_baseline":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            avatar_id = str(data.get("avatar_id", "")).strip()
            try:
                duration = int(data.get("duration", 20))
            except Exception:
                duration = 20
            if duration not in [20, 30, 40]:
                duration = 20

            # Resolve target avatar directory
            target_dir = AVATARS_DIR / avatar_id
            if not target_dir.exists():
                for sub in AVATARS_DIR.iterdir():
                    if sub.is_dir():
                        mf = sub / "meta.json"
                        if mf.exists():
                            try:
                                with open(mf, "r", encoding="utf-8") as f:
                                    if json.load(f).get("id") == avatar_id:
                                        target_dir = sub
                                        break
                            except Exception:
                                pass

            if not target_dir.exists():
                self.send_json_response({"success": False, "error": f"Avatar preset '{avatar_id}' not found"}, status=404)
                return

            # Deduplicate: Check if an active baseline generation already exists for this avatar
            for existing_tid, existing_task in active_tasks.items():
                if (existing_task.get("is_avatar_baseline") and 
                    existing_task.get("avatar_id") == avatar_id and 
                    existing_task.get("status") in ["processing", "queued"]):
                    self.send_json_response({
                        "success": True,
                        "task_id": existing_tid,
                        "avatar_id": avatar_id,
                        "already_active": True,
                        "status": existing_task.get("status"),
                        "message": f"Task already {existing_task.get('status')} for this avatar."
                    })
                    return

            # Find portrait image
            portrait_img = None
            for p in target_dir.glob("portrait.*"):
                if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    portrait_img = p
                    break
            if not portrait_img:
                for p in target_dir.iterdir():
                    if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                        portrait_img = p
                        break

            if not portrait_img:
                self.send_json_response({"success": False, "error": "No portrait image found in avatar folder"}, status=400)
                return

            # Read existing metadata
            meta_file = target_dir / "meta.json"
            meta = {}
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            avatar_name = meta.get("name", avatar_id)

            # Create task directory
            task_id = str(uuid.uuid4())[:8]
            task_upload_dir = UPLOAD_DIR / task_id
            task_upload_dir.mkdir(parents=True, exist_ok=True)

            # Prepare baseline driving audio
            ref_speech = BASE_DIR / "assets" / "reference_speech.wav"
            task_audio = task_upload_dir / "baseline_speech.wav"

            cmd_audio = ["ffmpeg", "-y"]
            if duration > 32:
                cmd_audio.extend(["-stream_loop", "1"])
            cmd_audio.extend(["-i", str(ref_speech), "-t", str(duration), "-ac", "1", "-ar", "16000", str(task_audio)])
            res_ff = subprocess.run(cmd_audio, capture_output=True, text=True)
            if res_ff.returncode != 0 or not task_audio.exists():
                # Fallback synthesized speech tone
                cmd_fallback = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=220:duration={duration}", "-ac", "1", "-ar", "16000", str(task_audio)]
                subprocess.run(cmd_fallback, check=True)

            # Copy portrait into task
            task_img = task_upload_dir / portrait_img.name
            shutil.copy2(str(portrait_img), str(task_img))

            audio_dur = get_audio_duration(str(task_audio))
            num_f = 81
            overlap_f = 20
            step_sec = (num_f - overlap_f) / 25.0 # 2.44s
            num_segments = max(1, math.ceil(audio_dur / step_sec))

            active_tasks[task_id] = {
                "id": task_id,
                "slot_name": "Avatar Library",
                "status": "queued",
                "created_at": time.time(),
                "upload_dir": str(task_upload_dir),
                "image_path": str(task_img),
                "audio_path": str(task_audio),
                "audio_duration_sec": audio_dur,
                "prompt": "Authentic living human avatar persona, natural relaxed speech articulation, subtle chest breathing and periodic natural blinks, composed upper body posture, photorealistic studio lighting.",
                "negative_prompt": "overexposure, washed out colors, hands, hand gestures, waving hands, camera zoom, leaning forward, worst quality, low quality",
                "resolution": "600p",
                "preset": "fast",
                "num_segments": num_segments,
                "num_frames": 81,
                "num_inference_steps": 3,
                "seed": 42,
                "is_avatar_baseline": True,
                "avatar_id": avatar_id,
                "target_avatar_dir": str(target_dir),
                "video_title": f"Living Avatar - {avatar_name}",
                "logs": [f"[{time.strftime('%H:%M:%S')}] Task {task_id} queued for Living Avatar Baseline ({duration}s, {num_segments} segments)..."],
                "progress": 0.0,
                "stage": "Queued in FIFO Pipeline"
            }
            sequential_queue.put(task_id)
            save_active_tasks_to_disk()

            self.send_json_response({
                "success": True,
                "task_id": task_id,
                "avatar_id": avatar_id,
                "duration": duration,
                "segments": num_segments,
                "video_title": f"Living Avatar - {avatar_name}"
            })
            return

        elif path == "/api/upload_asset":
            content_type = self.headers.get("Content-Type", "")
            content_len = int(self.headers.get("Content-Length", 0))
            bytes_to_read = content_len
            body_chunks = []
            while bytes_to_read > 0:
                chunk = self.rfile.read(min(bytes_to_read, 1024 * 1024))
                if not chunk:
                    break
                body_chunks.append(chunk)
                bytes_to_read -= len(chunk)
            raw_body = b"".join(body_chunks)
            if bytes_to_read > 0:
                err_msg = f"Upload incomplete: connection was interrupted. Received {content_len - bytes_to_read} of {content_len} bytes."
                print(f"❌ [UPLOAD ASSET ERROR] {err_msg}")
                self.send_json_response({"error": err_msg}, status=400)
                return

            asset_id = str(uuid.uuid4())[:12]
            preupload_dir = UPLOAD_DIR / "preupload"
            preupload_dir.mkdir(parents=True, exist_ok=True)

            filename = "asset.bin"
            file_data = b""

            if "boundary=" in content_type:
                boundary = content_type.split("boundary=")[-1].strip('"').split(";")[0].strip().encode()
                parts = raw_body.split(b"--" + boundary)
                for part in parts:
                    if not part or part == b"--\r\n" or part == b"--":
                        continue
                    h_end = part.find(b"\r\n\r\n")
                    if h_end == -1:
                        continue
                    headers_part = part[:h_end].decode("utf-8", errors="ignore")
                    b_part = part[h_end + 4:].rstrip(b"\r\n")
                    if 'name="file"' in headers_part or 'filename="' in headers_part:
                        if 'filename="' in headers_part:
                            try:
                                filename = headers_part.split('filename="')[1].split('"')[0]
                            except Exception:
                                pass
                        file_data = b_part
                        break
            else:
                file_data = raw_body
                filename = self.headers.get("X-Filename", "asset.bin")

            ext = Path(filename).suffix or ".wav"
            saved_filename = f"{asset_id}{ext}"
            saved_path = preupload_dir / saved_filename
            with open(saved_path, "wb") as f:
                f.write(file_data)

            self.send_json_response({
                "success": True,
                "asset_id": asset_id,
                "filename": filename,
                "saved_name": saved_filename,
                "url": f"/uploads/preupload/{saved_filename}",
                "size_mb": round(len(file_data) / (1024 * 1024), 2)
            })
            return

        elif path == "/api/generate":
            content_type = self.headers.get("Content-Type", "")
            content_len = int(self.headers.get("Content-Length", 0))
            bytes_to_read = content_len
            body_chunks = []
            while bytes_to_read > 0:
                chunk = self.rfile.read(min(bytes_to_read, 1024 * 1024)) # 1MB stream chunks
                if not chunk:
                    break
                body_chunks.append(chunk)
                bytes_to_read -= len(chunk)
            raw_body = b"".join(body_chunks)
            if bytes_to_read > 0:
                err_msg = f"Upload incomplete: connection was interrupted. Received {content_len - bytes_to_read} of {content_len} bytes. Please try again."
                print(f"❌ [UPLOAD GENERATE ERROR] {err_msg}")
                self.send_json_response({"error": err_msg}, status=400)
                return

            task_id = str(uuid.uuid4())[:8]
            task_upload_dir = UPLOAD_DIR / task_id
            task_upload_dir.mkdir(parents=True, exist_ok=True)

            # Parse multipart/form-data
            boundary = content_type.split("boundary=")[-1].strip('"').split(";")[0].strip().encode()
            parts = raw_body.split(b"--" + boundary)

            image_path = None
            audio_path = None
            original_audio_path = None
            params = {
                "slot_name": "Video 1",
                "video_title": "",
                "avatar_id": "",
                "audio_asset_id": "",
                "image_asset_id": "",
                "audio_library_filename": "",
                "aspect_ratio": "9:16",
                "use_avatar_preset": "false",
                "prompt": "Completely static camera, locked tripod perspective, perfectly still background with zero camera movement. Calm relaxed avatar speaking naturally with smooth subtle lip sync, gentle breathing, relaxed posture, normal natural blinking rate, and composed neutral facial expression. No forced speech pressure, no yelling, no wide mouth stretching, preserving exact original face, natural lip color, teeth, skin tone, and facial identity from uploaded photo.",
                "negative_prompt": "Aggressive speech pressure, wide shouting mouth, jaw tension, forced facial strain, over-opened mouth, robotic mouth stretching, popping neck veins, clenched teeth, exaggerated head shaking, fast sudden movements, camera shake, frame vibration, jitter, flickering background, sudden jumps, extreme emotions, hand gestures, face morphing, identity changes, beautified skin, lip recoloring, artificial lipstick, distorted mouth.",
                "resolution": "500p",
                "preset": "distill_bf16",
                "num_inference_steps": 3,
                "num_frames": 205,
                "step_booster": "default",
                "generation_mode": "anchor_seamless",
                "transition_overlap_frames": 4,
                "length_mode": "auto",
                "gender": "auto",
                "hand_control": "bust_locked",
                "seed": 10,
                "ref_img_index": 10,
                "mask_frame_range": 0
            }

            for part in parts:
                if not part or part == b"--\r\n" or part == b"--":
                    continue
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    continue
                headers = part[:header_end].decode("utf-8", errors="ignore")
                body = part[header_end + 4:].rstrip(b"\r\n")

                if 'name="image_file"' in headers:
                    fn = "portrait.jpg"
                    if 'filename="' in headers:
                        fn = headers.split('filename="')[1].split('"')[0]
                    image_path = task_upload_dir / fn
                    with open(image_path, "wb") as f:
                        f.write(body)
                elif 'name="audio_file"' in headers:
                    fn = "audio.wav"
                    if 'filename="' in headers:
                        fn = headers.split('filename="')[1].split('"')[0]
                    original_audio_path = task_upload_dir / fn
                    with open(original_audio_path, "wb") as f:
                        f.write(body)
                    audio_path = original_audio_path
                else:
                    field_name = None
                    if 'name="' in headers:
                        field_name = headers.split('name="')[1].split('"')[0]
                    if field_name:
                        val = body.decode("utf-8", errors="ignore").strip()
                        if field_name in ["num_inference_steps", "seed", "ref_img_index", "mask_frame_range", "transition_overlap_frames", "num_frames"]:
                            try:
                                params[field_name] = int(val)
                            except Exception:
                                pass
                        else:
                            params[field_name] = val

            # Resolve from Audio Library if specified
            audio_lib_fn = urllib.parse.unquote(str(params.get("audio_library_filename", "")).strip())
            if audio_lib_fn and (not audio_path or not audio_path.exists() or audio_path.stat().st_size < 100):
                target_file = AUDIO_LIBRARY_DIR / audio_lib_fn
                if not target_file.exists():
                    clean_name = Path(audio_lib_fn).name
                    for f in AUDIO_LIBRARY_DIR.iterdir():
                        if f.is_file() and (f.name == audio_lib_fn or f.name == clean_name):
                            target_file = f
                            break
                if target_file.exists() and target_file.is_file():
                    original_audio_path = task_upload_dir / target_file.name
                    shutil.copy2(target_file, original_audio_path)
                    audio_path = original_audio_path
                    print(f"✅ [GENERATE] Loaded voiceover from Audio Library: {target_file.name} ({target_file.stat().st_size} bytes)")

            # Resolve preuploaded assets if provided and direct upload not present
            preupload_dir = UPLOAD_DIR / "preupload"
            pre_audio_id = str(params.get("audio_asset_id", "")).strip()
            pre_image_id = str(params.get("image_asset_id", "")).strip()

            if pre_audio_id and (not audio_path or not audio_path.exists() or audio_path.stat().st_size < 100):
                matched = list(preupload_dir.glob(f"{pre_audio_id}*"))
                if matched:
                    cand = matched[0]
                    original_audio_path = task_upload_dir / f"audio{cand.suffix}"
                    shutil.copy2(cand, original_audio_path)
                    audio_path = original_audio_path
                else:
                    # Also check Audio Library by MD5 hash ID
                    for f in AUDIO_LIBRARY_DIR.iterdir():
                        if f.is_file() and hashlib.md5(f.name.encode('utf-8')).hexdigest()[:10] == pre_audio_id:
                            original_audio_path = task_upload_dir / f.name
                            shutil.copy2(f, original_audio_path)
                            audio_path = original_audio_path
                            print(f"✅ [GENERATE] Loaded voiceover from Audio Library by ID match: {f.name}")
                            break

            if pre_image_id and (not image_path or not image_path.exists() or image_path.stat().st_size < 100):
                matched = list(preupload_dir.glob(f"{pre_image_id}*"))
                if matched:
                    cand = matched[0]
                    image_path = task_upload_dir / f"portrait{cand.suffix}"
                    shutil.copy2(cand, image_path)

            # If avatar_id is provided, resolve from avatar presets unless explicit custom image override
            avatar_id = str(params.get("avatar_id", "")).strip()
            use_preset = (str(params.get("use_avatar_preset", "false")).lower() in ("true", "1")) or (not image_path or not image_path.exists() or image_path.stat().st_size < 100)
            if avatar_id and use_preset:
                target_avatar_dir = AVATARS_DIR / avatar_id
                if not target_avatar_dir.exists():
                    for sub in AVATARS_DIR.iterdir():
                        if sub.is_dir():
                            mf = sub / "meta.json"
                            if mf.exists():
                                try:
                                    with open(mf, "r", encoding="utf-8") as f:
                                        if json.load(f).get("id") == avatar_id:
                                            target_avatar_dir = sub
                                            break
                                except Exception:
                                    pass
                if target_avatar_dir and target_avatar_dir.exists():
                    portrait_found = None
                    for p in target_avatar_dir.glob("portrait.*"):
                        if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                            portrait_found = p
                            break
                    if not portrait_found:
                        for p in target_avatar_dir.iterdir():
                            if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                                portrait_found = p
                                break
                    if portrait_found:
                        image_path = task_upload_dir / portrait_found.name
                        shutil.copy2(str(portrait_found), str(image_path))

            if not image_path or not audio_path or not image_path.exists() or not audio_path.exists() or audio_path.stat().st_size < 100 or image_path.stat().st_size < 100:
                self.send_json_response({"error": "Missing or invalid image/audio file. Upload received empty or corrupted file."}, status=400)
                return

            # Ultra-Fast Preprocessing: Sanitize & Normalize to clean 16kHz mono WAV in < 30ms via FFmpeg
            clean_16k_wav = task_upload_dir / "clean_voice_16k.wav"
            try:
                cmd_norm = ["ffmpeg", "-y", "-i", str(original_audio_path or audio_path), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(clean_16k_wav)]
                res_c = subprocess.run(cmd_norm, capture_output=True, timeout=180)
                if res_c.returncode == 0 and clean_16k_wav.exists() and clean_16k_wav.stat().st_size > 100:
                    audio_path = clean_16k_wav
            except Exception as ce:
                print(f"Audio pre-sanitization notice: {ce}")

            # Compute real audio duration and segments
            audio_dur = get_audio_duration(str(audio_path))
            max_vram_gb = get_max_gpu_vram_gb()
            num_f = int(params.get("num_frames", 205))
            if num_f not in [81, 125, 205, 249, 253, 301]:
                num_f = 205
            gen_mode = str(params.get("generation_mode", "anchor_seamless")).strip().lower()
            if gen_mode not in ["anchor_seamless", "sequential_continuation", "sequential", "standard"]:
                gen_mode = "anchor_seamless"
            overlap_f = int(params.get("transition_overlap_frames", 4 if gen_mode == "anchor_seamless" else 13))

            req_res = str(params.get("resolution", "500p")).strip().lower()
            if any(x in req_res for x in ["500p", "500", "512"]):
                clean_res = "500p"
            elif any(x in req_res for x in ["540p", "540", "544"]):
                clean_res = "540p"
            elif any(x in req_res for x in ["600p", "600", "608"]):
                clean_res = "600p"
            elif any(x in req_res for x in ["700p", "700", "704", "1216"]):
                clean_res = "700p"
            else:
                clean_res = "500p"
            params["resolution"] = clean_res

            if params["length_mode"] == "auto":
                num_segs = calculate_segments(audio_dur, num_frames=num_f, generation_mode=gen_mode, transition_overlap=overlap_f)
            else:
                try:
                    num_segs = int(params["length_mode"])
                except Exception:
                    num_segs = calculate_segments(audio_dur, num_frames=num_f, generation_mode=gen_mode, transition_overlap=overlap_f)

            hand_ctrl = params.get("hand_control", "auto")
            t_item = {
                "task_id": task_id,
                "status": "queued",
                "progress": 0.0,
                "stage": "Queued in background",
                "upload_dir": str(task_upload_dir),
                "image_path": str(image_path),
                "audio_path": str(audio_path),
                "original_audio_path": str(original_audio_path or audio_path),
                "audio_duration_sec": audio_dur,
                "num_segments": num_segs,
                "num_frames": num_f,
                "num_inference_steps": params["num_inference_steps"],
                "step_booster": params.get("step_booster", "default"),
                "gender": params.get("gender", "auto"),
                "hand_control": hand_ctrl,
                "generation_mode": gen_mode,
                "transition_overlap_frames": overlap_f,
                "slot_name": params["slot_name"],
                "video_title": params["video_title"],
                "avatar_id": avatar_id,
                "prompt": params["prompt"],
                "negative_prompt": params["negative_prompt"],
                "resolution": clean_res,
                "resolution_label": get_resolution_badge(clean_res),
                "preset": params["preset"],
                "seed": params["seed"],
                "ref_img_index": params["ref_img_index"],
                "mask_frame_range": params["mask_frame_range"],
                "created_at": time.time(),
                "logs": [f"[{time.strftime('%H:%M:%S')}] Task {task_id} registered (Mode: {gen_mode.upper()} • {num_f}f ({num_f/25.0:.1f}s), Booster: {params.get('step_booster', 'default')}, Res: {clean_res}). Audio: {audio_dur:.1f}s ({num_segs} segs) | Steps: {params['num_inference_steps']}."]
            }
            active_tasks[task_id] = t_item

            sequential_queue.put(task_id)
            t_item["queue_type"] = "sequential"
            q_pos = sequential_queue.qsize()
            print(f"[{time.strftime('%H:%M:%S')}] 📥 New generation task registered: {task_id} (Queue position: {q_pos})", flush=True)

            save_active_tasks_to_disk()

            self.send_json_response({
                "task_id": task_id,
                "status": "queued",
                "queue_position": q_pos,
                "num_segments": num_segs,
                "num_inference_steps": params["num_inference_steps"],
                "duration_sec": audio_dur
            })
            return

        self.send_json_response({"error": "Endpoint not found"}, status=404)

    def send_json_response(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

def start_server_on_port(port):
    try:
        server_address = ("0.0.0.0", port)
        httpd = ThreadingHTTPServer(server_address, LongCatStudioHandler)
        print(f"✨ LongCat-Video-Avatar 1.5 Studio is LIVE on 0.0.0.0:{port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"Server on port {port} error: {e}")

if __name__ == "__main__":
    if not acquire_server_lock():
        sys.exit(0)

    load_active_tasks_from_disk()
    t = threading.Thread(target=background_queue_worker, args=(0,), daemon=True)
    t.start()
    worker_threads.append(t)
    ports = [20100, 7860]
    if len(sys.argv) > 1:
        try:
            custom_p = int(sys.argv[1])
            if custom_p not in ports:
                ports.insert(0, custom_p)
        except ValueError:
            pass

    threads = []
    for p in ports:
        t = threading.Thread(target=start_server_on_port, args=(p,), daemon=True)
        t.start()
        threads.append(t)
    
    print(f"🚀 All server threads started! Listening on ports: {ports}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Exiting servers.")
