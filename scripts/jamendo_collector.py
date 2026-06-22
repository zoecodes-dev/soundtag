#!/usr/bin/env python3
"""
MTG-Jamendo Selective Collector for SoundTag v2
================================================
v2: validate 단계 추가 — 삭제된 트랙 사전 필터링

사용법:
  1. Jamendo API client_id 발급: https://developer.jamendo.com/v3.0
  2. scripts/.env에 JAMENDO_CLIENT_ID=xxx 추가
  3. python jamendo_collector.py --prepare    (메타데이터 준비 — 전체 가용 트랙)
  4. python jamendo_collector.py --validate   (API로 존재 여부 체크, 빠름)
  5. python jamendo_collector.py --download   (검증된 트랙만 다운로드)

필요 패키지: pip install requests python-dotenv tqdm
"""

import os
import sys
import json
import csv
import time
import argparse
import random
from pathlib import Path
from collections import defaultdict

try:
    import requests
    from tqdm import tqdm
    from dotenv import load_dotenv
except ImportError:
    print("필요 패키지 설치: pip install requests python-dotenv tqdm")
    sys.exit(1)

# .env 로드 (scripts/ 안에서 실행)
load_dotenv(Path(__file__).parent.parent / ".env")

# ============================================================
# 설정
# ============================================================

MTG_REPO_PATH = Path(__file__).parent / "mtg-jamendo-dataset"
GENRE_TSV = MTG_REPO_PATH / "data" / "autotagging_genre.tsv"
META_TSV = MTG_REPO_PATH / "data" / "raw.meta.tsv"

# 출력 → 외장하드
OUTPUT_DIR = Path("/Volumes/One Touch/jamendo_data")
METADATA_FILE = OUTPUT_DIR / "jamendo_all_candidates.json"
VALIDATED_FILE = OUTPUT_DIR / "jamendo_validated_tracks.json"
AUDIO_DIR = OUTPUT_DIR / "audio"

JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID", "")
JAMENDO_API_BASE = "https://api.jamendo.com/v3.0"

# ============================================================
# SoundTag ↔ Jamendo 장르 매핑
# max_tracks = 목표 다운로드 수 (validate 후 이만큼만 다운)
# ============================================================

SOUNDTAG_MAPPING = {
    "House":      {"jamendo_tags": ["house", "deephouse"], "max_tracks": 200},
    "Techno":     {"jamendo_tags": ["techno"],              "max_tracks": 200},
    "Trance":     {"jamendo_tags": ["trance"],              "max_tracks": 138},
    "DnB":        {"jamendo_tags": ["drumnbass"],           "max_tracks": 200},
    "Dubstep":    {"jamendo_tags": ["dubstep"],             "max_tracks": 200},
    "Breakbeat":  {"jamendo_tags": ["breakbeat"],           "max_tracks": 200},
    "Electropop": {"jamendo_tags": ["electropop"],          "max_tracks": 200},
    "Disco":      {"jamendo_tags": ["disco"],               "max_tracks": 154},
    "Trip-hop":   {"jamendo_tags": ["triphop"],             "max_tracks": 38},
    "Synthpop":   {"jamendo_tags": ["synthpop"],            "max_tracks": 58},
    "EDM":        {"jamendo_tags": ["edm"],                 "max_tracks": 66},
    "Hip Hop":    {"jamendo_tags": ["hiphop", "rap"],       "max_tracks": 300},
    "Funk":       {"jamendo_tags": ["funk"],                "max_tracks": 200},
    "Jazz":       {"jamendo_tags": ["jazz", "acidjazz"],    "max_tracks": 200},
    "Latin":      {"jamendo_tags": ["latin", "bossanova"],  "max_tracks": 200},
    "R&B":        {"jamendo_tags": ["rnb", "soul"],         "max_tracks": 49},
}


# ============================================================
# Step 1: PREPARE — 전체 후보 트랙 선별 (가용 트랙 전부)
# ============================================================

