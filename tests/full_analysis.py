import librosa
import essentia.standard as es
import numpy as np
import json

print("=" * 50)
print("  SoundTag Analysis Report")
print("=" * 50)

# === 1. Essentia 기본 분석 (원곡) ===
audio_es = es.MonoLoader(filename="test_song.webm", sampleRate=16000)()

rhythm = es.RhythmExtractor2013(method="multifeature")
bpm, beats, beats_conf, _, _ = rhythm(audio_es)

key_ext = es.KeyExtractor()
key, scale, key_str = key_ext(audio_es)

dance = es.Danceability()
danceability, _ = dance(audio_es)

print(f"\n🎵 BPM: {bpm:.1f}")
print(f"🎹 Key: {key} {scale} (confidence: {key_str:.0%})")
print(f"💃 Danceability: {danceability:.3f}")

# === 2. Stem Prominence ===
stems = ["vocals", "drums", "bass", "other"]
stem_data = {}

for stem in stems:
    y, sr = librosa.load(f"{stem}.mp3", sr=22050)
    rms = librosa.feature.rms(y=y)[0]
    stem_data[stem] = {
        "avg_energy": float(np.mean(rms)),
        "max_energy": float(np.max(rms)),
    }

total = sum(d["avg_energy"] for d in stem_data.values())
for stem in stems:
    stem_data[stem]["prominence"] = stem_data[stem]["avg_energy"] / total * 100

print(f"\n📊 Stem Prominence:")
for stem in sorted(stems, key=lambda s: stem_data[s]["prominence"], reverse=True):
    p = stem_data[stem]["prominence"]
    bar = "█" * int(p / 2)
    print(f"  {stem:8s} {p:5.1f}% {bar}")

# === 3. 드럼 패턴 분석 ===
y_drums, sr = librosa.load("drums.mp3", sr=22050)
tempo, _ = librosa.beat.beat_track(y=y_drums, sr=sr)
onset_frames = librosa.onset.onset_detect(y=y_drums, sr=sr)
onset_times = librosa.frames_to_time(onset_frames, sr=sr)
duration = librosa.get_duration(y=y_drums, sr=sr)
hits_per_sec = len(onset_times) / duration

print(f"\n🥁 Drum Analysis:")
print(f"  Drum BPM: {tempo[0]:.1f}")
print(f"  Hits: {len(onset_times)} ({hits_per_sec:.1f}/sec)")

# 드럼 패턴 추정
if hits_per_sec > 4:
    pattern = "Dense/Complex (K-pop dance)"
elif hits_per_sec > 2.5:
    pattern = "Moderate (Pop/R&B)"
else:
    pattern = "Sparse (Ballad/Minimal)"
print(f"  Pattern: {pattern}")

# === 4. JSON 저장 ===
report = {
    "bpm": round(bpm, 1),
    "drum_bpm": round(float(tempo[0]), 1),
    "key": f"{key} {scale}",
    "key_confidence": round(key_str, 2),
    "danceability": round(danceability, 3),
    "drum_pattern": pattern,
    "drum_hits_per_sec": round(hits_per_sec, 1),
    "stems": {s: {"prominence": round(stem_data[s]["prominence"], 1)} for s in stems}
}

with open("analysis_report.json", "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n✅ analysis_report.json 저장 완료!")