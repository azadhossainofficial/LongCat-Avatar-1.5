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

precision = os.environ.get('PRECISION', 'all').strip().lower()
if len(sys.argv) > 1 and sys.argv[1].startswith('--precision='):
    precision = sys.argv[1].split('=', 1)[1].strip().lower()
elif len(sys.argv) > 2 and sys.argv[1] == '--precision':
    precision = sys.argv[2].strip().lower()

# 1. Download Avatar 1.5 required components
print('\n[1/2] Downloading LongCat-Video-Avatar-1.5 specific components...')
avatar_allow_patterns = [
    'lora/*',
    'dmd_lora.safetensors',
    'whisper-large-v3/*',
    'vocal_separator/*',
    'scheduler/*',
    'config.json',
    'model_index.json'
]

if precision == 'bf16':
    print('🎯 Precision Mode: Pure BF16 Studio Master (Skipping INT8 to save 15.2 GB disk space)...')
    avatar_allow_patterns.append('base_model/*')
elif precision == 'int8':
    print('🎯 Precision Mode: Fast INT8 (Skipping BF16 to save 30.4 GB disk space)...')
    avatar_allow_patterns.append('base_model_int8/*')
else:
    print('🎯 Precision Mode: ALL (Downloading both BF16 and INT8 models)...')
    avatar_allow_patterns.extend(['base_model/*', 'base_model_int8/*'])
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
