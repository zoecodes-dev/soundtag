"""
SoundTag - Deezer K-pop 데이터 수집 파이프라인 v2
===================================================
v2 변경사항:
  - 아티스트 ID 직접 지정 (검색 오매칭 방지)
  - 팬 수 threshold 검증 (잘못된 아티스트 자동 필터)
  - Stray Kids 중복 제거
  - 검색 fallback: ID 없으면 검색 + 팬수 검증

사용법:
    python deezer_collector_v2.py                    # 기본 수집
    python deezer_collector_v2.py --download          # 프리뷰 MP3도 다운로드
    python deezer_collector_v2.py --query "BTS"       # 특정 아티스트 검색
    python deezer_collector_v2.py --min-fans 5000     # 팬수 threshold 변경
"""

import requests
import json
import time
import os
import argparse
from pathlib import Path
from datetime import datetime

# ─── 설정 ──────────────────────────────────────────────
BASE_URL = "https://api.deezer.com"
RATE_LIMIT_DELAY = 0.12  # Deezer 한도: 50req/5sec=0.1s, 약간 여유
OUTPUT_DIR = Path("./deezer_data")
PREVIEW_DIR = OUTPUT_DIR / "previews"
MIN_FANS_THRESHOLD = 5000  # 이 이하면 잘못된 매칭으로 간주

# ─── K-pop 아티스트 시드 (ID 직접 지정) ─────────────────
# 형식: (표시명, Deezer artist ID)
# ID는 deezer.com/artist/{id} URL에서 확인
KPOP_SEED_ARTISTS = [
    # ── 4세대+ 걸그룹 ──
    ("aespa", 113547672),
    ("NewJeans", 178008437),
    ("LE SSERAFIM", 168158797),
    ("ILLIT", 259645622),
    ("BABYMONSTER", 244386532),
    ("IVE", 153042292),        # 수정: 153042362 → 153042292
    ("NMIXX", 160138282),
    ("KISS OF LIFE", 6389700),
    ("tripleS", 7712602),      # 수정: MODHAUS tripleS
    ("ITZY", 3649631),         # 수정: 83106582(Itzy 다른 아티스트) → 3649631

    # ── 4세대+ 보이그룹 ──
    ("Stray Kids", 13923487),  # 수정: 213951267 → 13923487, 중복 제거
    ("ATEEZ", 49280302),
    ("ENHYPEN", 113915572),
    ("TOMORROW X TOGETHER", 60552072),  # 수정: TXT → 정식명 + ID
    ("RIIZE", 225538625),
    ("ZEROBASEONE", 219364175),

    # ── 3세대 ──
    ("BTS", 6982223),          # 수정: 3911971(B.T.S) → 6982223
    ("BLACKPINK", 10803980),
    ("TWICE", 161553),
    ("Red Velvet", 338654),
    ("EXO", 88684),
    ("GOT7", 6209854),
    ("SEVENTEEN", 240582),     # 수정: 59457072 → 240582
    ("NCT 127", 50306442),
    ("NCT DREAM", 11999322),
    ("(G)I-DLE", 15065941),
    ("MAMAMOO", 7161880),

    # ── 솔로 ──
    ("IU", 2810121),
    ("Jung Kook", 248616612),
    ("JENNIE", 54090322),
    ("ROSÉ", 126335112),
    ("TAEYEON", 2562931),
    ("SUNMI", 8904144),

    # ── K-Hip Hop / K-R&B ──
    ("Zico", 50101802),
    ("Jay Park", 650215),
    ("DEAN", 70036),           # 수정: Olivia Dean → 진짜 DEAN (딘)
    ("Crush", 131641),         # 수정: 신효섭 Crush (P NATION)
    ("pH-1", 12039028),
    ("BIBI", 11467),           # 수정: 김형서 BIBI (Feel GHood/88rising)
    ("DPR LIVE", 12133152),
    ("Colde", 13423415),
    ("HEIZE", 6777467),
]


def api_get(endpoint: str, params: dict = None) -> dict | None:
    """Deezer API GET 요청 (rate limit 적용)."""
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        time.sleep(RATE_LIMIT_DELAY)
        if resp.status_code == 200:
            data = resp.json()
            if "error" in data:
                print(f"  ⚠️ API error: {data['error'].get('message', 'unknown')}")
                return None
            return data
        else:
            print(f"  ⚠️ HTTP {resp.status_code}: {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed: {e}")
        return None


