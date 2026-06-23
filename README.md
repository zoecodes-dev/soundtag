# SoundTag

> K-pop 프로듀서를 위한 **데모 평가 + 레퍼런스 추천** 시스템

미발매 데모를 업로드하면 음원을 분리·분석하고, 발매곡 레퍼런스와 비교한다.
목표는 단순 "장르 분류"가 아니라 **창의적 조합의 질 평가**다 — 기존 레퍼런스와
유사도가 *너무 높으면*(=흔한 조합이면) 오히려 낮게 평가한다. 분류·분석은 그
평가를 떠받치는 기술 구성 요소다.

---

## 핵심 엔지니어링 결정 — "좋아 보이는 정확도를 의심한다"

이 프로젝트의 중심은 모델 한 개를 잘 만든 이야기가 아니라, **측정 체계의 결함을
발견하고 방법론을 다시 설계한 과정**이다.

- **증상** — 장르 분류 모델을 5번 학습했지만, 5번 모두 *학습 데이터 분포 안에서만*
  측정되었다. 가장 높았던 점수는 hybrid v1의 검증 정확도 **77.6%**였다.
- **진단** — 이 77.6%는 가짜 신호였다. 모델은 *장르*가 아니라 *데이터 출처*를 학습하고
  있었다(**source-type leakage**). 같은 장르라도 FSLD(wav)와 Freesound(mp3)는
  인코딩·길이·녹음 특성이 달라서, 모델이 그 출처 차이를 장르 신호로 오인했다.
- **근본 원인** — 진짜 문제는 모델이 아니라 측정이었다. **타겟 도메인인 K-pop 성능을
  실제 K-pop 데이터로 단 한 번도 측정한 적이 없었다.** 검증셋이 학습셋과 같은 출처에서
  나왔기 때문에, 구조적으로 leakage를 잡아낼 수 없는 측정 체계였다.
- **해결** —
  1. **출처 분리(dual-model)** — 입력 종류(드럼루프 / 풀트랙)별로 모델을 나눠, 한 모델
     안에서 출처가 섞이지 않게 한다.
  2. **K-pop hold-out 평가셋** — 학습에 한 번도 쓰지 않은 실제 K-pop 100곡을
     section-level로 라벨링해, 모든 측정을 이 셋으로만 한다.
  3. **가설 프로토콜** — 모든 실험 전에 falsifiable 가설을 1페이지로 문서화하고,
     K-pop hold-out + confusion matrix로만 검증한다.

> 5번의 실험은 버려진 시간이 아니라, 공통 원인(source-type leakage)을 진단하기 위한
> 분석 자산이다. → 자세한 근거: [`md/measurement-and-hypothesis-protocol.md`](md/measurement-and-hypothesis-protocol.md)

---

## 아키텍처 — Dual-Model

출처가 다른 오디오를 한 모델에 섞으면 source-type leakage가 발생한다. 그래서 **입력
종류별로 모델 자체를 분리**한다 — 이것이 핵심 설계 결정이다.

| 모델 | 대상 | 학습 데이터 | 추론 입력 | 분류 근거 |
|---|---|---|---|---|
| **Model A** | 드럼루프 | Hybrid v3 (FSLD + Freesound, 19 genres) | Demucs `drums` stem | 리듬 · 그루브 |
| **Model B** | 풀트랙 | Deezer 30초 프리뷰 819곡 *(planned)* | 원본 풀믹스 | 화성 · 음색 · 편곡 |

- **Model A**는 추론 시 입력곡을 Demucs로 분리한 `drums` stem만 받는다. 드럼 사운드만
  남기므로 출처별 풀믹스 특성에 휘둘리지 않는다.
- **Model B**는 풀믹스 전체를 받아 화성·편곡 차원을 담당한다(학습 예정).
- 두 모델을 합치지 않은 이유 = **source-type leakage 회피**. 하나의 모델에 드럼루프와
  풀트랙을 함께 넣으면, 다시 "장르가 아니라 입력 종류"를 학습하게 된다.

---

## 현재 상태

| 항목 | 상태 |
|---|---|
| Demucs stem 분리 + librosa/Essentia 분석 (`soundtag.py`) | ✅ done |
| Hybrid v3 드럼루프 데이터셋 구축 (19 genres) | ✅ done |
| Model A (드럼루프, AST fine-tune) 학습 | ✅ done |
| source-type leakage 진단 + 측정 프로토콜 수립 | ✅ done |
| Model B (풀트랙, Deezer 819곡) 학습 | 🔲 planned |
| K-pop hold-out 100곡 section-level 라벨링 | 🟡 in progress (템플릿/가이드 단계) |
| 레퍼런스 추천 + 유사도 기반 질 평가 통합 | 🔲 planned |

---

## 기술 스택

- **모델** — AST (Audio Spectrogram Transformer) fine-tune · CLAP (임베딩 / 초기 실험)
- **음원 분리** — Demucs (`htdemucs`), Replicate API
- **오디오 분석** — librosa · Essentia (BPM · 키 · 댄서빌리티 · stem prominence)
- **학습** — PyTorch · torchaudio · HuggingFace Transformers (Kaggle / Colab GPU)
- **데이터 수집** — Deezer · Freesound · Jamendo API · FSLD

## 저장소 구조

```
scripts/     수집기 · 데이터셋 구축 · CLAP 임베딩 · MLP 학습 · K-pop 믹서 등 파이프라인 코드
md/          설계 · 측정 프로토콜 · 모델 리서치 · 과거 전략 기록 문서
data/        장르 택소노미 · 메타데이터 · K-pop hold-out 템플릿 · 샘플 분석 결과
notebooks/   AST 모델 학습 노트북 (Kaggle)
tests/       stem · 드럼 · 장르 분석 실험 스크립트
```

> 대용량/생성 산출물(임베딩 `*.npz/*.npy`, 학습 모델 `*.pkl`, 수집 음원 `*.zip`,
> stem/믹스 `*.wav/*.mp3`, 중간 생성 JSON)과 API 키(`.env`)는 저작권·용량 문제로
> git에서 제외된다. 모두 코드를 통해 재생성하는 구조다.

## 주요 문서

- [`md/measurement-and-hypothesis-protocol.md`](md/measurement-and-hypothesis-protocol.md)
  — **(핵심)** source-type leakage 진단 사례 · hold-out 설계 · 실험 가설 프로토콜
- [`md/model_research_day6.md`](md/model_research_day6.md) — CLAP zero-shot 한계 분석과
  모델 선정 (이후 AST → dual-model로 진화, 과거 기록)
- [`md/soundtag-strategy-v3.md`](md/soundtag-strategy-v3.md) — 초기 제품 비전과 전략
  (과거 기록)
- [`md/kpop-degradation-pipeline.md`](md/kpop-degradation-pipeline.md) — 합성 학습 데이터
  파이프라인 (초기 실험)
- [`md/genre-taxonomy-update-system.md`](md/genre-taxonomy-update-system.md) — 장르
  택소노미 큐레이션 (Taxonomy v3, 161 genres)

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # API 키 채우기

python scripts/soundtag.py <audio_file>    # 음원 분리 + 분석
```
