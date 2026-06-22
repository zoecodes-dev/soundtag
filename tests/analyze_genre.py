import essentia.standard as es
from essentia.standard import MonoLoader, TensorflowPredictEffnetDiscogs, TensorflowPredict2D
import numpy as np
import json

# 원본 곡 로드 (stem 아니라 원곡으로)
audio = MonoLoader(filename="test_song.webm", sampleRate=16000)()

# --- 기본 feature 추출 ---
rhythm = es.RhythmExtractor2013(method="multifeature")
bpm, beats, beats_confidence, _, _ = rhythm(audio)

key_extractor = es.KeyExtractor()
key, scale, key_strength = key_extractor(audio)

energy = es.Energy()
loudness = es.Loudness()

print("=== 기본 분석 ===")
print(f"BPM: {bpm:.1f}")
print(f"Key: {key} {scale} (confidence: {key_strength:.2f})")
print(f"Energy: {energy(audio):.2f}")
print(f"Loudness: {loudness(audio):.2f}")

# --- 댄서빌리티 ---
dance = es.Danceability()
danceability, _ = dance(audio)
print(f"Danceability: {danceability:.3f}")