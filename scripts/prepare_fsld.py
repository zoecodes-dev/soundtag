"""
SoundTag - FSLD 드럼 루프 장르별 추출
=====================================
Freesound Loop Dataset에서 드럼 루프를 장르 태그 기반으로 추출.
SoundTag taxonomy에 매핑해서 학습 데이터 생성.

사용법:
    python prepare_fsld.py
    python prepare_fsld.py --min-per-genre 30
    python prepare_fsld.py --output-dir ./fsld_genre_data
"""

import json
import shutil
import argparse
from pathlib import Path
from collections import Counter, defaultdict

# ─── FSLD 태그 → SoundTag 장르 매핑 ─────────────
TAG_TO_GENRE = {
    # Electronic / Dance
    "electro": "Electropop",
    "techno": "EDM",
    "trance": "EDM",
    "house": "Dance Pop",
    "dubstep": "EDM",
    "breakbeat": "Hip Hop",

    # Hip Hop 계열
    "hip-hop": "Hip Hop",
    "hiphop": "Hip Hop",
    "trap": "Trap",
    "boom-bap": "Hip Hop",
    "boombap": "Hip Hop",
    "lofi": "Bedroom Pop",
    "lo-fi": "Bedroom Pop",

    # Bass Music
    "dnb": "EDM",
    "drum-and-bass": "EDM",

    # Rock / Funk / Soul
    "rock": "Pop Rock",
    "funk": "Funk Pop",
    "soul": "Contemporary R&B",
    "disco": "Disco",

    # Other
    "jazz": "Contemporary R&B",
    "latin": "Latin Pop",
    "reggae": "Reggaeton",
    "reggaeton": "Reggaeton",
    "garage": "UK Garage",
    "industrial": "Hyperpop",
    "ambient": "Ballad",
    "pop": "Dance Pop",
    "rnb": "Pop R&B",
    "dancehall": "Afrobeats",
    "synthwave": "Synth-pop",
    "afrobeat": "Afrobeats",
    "drill": "Drill",
}


def load_fsld(metadata_path: str, audio_dir: str):
    """FSLD 메타데이터 + 드럼 루프 필터링."""
    with open(metadata_path, "r") as f:
        meta = json.load(f)

    audio_path = Path(audio_dir)
    drum_keyword = {"drum", "drums", "drumloop", "drum-loop", "beat", "percussion"}

    drum_tracks = []
    for tid, info in meta.items():
        tags = [t.lower() for t in info.get("tags", [])]

        # 드럼 루프만 필터
        if not any(d in tags for d in drum_keyword):
            continue

        # 장르 태그 찾기
        genres = set()
        for tag in tags:
            if tag in TAG_TO_GENRE:
                genres.add(TAG_TO_GENRE[tag])

        if not genres:
            continue

        # 오디오 파일 찾기
        wav_files = list(audio_path.glob(f"{tid}_*.wav"))
        if not wav_files:
            continue

        drum_tracks.append({
            "track_id": tid,
            "audio_path": str(wav_files[0]),
            "genres": list(genres),
            "primary_genre": list(genres)[0],  # 첫 번째 매칭 장르
            "tags": tags,
            "name": info.get("name", ""),
            "duration": None,
        })

    return drum_tracks


def prepare_dataset(drum_tracks: list, output_dir: str, min_per_genre: int = 20, max_per_genre: int = 200):
    """장르별로 오디오 파일 복사 + 메타데이터 생성."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # 장르별 그룹핑
    genre_groups = defaultdict(list)
    for t in drum_tracks:
        for g in t["genres"]:
            genre_groups[g].append(t)

    # 분포 출력
    print(f"\n📊 장르별 드럼 루프 분포:")
    selected_genres = {}
    for genre, tracks in sorted(genre_groups.items(), key=lambda x: -len(x[1])):
        count = len(tracks)
        status = "✅" if count >= min_per_genre else "⚠️ "
        print(f"  {status} {genre:25s} {count:5d}")
        if count >= min_per_genre:
            selected_genres[genre] = tracks[:max_per_genre]

    # 파일 복사
    print(f"\n📁 Copying files to {output_dir}...")
    all_tracks = []
    for genre, tracks in selected_genres.items():
        genre_dir = output / genre.replace(" ", "_").replace("&", "and").replace("/", "_")
        genre_dir.mkdir(parents=True, exist_ok=True)

        copied = 0
        for t in tracks:
            src = Path(t["audio_path"])
            dst = genre_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
            t["local_path"] = str(dst)
            all_tracks.append({**t, "assigned_genre": genre})
            copied += 1

        print(f"  {genre:25s} → {copied} files")

    # 메타데이터 저장
    meta_out = {
        "total_tracks": len(all_tracks),
        "genres": len(selected_genres),
        "genre_distribution": {g: len(ts) for g, ts in selected_genres.items()},
        "tracks": all_tracks,
    }

    meta_path = output / "fsld_genre_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_out, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Metadata: {meta_path}")
    print(f"   Total: {len(all_tracks)} tracks across {len(selected_genres)} genres")

    return selected_genres


def main():
    parser = argparse.ArgumentParser(description="FSLD Genre Preparation")
    parser.add_argument("--metadata", type=str, default="/Volumes/One Touch/metadata.json")
    parser.add_argument("--audio-dir", type=str, default="/Volumes/One Touch/audio/wav")
    parser.add_argument("--output-dir", type=str, default="./fsld_genre_data")
    parser.add_argument("--min-per-genre", type=int, default=20)
    parser.add_argument("--max-per-genre", type=int, default=200)
    args = parser.parse_args()

    print("🎵 FSLD 드럼 루프 장르 추출")
    print(f"   Metadata: {args.metadata}")
    print(f"   Audio: {args.audio_dir}")

    drum_tracks = load_fsld(args.metadata, args.audio_dir)
    print(f"\n🥁 Found {len(drum_tracks)} drum loops with genre tags")

    prepare_dataset(drum_tracks, args.output_dir, args.min_per_genre, args.max_per_genre)


if __name__ == "__main__":
    main()
