"""
SoundTag - ReccoBeats API 테스트
================================
무료 API, 인증 불필요.
- 유사곡 추천
- Audio features (danceability, energy, tempo 등)
- 트랙 검색/상세

Base URL: https://api.reccobeats.com

사용법:
    python reccobeats_test.py
"""

import requests
import json
import time

BASE_URL = "https://api.reccobeats.com"
DELAY = 0.3  # rate limit 여유


def api_get(endpoint: str, params: dict = None) -> dict | None:
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        time.sleep(DELAY)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  ⚠️ HTTP {resp.status_code}: {url}")
            print(f"     {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def pretty(data):
    """JSON 보기 좋게 출력."""
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1500])


# ─── 테스트 1: 트랙 검색 (Spotify ID 기반) ─────────────
# ReccoBeats는 Spotify track ID를 사용
# aespa "Supernova" Spotify ID 예시
TEST_TRACKS = {
    "aespa - Supernova": "3MBrzM2hXA8VsLDmgyeIcP",
    "NewJeans - Ditto": "3r8RuvgbX9s7ammBn07D3W",
    "BTS - Dynamite": "0t1kP63rueHleOhQkYSXFY",
    "BLACKPINK - How You Like That": "4SpyEzmAvpq5hEMOCfxhkA",
    "IU - Blueming": "0LtOHfMQPDWBC6YhWEtPwi",
}


def test_track_detail(track_id: str, name: str):
    """트랙 상세 정보 조회."""
    print(f"\n{'='*50}")
    print(f"📋 Track Detail: {name}")
    print(f"   Spotify ID: {track_id}")
    data = api_get(f"/v1/track/{track_id}")
    if data:
        pretty(data)
    return data


def test_audio_features(track_id: str, name: str):
    """트랙 audio features 조회."""
    print(f"\n{'='*50}")
    print(f"🎵 Audio Features: {name}")
    data = api_get(f"/v1/track/{track_id}/audio-features")
    if data:
        # 핵심 features만 출력
        keys = ["danceability", "energy", "tempo", "valence",
                "acousticness", "instrumentalness", "speechiness",
                "liveness", "loudness", "key", "mode", "time_signature"]
        print("   Key features:")
        for k in keys:
            if k in data:
                print(f"     {k}: {data[k]}")
    return data


def test_recommendations(track_id: str, name: str, limit: int = 5):
    """유사곡 추천."""
    print(f"\n{'='*50}")
    print(f"🔍 Recommendations for: {name}")
    data = api_get("/v1/track/recommendation", {"track_id": track_id, "limit": limit})
    if data:
        tracks = data if isinstance(data, list) else data.get("tracks", data.get("data", []))
        if isinstance(tracks, list):
            for i, t in enumerate(tracks[:limit], 1):
                title = t.get("name", t.get("title", "?"))
                artist = t.get("artist", t.get("artists", "?"))
                if isinstance(artist, list):
                    artist = ", ".join(a.get("name", "?") for a in artist)
                elif isinstance(artist, dict):
                    artist = artist.get("name", "?")
                print(f"   {i}. {title} — {artist}")
        else:
            pretty(data)
    return data


def test_audio_feature_extraction():
    """오디오 파일 업로드 분석 (있으면 테스트)."""
    print(f"\n{'='*50}")
    print(f"🔬 Audio Feature Extraction (file upload)")
    print(f"   Endpoint: POST /v1/analysis/audio-features")
    print(f"   → 다운로드된 프리뷰 MP3가 있으면 테스트 가능")
    print(f"   → 예: curl -X POST {BASE_URL}/v1/analysis/audio-features -F 'file=@preview.mp3'")


def main():
    print("🎧 ReccoBeats API 테스트 시작")
    print(f"   Base URL: {BASE_URL}")
    print(f"   인증: 불필요")

    # ── 테스트 실행 ──
    all_results = {}

    for name, track_id in TEST_TRACKS.items():
        # 1. 트랙 상세
        detail = test_track_detail(track_id, name)

        # 2. Audio features
        features = test_audio_features(track_id, name)

        # 3. 유사곡 추천
        recs = test_recommendations(track_id, name)

        all_results[name] = {
            "track_id": track_id,
            "detail": detail,
            "features": features,
            "recommendations": recs,
        }

    # ── 파일 업로드 분석 안내 ──
    test_audio_feature_extraction()

    # ── 결과 저장 ──
    with open("reccobeats_test_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 결과 저장: reccobeats_test_results.json")

    # ── 요약 ──
    print(f"\n{'='*50}")
    print(f"📊 테스트 요약")
    for name, r in all_results.items():
        has_detail = "✅" if r["detail"] else "❌"
        has_features = "✅" if r["features"] else "❌"
        has_recs = "✅" if r["recommendations"] else "❌"
        print(f"   {name}: detail={has_detail} features={has_features} recs={has_recs}")


if __name__ == "__main__":
    main()
