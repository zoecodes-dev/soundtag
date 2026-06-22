"""
SoundTag - 장르별 비K-pop 데이터 수집
=====================================
SoundTag taxonomy의 각 장르를 Deezer에서 검색해서
장르 레이블이 정확한 학습 데이터를 수집.

전략: K-pop은 "모든 장르를 가져다 쓰는 장르"
→ 원본 장르 음악으로 학습 → K-pop 데모에 적용

사용법:
    python collect_genre_data.py                     # Tier 1 (27개) 수집
    python collect_genre_data.py --tier 2            # Tier 2까지
    python collect_genre_data.py --genre "Trap"      # 특정 장르만
    python collect_genre_data.py --download           # 프리뷰도 다운로드
    python collect_genre_data.py --per-genre 50       # 장르당 50곡
"""

import requests
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

BASE_URL = "https://api.deezer.com"
RATE_LIMIT_DELAY = 0.12
OUTPUT_DIR = Path("./genre_data")
PREVIEW_DIR = OUTPUT_DIR / "previews"

# ─── SoundTag Tier 1 장르 → Deezer 검색 쿼리 매핑 ──────
# 각 장르에 대해 Deezer에서 해당 장르를 찾기 위한 검색 전략 정의
# (장르명, [검색 쿼리들], 대표 아티스트들)
GENRE_SEARCH_CONFIG = {
    # ── Tier 1: Core (27개) ──
    "Dance Pop": {
        "tier": 1,
        "queries": ["dance pop", "dance pop hits"],
        "artists": ["Dua Lipa", "Carly Rae Jepsen", "Charli XCX"],
    },
    "Electropop": {
        "tier": 1,
        "queries": ["electropop", "electro pop"],
        "artists": ["Lady Gaga", "Grimes", "CHVRCHES"],
    },
    "Synth-pop": {
        "tier": 1,
        "queries": ["synth pop", "synthpop"],
        "artists": ["The Weeknd", "Daft Punk", "Depeche Mode"],
    },
    "Tropical House": {
        "tier": 1,
        "queries": ["tropical house"],
        "artists": ["Kygo", "Thomas Jack"],
    },
    "Future Bass": {
        "tier": 1,
        "queries": ["future bass"],
        "artists": ["Flume", "San Holo", "Illenium"],
    },
    "Trap": {
        "tier": 1,
        "queries": ["trap music", "trap beat", "trap hip hop"],
        "artists": ["Future", "Migos", "Travis Scott"],
    },
    "Pop R&B": {
        "tier": 1,
        "queries": ["pop rnb", "pop r&b"],
        "artists": ["SZA", "Khalid", "Brent Faiyaz"],
    },
    "Hip Hop": {
        "tier": 1,
        "queries": ["hip hop", "rap"],
        "artists": ["Kendrick Lamar", "Drake", "J. Cole"],
    },
    "EDM": {
        "tier": 1,
        "queries": ["edm", "electronic dance music"],
        "artists": ["Martin Garrix", "Marshmello", "Calvin Harris"],
    },
    "Moombahton": {
        "tier": 1,
        "queries": ["moombahton"],
        "artists": ["Major Lazer", "DJ Snake"],
    },
    "City Pop": {
        "tier": 1,
        "queries": ["city pop", "japanese city pop"],
        "artists": ["Tatsuro Yamashita", "Mariya Takeuchi"],
    },
    "Disco": {
        "tier": 1,
        "queries": ["disco", "disco funk"],
        "artists": ["Bee Gees", "Donna Summer", "Chic"],
    },
    "Nu-Disco": {
        "tier": 1,
        "queries": ["nu disco", "nu-disco"],
        "artists": ["Daft Punk", "Breakbot", "Chromeo"],
    },
    "Funk Pop": {
        "tier": 1,
        "queries": ["funk pop"],
        "artists": ["Bruno Mars", "Doja Cat", "Anderson .Paak"],
    },
    "Latin Pop": {
        "tier": 1,
        "queries": ["latin pop"],
        "artists": ["Bad Bunny", "Shakira", "Enrique Iglesias"],
    },
    "Reggaeton": {
        "tier": 1,
        "queries": ["reggaeton"],
        "artists": ["Daddy Yankee", "J Balvin", "Ozuna"],
    },
    "Pop Rock": {
        "tier": 1,
        "queries": ["pop rock"],
        "artists": ["Imagine Dragons", "OneRepublic", "Maroon 5"],
    },
    "Ballad": {
        "tier": 1,
        "queries": ["ballad", "pop ballad"],
        "artists": ["Adele", "Sam Smith", "Lewis Capaldi"],
    },
    "Contemporary R&B": {
        "tier": 1,
        "queries": ["contemporary r&b", "rnb"],
        "artists": ["The Weeknd", "Frank Ocean", "Daniel Caesar"],
    },
    "New Jack Swing": {
        "tier": 1,
        "queries": ["new jack swing"],
        "artists": ["Bobby Brown", "Bell Biv DeVoe", "Guy"],
    },
    "UK Garage": {
        "tier": 1,
        "queries": ["uk garage", "2-step garage"],
        "artists": ["Disclosure", "MJ Cole"],
    },
    "Jersey Club": {
        "tier": 1,
        "queries": ["jersey club"],
        "artists": ["DJ Smallz", "Cookiee Kawaii"],
    },
    "Afrobeats": {
        "tier": 1,
        "queries": ["afrobeats"],
        "artists": ["Burna Boy", "Wizkid", "Davido"],
    },
    "Drill": {
        "tier": 1,
        "queries": ["drill", "uk drill"],
        "artists": ["Pop Smoke", "Central Cee"],
    },
    "Hyperpop": {
        "tier": 1,
        "queries": ["hyperpop"],
        "artists": ["100 gecs", "A.G. Cook", "SOPHIE"],
    },
    "Bedroom Pop": {
        "tier": 1,
        "queries": ["bedroom pop"],
        "artists": ["Clairo", "Boy Pablo", "Beabadoobee"],
    },
}