def get_artist_by_id(artist_id: int) -> dict | None:
    """ID로 아티스트 직접 조회."""
    return api_get(f"artist/{artist_id}")


def search_artist_with_validation(name: str, min_fans: int = MIN_FANS_THRESHOLD) -> dict | None:
    """아티스트 검색 + 팬수 검증."""
    data = api_get("search/artist", {"q": name, "limit": 5})
    if not data or not data.get("data"):
        print(f"  ❌ Not found: {name}")
        return None

    # 팬수가 threshold 이상인 첫 번째 결과
    for artist in data["data"]:
        fans = artist.get("nb_fan", 0)
        if fans >= min_fans:
            print(f"  ✅ Found: {artist['name']} (id={artist['id']}, fans={fans:,})")
            return artist
        else:
            print(f"  ⏭️  Skip: {artist['name']} (fans={fans:,} < {min_fans:,})")

    print(f"  ❌ No match with enough fans for: {name}")
    return None


def get_artist_top_tracks(artist_id: int, limit: int = 50) -> list:
    data = api_get(f"artist/{artist_id}/top", {"limit": limit})
    return data.get("data", []) if data else []


def get_artist_albums(artist_id: int, limit: int = 50) -> list:
    data = api_get(f"artist/{artist_id}/albums", {"limit": limit})
    return data.get("data", []) if data else []


def get_album_tracks(album_id: int) -> list:
    data = api_get(f"album/{album_id}/tracks", {"limit": 100})
    return data.get("data", []) if data else []


def search_tracks(query: str, limit: int = 100) -> list:
    data = api_get("search/track", {"q": query, "limit": limit})
    return data.get("data", []) if data else []


def get_genre_list() -> list:
    data = api_get("genre")
    return data.get("data", []) if data else []


def extract_track_metadata(track: dict, artist_name: str = "") -> dict:
    """트랙 데이터에서 학습에 필요한 필드 추출."""
    return {
        "track_id": track.get("id"),
        "title": track.get("title"),
        "title_short": track.get("title_short"),
        "artist_name": track.get("artist", {}).get("name", artist_name),
        "artist_id": track.get("artist", {}).get("id"),
        "album_title": track.get("album", {}).get("title", ""),
        "album_id": track.get("album", {}).get("id"),
        "duration": track.get("duration"),
        "preview_url": track.get("preview"),
        "bpm": track.get("bpm", None),
        "gain": track.get("gain", None),
        "isrc": track.get("isrc", ""),
        "rank": track.get("rank", 0),
        "release_date": track.get("release_date", ""),
        "explicit": track.get("explicit_lyrics", False),
        "contributors": [c.get("name") for c in track.get("contributors", [])],
        "genre_id": track.get("album", {}).get("genre_id", None),
        "collected_at": datetime.now().isoformat(),
    }


def download_preview(preview_url: str, track_id: int, artist_name: str) -> str | None:
    """30초 프리뷰 MP3 다운로드."""
    if not preview_url:
        return None
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in artist_name if c.isalnum() or c in " _-").strip()
    filename = f"{safe_name}_{track_id}.mp3"
    filepath = PREVIEW_DIR / filename
    if filepath.exists():
        return str(filepath)
    try:
        resp = requests.get(preview_url, timeout=15)
        if resp.status_code == 200:
            filepath.write_bytes(resp.content)
            return str(filepath)
    except Exception as e:
        print(f"  ⚠️ Download failed for {track_id}: {e}")
    return None


