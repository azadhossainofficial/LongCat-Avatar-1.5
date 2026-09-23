"""
LongCat-Video-Avatar 1.5 — Dedicated Headless Inference Bridge
Executes single-person audio-driven talking photo generation with DMD 8-step distillation.
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path

def calculate_segments(audio_duration_sec: float, fps: int = 25, num_frames: int = 93, num_cond_frames: int = 13) -> int:
    """
    Calculates the exact number of autoregressive segments required for full audio length.
    Segment 1 = num_frames / fps = 93/25 = 3.72s
    Continuation segments = (num_frames - num_cond_frames) / fps = 80/25 = 3.20s each
    """
    if audio_duration_sec <= (num_frames / fps):
        return 1
    remaining_sec = audio_duration_sec - (num_frames / fps)
    step_sec = (num_frames - num_cond_frames) / fps
    return 1 + math.ceil(remaining_sec / step_sec)

def build_task_config(
    image_path: str,
    audio_path: str,
    output_json_path: str,
    prompt: str = "A professional person is speaking naturally, blinking smoothly, clear facial expressions, natural head tilts, crisp teeth and mouth movement, static background, studio lighting."
):
    """
    Constructs the input JSON configuration required by LongCat-Video-Avatar single runner.
    """
    config = {
        "prompt": prompt,
        "cond_image": os.path.abspath(image_path),
        "cond_audio": {
            "person1": os.path.abspath(audio_path)
        }
    }
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    return output_json_path

def build_torchrun_command(
    checkpoint_dir: str,
    input_json_path: str,
    output_dir: str,
    num_segments: int,
    resolution: str = "768x1280",
    use_int8: bool = False,
    ref_img_index: int = 10,
    mask_frame_range: int = 3,
    num_gpus: int = 1
) -> str:
    """
    Constructs the exact optimized torchrun command for A100 / H100 GPU servers.
    """
    res_arg = "720p" if "1280" in resolution or "768" in resolution else "480p"
    int8_flag = "--use_int8" if use_int8 else ""
    
    cmd = (
        f"torchrun --nproc_per_node={num_gpus} run_demo_avatar_single_audio_to_video.py "
        f"--checkpoint_dir={checkpoint_dir} "
        f"--stage_1=ai2v "
        f"--input_json={input_json_path} "
        f"--output_dir={output_dir} "
        f"--model_type avatar-v1.5 "
        f"--use_distill "
        f"--resolution {res_arg} "
        f"--ref_img_index {ref_img_index} "
        f"--mask_frame_range {mask_frame_range} "
        f"--num_segments {num_segments} "
        f"{int8_flag}"
    )
    return cmd.strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LongCat-Video-Avatar 1.5 Runner Bridge")
    parser.add_argument("--image", type=str, required=True, help="Path to avatar portrait image")
    parser.add_argument("--audio", type=str, required=True, help="Path to speech voiceover audio")
    parser.add_argument("--duration", type=float, default=10.0, help="Audio duration in seconds")
    parser.add_argument("--resolution", type=str, default="768x1280", help="Output video resolution")
    parser.add_argument("--output_dir", type=str, default="./outputs", help="Output directory")
    parser.add_argument("--checkpoint_dir", type=str, default="./weights/LongCat-Video-Avatar-1.5", help="Weights folder")
    parser.add_argument("--use_int8", action="store_true", help="Enable INT8 quantization")
    
    args = parser.parse_args()
    
    seg_count = calculate_segments(args.duration)
    print(f"[*] Total calculated segments for {args.duration}s audio: {seg_count}")
    
    json_path = "./temp_input.json"
    build_task_config(args.image, args.audio, json_path)
    
    cmd = build_torchrun_command(
        checkpoint_dir=args.checkpoint_dir,
        input_json_path=json_path,
        output_dir=args.output_dir,
        num_segments=seg_count,
        resolution=args.resolution,
        use_int8=args.use_int8
    )
    print(f"[*] Prepared Execution Command:\n{cmd}")
