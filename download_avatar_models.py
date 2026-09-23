import os
import sys
from huggingface_hub import snapshot_download

script_dir = os.path.dirname(os.path.abspath(__file__))
base_weights_dir = os.environ.get('WEIGHTS_DIR', os.path.join(script_dir, 'weights'))
avatar_weights_dir = os.path.join(base_weights_dir, 'LongCat-Video-Avatar-1.5')
foundation_weights_dir = os.path.join(base_weights_dir, 'LongCat-Video')

os.makedirs(avatar_weights_dir, exist_ok=True)
os.makedirs(foundation_weights_dir, exist_ok=True)

print('=' * 60)
print('🚀 Downloading ONLY Avatar 1.5 required components...')
print('=' * 60)

# 1. Download Avatar 1.5 required components
print('\n[1/2] Downloading LongCat-Video-Avatar-1.5 specific components (base_model_int8, lora, whisper, vocal_separator, scheduler)...')
avatar_allow_patterns = [
    'base_model/*',
    'base_model_int8/*',
    'lora/*',
    'dmd_lora.safetensors',
    'whisper-large-v3/*',
    'vocal_separator/*',
    'scheduler/*',
    'config.json',
    'model_index.json'
]
avatar_ignore_patterns = [
    '*.mp4',
    '*.png',
    '*.jpg',
    'assets/*',
    'whisper-large-v3/flax_model.msgpack',
    'whisper-large-v3/pytorch_model*.bin*',
    'whisper-large-v3/model.fp32*'
]

snapshot_download(
    repo_id='meituan-longcat/LongCat-Video-Avatar-1.5',
    local_dir=avatar_weights_dir,
    allow_patterns=avatar_allow_patterns,
    ignore_patterns=avatar_ignore_patterns,
    max_workers=8
)
print('✅ LongCat-Video-Avatar-1.5 components downloaded successfully.')

# 2. Download Foundation Base Model (Tokenizer, Text Encoder, VAE)
print('\n[2/2] Downloading LongCat-Video Base components (Tokenizer, Text Encoder, VAE)...')
foundation_allow_patterns = [
    'tokenizer/*',
    'text_encoder/*',
    'vae/*'
]

snapshot_download(
    repo_id='meituan-longcat/LongCat-Video',
    local_dir=foundation_weights_dir,
    allow_patterns=foundation_allow_patterns,
    max_workers=8
)
print('✅ LongCat-Video Base components downloaded successfully.')

print('\n🎉 ALL REQUIRED AVATAR 1.5 MODELS DOWNLOADED!')
