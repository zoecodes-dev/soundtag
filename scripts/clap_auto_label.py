"""
SoundTag - CLAP Zero-Shot Genre Auto-Labeler
=============================================
이미 추출된 CLAP 임베딩(512d)에 161개 장르 텍스트 임베딩을 매칭해서
auto-label을 생성.

전략:
  1. 장르명을 프롬프트 템플릿으로 감싸서 텍스트 임베딩 생성
  2. 오디오 임베딩 ↔ 텍스트 임베딩 cosine similarity 계산
  3. Top-K 장르 + confidence score로 auto-label

사용법:
    python clap_auto_label.py
    python clap_auto_label.py --top-k 5
    python clap_auto_label.py --tier 1    # Tier 1만
"""

import argparse
import json
import numpy as np
from pathlib import Path
from collections import Counter

# ─── Genre Taxonomy v3 (161개, 4-Tier) ─────────────────
# project-reference.md 기반
GENRE_TAXONOMY = {
    # ── Tier 1: Core (K-pop 타이틀곡 직접 차용) ──
    "Dance Pop": 1, "Electropop": 1, "Synth-pop": 1, "Tropical House": 1,
    "Future Bass": 1, "Trap": 1, "Pop R&B": 1, "K-R&B": 1,
    "Hip Hop": 1, "EDM": 1, "Moombahton": 1, "City Pop": 1,
    "Disco": 1, "Nu-Disco": 1, "Funk Pop": 1, "Latin Pop": 1,
    "Reggaeton": 1, "Pop Rock": 1, "Ballad": 1, "Contemporary R&B": 1,
    "New Jack Swing": 1, "UK Garage": 1, "Jersey Club": 1,
    "Afrobeats": 1, "Drill": 1, "Hyperpop": 1, "Bedroom Pop": 1,

    # ── Tier 2: Adjacent (B사이드/프로덕션 요소 차용) ──
    "Deep House": 2, "Tech House": 2, "Progressive House": 2,
    "Drum and Bass": 2, "Dubstep": 2, "Hardstyle": 2,
    "Lo-fi Hip Hop": 2, "Boom Bap": 2, "Trap Soul": 2,
    "Cloud Rap": 2, "Phonk": 2, "Emo Rap": 2,
    "Neo Soul": 2, "Alternative R&B": 2, "Quiet Storm": 2,
    "Indie Pop": 2, "Dream Pop": 2, "Shoegaze": 2,
    "Post-Punk": 2, "Indie Rock": 2, "Math Rock": 2,
    "Jazz Hop": 2, "Smooth Jazz": 2, "Acid Jazz": 2,
    "Bossa Nova": 2, "MPB": 2, "Samba": 2,
    "Dancehall": 2, "Soca": 2, "Zouk": 2,
    "Bachata": 2, "Cumbia": 2, "Merengue": 2,
    "Salsa": 2, "Dembow": 2, "Reggae": 2,
    "Trip-Hop": 2, "Downtempo": 2, "Chillwave": 2,
    "Synthwave": 2, "Vaporwave": 2, "Future Funk": 2,
    "Garage Rock": 2, "Surf Rock": 2, "Psychedelic Rock": 2,
    "Grunge": 2, "Emo": 2, "Pop Punk": 2,
    "Power Ballad": 2, "Adult Contemporary": 2,
    "Gospel": 2, "CCM": 2,
    "Amapiano": 2, "Gqom": 2, "Afro House": 2,
    "J-Pop": 2, "J-Rock": 2, "Visual Kei": 2,
    "Anime OST": 2, "Future Core": 2,
    "Country Pop": 2, "Folk Pop": 2,
    "Trot": 2, "Pansori": 2,
    "Baile Funk": 2, "Pagode": 2,
    "Bollywood": 2, "Bhangra": 2, "Filmi": 2,
    "C-Pop": 2, "Mandopop": 2,
    "Khaleeji": 2, "Mahraganat": 2, "Raï": 2,
    "Flamenco Pop": 2, "Turbo Folk": 2, "K-Indie": 2,
    "Europop": 2, "French Pop": 2,
    "Glitch Hop": 2, "Breakbeat": 2,
    "Electro Swing": 2, "Industrial": 2,
    "Minimal Techno": 2, "Trance": 2,
    "Gabber": 2,

    # ── Tier 3: Detection (분류 정확도용) ──
    "Heavy Metal": 3, "Death Metal": 3, "Black Metal": 3,
    "Thrash Metal": 3, "Doom Metal": 3,
    "Classical": 3, "Opera": 3, "Orchestral": 3,
    "Bluegrass": 3, "Americana": 3,
    "Blues Rock": 3, "Delta Blues": 3,
    "Ska": 3, "Punk Rock": 3, "Hardcore Punk": 3,
    "Free Jazz": 3, "Bebop": 3,
    "Noise": 3, "Drone": 3,
    "Gregorian Chant": 3, "Medieval": 3,
    "Polka": 3, "Klezmer": 3,
    "Throat Singing": 3, "Gamelan": 3,
    "Qawwali": 3, "Ghazal": 3,
    "Mariachi": 3, "Norteño": 3,
    "Fado": 3, "Rebetiko": 3,

    # ── Tier 4: Horizon (미개척, A&R 새 영감) ──
    "Alté": 4, "Gengetone": 4, "Kuduro": 4,
    "Balearic Beat": 4, "Organic House": 4,
    "Folktronica": 4, "Neo-Classical": 4,
    "Dark Pop": 4, "Witch House": 4,
    "PC Music": 4, "Deconstructed Club": 4,
    "Solarpunk": 4, "Healing Music": 4,
    "ASMR Pop": 4,
}

