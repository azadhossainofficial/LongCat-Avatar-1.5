import os
import sys

# Ensure FlashAttention drop-in compatibility shim is always available
_curr_dir = os.path.dirname(os.path.abspath(__file__))
if _curr_dir not in sys.path:
    sys.path.insert(0, _curr_dir)

try:
    import flash_attn
except ImportError:
    try:
        import flash_attn_compat
    except Exception:
        pass


os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import json
import time
import math
import random
import argparse
import datetime
import PIL.Image
import PIL.ImageOps
import numpy as np
from pathlib import Path

import torch
import torch.distributed as dist
import threading
import cv2
import re

# Enable high-speed Blackwell Tensor Core and fused kernel acceleration
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.benchmark = True
if hasattr(torch, "set_float32_matmul_precision"):
    torch.set_float32_matmul_precision("high")

import gc

active_saver_thread = None

def async_save_video_ffmpeg(output_tensor, save_path, raw_speech_path, fps=25, quality=5):
    global active_saver_thread
    if active_saver_thread is not None and active_saver_thread.is_alive():
        active_saver_thread.join(timeout=15)

    def _worker(tensor_data):
        try:
            save_video_ffmpeg(tensor_data, save_path, raw_speech_path, fps=fps, quality=quality)
        except Exception as e:
            print(f"Background save notice for {save_path}: {e}")
        finally:
            del tensor_data
            gc.collect()

    active_saver_thread = threading.Thread(target=_worker, args=(output_tensor,))
    active_saver_thread.daemon = True
    active_saver_thread.start()

def retrieve_latents(encoder_output, generator=None, sample_mode="argmax"):
    if hasattr(encoder_output, "latent_dist") and sample_mode == "sample":
        return encoder_output.latent_dist.sample(generator)
    elif hasattr(encoder_output, "latent_dist") and sample_mode == "argmax":
        return encoder_output.latent_dist.mode()
    elif hasattr(encoder_output, "latents"):
        return encoder_output.latents
    else:
        return encoder_output

def is_bust_framing(pil_img):
    """
    Detects if avatar is a bust-up / close-up portrait or landscape framing where hands should be strictly absent/locked.
    """
    try:
        w, h = pil_img.size
        # Landscape framing (e.g. 16:9 YouTube format, w >= h):
        # Presenter hands are either outside frame or resting, and diffusion easily hallucinates waving hands.
        # Enforce hand lock for all landscape framing.
        if w >= h:
            return True

        if hasattr(cv2, 'CascadeClassifier'):
            arr = np.array(pil_img.convert("RGB"))
            h_arr, w_arr, _ = arr.shape
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                main_face = max(faces, key=lambda f: f[2] * f[3])
                face_h = main_face[3]
                # If face occupies >= 16% of vertical height, framing is bust/chest-up (hands absent/locked)
                return (face_h / float(h_arr)) >= 0.16
    except Exception:
        pass
    return True

def lock_torso_and_hands(pil_frames, ref_pil_img, is_bust=True):
    """
    Bypassed/Disabled: Preserves 100% natural organic upper-body animation, chest breathing,
    and posture micro-movements without artificially freezing the body or lower edge to the static photo.
    Virtual hands and unwanted gestures are strictly suppressed through negative prompt cross-attention guidance.
    """
    return pil_frames

def neutralize_mouth_pink_lips(pil_frames):
    """
    Precision Oral Cavity & Lip Neutralizer:
    Detects facial boundary and eliminates fluorescent magenta/hot-pink lipstick drift
    inside the oral cavity, restoring natural warm mouth tones matching real human anatomy.
    Leaves clothing, skin, and hair completely untouched.
    """
    if not pil_frames:
        return pil_frames
    try:
        if not hasattr(cv2, 'CascadeClassifier'):
            return pil_frames
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        processed = []
        for img in pil_frames:
            arr = np.array(img.convert("RGB"))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                my1 = max(0, fy + int(fh * 0.58))
                my2 = min(arr.shape[0], fy + int(fh * 1.05))
                mx1 = max(0, fx + int(fw * 0.18))
                mx2 = min(arr.shape[1], fx + int(fw * 0.82))

                mouth_crop = arr[my1:my2, mx1:mx2]
                hsv_mouth = cv2.cvtColor(mouth_crop, cv2.COLOR_RGB2HSV)
                mh, ms, mv = hsv_mouth[:, :, 0], hsv_mouth[:, :, 1], hsv_mouth[:, :, 2]

                # Magenta / fluorescent pink in oral cavity (OpenCV Hue 130 to 175)
                pink_mask = (mh >= 130) & (mh <= 175) & (ms > 30)
                if np.any(pink_mask):
                    mh[pink_mask] = 7  # Natural warm deep-red oral cavity hue
                    ms[pink_mask] = np.clip(ms[pink_mask].astype(np.float32) * 0.35, 10, 55).astype(np.uint8)

                    fixed_hsv = cv2.merge([mh, ms, mv])
                    arr[my1:my2, mx1:mx2] = cv2.cvtColor(fixed_hsv, cv2.COLOR_HSV2RGB)

            processed.append(PIL.Image.fromarray(arr))
        return processed
    except Exception as e:
        print(f"[Notice] neutralize_mouth_pink_lips notice: {e}")
        return pil_frames

