"""
SoundTag - K-pop 데이터 정리
============================
오매칭 아티스트 제거, 비K-pop 피처링곡 필터링.

사용법:
    python clean_kpop_data.py
"""

import json
from pathlib import Path
from collections import Counter

# ─── 제거할 아티스트 (오매칭 or 비K-pop) ──────────────
REMOVE_ARTISTS = {
    # 완전 오매칭
    "GeniusVybz",         # IU 검색에 딸려온 다른 아티스트
    "Blue Kaufman",       # IU 관련 오매칭
    "kobasolo",           # IU 관련 오매칭
    "Lil Durk",           # Stray Kids 콜라보로 딸려옴
    "Alesso",             # Stray Kids 콜라보
    "Jason Derulo",       # BTS 리믹스
    "Lady Gaga",          # BLACKPINK 콜라보
    "Ellie Goulding",     # Red Velvet 리믹스
    "Pabllo Vittar",      # 비K-pop
    "Dimitri Vegas",      # 비K-pop
    "DJ Snake",           # 비K-pop
    "Lauv",               # 비K-pop
    "League Of Legends",  # 게임 OST
    "K/DA",               # 게임 가상그룹
    "VALORANT",           # 게임
    "Bryan Chase",        # 비K-pop
    "Robin x",            # 비K-pop
    "MENOR HG",           # 비K-pop
    "Stayc",              # aespa Whiplash 인스트가 잘못 매칭
    "Lolo Zouaï",         # BIBI 리믹스
    "jxng__ssxng",        # NewJeans 커버/비공식
    "benny blanco",       # BTS 콜라보
    "Moon",               # 비K-pop
}

# 의심스러운 아티스트 (곡 제목으로 추가 필터링)
SUSPICIOUS_ARTISTS = {
    "IU": {
        # 진짜 IU 곡이 아닌 것 제거
        "remove_titles": ["Naalungiaq annaasisoq", "Bhagoda", "Kaikai Kitan (BIGVAVE ver.)"],
    },
    "Jung Kook": {
        # 힌디어 곡 제거
        "remove_titles": ["लूच्ची तोपे विसवास", "जिसम में लगरी आग"],
    },
    "Zico": {
        # 스페인어 곡 = 다른 Zico. 한국어/영어 제목만 유지
        "remove_non_korean_english": True,
    },
}

# 한국어/영어/일본어 문자 판별
def is_kpop_title(title: str) -> bool:
    """한국어, 영어, 일본어가 포함된 제목인지 확인."""
    for ch in title:
        # 한글
        if '\uac00' <= ch <= '\ud7a3' or '\u3131' <= ch <= '\u3163':
            return True
        # 일본어 (히라가나/카타카나)
        if '\u3040' <= ch <= '\u309f' or '\u30a0' <= ch <= '\u30ff':
            return True
    # 영어/숫자만으로 된 제목도 K-pop일 수 있음
    ascii_chars = sum(1 for ch in title if ch.isascii())
    if ascii_chars / max(len(title), 1) > 0.7:
        return True
    return False


def clean_data(input_path: str, output_path: str = None):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_count = len(data["tracks"])
    print(f"📦 Original: {original_count} tracks")

    cleaned = []
    removed = {"artist_blocked": 0, "title_blocked": 0, "non_korean": 0}

    for t in data["tracks"]:
        artist = t.get("artist_name", "")

        # 1. 아티스트 완전 제거
        if artist in REMOVE_ARTISTS:
            removed["artist_blocked"] += 1
            continue

        # 2. 의심스러운 아티스트 — 곡별 필터
        if artist in SUSPICIOUS_ARTISTS:
            config = SUSPICIOUS_ARTISTS[artist]

            # 특정 곡 제거
            if t.get("title") in config.get("remove_titles", []):
                removed["title_blocked"] += 1
                continue

            # 비한국어 곡 제거
            if config.get("remove_non_korean_english"):
                if not is_kpop_title(t.get("title", "")):
                    removed["non_korean"] += 1
                    continue

        cleaned.append(t)

    # 결과
    print(f"\n🧹 Removed:")
    print(f"   Artist blocked: {removed['artist_blocked']}")
    print(f"   Title blocked:  {removed['title_blocked']}")
    print(f"   Non-Korean:     {removed['non_korean']}")
    print(f"\n✅ Cleaned: {len(cleaned)} tracks (removed {original_count - len(cleaned)})")

    # 아티스트별 분포
    artist_counter = Counter(t["artist_name"] for t in cleaned)
    print(f"\n📊 아티스트별 곡수 (정리 후):")
    for artist, count in artist_counter.most_common():
        print(f"   {artist:25s} {count:3d}")

    # 저장
    if not output_path:
        output_path = input_path.replace(".json", "_cleaned.json")

    data["tracks"] = cleaned
    data["metadata"]["total_tracks"] = len(cleaned)
    data["metadata"]["unique_artists"] = len(artist_counter)
    data["metadata"]["cleaned"] = True

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved: {output_path}")
    return output_path


def main():
    # 가장 최신 Deezer JSON 찾기
    deezer_dir = Path("./deezer_data")
    json_files = sorted(deezer_dir.glob("kpop_tracks_*.json"))
    if not json_files:
        print("❌ No Deezer JSON found in ./deezer_data/")
        return

    # _cleaned가 아닌 원본만
    originals = [f for f in json_files if "_cleaned" not in f.name]
    if not originals:
        print("❌ No original JSON found")
        return

    input_path = str(originals[-1])
    print(f"📂 Input: {input_path}")
    clean_data(input_path)


if __name__ == "__main__":
    main()
