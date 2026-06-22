import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

# 드럼 stem 로드
y, sr = librosa.load("drums.mp3", sr=22050)

# 에너지(RMS) 계산
rms = librosa.feature.rms(y=y)[0]
times = librosa.times_like(rms, sr=sr)

# onset 감지
onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
onset_times = librosa.frames_to_time(onset_frames, sr=sr)

# 그래프 그리기
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# 1. 파형 + 에너지
axes[0].set_title("Drum Energy Over Time")
axes[0].plot(times, rms, color="orange", linewidth=1.5, label="RMS Energy")
axes[0].set_xlabel("Time (sec)")
axes[0].set_ylabel("Energy")
axes[0].legend()

# 2. onset 히트맵 — 드럼이 치는 순간들
axes[1].set_title("Drum Hits")
axes[1].vlines(onset_times, 0, 1, color="red", alpha=0.5, linewidth=0.5)
axes[1].set_xlabel("Time (sec)")
axes[1].set_ylabel("Hit")

plt.tight_layout()
plt.savefig("drum_analysis.png", dpi=150)
print("drum_analysis.png 저장 완료!")