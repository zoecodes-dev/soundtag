"""
SoundTag - Genre MLP Classifier v2
===================================
장르별 수집 데이터(Trap__123.mp3 형태)의 CLAP 임베딩으로 학습.
파일명에서 장르 레이블 추출.

학습 후 K-pop 곡에 적용해서 장르 성분 분석.

사용법:
    python train_genre_mlp_v2.py
    python train_genre_mlp_v2.py --predict-kpop    # K-pop 곡에 적용
"""

import argparse
import json
import numpy as np
import pickle
from pathlib import Path
from collections import Counter

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, accuracy_score, top_k_accuracy_score
import warnings
warnings.filterwarnings("ignore")


def load_genre_embeddings(npz_path: str):
    """장르별 임베딩 로드 + 파일명에서 레이블 추출."""
    data = np.load(npz_path, allow_pickle=True)
    embeddings = data["embeddings"]
    filenames = list(data["filenames"])

    labels = []
    valid_indices = []
    for i, fname in enumerate(filenames):
        # 파일명 형태: Trap__12345.mp3 → "Trap"
        if "__" in fname:
            genre = fname.split("__")[0].replace("_", " ").replace("RandB", "R&B")
            labels.append(genre)
            valid_indices.append(i)

    valid_embeddings = embeddings[valid_indices]
    print(f"📦 Loaded {len(valid_embeddings)} embeddings with labels")
    print(f"   Classes: {len(set(labels))}")
    return valid_embeddings, labels, filenames


def train(embeddings, labels, epochs=200, test_size=0.2):
    """MLP 학습 + 평가."""
    le = LabelEncoder()
    y = le.fit_transform(labels)
    n_classes = len(le.classes_)
    class_names = list(le.classes_)

    # 분포
    print(f"\n📊 Dataset: {len(embeddings)} samples, {n_classes} classes")
    counter = Counter(labels)
    for genre, count in counter.most_common():
        print(f"   {genre:25s} {count}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, y, test_size=test_size, random_state=42, stratify=y
    )
    print(f"\n   Train: {len(X_train)}, Test: {len(X_test)}")

    # MLP
    print(f"\n🔧 Training MLP (epochs={epochs})...")
    mlp = MLPClassifier(
        hidden_layer_sizes=(512, 256, 128),
        activation="relu",
        solver="adam",
        max_iter=epochs,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=20,
        verbose=False,
        learning_rate_init=0.0005,
        batch_size=32,
    )
    mlp.fit(X_train, y_train)

    # 평가
    y_pred = mlp.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    y_proba = mlp.predict_proba(X_test)

    top3 = top_k_accuracy_score(y_test, y_proba, k=min(3, n_classes))
    top5 = top_k_accuracy_score(y_test, y_proba, k=min(5, n_classes))

    print(f"\n{'='*60}")
    print(f"📊 Results:")
    print(f"   Accuracy:       {acc:.1%}")
    print(f"   Top-3 Accuracy: {top3:.1%}")
    print(f"   Top-5 Accuracy: {top5:.1%}")
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names, zero_division=0))
    print(f"{'='*60}")

    return mlp, le, acc


def predict_kpop(mlp, le, kpop_npz: str, kpop_meta: str = None, top_k: int = 5):
    """학습된 모델로 K-pop 곡 장르 분석."""
    data = np.load(kpop_npz, allow_pickle=True)
    embeddings = data["embeddings"]
    filenames = list(data["filenames"])

    # 메타데이터 로드 — track_id로 매칭
    track_info = {}
    if kpop_meta and Path(kpop_meta).exists():
        with open(kpop_meta, "r") as f:
            meta = json.load(f)
        for t in meta.get("tracks", []):
            tid = t.get("track_id")
            if tid:
                track_info[str(tid)] = t

    # 파일명 → track_id 매칭 함수
    def get_track_meta(filename):
        # ATEEZ_1021374282.mp3 → "1021374282"
        name = filename.replace(".mp3", "")
        parts = name.rsplit("_", 1)
        if len(parts) == 2:
            return track_info.get(parts[1], {})
        return {}

    # 예측
    proba = mlp.predict_proba(embeddings)
    class_names = le.classes_

    print(f"\n🎵 K-pop 장르 분석 ({len(embeddings)} tracks)")
    print(f"{'='*60}")

    # 전체 통계: K-pop에서 가장 많이 감지되는 장르
    all_top1 = []
    results = []

    for i in range(len(embeddings)):
        top_indices = np.argsort(proba[i])[::-1][:top_k]
        top_genres = [(class_names[idx], float(proba[i][idx])) for idx in top_indices]
        all_top1.append(top_genres[0][0])

        meta = get_track_meta(filenames[i])
        results.append({
            "filename": filenames[i],
            "artist": meta.get("artist_name", "?"),
            "title": meta.get("title", "?"),
            "genres": [{"genre": g, "score": s} for g, s in top_genres],
        })

    # Top-1 분포
    top1_counter = Counter(all_top1)
    print(f"\n📊 K-pop 장르 성분 분포 (Top-1):")
    for genre, count in top1_counter.most_common():
        pct = count / len(embeddings) * 100
        bar = "█" * int(pct / 2)
        print(f"   {genre:25s} {count:4d} ({pct:5.1f}%) {bar}")

    # 샘플 출력
    print(f"\n📋 샘플 (처음 15곡):")
    for r in results[:15]:
        top3 = ", ".join(f"{g['genre']}({g['score']:.0%})" for g in r["genres"][:3])
        print(f"   {r['artist']} - {r['title']}")
        print(f"     → {top3}")

    # 저장
    with open("kpop_genre_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved: kpop_genre_analysis.json")

    return results


def main():
    parser = argparse.ArgumentParser(description="SoundTag Genre MLP v2")
    parser.add_argument("--embeddings", type=str, default="genre_clap_embeddings.npz")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--predict-kpop", action="store_true",
                        help="Apply model to K-pop embeddings")
    parser.add_argument("--kpop-embeddings", type=str, default="clap_embeddings_full.npz")
    parser.add_argument("--kpop-meta", type=str, default="clap_embeddings_full_meta.json")
    args = parser.parse_args()

    # 1. 학습
    embeddings, labels, filenames = load_genre_embeddings(args.embeddings)
    mlp, le, acc = train(embeddings, labels, epochs=args.epochs)

    # 모델 저장
    with open("genre_mlp_model.pkl", "wb") as f:
        pickle.dump({"mlp": mlp, "label_encoder": le}, f)
    print(f"💾 Model saved: genre_mlp_model.pkl")

    # 2. K-pop 예측 (옵션)
    if args.predict_kpop:
        if Path(args.kpop_embeddings).exists():
            predict_kpop(mlp, le, args.kpop_embeddings, args.kpop_meta)
        else:
            print(f"⚠️ K-pop embeddings not found: {args.kpop_embeddings}")


if __name__ == "__main__":
    main()
