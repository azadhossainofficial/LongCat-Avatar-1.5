import re

file_path = '/workspace/LongCat-Video/run_demo_avatar_single_audio_to_video.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Monkey patch librosa get_duration
if '_orig_get_duration' not in code:
    patch = '''import librosa
_orig_get_duration = librosa.get_duration
def _compat_get_duration(*args, **kwargs):
    if "filename" in kwargs and "path" not in kwargs:
        kwargs["path"] = kwargs.pop("filename")
    return _orig_get_duration(*args, **kwargs)
librosa.get_duration = _compat_get_duration
'''
    code = code.replace('import librosa', patch, 1)

# 2. Robust extract_vocal_from_speech
extract_func = '''def extract_vocal_from_speech(source_path, target_path, vocal_separator, audio_output_dir_temp):
    try:
        outputs = vocal_separator.separate(source_path)
        if len(outputs) <= 0:
            print("Audio separate returned empty. Using raw audio.")
            return str(source_path)
        
        vocal_filename = None
        for fn in outputs:
            if "Vocals" in fn:
                vocal_filename = fn
                break
        if not vocal_filename:
            vocal_filename = outputs[-1]

        candidates = [
            audio_output_dir_temp / "vocals" / vocal_filename,
            audio_output_dir_temp / vocal_filename,
            Path("audio_temp_file/vocals") / vocal_filename,
            Path("/tmp/audio_temp_file/vocals") / vocal_filename,
            Path(vocal_filename)
        ]

        for cand in candidates:
            if cand.exists():
                import shutil
                shutil.copy2(str(cand), str(target_path))
                print(f"Extracted vocal copied to: {target_path}")
                return str(target_path)
    except Exception as e:
        print(f"Vocal separation notice: {e}. Using raw audio.")
    
    return str(source_path)
'''
code = re.sub(r'def extract_vocal_from_speech\(.*?\):\n.*?(?=\ndef generate)', extract_func, code, flags=re.DOTALL)

# 3. Fallback for assert temp_vocal_path
code = re.sub(
    r'assert temp_vocal_path is not None and os\.path\.exists\(temp_vocal_path\), f"No vocal detected"',
    'if temp_vocal_path is None or not os.path.exists(temp_vocal_path):\n            print(f"Warning: Vocal stem not found. Using raw speech: {raw_speech_path}")\n            temp_vocal_path = raw_speech_path',
    code
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Successfully patched /workspace/LongCat-Video/run_demo_avatar_single_audio_to_video.py!")