def api_get(endpoint: str, params: dict = None) -> dict | None:
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        time.sleep(RATE_LIMIT_DELAY)
        if resp.status_code == 200:
            data = resp.json()
            if "error" in data:
                return None
            return data
        return None
    except:
        return None


def search_tracks(query: str, limit: int = 100) -> list:
    data = api_get("search/track", {"q": query, "limit": limit})
    return data.get("data", []) if data else []


def get_artist_top_tracks(artist_id: int, limit: int = 25) -> list:
    data = api_get(f"artist/{artist_id}/top", {"limit": limit})
    return data.get("data", []) if data else []


def search_artist(name: str) -> dict | None:
    data = api_get("search/artist", {"q": name, "limit": 1})
    if data and data.get("data"):
        return data["data"][0]
    return None


def download_preview(preview_url: str, genre: str, track_id: int) -> str | None:
    if not preview_url:
        return None
    genre_dir = PREVIEW_DIR / genre.replace(" ", "_").replace("/", "_").replace("&", "and")
    genre_dir.mkdir(parents=True, exist_ok=True)
    filepath = genre_dir / f"{track_id}.mp3"
    if filepath.exists():
        return str(filepath)
    try:
        resp = requests.get(preview_url, timeout=15)
        if resp.status_code == 200:
            filepath.write_bytes(resp.content)
            return str(filepath)
    except:
        pass
    return None


