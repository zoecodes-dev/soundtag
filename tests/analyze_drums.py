import librosa
import numpy as np

# 드럼 stem 로드
y, sr = librosa.load("drums.mp3", sr=22050)
duration = librosa.get_duration(y=y, sr=sr)

# BPM 추출
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
print(f"BPM: {tempo[0]:.1f}")
print(f"곡 길이: {duration:.1f}초")
print(f"비트 수: {len(beats)}")

# 드럼 onset 감지 (드럼이 치는 순간들)
onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
onset_times = librosa.frames_to_time(onset_frames, sr=sr)
print(f"드럼 히트 수: {len(onset_times)}")
print(f"초당 평균 히트: {len(onset_times)/duration:.1f}")

# 에너지 레벨 (RMS)
rms = librosa.feature.rms(y=y)[0]
print(f"평균 에너지: {np.mean(rms):.4f}")
print(f"최대 에너지: {np.max(rms):.4f}")