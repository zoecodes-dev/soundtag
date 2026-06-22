import replicate
import requests
import librosa
import essentia.standard as es
import numpy as np
import json
import sys
import os
from dotenv import load_dotenv

# === 설정 ===
load_dotenv()
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

def download_file(url, filename):
    """URL에서 파일 다운로드"""
    r = requests.get(url)         # URL에 HTTP 요청 보내기
    with open(filename, "wb") as f:  # wb = write binary (바이너리 쓰기)
        f.write(r.content)
    print(f"  저장: {filename}")

def separate(audio_path):
    """Demucs로 음원 분리 → stem 파일 저장"""
    print("\n🔀 음원 분리 중... (1-2분 소요)")
    
    client = replicate.Client(
        api_token=os.environ["REPLICATE_API_TOKEN"],
        timeout=300  # 5분 타임아웃
    )
    
    prediction = client.predictions.create(
        version="25a173108cff36ef9f80f854c162d01df9e6528be175794b81158fa03836d953",
        input={
            "audio": open(audio_path, "rb"),
            "model_name": "htdemucs",
            "output_format": "mp3",
            "mp3_bitrate": 320,
        }
    )
    prediction.wait()
    
    if prediction.status != "succeeded":
        print(f"❌ 분리 실패: {prediction.status}")
        return None
    
    # stem 파일 다운로드
    stems = {}
    for stem_name in ["vocals", "drums", "bass", "other"]:
        url = prediction.output.get(stem_name)
        if url:
            filename = f"stems_{stem_name}.mp3"
            download_file(url, filename)
            stems[stem_name] = filename
    
    return stems

def analyze(audio_path, stems):
    """전체 분석 실행"""
    print("\n🔍 분석 중...")
    
    # --- Essentia 기본 분석 ---
    audio_es = es.MonoLoader(filename=audio_path, sampleRate=16000)()
    
    key_ext = es.KeyExtractor()
    key, scale, key_str = key_ext(audio_es)
    
    dance = es.Danceability()
    danceability, _ = dance(audio_es)
    
    # --- 드럼 BPM (더 정확) ---
    y_drums, sr = librosa.load(stems["drums"], sr=22050)
    tempo, _ = librosa.beat.beat_track(y=y_drums, sr=sr)
    drum_bpm = float(tempo[0])
    
    # --- 드럼 onset ---
    onset_frames = librosa.onset.onset_detect(y=y_drums, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    duration = librosa.get_duration(y=y_drums, sr=sr)
    hits_per_sec = len(onset_times) / duration
    
    # --- 드럼 패턴 추정 ---
    if hits_per_sec > 4:
        pattern = "Dense/Complex"
    elif hits_per_sec > 2.5:
        pattern = "Moderate"
    else:
        pattern = "Sparse/Minimal"
    
    # --- Stem Prominence ---
    stem_data = {}
    for name, path in stems.items():
        y, sr = librosa.load(path, sr=22050)
        rms = librosa.feature.rms(y=y)[0]
        stem_data[name] = float(np.mean(rms))
    
    total = sum(stem_data.values())
    prominence = {s: round(v / total * 100, 1) for s, v in stem_data.items()}
    
    # --- 리포트 생성 ---
    report = {
        "bpm": round(drum_bpm, 1),
        "key": f"{key} {scale}",
        "key_confidence": round(key_str, 2),
        "danceability": round(danceability, 3),
        "duration": round(duration, 1),
        "drum_pattern": pattern,
        "drum_hits_per_sec": round(hits_per_sec, 1),
        "stems": prominence
    }
    
    return report

def print_report(report):
    """리포트 출력"""
    print("\n" + "=" * 50)
    print("  🏷️  SoundTag Analysis Report")
    print("=" * 50)
    print(f"  BPM: {report['bpm']}")
    print(f"  Key: {report['key']} ({report['key_confidence']:.0%})")
    print(f"  Danceability: {report['danceability']}")
    print(f"  Duration: {report['duration']}s")
    print(f"\n  🥁 Drum: {report['drum_pattern']} ({report['drum_hits_per_sec']}/sec)")
    print(f"\n  📊 Stem Prominence:")
    for stem in sorted(report["stems"], key=report["stems"].get, reverse=True):
        p = report["stems"][stem]
        bar = "█" * int(p / 2)
        print(f"    {stem:8s} {p:5.1f}% {bar}")

# === 실행 ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python soundtag.py <음원파일>")
        print("예시:  python soundtag.py test_song.webm")
        sys.exit(1)
    
    audio_path = sys.argv[1]  # 터미널에서 넘긴 파일명
    print(f"🎵 분석 시작: {audio_path}")
    
    # 1. 음원 분리
    stems = separate(audio_path)
    if not stems:
        sys.exit(1)
    
    # 2. 분석
    report = analyze(audio_path, stems)
    
    # 3. 출력
    print_report(report)
    
    # 4. JSON 저장
    json_path = audio_path.rsplit(".", 1)[0] + "_report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ {json_path} 저장 완료!")