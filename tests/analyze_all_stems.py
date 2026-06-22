import librosa
import numpy as np

stems = ["vocals", "drums", "bass", "other"]
results = {}

for stem in stems:
    y, sr = librosa.load(f"{stem}.mp3", sr=22050)
    rms = librosa.feature.rms(y=y)[0]
    
    results[stem] = {
        "avg_energy": float(np.mean(rms)),
        "max_energy": float(np.max(rms)),
        "prominence": 0  # 아래에서 계산
    }

# prominence 계산 — 전체 대비 각 stem의 비중 (%)
total = sum(r["avg_energy"] for r in results.values())
for stem in stems:
    results[stem]["prominence"] = results[stem]["avg_energy"] / total * 100

print("\n=== Stem Prominence ===")
for stem in sorted(results, key=lambda s: results[s]["prominence"], reverse=True):
    r = results[stem]
    bar = "█" * int(r["prominence"] / 2)  # 시각적 바
    print(f"{stem:8s} {r['prominence']:5.1f}% {bar}")
    print(f"         avg: {r['avg_energy']:.4f}  max: {r['max_energy']:.4f}")

# BPM도 같이
y_full, sr = librosa.load("drums.mp3", sr=22050)
tempo, _ = librosa.beat.beat_track(y=y_full, sr=sr)
print(f"\nBPM: {tempo[0]:.1f}")