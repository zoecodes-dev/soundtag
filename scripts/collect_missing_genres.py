"""
SoundTag — 부족 장르 3개 Deezer 보충 수집
=========================================
K-R&B, Neo Soul, Jazz Pop — FSLD에 없고 기존 Deezer에도 없는 장르.
기존 genre_data/previews/ 에 추가됨.

사용법:
    python collect_missing_genres.py
"""

import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime

BASE_URL = "https://api.deezer.com"
RATE_LIMIT_DELAY = 0.35
OUTPUT_DIR = Path("./genre_data/previews")
PER_GENRE = 100

# ── 수집할 3개 장르 ──
MISSING_GENRES = {
    "K-R&B": {
        "queries": ["korean R&B", "K R&B", "korean soul"],
        "artists": [
            ("DEAN", 70036),
            ("Crush", 4849528),
            ("Colde", 13423415),
            ("HEIZE", 6777467),
            ("BIBI", 75657692),
            ("pH-1", 12039028),
            ("DPR LIVE", 12133152),
            ("WOODZ", 51619862),
            ("Zion.T", 4321955),
            ("GRAY", 9735218),
        ],
    },
    "Neo Soul": {
        "queries": ["neo soul", "neo-soul", "modern soul"],
        "artists": [
            ("Erykah Badu", 906),
            ("D'Angelo", 1601),
            ("Lauryn Hill", 1424),
            ("Anderson .Paak", 5765363),
            ("Solange", 161593),
            ("Jorja Smith", 11498244),
            ("Tom Misch", 1587890),
            ("Hiatus Kaiyote", 4754003),
            ("Ravyn Lenae", 11862046),
            ("SZA", 4238195),
        ],
    },
    "Jazz Pop": {
        "queries": ["jazz pop", "pop jazz", "acid jazz"],
        "artists": [
            ("Norah Jones", 201),
            ("Michael Bublé", 180),
            ("Jamie Cullum", 1498),
            ("Snarky Puppy", 1234674),
            ("Robert Glasper", 56279),
            ("Jacob Collier", 8583400),
            ("Chet Baker", 1152),
            ("Diana Krall", 1143),
            ("Gregory Porter", 4495480),
            ("Esperanza Spalding", 316610),
        ],
    },
}


def api_get(endpoint, params=None):
    """Deezer API GET."""
    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        time.sleep(RATE_LIMIT_DELAY)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"  ❌ API error: {e}")
    return None


def download_preview(url, filepath):
    """MP3 프리뷰 다운로드."""
    if os.path.exists(filepath):
        return True
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False


def collect_from_artist(artist_name, artist_id, genre_dir, existing_ids):
    """아티스트 top tracks에서 수집."""
    tracks = []
    data = api_get(f"artist/{artist_id}/top", {"limit": 50})
    if not data or "data" not in data:
        return tracks

    for t in data["data"]:
        tid = t.get("id")
        preview = t.get("preview")
        if not tid or not preview or tid in existing_ids:
            continue

        filename = f"{artist_name.replace(' ', '_')}_{tid}.mp3"
        filepath = genre_dir / filename

        if download_preview(preview, str(filepath)):
            existing_ids.add(tid)
            tracks.append({
                "track_id": tid,
                "title": t.get("title", ""),
                "artist_name": artist_name,
                "artist_id": artist_id,
                "duration": t.get("duration", 0),
                "preview_url": preview,
                "local_path": str(filepath),
            })

    return tracks


def collect_from_search(query, genre_dir, existing_ids, limit=30):
    """검색 쿼리로 수집."""
    tracks = []
    data = api_get("search", {"q": query, "limit": limit})
    if not data or "data" not in data:
        return tracks

    for t in data["data"]:
        tid = t.get("id")
        preview = t.get("preview")
        if not tid or not preview or tid in existing_ids:
            continue

        artist_name = t.get("artist", {}).get("name", "Unknown")
        filename = f"{artist_name.replace(' ', '_')}_{tid}.mp3"
        filepath = genre_dir / filename

        if download_preview(preview, str(filepath)):
            existing_ids.add(tid)
            tracks.append({
                "track_id": tid,
                "title": t.get("title", ""),
                "artist_name": artist_name,
                "artist_id": t.get("artist", {}).get("id"),
                "duration": t.get("duration", 0),
                "preview_url": preview,
                "local_path": str(filepath),
            })

    return tracks


def main():
    print("🎵 SoundTag — 부족 장르 보충 수집")
    print(f"   장르: {', '.join(MISSING_GENRES.keys())}")
    print(f"   목표: 장르당 {PER_GENRE}곡\n")

    all_results = {}

    for genre_name, config in MISSING_GENRES.items():
        print(f"\n{'='*50}")
        print(f"🎤 {genre_name}")
        print(f"{'='*50}")

        # 장르 폴더 생성
        folder_name = genre_name.replace(" ", "_").replace("&", "and")
        genre_dir = OUTPUT_DIR / folder_name
        genre_dir.mkdir(parents=True, exist_ok=True)

        existing_ids = set()
        all_tracks = []

        # 1) 아티스트 top tracks
        for artist_name, artist_id in config["artists"]:
            tracks = collect_from_artist(artist_name, artist_id, genre_dir, existing_ids)
            all_tracks.extend(tracks)
            print(f"  ♪ {artist_name:20s} → {len(tracks)}곡")

            if len(all_tracks) >= PER_GENRE:
                break

        # 2) 검색으로 보충
        if len(all_tracks) < PER_GENRE:
            for query in config["queries"]:
                needed = PER_GENRE - len(all_tracks)
                if needed <= 0:
                    break
                tracks = collect_from_search(query, genre_dir, existing_ids, limit=needed + 10)
                all_tracks.extend(tracks)
                print(f"  🔍 '{query}' → {len(tracks)}곡")

        all_tracks = all_tracks[:PER_GENRE]
        all_results[genre_name] = all_tracks
        print(f"\n  ✅ {genre_name}: {len(all_tracks)}곡 수집 완료")

    # 결과 저장
    output = {
        "collected_at": datetime.now().isoformat(),
        "genres": {g: len(t) for g, t in all_results.items()},
        "tracks": {g: t for g, t in all_results.items()},
    }

    meta_path = OUTPUT_DIR.parent / "missing_genres_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"완료!")
    for g, t in all_results.items():
        print(f"  {g:15s} → {len(t)}곡")
    print(f"  메타데이터: {meta_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
