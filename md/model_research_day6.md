# SoundTag 오디오 분류 모델 리서치 — Day 6 (과거 기록, 2026-03-19)

> **📌 모델을 고르던 시점(Day 6)의 리서치 기록입니다.** 아래 CLAP zero-shot
> 한계 분석은 지금도 유효한 자료지만, 이후 방향은 **AST 채택 → dual-model(Model
> A 드럼루프 / Model B 풀트랙)**로 진화했고 "161개 단일 분류"라는 전제도
> 바뀌었습니다. 최신 방향은 [`../README.md`](../README.md)와
> [`../experiments/experiment-log.md`](../experiments/experiment-log.md)를
> 보시면 됩니다.

## 무엇을 풀어야 하나

SoundTag은 K-pop 데모를 161개 세부 장르(4-Tier)로 분류해야 합니다. 지금 쓰고
있는 CLAP zero-shot은 텍스트 키워드 유사도에 끌려다니는 게 문제입니다 — Trap이
61위로 밀려나는 식의 결과가 나오는데, 이건 튜닝으로 넘길 수준이 아니라
**근본적인 한계**입니다. 텍스트-오디오 정렬에 기댄 zero-shot으로는 K-pop의
미세한 장르 구분을 잡을 수 없다는 신호입니다.

그래서 필요한 모델의 조건은 분명합니다. trip-hop이나 UK garage 수준까지 가르는
161개 fine-grained 분류를 30초 오디오 입력으로 해내야 하고, "모든 장르를 가져다
쓰는 장르"인 K-pop의 성격상 multi-label이 가능해야 합니다. 학습은 Colab
Pro(A100/T4) 수준에서 돌아가야 하고, 학습 데이터는 Deezer 30초 프리뷰 + 장르
레이블로 수천~수만 곡을 모을 수 있습니다.

---

## 후보 세 가지

이 조건을 놓고 세 갈래를 검토했습니다. CLAP을 최대한 재활용하는 길, 분류
전용으로 검증된 모델을 새로 들이는 길, 그리고 CLAP의 zero-shot까지 끝까지 끌고
가는 길입니다.

### Option A — CLAP Audio Encoder + Linear Probe

CLAP의 audio encoder(HTSAT-base)를 feature extractor로 고정해두고, 그 위에 MLP
classifier를 얹어 fine-tune하는 방식입니다. 가장 큰 매력은 **전환 비용이 거의
없다**는 점입니다 — 이미 CLAP 파이프라인이 깔려 있고, audio encoder가 Music +
AudioSet으로 pretrain돼 있으며, GTZAN에서 zero-shot 71%가 나오니 fine-tune하면
훨씬 올라갈 여지가 큽니다. 임베딩을 뽑아두고 가벼운 classifier만 학습하면 되니
빠르고 저렴하고, 그 임베딩을 나중에 유사곡 검색에 그대로 재활용할 수도 있습니다.

대신 약점도 분명합니다. CLAP audio encoder는 10초 제한이 있어 30초 입력은
청크로 쪼개야 하고, 텍스트 encoder는 안 쓰게 되니 zero-shot은 포기하는 셈이며,
애초에 fine-grained 음악 장르 구분에 최적화된 모델은 아닙니다.

학습은 두 단계로 갑니다. **Phase 1**은 audio encoder를 freeze한 채 MLP만 빠르게
학습하는 linear probe, **Phase 2**는 audio encoder에 LoRA를 적용해 K-pop
도메인에 적응시키는 단계입니다. 리소스는 Colab Pro T4로 충분하고 임베딩 추출은
곡당 1초 미만입니다.

### Option B — AST(Audio Spectrogram Transformer) Fine-tuning

ViT를 오디오 spectrogram에 적용한 모델로, AudioSet pretrained를 우리 장르
데이터로 fine-tune합니다. 끌리는 이유는 **가장 검증된 분류 모델**이라는
점입니다 — AudioSet에서 SOTA(0.485 mAP)를 찍었고, HuggingFace Transformers에
완전히 통합돼 코드가 간결하며, variable length input을 받고, fine-tuning
가이드(Renumics, TDS 블로그 등)도 풍부합니다. classification head만 161
클래스로 갈아끼우면 바로 적용됩니다.