def collect_artist_data(
    display_name: str,
    artist_id: int | None = None,
    download: bool = False,
    max_tracks: int = 100,
    min_fans: int = MIN_FANS_THRESHOLD,
) -> list:
    """한 아티스트의 트랙 데이터 수집."""
    print(f"\n🎵 Collecting: {display_name}")

    # 1. 아티스트 조회 (ID 우선, 없으면 검색)
    if artist_id:
        artist = get_artist_by_id(artist_id)
        if artist:
            fans = artist.get("nb_fan", 0)
            print(f"  ✅ Loaded: {artist['name']} (id={artist_id}, fans={fans:,})")
            # 팬수 검증 (ID 직접 지정이라도 의심스러우면 경고)
            if fans < min_fans:
                print(f"  ⚠️ Warning: Low fan count ({fans:,}). Data may be limited.")
        else:
            print(f"  ❌ ID {artist_id} not found, trying search...")
            artist = search_artist_with_validation(display_name, min_fans)
    else:
        artist = search_artist_with_validation(display_name, min_fans)

    if not artist:
        return []

    actual_id = artist["id"]
    collected = {}

    # 2. Top tracks
    print(f"  📊 Fetching top tracks...")
    top_tracks = get_artist_top_tracks(actual_id, limit=50)
    for t in top_tracks:
        meta = extract_track_metadata(t, display_name)
        collected[meta["track_id"]] = meta
    print(f"    → {len(top_tracks)} top tracks")

    # 3. 앨범 트랙
    if len(collected) < max_tracks:
        print(f"  💿 Fetching albums...")
        albums = get_artist_albums(actual_id, limit=20)
        for album in albums:
            if len(collected) >= max_tracks:
                break
            tracks = get_album_tracks(album["id"])
            for t in tracks:
                if t.get("id") not in collected:
                    meta = extract_track_metadata(t, display_name)
                    meta["album_title"] = album.get("title", "")
                    meta["album_id"] = album.get("id")
                    meta["genre_id"] = album.get("genre_id")
                    meta["release_date"] = album.get("release_date", "")
                    collected[meta["track_id"]] = meta
        print(f"    → {len(collected)} total tracks after albums")

    # 4. 프리뷰 다운로드 (옵션)
    if download:
        print(f"  ⬇️  Downloading previews...")
        downloaded = 0
        for meta in collected.values():
            path = download_preview(meta["preview_url"], meta["track_id"], display_name)
            if path:
                meta["local_preview_path"] = path
                downloaded += 1
        print(f"    → {downloaded}/{len(collected)} previews downloaded")

    return list(collected.values())


def save_results(all_tracks: list, filename: str = None):
    """수집 결과를 JSON으로 저장."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kpop_tracks_{timestamp}.json"
    filepath = OUTPUT_DIR / filename

    total = len(all_tracks)
    with_preview = sum(1 for t in all_tracks if t.get("preview_url"))
    unique_artists = len(set(t["artist_name"] for t in all_tracks))

    output = {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "total_tracks": total,
            "tracks_with_preview": with_preview,
            "unique_artists": unique_artists,
            "version": "v2",
        },
        "tracks": all_tracks,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"💾 Saved: {filepath}")
    print(f"   Total tracks:       {total}")
    print(f"   With preview URL:   {with_preview}")
    print(f"   Unique artists:     {unique_artists}")
    print(f"{'='*60}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="SoundTag Deezer K-pop Collector v2")
    parser.add_argument("--query", type=str, help="Search query (uses fan validation)")
    parser.add_argument("--download", action="store_true", help="Download 30s previews")
    parser.add_argument("--list-genres", action="store_true", help="List Deezer genres")
    parser.add_argument("--artists-file", type=str, help="Custom artist list (name,id per line)")
    parser.add_argument("--max-tracks", type=int, default=100, help="Max tracks per artist")
    parser.add_argument("--min-fans", type=int, default=MIN_FANS_THRESHOLD, help="Min fan threshold")
    parser.add_argument("--output", type=str, help="Output filename")
    args = parser.parse_args()

    all_tracks = []

    if args.list_genres:
        genres = get_genre_list()
        print("\n📋 Deezer Genres:")
        for g in genres:
            print(f"  {g['id']:>6}: {g['name']}")
        return

    if args.query:
        # 검색 모드: 아티스트 검색 + 팬수 검증
        all_tracks = collect_artist_data(
            args.query, artist_id=None,
            download=args.download,
            max_tracks=args.max_tracks,
            min_fans=args.min_fans,
        )
    else:
        # 커스텀 아티스트 파일 or 기본 시드 리스트
        artists = KPOP_SEED_ARTISTS
        if args.artists_file:
            artists = []
            with open(args.artists_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(",", 1)
                    name = parts[0].strip()
                    aid = int(parts[1].strip()) if len(parts) > 1 else None
                    artists.append((name, aid))

        print(f"🎤 Collecting from {len(artists)} artists...")
        for display_name, artist_id in artists:
            tracks = collect_artist_data(
                display_name, artist_id=artist_id,
                download=args.download,
                max_tracks=args.max_tracks,
                min_fans=args.min_fans,
            )
            all_tracks.extend(tracks)

    if all_tracks:
        save_results(all_tracks, filename=args.output)
    else:
        print("⚠️ No tracks collected.")


if __name__ == "__main__":
    main()