# 프롬프트 템플릿 (CLAP 성능 개선용)
PROMPT_TEMPLATES = [
    "This is a {} song",
    "A {} music track",
    "This song is in the {} genre",
]


def load_clap_model():
    """CLAP 모델 로드 (텍스트 임베딩용)."""
    import laion_clap
    model = laion_clap.CLAP_Module(enable_fusion=False)
    model.load_ckpt()
    print("  ✅ CLAP model loaded")
    return model


def build_genre_text_embeddings(model, genres: dict, templates: list):
    """장르명 → 텍스트 임베딩 (여러 템플릿 평균)."""
    genre_names = list(genres.keys())
    all_embeddings = []

    for template in templates:
        prompts = [template.format(g) for g in genre_names]
        emb = model.get_text_embedding(prompts, use_tensor=False)
        all_embeddings.append(emb)

    # 템플릿별 임베딩 평균
    avg_embeddings = np.mean(all_embeddings, axis=0)  # (N_genres, dim)

    # L2 정규화
    norms = np.linalg.norm(avg_embeddings, axis=1, keepdims=True)
    avg_embeddings = avg_embeddings / norms

    print(f"  📝 Built text embeddings for {len(genre_names)} genres")
    print(f"     Shape: {avg_embeddings.shape}")
    print(f"     Templates used: {len(templates)}")

    return genre_names, avg_embeddings


def auto_label(audio_embeddings, genre_names, genre_text_embeddings, top_k=5):
    """오디오 임베딩에 장르 auto-label."""
    # 오디오 임베딩 L2 정규화
    norms = np.linalg.norm(audio_embeddings, axis=1, keepdims=True)
    audio_norm = audio_embeddings / norms

    # Cosine similarity: (N_tracks, N_genres)
    similarities = audio_norm @ genre_text_embeddings.T

    results = []
    for i in range(len(audio_embeddings)):
        scores = similarities[i]
        top_indices = np.argsort(scores)[::-1][:top_k]

        top_genres = []
        for idx in top_indices:
            top_genres.append({
                "genre": genre_names[idx],
                "tier": GENRE_TAXONOMY[genre_names[idx]],
                "score": float(scores[idx]),
            })
        results.append(top_genres)

    return results


