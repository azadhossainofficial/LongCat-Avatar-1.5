import subprocess, os, sys

cmd = [
    "/venv/main/bin/python", "-u", "-m", "torch.distributed.run",
    "--master_port=49123",
    "--nproc_per_node=2",
    "run_demo_avatar_single_audio_to_video.py",
    "--checkpoint_dir=/workspace/LongCat-Video/weights/LongCat-Video-Avatar-1.5",
    "--stage_1=ai2v",
    "--input_json=/workspace/LongCat-Video/uploads/4ff79a5c/input.json",
    "--output_dir=/workspace/LongCat-Video/outputs/test_max_speed",
    "--model_type=avatar-v1.5",
    "--use_distill",
    "--num_inference_steps=4",
    "--resolution=720p",
    "--ref_img_index=10",
    "--mask_frame_range=0",
    "--num_segments=1",
    "--num_frames=205",
    "--step_booster=maximum_speed",
    "--generation_mode=anchor_seamless",
    "--transition_overlap_frames=4",
    "--context_parallel_size=2"
]

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"
env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
env["PYTHONPATH"] = f"/workspace/LongCat-Video:{env.get('PYTHONPATH', '')}"

print('🚀 Running Maximum Speed test validation...')
p = subprocess.Popen(cmd, cwd="/workspace/LongCat-Video", env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for line in iter(p.stdout.readline, ''):
    print(line, end='', flush=True)
p.wait()
print(f'Test finished with returncode {p.returncode}')
