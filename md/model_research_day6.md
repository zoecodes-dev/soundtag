# SoundTag 오디오 분류 모델 리서치 — Day 6 (과거 기록, 2026-03-19)

> **📌 모델 선정 시점(Day 6)의 리서치 기록이다.** 아래 CLAP zero-shot 한계 분석은
> 유효한 자료지만, 이후 방향은 **AST 채택 → dual-model(Model A 드럼루프 /
> Model B 풀트랙)**로 진화했고, "161개 단일 분류" 전제도 바뀌었다.
> **최신 방향은 [`../README.md`](../README.md)와
> [`../experiments/experiment-log.md`](../experiments/experiment-log.md) 참조.**

## 문제 정의

SoundTag는 161개 세부 장르(4-Tier)로 K-pop 데모를 분류해야 한다.
현재 CLAP zero-shot은 텍스트 키워드 유사도에 끌려 Trap이 61위로 나오는 등 **근본적 한계**가 확인됨.

**필요 조건:**
- 161개 fine-grained 장르 분류 (trip-hop, UK garage 수준)
- 30초 오디오 입력
- K-pop = "모든 장르를 가져다 쓰는 장르" → multi-label 가능해야 함
- Colab Pro (A100/T4) 수준에서 학습 가능
- 학습 데이터: Deezer 30초 프리뷰 + 장르 레이블 (수천~수만 곡)

---

## 후보 모델 3가지

### Option A: CLAP Audio Encoder + Linear Probe

**개요:** CLAP의 audio encoder (HTSAT-base)를 feature extractor로 쓰고, 위에 MLP classifier를 얹어 fine-tune.

**장점:**
- 이미 CLAP 파이프라인 구축됨 — 전환 비용 최소
- Audio encoder가 음악 데이터(Music + AudioSet)로 pretrain되어 있음
- GTZAN에서 71% zero-shot → fine-tune 시 훨씬 높아질 것
- 임베딩 추출 후 lightweight classifier만 학습 → 빠르고 저렴
- 나중에 유사곡 검색에도 같은 임베딩 재활용 가능

**단점:**
- CLAP audio encoder는 10초 제한 (30초 → 청크 분할 필요)
- 텍스트 encoder 부분은 안 쓰게 됨 (zero-shot 포기)
- Fine-grained 음악 장르 구분에 최적화된 건 아님

**학습 전략:**
1. **Phase 1 — Linear Probe:** Audio encoder freeze → MLP만 학습 (빠름)
2. **Phase 2 — LoRA fine-tune:** Audio encoder에 LoRA 적용 (K-pop 도메인 적응)

**필요 리소스:** Colab Pro T4로 충분. 임베딩 추출: 곡당 <1초.

---

### Option B: AST (Audio Spectrogram Transformer) Fine-tuning

**개요:** ViT를 오디오 spectrogram에 적용한 모델. AudioSet pretrained → 우리 장르 데이터로 fine-tune.

**장점:**
- AudioSet에서 SOTA (0.485 mAP) — 가장 검증된 오디오 분류 모델
- HuggingFace Transformers 완전 통합 (코드 간결)
- Variable length input 지원
- Fine-tuning 가이드 풍부 (Renumics, TDS 블로그 등)
- Classification head만 교체하면 161 클래스 바로 적용

**단점:**
- CLAP과 달리 유사곡 검색용 임베딩으로 직접 쓰기 어려움
- 분류 전용 — 검색은 별도 시스템 필요
- Full fine-tune 시 A100 권장 (T4로도 가능하지만 느림)

**학습 전략:**
1. `MIT/ast-finetuned-audioset-10-10-0.4593` pretrained 로드
2. Classifier head를 161 클래스로 교체
3. Dataset 정규화 (mean/std 재계산 필수)
4. Learning rate warmup + cosine decay

**필요 리소스:** Colab Pro A100 1시간 내외 (수천 곡 기준).

---

### Option C: CLAP Full Fine-tuning (Audio + Text Encoder)

**개요:** CLAP 전체를 K-pop 장르 audio-text pair로 contrastive fine-tune.

