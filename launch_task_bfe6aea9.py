import subprocess, os, sys, json, time, re, signal, shutil
from pathlib import Path
from PIL import Image, ImageOps

BASE_DIR = Path("/workspace/LongCat-Video")
TASK_ID = "bfe6aea9"
UPLOAD_DIR = BASE_DIR / "uploads" / TASK_ID
OUTPUT_DIR = BASE_DIR / "outputs" / TASK_ID
MAIN_OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TASKS_FILE = BASE_DIR / "active_tasks.json"

def format_seconds_human(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def save_task(t):
    try:
        with open(TASKS_FILE, "r") as f:
            d = json.load(f)
        d[TASK_ID] = t
        with open(TASKS_FILE, "w") as f:
            json.dump(d, f, indent=2)
    except Exception as e:
        print("Save task error:", e)

with open(TASKS_FILE, "r") as f:
    active_tasks = json.load(f)

task = active_tasks.get(TASK_ID, {})
task["status"] = "processing"
task["stage"] = "Initializing Neural Pipeline on 2x RTX 4090..."
task["progress"] = 5.0
task["logs"] = [f"[{time.strftime('%H:%M:%S')}] 🚀 Launching task {TASK_ID} on 2x RTX 4090 GPUs..."]
save_task(task)

start_time = time.time()
cmd = [
    "/venv/main/bin/python", "-u", "-m", "torch.distributed.run",
    "--master_port=46795",
    "--nproc_per_node=2",
    "run_demo_avatar_single_audio_to_video.py",
    "--checkpoint_dir=/workspace/LongCat-Video/weights/LongCat-Video-Avatar-1.5",
    "--stage_1=ai2v",
    f"--input_json={UPLOAD_DIR}/input.json",
    f"--output_dir={OUTPUT_DIR}",
    "--model_type=avatar-v1.5",
    "--use_distill",
    "--num_inference_steps=4",
    "--resolution=480p",
    "--ref_img_index=10",
    "--mask_frame_range=0",
    "--num_segments=154",
    "--num_frames=205",
    "--step_booster=default",
    "--generation_mode=anchor_seamless",
    "--transition_overlap_frames=4",
    "--context_parallel_size=2"
]

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"
env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
env["PYTHONPATH"] = f"{BASE_DIR}:{env.get('PYTHONPATH', '')}"

print("Launching:", " ".join(cmd), flush=True)
proc = subprocess.Popen(
    cmd,
    cwd=str(BASE_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1,
    env=env,
    preexec_fn=os.setsid
)

num_segments = 154
current_segment = 1
buffer = ""
last_save_time = 0

while True:
    char = proc.stdout.read(1)
    if not char:
        break
    if char in ['\r', '\n']:
        clean_line = buffer.strip()
        buffer = ""
        if not clean_line:
            continue
        print(f"[TASK] {clean_line}", flush=True)
        if len(task.get("logs", [])) > 200:
            task["logs"] = task["logs"][-150:]
        task.setdefault("logs", []).append(f"[{time.strftime('%H:%M:%S')}] {clean_line}")

        if "Generating segment" in clean_line:
            m = re.search(r'Generating segment\s+(\d+)/(\d+)', clean_line)
            if m:
                current_segment = int(m.group(1))
                num_segments = int(m.group(2))
                base_pct = 10.0 + ((current_segment - 1) / max(1, num_segments)) * 85.0
                task["progress"] = round(base_pct, 1)
                task["stage"] = f"Generating Segment {current_segment}/{num_segments}"
                task["current_segment"] = current_segment
                task["total_segments"] = num_segments
        elif "Denoising:" in clean_line:
            st_match = re.search(r'(\d+)/(\d+)\s+\[', clean_line)
            if st_match:
                s_c = float(st_match.group(1))
                s_t = float(st_match.group(2))
                if s_t > 0:
                    sub_pct = (s_c / max(1.0, s_t))
                    total_seg_progress = (current_segment - 1 + sub_pct) / num_segments
                    pct = min(95.0, 10.0 + total_seg_progress * 85.0)
                    task["progress"] = round(pct, 1)
                    task["stage"] = f"Denoising Segment {current_segment}/{num_segments} (Step {int(s_c)}/{int(s_t)})"

        if time.time() - last_save_time > 2.0:
            save_task(task)
            last_save_time = time.time()
    else:
        buffer += char

proc.stdout.close()
proc.wait()

print(f"Process finished with return code {proc.returncode}")

# Find output video and package
found_videos = [f for f in OUTPUT_DIR.glob("video_continue_*.mp4") if not f.name.endswith("-cropvideo.mp4") and not f.name.endswith("-temp.mp4")]
if not found_videos:
    found_videos = [f for f in OUTPUT_DIR.glob("*.mp4") if not f.name.endswith("-cropvideo.mp4") and not f.name.endswith("-temp.mp4")]

if found_videos:
    def sort_key(p):
        m = re.search(r'video_continue_(\d+)', p.stem)
        if m:
            return (1, int(m.group(1)))
        return (0, p.stat().st_mtime)

    found_videos.sort(key=sort_key, reverse=True)
    final_video = found_videos[0]
    audio_path = UPLOAD_DIR / "Audio_1_My_Husband_Left_Me_for_His_Secretary_After_17_Years_The_Next_Morning_I_Took_Back_Everything_46211e3d.wav"
    image_path = UPLOAD_DIR / "Woman_skin_tone_natural_beauty_202608250107.jpeg"

    # Packaging 1080P Studio Master
    dest_filename = "Video_1_My_Husband_Left_Me_for_His_Secretary_After_17_Years_The_Next_Morning_I_Took_Back_Everything.mp4"
    dest_path = MAIN_OUTPUT_DIR / dest_filename
    dest_path_720p = MAIN_OUTPUT_DIR / dest_filename.replace(".mp4", "_720p.mp4")

    # Mux audio & scale to 1080p
    cmd_1080 = [
        "ffmpeg", "-y", "-i", str(final_video), "-i", str(audio_path),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,cas=0.55",
        "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        str(dest_path)
    ]
    subprocess.run(cmd_1080, check=True)

    # 720p
    cmd_720 = [
        "ffmpeg", "-y", "-i", str(dest_path),
        "-vf", "scale=1280:720:flags=lanczos,cas=0.45",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart",
        str(dest_path_720p)
    ]
    subprocess.run(cmd_720, check=True)

    # Poster
    dest_path_poster = MAIN_OUTPUT_DIR / dest_filename.replace(".mp4", ".jpg")
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:00.200", "-i", str(dest_path), "-vframes", "1", "-q:v", "2", str(dest_path_poster)], check=True)

    total_sec = max(1, int(time.time() - start_time))
    task["status"] = "completed"
    task["progress"] = 100.0
    task["stage"] = "Completed — Video Ready"
    task["output_video_url"] = f"/outputs/{dest_filename}"
    task["output_filename"] = dest_filename
    task["output_video_url_720p"] = f"/outputs/{dest_filename.replace('.mp4', '_720p.mp4')}"
    task["output_filename_720p"] = dest_filename.replace(".mp4", "_720p.mp4")
    task["poster_url"] = f"/outputs/{dest_filename.replace('.mp4', '.jpg')}"
    task["generation_time_sec"] = total_sec
    task["generation_time_formatted"] = format_seconds_human(total_sec)
    save_task(task)
    print("Task completed and saved successfully!")
