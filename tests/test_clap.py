from msclap import CLAP
import numpy as np

print("CLAP 모델 로딩 중...")
clap = CLAP(version="2023", use_cuda=False)

# 원곡 임베딩
print("원곡 임베딩 생성 중...")
emb_full = clap.get_audio_embeddings(["test_song.mp3"])

# 각 stem 임베딩
stems = ["stems_vocals.mp3", "stems_drums.mp3", "stems_bass.mp3", "stems_other.mp3"]
print("Stem 임베딩 생성 중...")
emb_stems = clap.get_audio_embeddings(stems)

print(f"\n임베딩 차원: {emb_full.shape}")
# shape = (1, 1024) — 곡 하나가 1024차원 벡터로 표현됨

# CLAP의 강점: 텍스트로도 검색 가능
print("\n텍스트 유사도 테스트:")
genres = [
    "k-pop dance music with heavy bass",
    "trip-hop with slow drums",
    "trap beat with 808 bass",
    "r&b ballad with soft vocals",
    "edm drop with synthesizers",
    "jersey club with fast rhythm",
    "neo soul with jazz chords",
    "phonk with aggressive drums"
]

emb_text = clap.get_text_embeddings(genres)

# 코사인 유사도 계산
# np.dot = 두 벡터의 내적, np.linalg.norm = 벡터 크기
# 코사인 유사도가 1에 가까울수록 비슷한 것
similarities = []
for i, genre in enumerate(genres):
    sim = np.dot(emb_full[0], emb_text[i]) / (
        np.linalg.norm(emb_full[0]) * np.linalg.norm(emb_text[i])
    )
    similarities.append((genre, float(sim)))

# 유사도 높은 순으로 정렬
similarities.sort(key=lambda x: x[1], reverse=True)

for genre, sim in similarities:
    bar = "█" * int(sim * 50)
    print(f"  {sim:.3f} {bar} {genre}")