**장점:**
- Zero-shot 능력 유지 — 새 장르 추가 시 학습 없이 텍스트만 추가
- 유사곡 검색과 분류를 하나의 모델로
- Taxonomy 자동 업데이트 시스템과 시너지

**단점:**
- Audio-text pair 데이터 필요 (장르명 → 설명 텍스트 생성 필요)
- 학습 비용 가장 높음 (V100/A100 필수, 대규모 배치)
- K-pop 161개 장르의 "좋은 텍스트 설명"을 만드는 게 핵심 병목
- 현재 CLAP의 한계가 audio encoder가 아니라 text-audio alignment에 있을 수 있음

**학습 전략:**
1. Genre taxonomy → Claude API로 장르별 상세 텍스트 설명 생성
2. Deezer 프리뷰 + 설명 텍스트로 contrastive learning
3. LoRA로 양쪽 encoder 동시 fine-tune

**필요 리소스:** Colab Pro A100 필수. 배치 사이즈가 핵심.

---

## 비교 요약

| 기준 | A: CLAP + Probe | B: AST Fine-tune | C: CLAP Full FT |
|------|----------------|-------------------|------------------|
| **학습 난이도** | ★☆☆ | ★★☆ | ★★★ |
| **학습 비용** | 낮음 (T4) | 중간 (A100) | 높음 (A100+) |
| **분류 성능 예상** | 중상 | 최상 | 중 (데이터 의존) |
| **유사곡 검색 재활용** | ✅ (임베딩) | ❌ (별도 필요) | ✅ (임베딩) |
| **새 장르 추가** | 재학습 필요 | 재학습 필요 | 텍스트만 추가 |
| **기존 코드 호환** | 높음 | 중간 | 높음 |
| **K-pop 적응** | LoRA Phase 2 | Full FT | LoRA 양쪽 |
| **Multi-label** | ✅ Sigmoid | ✅ Sigmoid | ✅ (자연스러움) |

---

## 추천: Option A → B 단계적 접근

### 이유

1. **Option A (CLAP + Linear Probe)부터 시작:**
   - 기존 CLAP 파이프라인과 호환
   - 가장 빠르게 baseline 확보 (임베딩 추출 → MLP 학습)
   - 유사곡 검색과 분류를 하나의 임베딩으로 처리
   - 결과가 부족하면 LoRA fine-tune으로 확장

2. **Option A 성능이 161개 장르에서 부족하면 → Option B 추가:**
   - AST를 분류 전용으로 도입
   - CLAP은 유사곡 검색용으로 유지
   - 두 모델 병렬 운용: AST(분류) + CLAP(검색/임베딩)

3. **Option C는 보류:**
   - 텍스트 설명 품질에 너무 의존
   - 현재 데이터 규모에서는 ROI 낮음
   - 데이터 1만곡+ 확보 후 재검토

### 구체적 다음 단계

```
Phase 0 (이번 주): Deezer 데이터 수집 + CLAP Linear Probe 실험
  ├─ Deezer API로 K-pop 곡 2,000~5,000개 수집 (프리뷰 + 장르)
  ├─ CLAP audio encoder로 임베딩 추출
  ├─ 161 장르 매핑 (Deezer 장르 → SoundTag taxonomy)
  └─ MLP classifier 학습 + 평가

Phase 1 (다음 주): 성능 평가 + 방향 결정
  ├─ A가 충분하면 → LoRA fine-tune으로 개선
  └─ A가 부족하면 → AST fine-tune 도입 (분류 전용)
```

---

## 참고: Deezer 장르 → SoundTag Taxonomy 매핑 이슈

Deezer API의 장르 체계는 매우 broad (Pop, Rap/Hip Hop, Rock, R&B 등 ~20개).
SoundTag는 161개 fine-grained 장르. 매핑 전략:

1. **Deezer 장르 = 대분류 레이블로 사용** (1차 필터)
2. **CLAP 임베딩 기반 fine-grained 분류** (2차)
3. **수동 레이블링** (소규모 검증 세트, 100~200곡)
4. **약한 레이블링 (weak supervision)**: Deezer 장르 + 아티스트 스타일 조합

---

*작성: Day 6 (2026-03-19)*