def main():
    parser = argparse.ArgumentParser(description="SoundTag CLAP Auto-Labeler")
    parser.add_argument("--embeddings", type=str, default="clap_embeddings.npz")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--tier", type=int, default=None,
                        help="Filter by tier (1, 2, 3, 4)")
    parser.add_argument("--output", type=str, default="auto_labels.json")
    args = parser.parse_args()

    # 1. 오디오 임베딩 로드
    data = np.load(args.embeddings, allow_pickle=True)
    audio_embeddings = data["embeddings"]
    filenames = list(data["filenames"])
    print(f"📦 Loaded {len(audio_embeddings)} audio embeddings (dim={audio_embeddings.shape[1]})")

    # 메타데이터 로드
    meta_path = args.embeddings.replace(".npz", "_meta.json")
    track_meta = {}
    if Path(meta_path).exists():
        with open(meta_path, "r") as f:
            meta = json.load(f)
        for t in meta.get("tracks", []):
            fname = t.get("filename", "")
            if fname:
                track_meta[fname] = t

    # 2. 장르 필터 (tier)
    genres = GENRE_TAXONOMY
    if args.tier:
        genres = {k: v for k, v in genres.items() if v == args.tier}
        print(f"  🎯 Filtered to Tier {args.tier}: {len(genres)} genres")
    else:
        print(f"  🎯 All tiers: {len(genres)} genres")

    # 3. CLAP 모델 로드 + 텍스트 임베딩
    print("\n🔧 Loading CLAP model...")
    model = load_clap_model()

    print("\n📝 Building genre text embeddings...")
    genre_names, genre_text_emb = build_genre_text_embeddings(
        model, genres, PROMPT_TEMPLATES
    )

    # 4. Auto-label
    print(f"\n🏷️  Auto-labeling {len(audio_embeddings)} tracks (top-{args.top_k})...")
    results = auto_label(audio_embeddings, genre_names, genre_text_emb, top_k=args.top_k)

    # 5. 결과 분석
    print(f"\n{'='*60}")
    print(f"📊 Auto-Label 결과 분석")

    # Top-1 장르 분포
    top1_genres = [r[0]["genre"] for r in results]
    top1_counter = Counter(top1_genres)
    print(f"\n  Top-1 장르 분포 (상위 15):")
    for genre, count in top1_counter.most_common(15):
        tier = GENRE_TAXONOMY[genre]
        pct = count / len(results) * 100
        bar = "█" * int(pct / 2)
        print(f"    T{tier} {genre:25s} {count:4d} ({pct:5.1f}%) {bar}")

    # Top-1 confidence 분포
    top1_scores = [r[0]["score"] for r in results]
    print(f"\n  Top-1 confidence: mean={np.mean(top1_scores):.3f}, "
          f"median={np.median(top1_scores):.3f}, "
          f"min={np.min(top1_scores):.3f}, max={np.max(top1_scores):.3f}")

    # Tier 분포
    tier_counter = Counter(GENRE_TAXONOMY[g] for g in top1_genres)
    print(f"\n  Tier 분포:")
    for tier in sorted(tier_counter.keys()):
        count = tier_counter[tier]
        print(f"    Tier {tier}: {count} tracks ({count/len(results)*100:.1f}%)")

    # 6. 샘플 출력
    print(f"\n  📋 샘플 결과 (처음 10곡):")
    for i in range(min(10, len(results))):
        fname = filenames[i]
        meta = track_meta.get(fname, {})
        title = meta.get("title", fname)
        artist = meta.get("artist_name", "?")
        top3 = ", ".join(f"{r['genre']}({r['score']:.2f})" for r in results[i][:3])
        print(f"    {artist} - {title}")
        print(f"      → {top3}")

    # 7. 저장
    output_data = {
        "total_tracks": len(results),
        "total_genres": len(genre_names),
        "top_k": args.top_k,
        "tier_filter": args.tier,
        "labels": [],
    }
    for i, (fname, result) in enumerate(zip(filenames, results)):
        meta = track_meta.get(fname, {})
        output_data["labels"].append({
            "filename": fname,
            "track_id": meta.get("track_id"),
            "title": meta.get("title", ""),
            "artist_name": meta.get("artist_name", ""),
            "top_genres": result,
        })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved: {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