def collect_genre(genre_name: str, config: dict, per_genre: int = 30, download: bool = False) -> list:
    """한 장르의 트랙 수집."""
    print(f"\n🎵 [{config['tier']}] {genre_name}")
    collected = {}  # track_id → metadata

    # 1. 검색 쿼리로 수집
    for query in config["queries"]:
        tracks = search_tracks(query, limit=100)
        for t in tracks:
            tid = t.get("id")
            if tid and tid not in collected and len(collected) < per_genre:
                collected[tid] = {
                    "track_id": tid,
                    "title": t.get("title"),
                    "artist_name": t.get("artist", {}).get("name", ""),
                    "artist_id": t.get("artist", {}).get("id"),
                    "album_title": t.get("album", {}).get("title", ""),
                    "duration": t.get("duration"),
                    "preview_url": t.get("preview"),
                    "rank": t.get("rank", 0),
                    "genre_label": genre_name,
                    "tier": config["tier"],
                    "source": "search",
                }

    # 2. 대표 아티스트 top tracks로 보강
    if len(collected) < per_genre:
        for artist_name in config.get("artists", []):
            if len(collected) >= per_genre:
                break
            artist = search_artist(artist_name)
            if artist:
                tracks = get_artist_top_tracks(artist["id"], limit=25)
                for t in tracks:
                    tid = t.get("id")
                    if tid and tid not in collected and len(collected) < per_genre:
                        collected[tid] = {
                            "track_id": tid,
                            "title": t.get("title"),
                            "artist_name": t.get("artist", {}).get("name", artist_name),
                            "artist_id": t.get("artist", {}).get("id"),
                            "album_title": t.get("album", {}).get("title", ""),
                            "duration": t.get("duration"),
                            "preview_url": t.get("preview"),
                            "rank": t.get("rank", 0),
                            "genre_label": genre_name,
                            "tier": config["tier"],
                            "source": "artist",
                        }

    # 3. 프리뷰 다운로드
    if download:
        dl_count = 0
        for meta in collected.values():
            path = download_preview(meta["preview_url"], genre_name, meta["track_id"])
            if path:
                meta["local_preview_path"] = path
                dl_count += 1
        print(f"  ⬇️  {dl_count}/{len(collected)} previews downloaded")

    with_preview = sum(1 for t in collected.values() if t.get("preview_url"))
    print(f"  → {len(collected)} tracks ({with_preview} with preview)")
    return list(collected.values())


def save_results(all_tracks: list, filename: str = None):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"genre_tracks_{timestamp}.json"
    filepath = OUTPUT_DIR / filename

    # 통계
    from collections import Counter
    genre_counter = Counter(t["genre_label"] for t in all_tracks)

    output = {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "total_tracks": len(all_tracks),
            "genres": len(genre_counter),
            "genre_distribution": dict(genre_counter.most_common()),
        },
        "tracks": all_tracks,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"💾 Saved: {filepath}")
    print(f"   Total: {len(all_tracks)} tracks across {len(genre_counter)} genres")
    print(f"\n   장르별 분포:")
    for genre, count in genre_counter.most_common():
        print(f"     {genre:25s} {count:4d}")
    print(f"{'='*60}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="SoundTag Genre Data Collector")
    parser.add_argument("--tier", type=int, default=1, help="Max tier to collect (1-4)")
    parser.add_argument("--genre", type=str, default=None, help="Specific genre to collect")
    parser.add_argument("--per-genre", type=int, default=30, help="Tracks per genre")
    parser.add_argument("--download", action="store_true", help="Download previews")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    all_tracks = []

    if args.genre:
        # 특정 장르만
        if args.genre in GENRE_SEARCH_CONFIG:
            config = GENRE_SEARCH_CONFIG[args.genre]
            tracks = collect_genre(args.genre, config, args.per_genre, args.download)
            all_tracks.extend(tracks)
        else:
            print(f"❌ Unknown genre: {args.genre}")
            print(f"   Available: {', '.join(GENRE_SEARCH_CONFIG.keys())}")
            return
    else:
        # Tier 기준으로 수집
        genres = {k: v for k, v in GENRE_SEARCH_CONFIG.items() if v["tier"] <= args.tier}
        print(f"🎤 Collecting {len(genres)} genres (Tier 1~{args.tier}, {args.per_genre}/genre)")

        for genre_name, config in genres.items():
            tracks = collect_genre(genre_name, config, args.per_genre, args.download)
            all_tracks.extend(tracks)

    if all_tracks:
        save_results(all_tracks, args.output)
    else:
        print("⚠️ No tracks collected.")


if __name__ == "__main__":
    main()
