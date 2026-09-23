import os, sys, json, torch
sys.path.insert(0, '/workspace/LongCat-Video')

from transformers import AutoTokenizer, UMT5EncoderModel
from diffusers.schedulers import FlowMatchEulerDiscreteScheduler
from longcat_video.modules.autoencoder_kl_wan import AutoencoderKLWan
from longcat_video.modules.avatar.longcat_video_dit_avatar import LongCatVideoAvatarTransformer3DModel
from longcat_video.modules.quantization import load_quantized_dit
from longcat_video.pipeline_longcat_video_avatar import LongCatVideoAvatarPipeline

def mem(tag):
    allocated = torch.cuda.memory_allocated(0) / (1024**3)
    reserved = torch.cuda.memory_reserved(0) / (1024**3)
    max_alloc = torch.cuda.max_memory_allocated(0) / (1024**3)
    print(f"[{tag}] Allocated: {allocated:.2f} GB | Reserved: {reserved:.2f} GB | Peak: {max_alloc:.2f} GB")

checkpoint_dir = '/workspace/LongCat-Video/weights/LongCat-Video-Avatar-1.5'
base_longcat_dir = os.path.normpath(os.path.join(checkpoint_dir, '..', 'LongCat-Video'))

mem("Start")
tokenizer = AutoTokenizer.from_pretrained(base_longcat_dir, subfolder="tokenizer", torch_dtype=torch.bfloat16)
text_encoder = UMT5EncoderModel.from_pretrained(base_longcat_dir, subfolder="text_encoder", torch_dtype=torch.bfloat16)
vae = AutoencoderKLWan.from_pretrained(base_longcat_dir, subfolder="vae", torch_dtype=torch.bfloat16)
vae.disable_tiling()
vae.enable_slicing()
scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(checkpoint_dir, subfolder="scheduler", torch_dtype=torch.bfloat16)

mem("Pre-DiT")
dit = load_quantized_dit(checkpoint_dir, subfolder="base_model_int8", cp_split_hw=[1, 1])
distill_checkpoint_path = os.path.join(checkpoint_dir, 'lora', 'dmd_lora.safetensors')
dit.load_lora(distill_checkpoint_path, "dmd", multiplier=1.0, lora_network_dim=128, lora_network_alpha=64)
dit.enable_loras(["dmd"])

from run_demo_avatar_single_audio_to_video import get_audio_encoder, get_audio_feature_extractor
audio_model_checkpoint_path = os.path.join(checkpoint_dir, 'whisper-large-v3')
audio_encoder = get_audio_encoder(audio_model_checkpoint_path, "avatar-v1.5")
audio_feature_extractor = get_audio_feature_extractor(audio_model_checkpoint_path, "avatar-v1.5")

pipe = LongCatVideoAvatarPipeline(
    tokenizer=tokenizer,
    text_encoder=text_encoder,
    vae=vae,
    scheduler=scheduler,
    dit=dit,
    audio_encoder=audio_encoder,
    audio_feature_extractor=audio_feature_extractor,
    model_type="avatar-v1.5"
)
mem("Pre pipe.to(0)")
pipe.to(0)
mem("Post pipe.to(0)")

prompt = "Elderly man talking naturally with authentic expressive mouth movement"
mem("Pre encode_prompt")
prompt_embeds, prompt_attention_mask, neg_embeds, neg_mask = pipe.encode_prompt(
    prompt=prompt,
    do_classifier_free_guidance=False,
    device=torch.device("cuda:0"),
    dtype=pipe.dit.dtype
)
mem("Post encode_prompt")

import librosa
audio_path = "/workspace/LongCat-Video/uploads/274fd642/Audio_1_I_m_89_years.wav"
speech_array, sr = librosa.load(audio_path, sr=16000)
mem("Pre audio_embedding")
full_audio_emb = pipe.get_audio_embedding_whisper(speech_array, fps=25, device=torch.device("cuda:0"))
indices = torch.arange(2 * 2 + 1) - 2
center_indices = torch.arange(0, 205, 1).unsqueeze(1) + indices.unsqueeze(0)
center_indices = torch.clamp(center_indices, min=0, max=full_audio_emb.shape[0]-1)
audio_emb = full_audio_emb[center_indices][None, ...].to(0)
mem("Post audio_embedding")

from PIL import Image
image = Image.open("/workspace/LongCat-Video/uploads/274fd642/Elderly_man_sitting_in_kitchen_202608201814.jpeg").convert("RGB")
mem("Pre prepare_latents")
image_tensor = pipe.video_processor.preprocess(image, height=600, width=1040, resize_mode="crop")
image_tensor = image_tensor.to(device=torch.device("cuda:0"), dtype=prompt_embeds.dtype)
latents = pipe.prepare_latents(
    image=image_tensor,
    batch_size=1,
    num_channels_latents=pipe.dit.config.in_channels,
    height=600,
    width=1040,
    num_frames=205,
    num_cond_frames=1,
    dtype=torch.float32,
    device=torch.device("cuda:0"),
)
mem("Post prepare_latents")

mem("Pre dit forward")
dit_dtype = pipe.dit.dtype
latent_model_input = latents.to(dit_dtype)
timestep = torch.tensor([1000.0], device="cuda:0", dtype=dit_dtype).unsqueeze(-1).repeat(1, latent_model_input.shape[2])
timestep[:, :1] = 0

mem("Pre dit call")
try:
    with torch.no_grad():
        out = pipe.dit(
            hidden_states=latent_model_input,
            timestep=timestep,
            encoder_hidden_states=prompt_embeds,
            encoder_attention_mask=prompt_attention_mask,
            num_cond_latents=1,
            audio_embs=audio_emb,
            ref_target_masks=None
        )
    mem("Post dit call SUCCESS!")
except Exception as e:
    import traceback
    traceback.print_exc()
    mem("During/After dit call ERROR")