def prepare_metadata():
    if not GENRE_TSV.exists():
        print(f"❌ {GENRE_TSV} 없음")
        print("   cd scripts && git clone --depth 1 https://github.com/MTG/mtg-jamendo-dataset.git")
        return

    print("📂 장르 메타데이터 로딩...")
    tracks_by_tag = defaultdict(list)
    with open(GENRE_TSV, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        for row in reader:
            track_id = row[0]
            path = row[3]
            duration = float(row[4])
            tag = row[5].strip().replace("\r", "").replace("genre---", "")
            jamendo_id = path.split("/")[-1].replace(".mp3", "")
            tracks_by_tag[tag].append({
                "mtg_track_id": track_id,
                "jamendo_id": jamendo_id,
                "path": path,
                "duration": duration,
                "jamendo_tag": tag,
            })

    print("📂 트랙 메타 로딩...")
    track_meta = {}
    if META_TSV.exists():
        with open(META_TSV, "r") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for row in reader:
                track_meta[row[0]] = {
                    "track_name": row[3],
                    "artist_name": row[4],
                    "album_name": row[5],
                }

    print("\n🎯 전체 후보 트랙 선별 (장르별 가용 전부)...")
    candidates = {}
    total = 0

    for st_genre, config in SOUNDTAG_MAPPING.items():
        genre_tracks = []
        for jm_tag in config["jamendo_tags"]:
            genre_tracks.extend(tracks_by_tag.get(jm_tag, []))

        random.seed(42)
        random.shuffle(genre_tracks)

        for t in genre_tracks:
            meta = track_meta.get(t["mtg_track_id"], {})
            t["track_name"] = meta.get("track_name", "")
            t["artist_name"] = meta.get("artist_name", "")
            t["soundtag_genre"] = st_genre

        target = config["max_tracks"]
        avail = len(genre_tracks)
        total += avail
        print(f"  {st_genre:<15} 가용: {avail:>5}  (목표: {target})")
        candidates[st_genre] = genre_tracks

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 후보 트랙 저장: {METADATA_FILE}")
    print(f"   총 {total}개 후보, 16개 장르")
    print(f"\n다음: python jamendo_collector.py --validate")


# ============================================================
# Step 2: VALIDATE — API로 존재 여부 배치 체크
# ============================================================

def validate_tracks():
    if not METADATA_FILE.exists():
        print("❌ 먼저 --prepare 실행")
        return

    if not JAMENDO_CLIENT_ID:
        print("❌ JAMENDO_CLIENT_ID 필요! .env 확인")
        return

    with open(METADATA_FILE) as f:
        candidates = json.load(f)

    # 이미 validate된 결과가 있으면 이어서
    validated = {}
    already_checked = set()
    if VALIDATED_FILE.exists():
        with open(VALIDATED_FILE) as f:
            validated = json.load(f)
        for genre, tracks in validated.items():
            for t in tracks:
                already_checked.add(t["jamendo_id"])
        print(f"📋 이전 검증 결과 로드: {len(already_checked)}개 이미 체크됨")

    print(f"\n🔍 Jamendo API 존재 여부 체크 (배치 10개씩)...")

    for st_genre, config in SOUNDTAG_MAPPING.items():
        target = config["max_tracks"]
        genre_candidates = candidates.get(st_genre, [])

        # 이미 충분히 검증됨?
        existing_valid = len(validated.get(st_genre, []))
        if existing_valid >= target:
            print(f"  ✅ {st_genre:<15} 이미 {existing_valid}/{target} 확보")
            continue

        # 아직 체크 안 된 후보만
        unchecked = [t for t in genre_candidates if t["jamendo_id"] not in already_checked]
        if not unchecked:
            print(f"  ⚠️  {st_genre:<15} 후보 소진 ({existing_valid}/{target})")
            continue

        valid_tracks = validated.get(st_genre, [])
        need = target - len(valid_tracks)

        print(f"  🔍 {st_genre:<15} 추가 {need}곡 필요, 미체크 {len(unchecked)}곡...")

        # 배치 10개씩 API 호출
        batch_size = 10
        for i in range(0, len(unchecked), batch_size):
            if len(valid_tracks) >= target:
                break

            batch = unchecked[i:i + batch_size]
            ids = "+".join(t["jamendo_id"] for t in batch)

            try:
                url = (
                    f"{JAMENDO_API_BASE}/tracks/"
                    f"?client_id={JAMENDO_CLIENT_ID}"
                    f"&format=json&id={ids}"
                    f"&audioformat=mp32"
                )
                resp = requests.get(url, timeout=15)
                data = resp.json()

                if data["headers"]["status"] != "success":
                    time.sleep(1)
                    continue

                # 존재하는 트랙 ID 수집
                found_ids = set()
                download_allowed = {}
                for r in data["results"]:
                    rid = str(r["id"])
                    found_ids.add(rid)
                    download_allowed[rid] = r.get("audiodownload_allowed", True)

                for t in batch:
                    already_checked.add(t["jamendo_id"])
                    if t["jamendo_id"] in found_ids:
                        t["download_allowed"] = download_allowed.get(t["jamendo_id"], True)
                        if t["download_allowed"]:
                            t["download_url"] = (
                                f"https://prod-1.storage.jamendo.com/download/"
                                f"track/{t['jamendo_id']}/mp32/"
                            )
                        else:
                            t["download_url"] = (
                                f"https://prod-1.storage.jamendo.com/"
                                f"?trackid={t['jamendo_id']}&format=mp32"
                            )
                        valid_tracks.append(t)

                time.sleep(0.3)  # rate limit

            except Exception as e:
                print(f"    ⚠️  배치 에러: {e}")
                time.sleep(2)

        validated[st_genre] = valid_tracks[:target]  # 목표까지만
        found = len(validated[st_genre])
        status = "✅" if found >= target else "⏳"
        print(f"  {status} {st_genre:<15} {found}/{target}")

        # 중간 저장
        with open(VALIDATED_FILE, "w") as f:
            json.dump(validated, f, ensure_ascii=False, indent=2)

    # 최종 결과
    print(f"\n{'='*50}")
    total_valid = sum(len(v) for v in validated.values())
    total_target = sum(c["max_tracks"] for c in SOUNDTAG_MAPPING.values())
    print(f"✅ 검증 완료: {total_valid}/{total_target}")
    print(f"   저장: {VALIDATED_FILE}")
    print(f"\n다음: python jamendo_collector.py --download")


# ============================================================
# Step 3: DOWNLOAD — 검증된 트랙만 다운로드
# ============================================================

def download_tracks(max_per_session=None):
    if not VALIDATED_FILE.exists():
        print("❌ 먼저 --validate 실행")
        return

    with open(VALIDATED_FILE) as f:
        validated = json.load(f)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # 전체 다운로드 목록
    all_tracks = []
    for genre, tracks in validated.items():
        genre_folder = genre.replace(" ", "_").replace("&", "and")
        (AUDIO_DIR / genre_folder).mkdir(parents=True, exist_ok=True)
        for t in tracks:
            t["_genre_folder"] = genre_folder
            all_tracks.append(t)

    # 이미 다운로드된 거 스킵
    existing = set()
    for mp3 in AUDIO_DIR.rglob("*.mp3"):
        if mp3.stat().st_size > 100_000:
            existing.add(mp3.stem)

    remaining = [t for t in all_tracks if t["jamendo_id"] not in existing]

    print(f"📥 다운로드: {len(remaining)}/{len(all_tracks)} (완료: {len(existing)})")

    if max_per_session:
        remaining = remaining[:max_per_session]
        print(f"   이번 세션: {len(remaining)}곡")

    success = 0
    failed = []

    for track in tqdm(remaining, desc="다운로드 중"):
        output_path = AUDIO_DIR / track["_genre_folder"] / f"{track['jamendo_id']}.mp3"

        try:
            resp = requests.get(track["download_url"], timeout=60, stream=True)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                if output_path.stat().st_size < 100_000:
                    output_path.unlink()
                    failed.append((track["jamendo_id"], "파일 너무 작음"))
                else:
                    success += 1
            else:
                failed.append((track["jamendo_id"], f"HTTP {resp.status_code}"))

            time.sleep(0.3)

        except Exception as e:
            failed.append((track["jamendo_id"], str(e)))

    print(f"\n✅ 다운로드 완료: {success}/{len(remaining)}")
    if failed:
        print(f"❌ 실패: {len(failed)}개")
        for jid, reason in failed[:10]:
            print(f"   - {jid}: {reason}")

    _print_status(validated)


def _print_status(validated=None):
    if validated is None:
        if not VALIDATED_FILE.exists():
            print("❌ 먼저 --validate 실행")
            return
        with open(VALIDATED_FILE) as f:
            validated = json.load(f)

    print("\n📊 장르별 현황:")
    total_target = 0
    total_done = 0

    for genre in SOUNDTAG_MAPPING:
        target = SOUNDTAG_MAPPING[genre]["max_tracks"]
        validated_count = len(validated.get(genre, []))
        genre_folder = genre.replace(" ", "_").replace("&", "and")
        genre_dir = AUDIO_DIR / genre_folder
        downloaded = len([f for f in genre_dir.glob("*.mp3") if f.stat().st_size > 100_000]) if genre_dir.exists() else 0

        total_target += target
        total_done += downloaded
        status = "✅" if downloaded >= target else ("⏳" if downloaded > 0 else "❌")
        bar = "█" * int(downloaded / max(target, 1) * 20)
        print(f"  {status} {genre:<15} {downloaded:>4}/{target:<4} 검증:{validated_count:<4} {bar}")

    print(f"\n  총합: {total_done}/{total_target}")
    if total_done > 0:
        size_mb = sum(f.stat().st_size for f in AUDIO_DIR.rglob("*.mp3")) / (1024 * 1024)
        print(f"  용량: {size_mb:.0f} MB ({size_mb/1024:.1f} GB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MTG-Jamendo → SoundTag v2")
    parser.add_argument("--prepare", action="store_true", help="Step 1: 후보 트랙 선별")
    parser.add_argument("--validate", action="store_true", help="Step 2: API 존재 여부 체크")
    parser.add_argument("--download", action="store_true", help="Step 3: 오디오 다운로드")
    parser.add_argument("--status", action="store_true", help="현황 확인")
    parser.add_argument("--max", type=int, default=None, help="이번 세션 최대 다운로드 수")

    args = parser.parse_args()

    if args.prepare:
        prepare_metadata()
    elif args.validate:
        validate_tracks()
    elif args.download:
        download_tracks(max_per_session=args.max)
    elif args.status:
        _print_status()
    else:
        parser.print_help()
