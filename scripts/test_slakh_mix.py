import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
import sys
sys.path.append("scripts")
from kpop_mixer import create_kpop_mix, ensure_mono, normalize

track_dir = Path("data/slakh/babyslakh_16k/Track00012")

stem_map = {
    "kick":       "S00",  # Drums
    "guitar":     "S01",  # Funk Guitar
    "piano":      "S03",  # Piano
    "lead_synth": "S04",  # Electric Piano (신스 대용)
    "bass":       "S05",  # Pop Bass
    "strings":    "S06",  # String Ensemble
    "pad":        "S07",  # Choir (패드 대용)
}

stems = {}
for name, stem_id in stem_map.items():
    filepath = track_dir / "stems" / f"{stem_id}.wav"
    if filepath.exists():
        audio, sr = librosa.load(str(filepath), sr=44100)
        stems[name] = audio
        print(f"  {name}: {stem_id} ({len(audio)/sr:.1f}초)")

print(f"\n총 {len(stems)}개 stem 로드")

# 원본 믹스 (비교용)
raw_mix = sum(stems.values())
raw_mix = normalize(raw_mix)
sf.write("test_output/raw_mix_t12.wav", raw_mix, 44100)
print("원본 믹스 저장: raw_mix_t12.wav")

# kpop_mixer 적용
for v in range(3):
    print(f"\n변형 {v+1}/3 생성 중...")
    mix, _ = create_kpop_mix(stems, 44100)
    mix_mono = ensure_mono(mix)
    sf.write(f"test_output/kpop_t12_v{v}.wav", mix_mono, 44100)
    print(f"  저장: kpop_t12_v{v}.wav")

print("\n비교해서 들어봐:")
print("  raw_mix_t12.wav  — 클린 (이펙트 제로)")
print("  kpop_t12_v0.wav  — kpop_mixer 적용")
print("  kpop_t12_v1.wav  — 다른 랜덤 세팅")
print("  kpop_t12_v2.wav  — 또 다른 세팅")