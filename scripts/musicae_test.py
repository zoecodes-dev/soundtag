"""
SoundTag - Musicae API 테스트
==============================
Spotify Extended Audio Features API (via RapidAPI)
Audio features, recommendations, related artists 테스트.

사용법:
    python musicae_test.py
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# .env에서 API 키 로드
load_dotenv()
API_KEY = os.getenv("RAPIDAPI_KEY")
if not API_KEY:
    print("❌ RAPIDAPI_KEY not found in .env")
    exit(1)

BASE_URL = "https://spotify-extended-audio-features-api.p.rapidapi.com/v1"
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "spotify-extended-audio-features-api.p.rapidapi.com",
}

# K-pop 테스트 곡들 (Spotify track ID)
TEST_TRACKS = {
    "BTS - Dynamite": "0t1kP63rueHleOhQkYSXFY",
    "BLACKPINK - DDU-DU DDU-DU": "4lJNJMHeAJCfbJgKMxjHMn",
    "aespa - Supernova": "3MBrzM2hXA8VsLDmgyeIcP",
    "IU - Blueming": "0LtOHfMQPDWBC6YhWEtPwi",
    "NewJeans - Hype Boy": "0a4MMyCrzT0En247IhqZbD",
    "Stray Kids - MANIAC": "4fMSCViMPb89ppCm2YPa5m",
    "Red Velvet - Psycho": "5A9EvZZ9dKDsEkYlxCYDrP",
}


def api_get(endpoint: str) -> dict | None:
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  ⚠️ HTTP {resp.status_code}: {endpoint}")
            print(f"     {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def test_audio_features(track_id: str, name: str):
    """Audio features 조회."""
    print(f"\n🎵 Audio Features: {name}")
    data = api_get(f"/audio-features/{track_id}")
    if data:
        keys = ["danceability", "energy", "tempo", "valence",
                "acousticness", "instrumentalness", "speechiness",
                "liveness", "loudness", "key", "mode"]
        for k in keys:
            if k in data:
                print(f"   {k:20s}: {data[k]}")
    return data


def test_track_detail(track_id: str, name: str):
    """트랙 상세 정보."""
    print(f"\n📋 Track Detail: {name}")
    data = api_get(f"/tracks/{track_id}")
    if data:
        print(f"   Name: {data.get('name')}")
        artists = data.get('artists', [])
        if artists:
            print(f"   Artist: {artists[0].get('name')}")
        print(f"   Album: {data.get('album', {}).get('name')}")
        print(f"   Popularity: {data.get('popularity')}")
    return data


def test_recommendations(track_id: str, name: str):
    """유사곡 추천."""
    print(f"\n🔍 Recommendations for: {name}")
    data = api_get(f"/recommendations?seed_tracks={track_id}&limit=5")
    if data:
        tracks = data.get("tracks", [])
        for i, t in enumerate(tracks[:5], 1):
            artists = ", ".join(a.get("name", "?") for a in t.get("artists", []))
            print(f"   {i}. {t.get('name')} — {artists}")
    return data


def test_genre_seeds():
    """사용 가능한 장르 시드 목록."""
    print(f"\n📋 Available Genre Seeds:")
    data = api_get("/recommendations/available-genre-seeds")
    if data:
        genres = data.get("genres", [])
        print(f"   Total: {len(genres)}")
        print(f"   Sample: {genres[:20]}")
    return data


def test_related_artists(artist_id: str, name: str):
    """관련 아티스트."""
    print(f"\n👥 Related Artists: {name}")
    data = api_get(f"/artists/{artist_id}/related-artists")
    if data:
        artists = data.get("artists", [])
        for i, a in enumerate(artists[:5], 1):
            genres = ", ".join(a.get("genres", [])[:3])
            print(f"   {i}. {a.get('name')} [{genres}]")
    return data


def main():
    print("🎧 Musicae API 테스트")
    print(f"   Host: {HEADERS['X-RapidAPI-Host']}")
    print(f"   Key: {API_KEY[:8]}...")

    results = {}

    # 1. 장르 시드 목록
    genre_seeds = test_genre_seeds()

    # 2. 각 곡별 테스트
    for name, track_id in TEST_TRACKS.items():
        print(f"\n{'='*50}")
        detail = test_track_detail(track_id, name)
        features = test_audio_features(track_id, name)
        recs = test_recommendations(track_id, name)

        results[name] = {
            "track_id": track_id,
            "detail": detail,
            "features": features,
            "recommendations": recs,
        }

    # 3. BTS 관련 아티스트 (artist ID)
    test_related_artists("3Nrfpe0tUJi4K4DXYWgMUX", "BTS")

    # 4. 결과 저장
    with open("musicae_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    # 5. 요약
    print(f"\n{'='*50}")
    print(f"📊 테스트 요약:")
    for name, r in results.items():
        has_detail = "✅" if r["detail"] else "❌"
        has_features = "✅" if r["features"] else "❌"
        has_recs = "✅" if r["recommendations"] else "❌"
        print(f"   {name}: detail={has_detail} features={has_features} recs={has_recs}")

    print(f"\n💾 Saved: musicae_test_results.json")


if __name__ == "__main__":
    main()
