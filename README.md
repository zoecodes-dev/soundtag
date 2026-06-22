# SoundTag

> 데모 하나 넣으면 모든 답이 나오는 **K-pop A&R 음악 분석 도구**

등록되지 않은 데모 상태의 곡을 업로드하면 음원을 분리하고, 161개 세부 장르(4-Tier 택소노미)로
분류하며, 프로덕션 특성을 분석한다. CLAP zero-shot의 한계를 넘기 위해 **CLAP 임베딩 + MLP 분류기**
구조를 직접 학습시키고, 부족한 장르 데이터는 합성 파이프라인으로 보강했다.

## 핵심 기능

| 영역 | 내용 |
|---|---|
| **음원 분리** | Demucs(Replicate API)로 vocals / drums / bass / other stem 분리 |
| **장르 분류** | CLAP 임베딩 추출 → MLP 분류기 학습 (161개 세부 장르, 4-Tier) |
| **데이터 수집** | Jamendo · Deezer · Freesound API 기반 장르별 오디오 수집기 |
| **합성 데이터** | 클린 stem에 K-pop 프로덕션 수준 이펙트를 적용하는 degradation 파이프라인 |
| **택소노미** | Every Noise at Once 6,043개 장르를 큐레이션한 자동 업데이트 체계 |

## 저장소 구조

```
scripts/     수집기 · CLAP 임베딩 · MLP 학습 · K-pop 믹서 등 핵심 파이프라인 코드
md/          설계 문서 (전략 v3, 장르 택소노미, degradation 파이프라인, 모델 리서치)
data/        장르 리스트 · 택소노미 · 메타데이터 · 샘플 분석 결과
tests/       stem · 드럼 · 장르 분석 실험 스크립트
notebooks/   AST 모델 실험 노트북
```

> 대용량/생성 산출물(임베딩 `*.npz/*.npy`, 학습 모델 `*.pkl`, 수집 음원 `*.zip`,
> stem/믹스 `*.wav/*.mp3`, 중간 생성 JSON)과 API 키(`.env`)는 저작권·용량 문제로
> git에서 제외된다. 모두 코드를 통해 재생성하는 구조다.

## 주요 문서

- [`md/soundtag-strategy-v3.md`](md/soundtag-strategy-v3.md) — 프로젝트 비전과 최종 전략
- [`md/model_research_day6.md`](md/model_research_day6.md) — CLAP zero-shot 한계 분석과 모델 선정
- [`md/kpop-degradation-pipeline.md`](md/kpop-degradation-pipeline.md) — 합성 학습 데이터 파이프라인
- [`md/genre-taxonomy-update-system.md`](md/genre-taxonomy-update-system.md) — 장르 택소노미 큐레이션

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # API 키 채우기

python scripts/soundtag.py <audio_file>    # 음원 분리 + 분석
```

## 기술 스택

Python · PyTorch · CLAP · Demucs · librosa · essentia · pedalboard · scikit-learn ·
Replicate / Jamendo / Deezer / Freesound API