약점은 검색 쪽입니다. CLAP과 달리 유사곡 검색용 임베딩으로 직접 쓰기 어려워서
분류 전용이 되고, 검색은 별도 시스템으로 받쳐야 합니다. full fine-tune은 A100을
권장합니다(T4로도 되지만 느립니다).

학습은 `MIT/ast-finetuned-audioset-10-10-0.4593`을 로드해 classifier head를 161
클래스로 교체하고, dataset 정규화(mean/std 재계산이 필수입니다)를 거쳐 learning
rate warmup + cosine decay로 돌립니다. 수천 곡 기준 Colab Pro A100으로 1시간
안팎이면 끝납니다.

### Option C — CLAP Full Fine-tuning (Audio + Text Encoder)

CLAP 전체를 K-pop 장르 audio-text pair로 contrastive fine-tune하는, 가장 야심
찬 길입니다. 제대로 되면 보상이 큽니다 — zero-shot 능력을 유지하니 새 장르는
학습 없이 텍스트만 추가하면 되고, 유사곡 검색과 분류를 한 모델로 처리하며,
Taxonomy 자동 업데이트 시스템과도 시너지가 납니다.

문제는 비용과 데이터입니다. audio-text pair 데이터가 필요해서 장르명마다 설명
텍스트를 만들어야 하고, 학습 비용이 셋 중 가장 높으며(V100/A100 필수, 대규모
배치), K-pop 161개 장르의 "좋은 텍스트 설명"을 만드는 일 자체가 핵심
병목입니다. 무엇보다 — 지금 CLAP의 한계가 audio encoder가 아니라 **text-audio
alignment**에 있을 수 있다는 의심이 듭니다. 그렇다면 이 길은 문제의 핵심을
비껴가는 셈입니다.

학습은 genre taxonomy를 Claude API로 장르별 상세 설명으로 풀어내고, Deezer
프리뷰 + 설명 텍스트로 contrastive learning을 돌리며, LoRA로 양쪽 encoder를
동시에 fine-tune하는 식입니다. Colab Pro A100이 필수이고 배치 사이즈가 성패를
가릅니다.

---

## 한눈에 비교

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

## 결론 — A에서 시작해 B로

**Option A(CLAP + Linear Probe)로 먼저 출발합니다.** 기존 CLAP 파이프라인과
호환되고, 임베딩 추출 → MLP 학습으로 baseline을 가장 빠르게 잡을 수 있으며,
유사곡 검색과 분류를 하나의 임베딩으로 처리하기 때문입니다. 여기서 결과가
부족하면 LoRA fine-tune으로 한 단계 늘립니다.

**A가 161개 장르에서 한계를 보이면 그때 Option B를 더합니다.** AST를 분류
전용으로 들이고 CLAP은 유사곡 검색용으로 남겨, AST(분류)와 CLAP(검색/임베딩)을
병렬로 운용하는 그림입니다.

**Option C는 보류합니다.** 텍스트 설명 품질에 지나치게 의존하고, 지금 데이터
규모에서는 ROI가 낮습니다. 데이터가 1만 곡을 넘기면 그때 다시 봅니다.

구체적인 다음 단계는 두 주로 끊습니다.

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

## 풀어야 할 숙제: Deezer 장르 → SoundTag Taxonomy 매핑

여기에 함정이 하나 있습니다. Deezer API의 장르 체계는 Pop, Rap/Hip Hop, Rock,
R&B 같은 ~20개짜리로 매우 broad한데, SoundTag은 161개 fine-grained 장르를
다룹니다. 이 둘을 잇는 데는 네 겹의 전략이 필요합니다. Deezer 장르를 대분류
레이블로 써서 1차로 거르고, 그 안에서 CLAP 임베딩으로 fine-grained 분류를 돌리고,
소규모 검증 세트(100~200곡)는 수동으로 레이블링하며, Deezer 장르 + 아티스트
스타일을 묶어 약한 레이블링(weak supervision)으로 보강합니다.

---

*작성: Day 6 (2026-03-19)*
