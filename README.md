# SoundTag

> K-pop 프로듀서를 위한 데모 평가 · 레퍼런스 추천 시스템
> A demo-evaluation and reference-recommendation system for K-pop producers

미등록 데모를 업로드하면 음원을 분리하고, 장르·에너지·무드를 분석해 발매곡 중
적절한 레퍼런스를 추천합니다. 핵심 목표는 "장르 분류"가 아니라 **창의적 조합의
질 평가**입니다 — 레퍼런스에서 유사도가 너무 높으면 오히려 탈락 신호로 봅니다.

---

## 이 프로젝트의 핵심 — 가짜 신호를 의심하다

> **AI/ML 관점에서 이 저장소가 보여주는 것: 좋아 보이는 숫자를 의심하고,
> 측정 체계 자체의 결함을 진단해 방법론을 재설계한 과정.**

AST(Audio Spectrogram Transformer)로 장르 분류 모델을 5번 학습했습니다.
가장 높았던 validation accuracy는 **77.6%**였습니다. 처음엔 성능이 잘 나온다고
판단했습니다.

하지만 결과를 뜯어보니, 모델이 학습한 것은 '장르'가 아니라 **'데이터의 출처
유형'**이었습니다. 드럼루프(FSLD)와 풀트랙(Deezer)을 장르 라벨링 맞춰 한
데이터셋에 섞었는데, 모델은 구분하기 쉬운 **소스 특성**을 학습한 것입니다.
77.6%는 실력이 아니라 **source-type leakage에 의한 가짜 신호**였습니다.

![accuracy trajectory](experiments/accuracy_trajectory.png)

소스 갭을 한 겹씩 제거하자 정확도는 77.6% → 59% → 47.8% → 43.5% → 46%로
떨어졌습니다. **이 하락이 곧 발전입니다.** Train accuracy는 5번 내내 99%대에
고정 → 모델은 항상 학습 데이터를 외웠고, validation이 떨어진 건 인위적으로 새던
"소스 단서"가 사라졌기 때문입니다. 46%가 이 문제의 진짜 baseline입니다.

**근본 원인**은 단일 버그가 아니라 측정 체계의 결함이었습니다. 5번의 학습이 전부
학습 데이터 분포 내에서만 측정되어, 진짜 목표인 K-pop 성능은 한 번도 평가되지
않았습니다. **좋은 모델을 만들기 전에, 무엇을 성능이라 부를지부터 잘못 정의돼
있었던 것입니다.**

→ 전체 분석: **[experiments/experiment-log.md](experiments/experiment-log.md)**

---

## 재설계 — measurement-first

가짜 신호는 더 열심히 골라낸다고 막히지 않습니다. 애초에 새어 들어올 구멍을
구조로 닫아야 합니다. 그래서 세 가지를 도입했습니다.

1. **K-pop hold-out 평가셋** — K-pop 100곡을 섹션 단위로 멀티라벨 어노테이션
   (genres 1–3 + energy 1–5 + mood). 학습에 절대 쓰지 않으며, 모든 모델의
   유일한 성능 기준. → [md/labeling-guide.md](md/labeling-guide.md)
2. **반증 가능한 가설 프로토콜** — 모든 실험 전 1페이지 가설 문서 작성 →
   24시간 quick test → K-pop hold-out으로만 측정 → confusion matrix 분석.
3. **dual-model 아키텍처** — 소스 갭을 데이터로 섞지 않고 모델을 분리해 회피.

---

## 아키텍처

```
                  K-pop demo (audio)
                         │
                  Demucs separation
                ┌────────┴─────────┐
          drums stem          full mix
                │                  │
         ┌──────┼──────┐    ┌──────┼──────┐
         │   Model A   │    │   Model B   │
         │  drum-loop  │    │ full-track  │
         │ (hybrid v3) │    │  (Deezer)   │
         └──────┬──────┘    └──────┬──────┘
                └─────────┬─────────┘
                K-pop hold-out set
              (100 songs, single gate)
                         │
            Reference recommendation
           (CLAP similarity; too-high = reject)
```

소스 타입별로 모델을 분리한 것이 핵심 설계 결정입니다 — 한 모델에 섞으면
source-type leakage가 재발하기 때문입니다.

---

## 현재 상태 (Status)

| 구성 요소 | 상태 |
|---|---|
| AST 학습 파이프라인 (5회 실험 완료) | ✅ Done |
| source-type leakage 진단 + 분석 | ✅ Done |
| Model A (드럼루프, hybrid v3) | ✅ Done — Val 46.0% |
| Demucs stem 분리 파이프라인 | ✅ Done |
| K-pop hold-out 평가셋 — labeling guide | 🟡 In progress |
| Model B (풀트랙, Deezer) | 🔲 Planned |
| CLAP 레퍼런스 추천 | 🔲 Planned |

---

## 저장소 구조

```
experiments/   5회 학습 기록 · leakage 분석 · 노트북 (포트폴리오 핵심)
scripts/       수집기 · CLAP 임베딩 · 데이터 준비 · 분석 파이프라인
md/            설계 문서 (전략, 장르 택소노미, 라벨링 가이드, 모델 리서치)
data/          장르 택소노미 · 메타데이터 · 샘플 분석 결과
tests/         stem · 드럼 · 장르 분석 실험 스크립트
notebooks/     초기 AST 실험 노트북
```

> 학습 데이터(오디오), 모델 가중치(`*.pt`, 각 ~345MB), CLAP 임베딩(`*.npz`)은
> 용량·저작권 문제로 git에서 제외합니다. Kaggle 데이터셋(`soundtag-hybrid-v3`,
> `soundtag-kpop-previews` 등)과 코드로 재현 가능합니다.

---

## 핵심 학습 (Key Learnings)

- **Measurement before training** — 측정 기준이 틀려 있으면 모델을 아무리
  손봐도 의미가 없습니다. 5번의 실패는 전부 측정 체계의 결함에서 나왔습니다.
- **Data quality ≫ quantity** — 전문가가 태깅한 데이터(FSLD)가 검색으로
  긁어모은 데이터(Deezer)보다 적은 양으로 더 높은 recall을 냈습니다.
- **Source-type leakage** — 출처가 다른 데이터를 라벨만 맞춰 섞으면, 모델은
  장르가 아니라 데이터 출처를 학습합니다. 정확도가 높을수록 오히려 의심해야 합니다.
- **Falsifiable hypotheses** — 사전 가설이 없는 실험은 같은 실수를, 그것도
  보이지 않는 채로 반복합니다.

---

## 기술 스택

Python · PyTorch · AST · CLAP · Demucs · librosa · essentia · scikit-learn
Kaggle (T4 GPU) · Deezer / Freesound API

---

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # API 키 채우기

python scripts/soundtag.py <audio_file>    # 음원 분리 + 분석
```
