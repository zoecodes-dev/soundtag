from msclap import CLAP
import numpy as np
import json
from genre_audio_profiles import GENRE_PROFILES, verify_genre_match

print("CLAP 모델 로딩 중...")
clap = CLAP(version="2023", use_cuda=False)

# 데이터 로드
embeddings = np.load("data/genre_embeddings_v3.npy")
with open("data/genre_metadata_v3.json") as f:
    meta = json.load(f)
with open("data/genre_taxonomy_v3.json") as f:
    taxonomy = json.load(f)
with open("data/analysis_report.json") as f:
    audio_features = json.load(f)

genre_names = meta["genre_names"]
genre_tiers = meta["genre_tiers"]

genre_to_category = {}
for cat, genres_list in meta["categories"].items():
    for g in genres_list:
        genre_to_category[g] = cat

# 1차: CLAP 매칭
print("1차: CLAP 텍스트-오디오 매칭...")
audio_emb = clap.get_audio_embeddings(["audio/test_song.mp3"])
audio_np = audio_emb.detach().numpy()

from numpy.linalg import norm
clap_scores = []
for i, emb in enumerate(embeddings):
    cos = np.dot(audio_np[0], emb) / (norm(audio_np[0]) * norm(emb))
    clap_scores.append(cos)

# Top 20 후보 추출
ranked = sorted(enumerate(clap_scores), key=lambda x: x[1], reverse=True)
top20 = ranked[:20]

# 2차: 오디오 feature 검증
print("2차: 오디오 프로필 검증...")
final_results = []
for i, clap_score in top20:
    name = genre_names[i]
    tier = genre_tiers[i]
    cat = genre_to_category.get(name, "?")

    audio_score, reasons = verify_genre_match(name, audio_features)

    if audio_score is not None:
        # CLAP 70% + Audio 30% 가중 결합
        combined = clap_score * 0.7 + audio_score * 0.3
    else:
        combined = clap_score * 0.85  # 프로필 없으면 CLAP만 약간 할인

    final_results.append({
        "name": name,
        "category": cat,
        "tier": tier,
        "clap_score": clap_score,
        "audio_score": audio_score,
        "combined_score": combined,
        "reasons": reasons
    })

# 최종 순위
final_results.sort(key=lambda x: x["combined_score"], reverse=True)

# 리포트 출력
print("\n" + "="*70)
print(f"GOT7 'Python' — 2차 검증 결과")
print(f"BPM: {audio_features['drum_bpm']} | Key: {audio_features['key']} | "
      f"Bass: {audio_features['stems']['bass']['prominence']}% | "
      f"Dance: {audio_features['danceability']:.2f}")
print("="*70)

for rank, r in enumerate(final_results[:15], 1):
    tier_label = {1: "Core", 2: "Adj", 3: "Det", 4: "Hor"}[r["tier"]]
    audio_str = f"{r['audio_score']:.2f}" if r['audio_score'] is not None else "n/a"
    print(f"\n#{rank}  {r['name']} [{r['category']}] T{r['tier']}({tier_label})")
    print(f"     CLAP: {r['clap_score']:.3f} | Audio: {audio_str} | Combined: {r['combined_score']:.3f}")
    for reason in r["reasons"]:
        print(f"     {reason}")
        
# Trap 계열 CLAP 순위 확인
print("\n" + "="*50)
print("=== Trap 계열 CLAP 원본 순위 (161개 중) ===")
trap_genres = ["Trap", "Atlanta Trap", "Drill", "Pluggnb", 
               "Trap Soul", "Phonk", "Drift Phonk", "Rage"]
for rank_idx, (i, sim) in enumerate(ranked, 1):
    name = genre_names[i]
    if name in trap_genres:
        print(f"  #{rank_idx}/161  {name}: {sim:.3f}")