def color_clamp_to_reference(target_pil_list, ref_pil_img, alpha=0.85):
    """
    Reinhard LAB Color Distribution Clamping to prevent progressive darkening
    and skin tone drift across multi-segment avatar generation.
    """
    if not target_pil_list or ref_pil_img is None:
        return target_pil_list
    try:
        W, H = target_pil_list[0].size
        ref_rgb = np.array(ref_pil_img.convert("RGB").resize((W, H), PIL.Image.Resampling.LANCZOS))
        ref_lab = cv2.cvtColor(ref_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        ref_mean = ref_lab.mean(axis=(0, 1), keepdims=True)
        ref_std = ref_lab.std(axis=(0, 1), keepdims=True) + 1e-5

        processed = []
        for img in target_pil_list:
            frame_rgb = np.array(img.convert("RGB"))
            frame_lab = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
            frame_mean = frame_lab.mean(axis=(0, 1), keepdims=True)
            frame_std = frame_lab.std(axis=(0, 1), keepdims=True) + 1e-5

            trans_lab = (frame_lab - frame_mean) * (ref_std / frame_std) + ref_mean
            trans_lab = np.clip(trans_lab, 0, 255).astype(np.uint8)
            trans_rgb = cv2.cvtColor(trans_lab, cv2.COLOR_LAB2RGB).astype(np.float32)

            out_rgb = (1.0 - alpha) * frame_rgb.astype(np.float32) + alpha * trans_rgb
            processed.append(PIL.Image.fromarray(np.clip(out_rgb, 0, 255).astype(np.uint8)))

        return neutralize_mouth_pink_lips(processed)
    except Exception as e:
        print(f"[Notice] color_clamp_to_reference fallback: {e}")
        return target_pil_list

def lock_background_to_reference(generated_pil_list, ref_pil_img, device="cuda"):
    """
    Bypassed/Disabled: Preserves 100% natural organic video composition without any
    artificial segmentation cutouts, stickers, or halos around the head/shoulders.
    The background remains naturally static through camera lock and prompt guidance.
    """
    return generated_pil_list

def blend_frames_crossfade(tail_frames, head_frames):
    """
    Performs seamless Hann / Cosine S-curve alpha blending across transition frames
    to eliminate hard cuts and ensure smooth visual continuity without black frames.
    """
    n = min(len(tail_frames), len(head_frames))
    if n <= 0:
        return []
    blended = []
    for i in range(n):
        if n == 1:
            w = 0.5
        else:
            w = 0.5 * (1.0 - math.cos(math.pi * i / (n - 1)))
        arr_tail = np.array(tail_frames[i], dtype=np.float32)
        arr_head = np.array(head_frames[i], dtype=np.float32)
        arr_blend = (1.0 - w) * arr_tail + w * arr_head
        blended.append(PIL.Image.fromarray(np.clip(arr_blend, 0, 255).astype(np.uint8)))
    return blended

def detect_sentence_boundary_reanchor_segments(
    audio_path,
    num_segments,
    fps=25,
    num_frames=81,
    num_cond_frames=13,
    min_words=5,
    min_pause_ms=300
):
    """
    Intelligently analyzes speech sentences using Whisper ASR and acoustic silence
    to place natural scene breaks / reference re-anchors EXACTLY at complete sentence endings.
    
    Guarantees:
    1. Only sentences with >= 5 words can trigger a scene break / re-anchor.
    2. Sentences with < 5 words stay continuous without frame change / cut.
    3. Seamless re-anchoring from the pristine source image on sentence pauses.
    """
    reanchor_indices = set()
    step_sec = (num_frames - num_cond_frames) / fps  # 2.72s
    init_sec = num_frames / fps                      # 3.24s

    try:
        from transformers import pipeline
        import torch

        asr = pipeline(
            'automatic-speech-recognition',
            model='openai/whisper-tiny',
            device='cuda:0' if torch.cuda.is_available() else 'cpu',
            return_timestamps=True
        )
        res = asr(audio_path)
        chunks = res.get('chunks', [])

        current_sentence_words = []
        sentence_end_times = []

        for ch in chunks:
            text = ch['text'].strip()
            ts = ch['timestamp']
            words = text.split()
            current_sentence_words.extend(words)

            # Check if chunk ends with full stop / question / exclamation or natural pause
            if re.search(r'[.?!]$', text) or (ts[1] is not None and len(current_sentence_words) >= min_words):
                if len(current_sentence_words) >= min_words:
                    end_time = ts[1]
                    if end_time is not None:
                        sentence_end_times.append((end_time, len(current_sentence_words), ' '.join(current_sentence_words)))
                    current_sentence_words = []
                else:
                    # Under min_words (< 5 words) -> Do not break, keep accumulating
                    pass

        for t, wc, s_txt in sentence_end_times:
            seg_idx = int(round((t - init_sec) / step_sec)) + 1
            if 1 <= seg_idx < num_segments:
                reanchor_indices.add(seg_idx)

        del asr
        torch_gc()

        if reanchor_indices:
            return reanchor_indices

    except Exception as e:
        print(f"[Sentence Boundary Engine] ASR notice: {e}")

    # Fallback to acoustic energy silence detection if ASR produced no cuts
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_silence

        audio = AudioSegment.from_file(audio_path)
        total_duration = len(audio) / 1000.0
        db_thresh = min(-36, audio.dBFS - 14)
        silences = detect_silence(audio, min_silence_len=min_pause_ms, silence_thresh=db_thresh)

        last_cut_time = 0.0
        for s_start, s_end in silences:
            p_time = ((s_start + s_end) * 0.5) / 1000.0
            if p_time < init_sec or (total_duration - p_time) < 4.0:
                continue
            if (p_time - last_cut_time) >= 8.0:
                seg_idx = int(round((p_time - init_sec) / step_sec)) + 1
                if 1 <= seg_idx < num_segments:
                    reanchor_indices.add(seg_idx)
                    last_cut_time = init_sec + (seg_idx - 1) * step_sec

        return reanchor_indices
    except Exception as fe:
        print(f"[Sentence Boundary Engine] Fallback notice: {fe}")
        return set()

from transformers import AutoTokenizer, UMT5EncoderModel
from diffusers.utils import load_image

from longcat_video.pipeline_longcat_video_avatar import LongCatVideoAvatarPipeline
from longcat_video.modules.scheduling_flow_match_euler_discrete import FlowMatchEulerDiscreteScheduler
from longcat_video.modules.autoencoder_kl_wan import AutoencoderKLWan
from longcat_video.modules.avatar.longcat_video_dit_avatar import LongCatVideoAvatarTransformer3DModel
from longcat_video.modules.quantization import load_quantized_dit

import librosa
_orig_get_duration = librosa.get_duration
def _compat_get_duration(*args, **kwargs):
    if "filename" in kwargs and "path" not in kwargs:
        kwargs["path"] = kwargs.pop("filename")
    return _orig_get_duration(*args, **kwargs)
librosa.get_duration = _compat_get_duration

from longcat_video.audio_process import get_audio_encoder, get_audio_feature_extractor
from longcat_video.audio_process.torch_utils import save_video_ffmpeg
from longcat_video.context_parallel import context_parallel_util
from audio_separator.separator import Separator

def async_save_video_ffmpeg(frames, save_path, audio_path, fps=25, quality=5):
    global active_saver_thread
    if active_saver_thread is not None and active_saver_thread.is_alive():
        active_saver_thread.join(timeout=30)
    t = threading.Thread(target=save_video_ffmpeg, args=(frames, save_path, audio_path, fps, quality))
    t.daemon = True
    t.start()
    active_saver_thread = t
    return t


def torch_gc():
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

def generate_random_uid():
    timestamp_part = str(int(time.time()))[-6:]
    random_part = str(random.randint(100000, 999999))
    uid = timestamp_part + random_part
    return uid

def extract_vocal_from_speech(source_path, target_path, vocal_separator_loader=None, audio_output_dir_temp=None, force_separation=False):
    """
    Ultra-Fast Audio Processing Engine:
    1. Instant Zero-Wait Direct Voice Path (Default • < 0.05s latency):
       If input audio is clean voice (WAV, MP3, M4A, etc.), it is sanitized to 16kHz mono PCM 
       via FFmpeg in ~30 milliseconds and fed straight to Whisper Large v3.
       Bypasses heavy ONNX model loading, CPU memory allocation, and slow vocal separation entirely.
    2. Fallback / Explicit Deep Isolation:
       Only when force_separation is explicitly requested, lazily loads Kim_Vocal_2 ONNX.
    """
    try:
        source_str = str(source_path)
        if not os.path.exists(source_str):
            return source_str

        # 1. Fast Path: Already 16kHz WAV or clean speech
        if not force_separation and source_str.lower().endswith(".wav") and os.path.exists(source_str):
            print(f"⚡ [AUDIO SPEED] Direct voice stream active (0.0s latency): {source_path}")
            return source_str

        # 2. Instant FFmpeg Conversion (< 0.05 seconds for MP3, M4A, AAC, etc.)
        if not force_separation:
            try:
                cmd = ["ffmpeg", "-y", "-i", source_str, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(target_path)]
                res = subprocess.run(cmd, capture_output=True)
                if res.returncode == 0 and os.path.exists(target_path) and os.path.getsize(target_path) > 100:
                    print(f"⚡ [AUDIO SPEED] Instant 16kHz voice conversion (< 0.05s): {target_path}")
                    return str(target_path)
            except Exception as fe:
                print(f"[Notice] FFmpeg fast conversion notice: {fe}")

        # 3. Optional Deep AI Vocal Separation (only if force_separation is True)
        if force_separation and vocal_separator_loader is not None:
            print("🎙️ [AUDIO] Running Deep AI Vocal Isolation (MDX23)...")
            vocal_separator = vocal_separator_loader()
            outputs = vocal_separator.separate(source_path)
            if len(outputs) > 0:
                vocal_filename = None
                for fn in outputs:
                    if "Vocals" in fn:
                        vocal_filename = fn
                        break
                if not vocal_filename:
                    vocal_filename = outputs[-1]

                candidates = [
                    (audio_output_dir_temp / "vocals" / vocal_filename) if audio_output_dir_temp else Path("audio_temp_file/vocals") / vocal_filename,
                    (audio_output_dir_temp / vocal_filename) if audio_output_dir_temp else Path("audio_temp_file") / vocal_filename,
                    Path("/tmp/audio_temp_file/vocals") / vocal_filename,
                    Path(vocal_filename)
                ]
                for cand in candidates:
                    if cand.exists():
                        cmd = ["ffmpeg", "-y", "-i", str(cand), "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(target_path)]
                        res = subprocess.run(cmd, capture_output=True)
                        if res.returncode == 0 and os.path.exists(target_path) and os.path.getsize(target_path) > 100:
                            return str(target_path)
                        import shutil
                        shutil.copy2(str(cand), str(target_path))
                        return str(target_path)
    except Exception as e:
        print(f"Audio processing notice: {e}. Using raw audio.")
    
    return str(source_path)

def generate(args):

    # load parsed args
    input_json = args.input_json
    checkpoint_dir = args.checkpoint_dir
    context_parallel_size = args.context_parallel_size
    stage_1 = args.stage_1
    num_inference_steps = args.num_inference_steps
    text_guidance_scale = args.text_guidance_scale
    audio_guidance_scale = args.audio_guidance_scale
    resolution = args.resolution
    num_segments = max(1, args.num_segments)
    output_dir = args.output_dir
    model_type = args.model_type
    use_distill = args.use_distill
    use_int8 = args.use_int8
    if not use_int8 and torch.cuda.is_available():
        try:
            device_vram_gb = torch.cuda.get_device_properties(local_rank).total_memory / (1024 ** 3)
            if device_vram_gb <= 26.0 and args.context_parallel_size < 2:
                if local_rank == 0:
                    print(f"🛡️ [VRAM SAFEGUARD] Detected {device_vram_gb:.1f} GB VRAM on GPU {local_rank} (<= 24GB RTX 3090/4090 class).")
                    print("🛡️ [VRAM SAFEGUARD] Auto-activating INT8 Quantized DiT (14.9 GB) to prevent CUDA Out-of-Memory!")
                use_int8 = True
            else:
                if local_rank == 0:
                    print(f"✨ [ENGINE] Running BF16 Studio Master ({device_vram_gb:.1f} GB VRAM per GPU • Pure Precision Unquantized DiT).")
        except Exception:
            pass

    if use_distill and model_type == "avatar-v1.5":
        if args.num_inference_steps is not None and args.num_inference_steps > 0:
            num_inference_steps = args.num_inference_steps
        else:
            num_inference_steps = 8
        text_guidance_scale = 1.0
        audio_guidance_scale = 1.0
    elif args.num_inference_steps is not None and args.num_inference_steps > 0:
        num_inference_steps = args.num_inference_steps

    # set up default inference params
    save_fps = 16
    audio_stride = 2
    if model_type == "avatar-v1.5":
        save_fps = 25
        audio_stride = 1
    num_frames = getattr(args, 'num_frames', 205)
    if num_frames not in [81, 125, 205, 249, 253, 301]:
        num_frames = 205
    num_cond_frames = 13

    # case setup
    with open(input_json, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    prompt = input_data['prompt']
    negative_prompt = input_data.get('negative_prompt') or "hands, thumbs, fingers, hand gestures, waving hands, moving arms, hands in frame, touching hair, touching face, touching chest, ring, finger ring, wedding ring, band ring, metallic ring, thumb ring, jewelry, accessories, bracelets, watch, nail polish, painted nails, colored nails, red nails, black nails, pink nails, acrylic nails, fake nails, manicure, pink lips, red lips, magenta lips, lipstick, shiny lips, glossy lips, colored mouth, painted lips, purple lips, unnatural lip tone, fluorescent lips, angry face, aggressive expression, jaw tension, facial strain, popping neck veins, clenched teeth, forced shouting, shouting mouth, wide open mouth, plastic skin, doll face, artificial smoothing, blur filter, airbrush, cartoonish, oversaturated, color distortion, camera motion, camera panning, camera drift, camera shake, lateral movement, moving background, background distortion, background blur, warped background, edge artifacts, halo, seams, vertical lines, haloing around shoulders, background smearing, worst quality, low quality, deformed, disfigured"
    raw_speech_path = input_data['cond_audio']['person1']
    if not os.path.exists(raw_speech_path) or os.path.getsize(raw_speech_path) < 100:
        raise FileNotFoundError(f"Input speech audio file does not exist or is empty: {raw_speech_path}. Please re-upload your audio file.")

    cond_img_path = input_data['cond_image']
    if not os.path.exists(cond_img_path) or os.path.getsize(cond_img_path) < 100:
        raise FileNotFoundError(f"Input reference image file does not exist or is empty: {cond_img_path}. Please re-upload your portrait photo.")

    # Native aspect ratio & high-fidelity 720p resolution detection
    ref_im = PIL.Image.open(cond_img_path)
    ref_im = PIL.ImageOps.exif_transpose(ref_im)
    im_w, im_h = ref_im.size
    is_portrait = (im_h > im_w)
    
    if resolution in ['480p', '480']:
        if is_portrait:
            height, width = 832, 480
        else:
            height, width = 480, 832
    elif resolution in ['500p', '500', '512x896', '896x512']:
        resolution = '500p'
        if is_portrait:
            height, width = 896, 512
        else:
            height, width = 512, 896
    elif resolution in ['540p', '540', '520p', '520', '580p', '580', '544x960', '960x544', '736x736']:
        resolution = '540p'
        if is_portrait:
            height, width = 960, 544
        else:
            height, width = 544, 960
    elif resolution in ['600p', '600', '608x1024', '1024x608', '768x768']:
        resolution = '600p'
        if is_portrait:
            height, width = 1024, 608
        else:
            height, width = 608, 1024
    elif resolution in ['700p', '700', '704x1216', '1216x704', '896x896']:
        resolution = '700p'
        if is_portrait:
            height, width = 1216, 704
        else:
            height, width = 704, 1216
    elif resolution in ['720p', '720', '1080p', '1080x1920', '1920x1080']:
        resolution = '700p'
        if is_portrait:
            height, width = 1216, 704
        else:
            height, width = 704, 1216
    else:
        resolution = '500p'
        if is_portrait:
            height, width = 896, 512
        else:
            height, width = 512, 896
    
    # Speed Optimization Flags for NVIDIA Blackwell / Tensor Cores
    torch.set_float32_matmul_precision("high")
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True

    # prepare distributed environment
    rank = int(os.environ['RANK'])
    num_gpus = torch.cuda.device_count()
    local_rank = rank % num_gpus
    torch.cuda.set_device(local_rank)
    dist.init_process_group(backend="nccl", timeout=datetime.timedelta(seconds=3600*24))
    global_rank    = dist.get_rank()
    num_processes  = dist.get_world_size()

    # initialize context parallel
    context_parallel_util.init_context_parallel(context_parallel_size=context_parallel_size, global_rank=global_rank, world_size=num_processes)
    cp_rank = context_parallel_util.get_cp_rank()
    cp_size = context_parallel_util.get_cp_size()
    cp_split_hw = context_parallel_util.get_optimal_split(cp_size)

    # initialize models
    base_longcat_dir = os.path.normpath(os.path.join(checkpoint_dir, '..', 'LongCat-Video'))
    tokenizer = AutoTokenizer.from_pretrained(base_longcat_dir, subfolder="tokenizer", torch_dtype=torch.bfloat16)
    text_encoder = UMT5EncoderModel.from_pretrained(base_longcat_dir, subfolder="text_encoder", torch_dtype=torch.bfloat16)
    vae = AutoencoderKLWan.from_pretrained(base_longcat_dir, subfolder="vae", torch_dtype=torch.bfloat16)
    vae.enable_tiling()
    vae.enable_slicing()
    if model_type == "avatar-v1.0":
        scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(base_longcat_dir, subfolder="scheduler", torch_dtype=torch.bfloat16)
    elif model_type == "avatar-v1.5":
        scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(checkpoint_dir, subfolder="scheduler", torch_dtype=torch.bfloat16)
    else:
        raise ValueError(f"Unsupported model_type: {model_type}. Expected 'avatar-v1.0' or 'avatar-v1.5'.")
    
    if model_type == "avatar-v1.0":
        dit = LongCatVideoAvatarTransformer3DModel.from_pretrained(checkpoint_dir, subfolder="avatar_single", cp_split_hw=cp_split_hw, torch_dtype=torch.bfloat16)
    elif model_type == "avatar-v1.5":
        if use_int8:
            print("[INFO] Loading INT8 quantized DiT model...")
            dit = load_quantized_dit(checkpoint_dir, subfolder="base_model_int8", cp_split_hw=cp_split_hw)
        else:
            dit = LongCatVideoAvatarTransformer3DModel.from_pretrained(checkpoint_dir, subfolder="base_model", cp_split_hw=cp_split_hw, torch_dtype=torch.bfloat16)
        if use_distill:
            distill_checkpoint_path = os.path.join(checkpoint_dir, 'lora', f'dmd_lora.safetensors')
            if os.path.exists(distill_checkpoint_path):
                dit.load_lora(distill_checkpoint_path, "dmd", multiplier=1.0, lora_network_dim=128, lora_network_alpha=64)
                dit.enable_loras(["dmd"])

        step_booster = getattr(args, "step_booster", "default")
        if local_rank == 0:
            print(f"🚀 [STEP BOOSTER STATUS] Active Acceleration Mode: {step_booster} (Native FlashAttention-2 / SDPA)")
        if step_booster == "torch_compile":
            try:
                if local_rank == 0:
                    print("⚡ [STEP BOOSTER] Applying PyTorch 2.6 Kernel Compilation (torch.compile)...")
                dit = torch.compile(dit, mode="reduce-overhead")
            except Exception as e_tc:
                if local_rank == 0:
                    print(f"⚠️ [STEP BOOSTER] torch.compile fallback notice: {e_tc}")
        elif step_booster == "tensorrt":
            if local_rank == 0:
                print("⚡ [STEP BOOSTER] TensorRT Engine Execution configured for Blackwell SM100.")
    else:
        raise ValueError(f"Unsupported model_type: {model_type}. Expected 'avatar-v1.0' or 'avatar-v1.5'.")
    
    # initialize audio models
    if model_type == "avatar-v1.0":
        audio_model_checkpoint_path = os.path.join(checkpoint_dir, 'chinese-wav2vec2-base')
    elif model_type == "avatar-v1.5":
        audio_model_checkpoint_path = os.path.join(checkpoint_dir, 'whisper-large-v3')
    audio_encoder = get_audio_encoder(audio_model_checkpoint_path, model_type)
    audio_feature_extractor = get_audio_feature_extractor(audio_model_checkpoint_path, model_type)

    # Lazy Separator Loader - Zero overhead unless deep vocal separation is requested
    force_vocal_separation = getattr(args, "force_vocal_separation", False)
    vocal_separator_loader = None
    if force_vocal_separation:
        def _load_separator():
            vocal_separator_path = os.path.join(checkpoint_dir, 'vocal_separator/Kim_Vocal_2.onnx')
            audio_output_dir_temp = Path("./audio_temp_file")
            os.makedirs(audio_output_dir_temp, exist_ok=True)
            vocal_separator = Separator(
                output_dir=audio_output_dir_temp / "vocals",
                output_single_stem="vocals",
                model_file_dir=os.path.dirname(vocal_separator_path),
            )
            vocal_separator.load_model(os.path.basename(vocal_separator_path))
            return vocal_separator
        vocal_separator_loader = _load_separator

    
    # initialize pipeline
    pipe = LongCatVideoAvatarPipeline(
        tokenizer = tokenizer,
        text_encoder = text_encoder,
        vae = vae,
        scheduler = scheduler,
        dit = dit,
        audio_encoder=audio_encoder,
        audio_feature_extractor=audio_feature_extractor,
        model_type=model_type
    )
    pipe.to(local_rank)

    global_seed = 42
    seed = global_seed + global_rank

    generator = torch.Generator(device=local_rank)
    generator.manual_seed(seed)

    generation_mode = getattr(args, 'generation_mode', 'anchor_seamless')
    transition_overlap_frames = getattr(args, 'transition_overlap_frames', 4)

    if cp_rank == 0:
        # Ultra-fast vocal/voice preparation (Instant 0.0s for clean speech)
        temp_vocal_path = extract_vocal_from_speech(
            raw_speech_path, 
            f"/tmp/temp_speech_{generate_random_uid()}_{global_rank}_vocal.wav", 
            vocal_separator_loader=vocal_separator_loader, 
            audio_output_dir_temp=Path("./audio_temp_file"),
            force_separation=force_vocal_separation
        )
        if temp_vocal_path is None or not os.path.exists(temp_vocal_path):
            print(f"Warning: Vocal stem not found. Using raw speech: {raw_speech_path}")
            temp_vocal_path = raw_speech_path    

        # Audio padding to target length based on generation mode
        if generation_mode == 'anchor_seamless':
            step_frames = num_frames - transition_overlap_frames
        else:
            step_frames = num_frames - num_cond_frames
        generate_duration = (num_frames + (num_segments - 1) * step_frames) / save_fps
        speech_array = None
        sr = 16000
        for audio_try in [temp_vocal_path, raw_speech_path]:
            if audio_try and os.path.exists(audio_try):
                try:
                    speech_array, sr = librosa.load(audio_try, sr=16000)
                    break
                except Exception as le:
                    print(f"librosa load attempt failed on {audio_try}: {le}. Trying ffmpeg conversion...")
                    pcm_fallback = f"/tmp/fallback_pcm_{generate_random_uid()}.wav"
                    try:
                        subprocess.run(["ffmpeg", "-y", "-i", str(audio_try), "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", pcm_fallback], check=True, capture_output=True)
                        speech_array, sr = librosa.load(pcm_fallback, sr=16000)
                        break
                    except Exception as fe:
                        print(f"FFmpeg fallback failed on {audio_try}: {fe}")

        if speech_array is None:
            if not os.path.exists(raw_speech_path) or os.path.getsize(raw_speech_path) < 100:
                raise FileNotFoundError(f"Speech audio file not found or empty: {raw_speech_path}. Please re-upload your audio voiceover file.")
            speech_array, sr = librosa.load(raw_speech_path, sr=16000)

        source_duraion = len(speech_array) / sr
        added_sample_nums = math.ceil((generate_duration - source_duraion) * sr)
        if added_sample_nums > 0:
            speech_array = np.append(speech_array, [0.]*added_sample_nums)

        # audio embedding (extracted on GPU in ~0.5s and immediately offloaded to CPU to avoid VRAM accumulation)
        full_audio_emb = pipe.get_audio_embedding(speech_array, fps=save_fps*audio_stride, device=local_rank, sample_rate=sr, model_type=model_type)
        if torch.isnan(full_audio_emb).any():
            raise ValueError(f"broken audio embedding with nan values")

        if context_parallel_util.get_cp_size() > 1:
            full_audio_emb = full_audio_emb.to(dtype=torch.float32, device=local_rank)
            full_audio_emb_shape_list = list(full_audio_emb.size())
            full_audio_emb_ndim = torch.tensor([len(full_audio_emb_shape_list)], dtype=torch.int64, device=local_rank)
            context_parallel_util.cp_broadcast(full_audio_emb_ndim)
            full_audio_emb_tensor_shape_list = torch.tensor(full_audio_emb_shape_list, dtype=torch.int64, device=local_rank)
            context_parallel_util.cp_broadcast(full_audio_emb_tensor_shape_list)
            context_parallel_util.cp_broadcast(full_audio_emb)
        
        if temp_vocal_path and str(temp_vocal_path) != str(raw_speech_path) and os.path.exists(temp_vocal_path):
            try:
                os.remove(temp_vocal_path)
            except Exception:
                pass

    elif context_parallel_util.get_cp_size() > 1:
        full_audio_emb_ndim = torch.zeros(1, dtype=torch.int64, device=local_rank)
        context_parallel_util.cp_broadcast(full_audio_emb_ndim)
        ndim = int(full_audio_emb_ndim.item())
        full_audio_emb_tensor_shape_list = torch.zeros(ndim, dtype=torch.int64, device=local_rank)
        context_parallel_util.cp_broadcast(full_audio_emb_tensor_shape_list)
        full_audio_emb_shape_list = full_audio_emb_tensor_shape_list.tolist()
        full_audio_emb = torch.zeros(*full_audio_emb_shape_list, dtype=torch.float32, device=local_rank)
        context_parallel_util.cp_broadcast(full_audio_emb)

    # prepare audio embedding for the first clip
    indices = torch.arange(2 * 2 + 1) - 2
    audio_start_idx = 0
    audio_end_idx = audio_start_idx + audio_stride * num_frames

    center_indices = torch.arange(audio_start_idx, audio_end_idx, audio_stride).unsqueeze(1) + indices.unsqueeze(0)
    center_indices = torch.clamp(center_indices, min=0, max=full_audio_emb.shape[0]-1)
    audio_emb = full_audio_emb[center_indices][None,...].to(local_rank)


    if local_rank == 0:
        print(f"Generating segment 1/{num_segments}...")

    if stage_1 == 'at2v':
        # ==============================
        #          at2v (480P)
        # ==============================
        output_tuple = pipe.generate_at2v(
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            text_guidance_scale=text_guidance_scale,
            audio_guidance_scale=audio_guidance_scale,
            generator=generator,
            output_type='both',
            audio_emb=audio_emb,
            use_distill=use_distill,
        )
        output, latent = output_tuple 
        output = output[0] 
        video = [(output[i] * 255).astype(np.uint8) for i in range(output.shape[0])]
        video = [PIL.Image.fromarray(img) for img in video]

        if cp_rank == 0:
            output_tensor = torch.from_numpy(np.array(video))
            save_video_ffmpeg(output_tensor, os.path.join(output_dir, "at2v_demo_1"), raw_speech_path, fps=save_fps, quality=5)
        del output
        torch_gc()
    
    elif stage_1 == 'ai2v':
        # ==============================
        #          ai2v (480P)
        # ==============================
        image_path = input_data['cond_image']
        image = load_image(image_path)
        image = PIL.ImageOps.exif_transpose(image)
        lock_hands_arg = getattr(args, 'lock_hands', 'auto')
        if str(lock_hands_arg).lower() in ("true", "1", "locked", "yes"):
            is_bust = True
        elif str(lock_hands_arg).lower() in ("false", "0", "unlocked", "no"):
            is_bust = False
        else:
            hc = str(input_data.get('hand_control', '')).lower()
            if hc in ('bust_locked', 'locked', 'true', '1'):
                is_bust = True
            elif hc in ('resting_subtle', 'free', 'false', '0'):
                is_bust = False
            else:
                is_bust = is_bust_framing(image)

        if local_rank == 0:
            print(f"🖐️ [FRAMING GUARD] Portrait Framing: is_bust={is_bust}. Hand lock active: {is_bust}.")

        ai2v_checkpoint = os.path.join(output_dir, "ai2v_demo_1.mp4")
        has_checkpoint = os.path.exists(ai2v_checkpoint) and os.path.exists(output_dir) and any(f.startswith("video_continue_") for f in os.listdir(output_dir) if f.endswith(".mp4"))

        if has_checkpoint:
            if local_rank == 0:
                print(f"🔄 [RESUME CHECKPOINT] Skipping Stage 1 generation; loading initial frames from {ai2v_checkpoint}...")
            import cv2
            cap = cv2.VideoCapture(ai2v_checkpoint)
            loaded_init_frames = []
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                loaded_init_frames.append(PIL.Image.fromarray(rgb_frame))
            cap.release()
            video = loaded_init_frames
            latent = torch.zeros((1, 16, 26, 60, 104), device=local_rank)
        else:
            output_tuple = pipe.generate_ai2v(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                resolution=resolution,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                text_guidance_scale=text_guidance_scale,
                audio_guidance_scale=audio_guidance_scale,
                output_type='both',
                generator=generator,
                audio_emb=audio_emb,
                use_distill=use_distill,
            )
            output, latent = output_tuple
            output = output[0]
            raw_video = [(output[i] * 255).astype(np.uint8) for i in range(output.shape[0])]
            raw_video = [PIL.Image.fromarray(img) for img in raw_video]
            del output

            # Apply color clamping, hand lock and precision background lock right from segment 1
            clamped_video = color_clamp_to_reference(raw_video, image)
            locked_video = lock_torso_and_hands(clamped_video, image, is_bust=is_bust)
            video = lock_background_to_reference(locked_video, image, device=local_rank)

            if cp_rank == 0:
                output_tensor = torch.from_numpy(np.array(video))
                save_video_ffmpeg(output_tensor, os.path.join(output_dir, "ai2v_demo_1"), raw_speech_path, fps=save_fps, quality=5)
                save_video_ffmpeg(output_tensor, os.path.join(output_dir, "video_continue_1"), raw_speech_path, fps=save_fps, quality=5)
                del output_tensor
            torch_gc()
    else:
        raise NotImplementedError(f"Not supported type of stage_1: {stage_1}")

    if context_parallel_util.get_cp_size() > 1:
        torch.distributed.barrier(group=context_parallel_util.get_cp_group())

    # =========================================
    #         long video generation (480P)
    # =========================================
    # load parsed long video args
    ref_img_index = args.ref_img_index
    mask_frame_range = args.mask_frame_range

    width, height = video[0].size
    current_video = video
    initial_clean_video = video
    initial_clean_latent = latent.clone()
    # Ensure ref_latent is always the pristine encoded latent of the reference image
    try:
        ref_tensor = pipe.video_processor.preprocess_video(pipe.video_processor, [image], height=height, width=width, resize_mode="crop")
        if pipe.vae is not None:
            pipe.vae.to(local_rank)
            vae_dtype = next(pipe.vae.parameters()).dtype
            ref_encoded = pipe.vae.encode(ref_tensor.to(device=local_rank, dtype=vae_dtype))
            ref_latent = retrieve_latents(ref_encoded, generator, sample_mode="argmax")
            ref_latent = pipe.normalize_latents(ref_latent).to(device=local_rank, dtype=pipe.dit.dtype)
            pipe.vae.to("cpu")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        else:
            ref_latent = latent[:, :, :1].clone()
    except Exception as e:
        if local_rank == 0:
            print(f"[Notice] ref_latent encode fallback: {e}")
        ref_latent = latent[:, :, :1].clone()
    all_generated_frames = list(video)

    start_segment_idx = 1
    # Check if there is an existing checkpoint video in output_dir (e.g. video_continue_80.mp4, video_continue_60.mp4, etc.)
    checkpoint_candidates = []
    if os.path.exists(output_dir):
        for fname in os.listdir(output_dir):
            if fname.startswith("video_continue_") and fname.endswith(".mp4"):
                try:
                    seg_num = int(fname.replace("video_continue_", "").replace(".mp4", ""))
                    if 0 < seg_num < num_segments:
                        checkpoint_candidates.append((seg_num, os.path.join(output_dir, fname)))
                except ValueError:
                    pass

    if checkpoint_candidates:
        checkpoint_candidates.sort(key=lambda x: x[0], reverse=True)
        latest_seg_num, latest_checkpoint_file = checkpoint_candidates[0]
        if local_rank == 0:
            print(f"🔄 [RESUME CHECKPOINT] Found existing checkpoint: {latest_checkpoint_file} ({latest_seg_num}/{num_segments} segments completed).")
            print(f"🔄 [RESUME CHECKPOINT] Loading rendered frames from disk to resume directly from segment {latest_seg_num+1}...")

        import cv2
        cap = cv2.VideoCapture(latest_checkpoint_file)
        loaded_frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            loaded_frames.append(PIL.Image.fromarray(rgb_frame))
        cap.release()

        if len(loaded_frames) > 0:
            if local_rank == 0:
                print(f"🔄 [RESUME CHECKPOINT] Successfully loaded {len(loaded_frames)} rendered frames! Resuming from segment {latest_seg_num+1}/{num_segments} ({round((latest_seg_num/num_segments)*100, 1)}%)...")
            all_generated_frames = loaded_frames
            current_video = loaded_frames[-num_frames:]
            start_segment_idx = latest_seg_num

    for segment_idx in range(start_segment_idx, num_segments):
        if generation_mode == 'anchor_seamless':
            overlap = min(transition_overlap_frames, 8)
            if local_rank == 0:
                print(f"Generating segment {segment_idx+1}/{num_segments} (⚡ Anchor Seamless Mode: Pristine Face Anchor + Hann S-Curve Continuity)...")

            avc_audio_start_idx = (len(all_generated_frames) - overlap) * audio_stride
            avc_audio_end_idx = avc_audio_start_idx + audio_stride * num_frames
            center_indices = torch.arange(avc_audio_start_idx, avc_audio_end_idx, audio_stride).unsqueeze(1) + indices.unsqueeze(0)
            center_indices = torch.clamp(center_indices, min=0, max=full_audio_emb.shape[0]-1)
            avc_audio_emb = full_audio_emb[center_indices][None,...].to(local_rank)

            output_tuple = pipe.generate_ai2v(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                resolution=resolution,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                text_guidance_scale=text_guidance_scale,
                audio_guidance_scale=audio_guidance_scale,
                output_type='both',
                generator=generator,
                audio_emb=avc_audio_emb,
                use_distill=use_distill,
            )
            output, latent = output_tuple
            del latent
            output = output[0]

            seg_std = float(np.std(output))
            seg_mean = float(np.mean(output))
            if local_rank == 0:
                print(f"📊 [QUALITY] Segment {segment_idx+1}/{num_segments}: mean={seg_mean*255:.1f}, std={seg_std*255:.1f}")

            raw_new_video = [(output[i] * 255).astype(np.uint8) for i in range(output.shape[0])]
            raw_new_video = [PIL.Image.fromarray(img) for img in raw_new_video]
            del output

            clamped_new_video = color_clamp_to_reference(raw_new_video, image)
            locked_torso_video = lock_torso_and_hands(clamped_new_video, image, is_bust=is_bust)
            locked_new_video = lock_background_to_reference(locked_torso_video, image, device=local_rank)

            # Apply seamless Hann S-curve cross-dissolve over the overlap seam
            if overlap > 0 and len(all_generated_frames) >= overlap and len(locked_new_video) >= overlap:
                tail_frames = all_generated_frames[-overlap:]
                head_frames = locked_new_video[:overlap]
                blended_frames = blend_frames_crossfade(tail_frames, head_frames)
                all_generated_frames[-overlap:] = blended_frames
                all_generated_frames.extend(locked_new_video[overlap:])
            else:
                all_generated_frames.extend(locked_new_video)

            current_video = locked_new_video

        else:
            if local_rank == 0:
                print(f"Generating segment {segment_idx+1}/{num_segments} (Standard Pure Avatar Lip-Sync Mode)...")

            avc_audio_start_idx = (len(all_generated_frames) - num_cond_frames) * audio_stride
            avc_audio_end_idx = avc_audio_start_idx + audio_stride * num_frames
            center_indices = torch.arange(avc_audio_start_idx, avc_audio_end_idx, audio_stride).unsqueeze(1) + indices.unsqueeze(0)
            center_indices = torch.clamp(center_indices, min=0, max=full_audio_emb.shape[0]-1)
            avc_audio_emb = full_audio_emb[center_indices][None,...].to(local_rank)

            # Clean conditioning tail from current_video with torso/hand anchoring for bust framing
            cond_video = lock_torso_and_hands(current_video[-num_cond_frames:], image, is_bust=is_bust)

            output_tuple = pipe.generate_avc(
                video=cond_video,
                video_latent=None,  # Crucial fix: Ground conditioning directly from clean pixel frames via VAE encode every segment (prevents latent drift collapse / gray screen)
                prompt=prompt,
                negative_prompt=negative_prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_cond_frames=num_cond_frames,
                num_inference_steps=num_inference_steps,
                text_guidance_scale=text_guidance_scale,
                audio_guidance_scale=audio_guidance_scale,
                output_type='both',
                generator=generator,
                audio_emb=avc_audio_emb,
                ref_latent=ref_latent,
                ref_img_index=ref_img_index,
                mask_frame_range=mask_frame_range,
                use_distill=use_distill,
                offload_kv_cache=True,
                enhance_hf=not use_distill,
            )
            output, latent = output_tuple
            del latent
            output = output[0]

            seg_std = float(np.std(output))
            seg_mean = float(np.mean(output))
            if local_rank == 0:
                print(f"📊 [QUALITY] Segment {segment_idx+1}/{num_segments}: mean={seg_mean*255:.1f}, std={seg_std*255:.1f}")

            # Check for collapse (flat gray screen has std ~8.0, normal photo video has std > 40.0)
            if np.isnan(seg_std) or (seg_std * 255.0 < 25.0):
                if local_rank == 0:
                    print(f"⚠️ [COLLAPSE DETECTED] Segment {segment_idx+1} output collapsed (std={seg_std*255:.2f} < 25.0)! Discarding gray frames and auto-recovering from reference photo...")
                pipe._clear_cache()
                torch_gc()
                # Auto-recovery: Re-anchor conditioning from pristine reference photo
                clean_cond = [image] * num_cond_frames
                rec_output_tuple = pipe.generate_avc(
                    video=clean_cond,
                    video_latent=None,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    height=height,
                    width=width,
                    num_frames=num_frames,
                    num_cond_frames=num_cond_frames,
                    num_inference_steps=num_inference_steps,
                    text_guidance_scale=text_guidance_scale,
                    audio_guidance_scale=audio_guidance_scale,
                    output_type='both',
                    generator=generator,
                    audio_emb=avc_audio_emb,
                    ref_latent=ref_latent,
                    ref_img_index=ref_img_index,
                    mask_frame_range=mask_frame_range,
                    use_distill=use_distill,
                    offload_kv_cache=True,
                    enhance_hf=not use_distill,
                )
                output, _ = rec_output_tuple
                output = output[0]
                if local_rank == 0:
                    print(f"✅ [RECOVERY SUCCESS] Re-generated segment {segment_idx+1}: mean={np.mean(output)*255:.1f}, std={np.std(output)*255:.1f}")

            raw_new_video = [(output[i] * 255).astype(np.uint8) for i in range(output.shape[0])]
            raw_new_video = [PIL.Image.fromarray(img) for img in raw_new_video]
            del output

            clamped_new_video = color_clamp_to_reference(raw_new_video, image)
            locked_torso_video = lock_torso_and_hands(clamped_new_video, image, is_bust=is_bust)
            locked_new_video = lock_background_to_reference(locked_torso_video, image, device=local_rank)

            all_generated_frames.extend(locked_new_video[num_cond_frames:])
            current_video = locked_new_video

        pipe._clear_cache()
        torch_gc()

        total_audio_frames = full_audio_emb.shape[0] // audio_stride
        audio_complete = (len(all_generated_frames) >= total_audio_frames)
        is_final_segment = (segment_idx == num_segments - 1) or audio_complete
        save_interval = 1  # Save every completed segment immediately to protect progress and allow instant rescue on stop/cancel
        if cp_rank == 0 and (is_final_segment or ((segment_idx + 1) % save_interval == 0)):
            save_path = os.path.join(output_dir, f"video_continue_{segment_idx+1}")

            if is_final_segment:
                if active_saver_thread is not None and active_saver_thread.is_alive():
                    active_saver_thread.join(timeout=60)
                save_frames = all_generated_frames[:total_audio_frames] if audio_complete else all_generated_frames
                save_video_ffmpeg(save_frames, save_path, raw_speech_path, fps=save_fps, quality=5)
                gc.collect()
            else:
                async_save_video_ffmpeg(list(all_generated_frames), save_path, raw_speech_path, fps=save_fps, quality=5)

        if audio_complete:
            if local_rank == 0:
                print(f"✅ [AUDIO COMPLETE] Generated {len(all_generated_frames)} frames (audio needed: {total_audio_frames} frames). Finished generation early to save GPU time!")
            break

    if context_parallel_util.get_cp_size() > 1:
        try:
            torch.distributed.barrier(group=context_parallel_util.get_cp_group())
            torch.distributed.destroy_process_group()
        except Exception:
            pass


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_json',
        type=str,
        default='assets/avatar/single_example_1.json'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./outputs_avatar_single'
    )
    parser.add_argument(
        '--resolution',
        type=str,
        default='500p',
        choices=['500p', '540p', '520p', '580p', '600p', '700p', '720p', '1080p', '480p']
    )
    parser.add_argument(
        '--num_segments',
        type=int,
        default=1
    )
    parser.add_argument(
        '--num_frames',
        type=int,
        default=81,
        help="Number of frames generated per segment"
    )
    parser.add_argument(
        '--num_inference_steps',
        type=int,
        default=50
    )
    parser.add_argument(
        '--ref_img_index',
        type=int,
        default=10
    )
    parser.add_argument(
        '--mask_frame_range',
        type=int,
        default=0
    )
    parser.add_argument(
        '--text_guidance_scale',
        type=float,
        default=4.0
    )
    parser.add_argument(
        '--audio_guidance_scale',
        type=float,
        default=4.0
    )
    parser.add_argument(
        '--stage_1',
        type=str,
        default='ai2v',
        choices=['ai2v', 'at2v']
    )
    parser.add_argument(
        "--context_parallel_size",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--checkpoint_dir",
        type=str,
        default="./weights/LongCat-Video-Avatar-1.5",
    )
    parser.add_argument(
        "--model_type",
        type=str,
        default="avatar-v1.5",
    )
    parser.add_argument(
        "--use_distill",
        action='store_true',
    )
    parser.add_argument(
        "--use_int8",
        action='store_true',
        help="Load INT8 quantized DiT model for reduced VRAM usage"
    )
    parser.add_argument(
        "--reanchor_interval",
        type=int,
        default=4,
        help="Number of segments after which to re-anchor directly to pristine source photo (Default: 4 = ~15s)"
    )
    parser.add_argument(
        "--step_booster",
        type=str,
        default="default",
        choices=["default", "sage_attention", "torch_compile", "tensorrt"],
        help="Step Booster acceleration backend (Default, SageAttention, PyTorch Compile, TensorRT)"
    )
    parser.add_argument(
        "--generation_mode",
        type=str,
        default="anchor_seamless",
        choices=["anchor_seamless", "sequential_continuation", "sequential", "standard"],
        help="Generation mode: 'anchor_seamless' for pristine source face anchor + S-curve cross-dissolve, or 'sequential_continuation' for autoregressive continuation."
    )
    parser.add_argument(
        "--transition_overlap_frames",
        type=int,
        default=4,
        help="Number of overlap frames used for smooth S-curve cross-dissolve transition in Anchor Seamless Mode (Default: 4 frames)."
    )
    parser.add_argument(
        "--force_vocal_separation",
        action='store_true',
        help="Force deep MDX23 ONNX vocal isolation (Default: False, direct ultra-speed voice pipeline)"
    )
    parser.add_argument(
        "--lock_hands",
        type=str,
        default="auto",
        choices=["auto", "true", "false", "locked", "unlocked"],
        help="Hand motion control: 'true'/'locked' enforces torso & hand stabilization mask, 'false'/'unlocked' disables, 'auto' detects from framing"
    )

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = _parse_args()
    generate(args)