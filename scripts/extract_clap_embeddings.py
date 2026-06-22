"""
SoundTag - CLAP 임베딩 추출기
==============================
Deezer 프리뷰 MP3 → CLAP audio encoder → 1024차원 임베딩 벡터
나중에 MLP classifier 학습 + 유사곡 검색에 사용.

사용법:
    python extract_clap_embeddings.py                          # 기본
    python extract_clap_embeddings.py --preview-dir ./deezer_data/previews
    python extract_clap_embeddings.py --model music            # 음악 특화 모델
"""

import argparse
import json
import numpy as np
import os
import time
from pathlib import Path

# ─── CLAP 모델 로드 (첫 실행 시 체크포인트 자동 다운로드) ───
def load_clap_model(model_type: str = "default"):
    """CLAP 모델 로드."""
    import laion_clap

    if model_type == "music":
        # 음악 특화 모델 (더 큰 audio encoder)
        model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base')
        # 음악 특화 체크포인트가 있으면 로드 (없으면 기본 사용)
        ckpt_path = Path("music_audioset_epoch_15_esc_90.14.pt")
        if ckpt_path.exists():
            model.load_ckpt(str(ckpt_path))
            print(f"  ✅ Music model loaded: {ckpt_path}")
        else:
            model.load_ckpt()
            print(f"  ⚠️ Music checkpoint not found, using default.")
            print(f"     Download from: https://huggingface.co/lukewys/laion_clap/")
    else:
        model = laion_clap.CLAP_Module(enable_fusion=False)
        model.load_ckpt()
        print(f"  ✅ Default CLAP model loaded")

    return model


def extract_embeddings(
    model,
    preview_dir: str,
    metadata_json: str = None,
    output_path: str = "clap_embeddings.npz",
    batch_size: int = 16,
):
    """프리뷰 MP3들에서 CLAP 임베딩 추출."""
    preview_dir = Path(preview_dir)
    mp3_files = sorted(preview_dir.glob("*.mp3"))

    if not mp3_files:
        print(f"❌ No MP3 files found in {preview_dir}")
        return

    print(f"\n🎵 Found {len(mp3_files)} MP3 files in {preview_dir}")

    # 메타데이터 로드 (있으면)
    track_meta = {}
    if metadata_json:
        meta_path = Path(metadata_json)
        if meta_path.exists():
            with open(meta_path, "r") as f:
                data = json.load(f)
            tracks = data.get("tracks", [])
            for t in tracks:
                local_path = t.get("local_preview_path", "")
                if local_path:
                    fname = Path(local_path).name
                    track_meta[fname] = {
                        "track_id": t.get("track_id"),
                        "title": t.get("title"),
                        "artist_name": t.get("artist_name"),
                        "genre_id": t.get("genre_id"),
                    }
            print(f"  📋 Loaded metadata for {len(track_meta)} tracks")

    # 배치 처리
    all_embeddings = []
    all_filenames = []
    all_metadata = []
    errors = []

    total = len(mp3_files)
    start_time = time.time()

    for i in range(0, total, batch_size):
        batch_files = mp3_files[i:i + batch_size]
        batch_paths = [str(f) for f in batch_files]

        try:
            # CLAP audio embedding 추출
            embeddings = model.get_audio_embedding_from_filelist(
                batch_paths, use_tensor=False
            )
            # embeddings shape: (batch_size, 512) or (batch_size, 1024)

            for j, f in enumerate(batch_files):
                all_embeddings.append(embeddings[j])
                all_filenames.append(f.name)

                # 메타데이터 매칭
                meta = track_meta.get(f.name, {"filename": f.name})
                all_metadata.append(meta)

        except Exception as e:
            for f in batch_files:
                errors.append((f.name, str(e)))
            print(f"  ⚠️ Batch error at {i}: {e}")

        # 진행률
        done = min(i + batch_size, total)
        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        print(f"  [{done}/{total}] {rate:.1f} files/sec, ETA: {eta:.0f}s", end="\r")

    print(f"\n\n✅ Extracted {len(all_embeddings)} embeddings")
    if errors:
        print(f"  ⚠️ {len(errors)} errors")

    # 저장
    embeddings_array = np.array(all_embeddings)  # (N, dim)
    print(f"  Shape: {embeddings_array.shape}")
    print(f"  Embedding dim: {embeddings_array.shape[1]}")

    np.savez_compressed(
        output_path,
        embeddings=embeddings_array,
        filenames=np.array(all_filenames),
    )
    print(f"💾 Saved: {output_path} ({os.path.getsize(output_path) / 1024 / 1024:.1f} MB)")

    # 메타데이터 별도 저장
    meta_output = output_path.replace(".npz", "_meta.json")
    with open(meta_output, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(all_embeddings),
            "embedding_dim": int(embeddings_array.shape[1]),
            "errors": len(errors),
            "tracks": all_metadata,
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Metadata: {meta_output}")

    return embeddings_array, all_filenames, all_metadata


def main():
    parser = argparse.ArgumentParser(description="SoundTag CLAP Embedding Extractor")
    parser.add_argument("--preview-dir", type=str, default="./deezer_data/previews",
                        help="Directory with preview MP3s")
    parser.add_argument("--metadata", type=str, default=None,
                        help="Deezer JSON metadata file (for track info matching)")
    parser.add_argument("--output", type=str, default="clap_embeddings.npz",
                        help="Output .npz file")
    parser.add_argument("--model", type=str, default="default",
                        choices=["default", "music"],
                        help="CLAP model type")
    parser.add_argument("--batch-size", type=int, default=16,
                        help="Batch size for embedding extraction")
    args = parser.parse_args()

    # 메타데이터 자동 탐지
    if not args.metadata:
        deezer_dir = Path("./deezer_data")
        json_files = sorted(deezer_dir.glob("kpop_tracks_*.json"))
        if json_files:
            args.metadata = str(json_files[-1])  # 가장 최신
            print(f"  📋 Auto-detected metadata: {args.metadata}")

    print("🔧 Loading CLAP model...")
    model = load_clap_model(args.model)

    extract_embeddings(
        model,
        preview_dir=args.preview_dir,
        metadata_json=args.metadata,
        output_path=args.output,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
