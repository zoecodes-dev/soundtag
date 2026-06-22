#!/usr/bin/env python3
"""
하이브리드 v3 데이터셋 구축
============================
FSLD 드럼루프 + Freesound 드럼루프 (Jamendo 제외)
소스:
  1. FSLD (전문가 태깅, wav)
  2. Freesound (장르별 수집, mp3)
사용법:
  python prepare_hybrid_v3.py --scan
  python prepare_hybrid_v3.py --build
"""
import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from collections import defaultdict

# ============================================================
# 경로 설정
# ============================================================
FSLD_WAV_DIR = Path("/Volumes/One Touch/audio/wav")
FSLD_METADATA = Path("/Volumes/One Touch/metadata.json")
FREESOUND_DIR = Path("/Volumes/One Touch/freesound_drums")
OUTPUT_DIR = Path("/Volumes/One Touch/hybrid_v3")
MERGED_DIR = OUTPUT_DIR / "merged"
METADATA_OUT = OUTPUT_DIR / "hybrid_v3_metadata.json"

# ============================================================
# 장르 매핑
# ============================================================
FSLD_TAG_MAP = {
    "trap": "Trap",
    "hiphop": "Hip_Hop", "hip-hop": "Hip_Hop", "boom-bap": "Hip_Hop", "boombap": "Hip_Hop",
    "disco": "Disco",
    "funk": "Funk",
    "pop": "Pop_Rock", "rock": "Pop_Rock", "pop-rock": "Pop_Rock",
    "lofi": "Lo_fi", "lo-fi": "Lo_fi", "chillhop": "Lo_fi",
    "electropop": "Electropop", "synthpop": "Electropop", "synthwave": "Electropop",
    "dnb": "DnB", "drum-and-bass": "DnB",
    "techno": "Techno",
    "trance": "Trance",
    "house": "House", "deep-house": "House", "garage": "House",
    "dubstep": "Dubstep",
    "breakbeat": "Breakbeat", "breaks": "Breakbeat",
    "edm": "EDM", "electronic": "EDM",
    "dancehall": "Dancehall",
    "rnb": "Neo_Soul", "soul": "Neo_Soul",
    "latin": "Latin_Pop",
    "jersey": "Jersey_Club",
    "reggaeton": "Reggaeton",
}

# Freesound 폴더명 → 장르명 매핑
FREESOUND_GENRE_MAP = {
    "Disco": "Disco",
    "Electropop": "Electropop",
    "Trip_hop": "Trip_hop",
    "Neo_Soul": "Neo_Soul",
    "House": "House",
    "Trap": "Trap",
    "Hip_Hop": "Hip_Hop",
    "Future_Bass": "Future_Bass",
    "DnB": "DnB",
    "Techno": "Techno",
}

def load_fsld_metadata():
    with open(FSLD_METADATA) as f:
        return json.load(f)  # dict 반환

def get_fsld_genre(tags):
    for tag in tags:
        tag_lower = tag.lower().replace(" ", "-")
        if tag_lower in FSLD_TAG_MAP:
            return FSLD_TAG_MAP[tag_lower]
    return None

def scan():
    print("=== FSLD 현황 ===")
    meta = load_fsld_metadata()  # dict
    fsld_counts = defaultdict(int)
    for sound_id, item in meta.items():  # ← dict.items()로 변경
        tags = item.get('tags', [])
        genre = get_fsld_genre(tags)
        if genre:
            fsld_counts[genre] += 1
    for genre, count in sorted(fsld_counts.items()):
        print(f"  {genre:20s} {count}개")
    print(f"  총: {sum(fsld_counts.values())}개")

    print("\n=== Freesound 현황 ===")
    freesound_counts = defaultdict(int)
    for genre_dir in sorted(FREESOUND_DIR.iterdir()):
        if not genre_dir.is_dir():
            continue
        count = sum(1 for f in genre_dir.glob('*.mp3')
                   if not f.name.startswith('._'))
        genre = FREESOUND_GENRE_MAP.get(genre_dir.name, genre_dir.name)
        freesound_counts[genre] = count
        print(f"  {genre:20s} {count}개")
    print(f"  총: {sum(freesound_counts.values())}개")

def build():
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    metadata = []
    counts = defaultdict(int)

    # 1. FSLD — v2 방식으로 수정
    print("FSLD 처리 중...")
    fsld_meta = load_fsld_metadata()
    
    # wav 파일 인덱스 구축
    wav_files = {}
    for wav in FSLD_WAV_DIR.glob("*.wav"):
        if wav.name.startswith("._"):
            continue
        fid = wav.stem.split("_")[0]
        wav_files[fid] = wav
    
    for fid, item in fsld_meta.items():
        tags = [t.lower() for t in item.get("tags", [])]
        
        # 드럼 태그 체크
        is_drums = "drums" in tags or "drum" in tags
        if not is_drums:
            continue
        
        # 장르 매핑
        genre = None
        for tag in tags:
            if tag in FSLD_TAG_MAP:
                genre = FSLD_TAG_MAP[tag]
                break
        
        if not genre or fid not in wav_files:
            continue
        
        src = wav_files[fid]
        genre_folder = genre.replace(" ", "_").replace("&", "and")
        out_dir = MERGED_DIR / genre_folder
        out_dir.mkdir(exist_ok=True)
        dst = out_dir / f"fsld_{src.name}"
        if not dst.exists():
            shutil.copy2(src, dst)
        counts[genre] += 1
        metadata.append({'file': str(dst.relative_to(OUTPUT_DIR)), 'genre': genre, 'source': 'fsld'})

    print(f"  FSLD: {sum(counts.values())}개")

    # 2. Freesound
    print("Freesound 처리 중...")
    for genre_dir in sorted(FREESOUND_DIR.iterdir()):
        if not genre_dir.is_dir():
            continue
        genre = FREESOUND_GENRE_MAP.get(genre_dir.name)
        if not genre:
            continue
        genre_folder = genre.replace(" ", "_").replace("&", "and")
        out_dir = MERGED_DIR / genre_folder
        out_dir.mkdir(exist_ok=True)
        for f in sorted(genre_dir.glob('*.mp3')):
            if f.name.startswith('._') or 'quarantine' in str(f):
                continue
            dst = out_dir / f"freesound_{f.name}"
            if not dst.exists():
                shutil.copy2(f, dst)
            counts[genre] += 1
            metadata.append({'file': str(dst.relative_to(OUTPUT_DIR)), 'genre': genre, 'source': 'freesound'})

    # 메타데이터 저장
    with open(METADATA_OUT, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("\n=== 구축 완료 ===")
    total = 0
    for genre, count in sorted(counts.items()):
        print(f"  {genre:20s} {count}개")
        total += count
    print(f"  총: {total}개")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scan', action='store_true')
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()

    if args.scan:
        scan()
    elif args.build:
        build()
    else:
        parser.print_help()