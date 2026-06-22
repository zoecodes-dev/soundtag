from msclap import CLAP
import numpy as np
import json
import time

print("CLAP 모델 로딩 중...")
clap = CLAP(version="2023", use_cuda=False)

# v3 taxonomy에서 clap_text 추출
with open("data/genre_taxonomy_v3.json", "r") as f:
    taxonomy = json.load(f)

genres = []
genre_names = []
genre_tiers = []

for category, cat_data in taxonomy.items():
    if category.startswith("_"):
        continue
    if "genres" not in cat_data:
        continue
    for genre_name, genre_info in cat_data["genres"].items():
        genre_names.append(genre_name)
        genres.append(genre_info["clap_text"])
        genre_tiers.append(genre_info.get("tier", 0))

print(f"총 {len(genres)}개 장르 임베딩 시작...")
print(f"  Tier 1: {genre_tiers.count(1)} | Tier 2: {genre_tiers.count(2)} | Tier 3: {genre_tiers.count(3)} | Tier 4: {genre_tiers.count(4)}")

# 배치 처리
batch_size = 50
all_embeddings = []
start = time.time()

for i in range(0, len(genres), batch_size):
    batch = genres[i:i+batch_size]
    emb = clap.get_text_embeddings(batch)
    all_embeddings.append(emb.detach().numpy())
    print(f"  {min(i+batch_size, len(genres))}/{len(genres)} 완료")

embeddings = np.concatenate(all_embeddings, axis=0)

# 임베딩 + 메타데이터 저장
np.save("data/genre_embeddings_v3.npy", embeddings)

metadata = {
    "version": "3.0",
    "genre_count": len(genres),
    "genre_names": genre_names,
    "genre_tiers": genre_tiers,
    "categories": {}
}
for category, cat_data in taxonomy.items():
    if category.startswith("_") or "genres" not in cat_data:
        continue
    metadata["categories"][category] = list(cat_data["genres"].keys())

with open("data/genre_metadata_v3.json", "w") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

elapsed = time.time() - start
print(f"\n완료! {elapsed:.1f}초 소요")
print(f"임베딩: data/genre_embeddings_v3.npy ({embeddings.shape})")
print(f"메타데이터: data/genre_metadata_v3.json")