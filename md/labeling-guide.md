# SoundTag K-pop 평가셋 라벨링 가이드 v1 (초안)

**목적**: 100곡 K-pop 평가셋의 ground truth 어노테이션 기준 고정.
이 문서가 확정되기 전에는 라벨링을 시작하지 않는다.

---

## 1. 라벨링 단위: 섹션

곡 전체가 아니라 **섹션 단위**로 라벨링한다. (K-pop은 후반부에 장르가 전환되는 구조가 많으므로)

**섹션 타입 (고정)**: `Intro` / `Verse` / `Pre-Chorus` / `Chorus` / `Post-Chorus` / `Bridge` / `Dance Break` / `Outro`

**경계 규칙**:
- timestamp는 초 단위 (예: 0–14, 14–42)
- 5초 미만 섹션은 인접 섹션에 병합
- 같은 타입이 반복되어도 사운드가 다르면 별도 기록 (예: Chorus 1 vs 마지막 Chorus 키체인지)
- 사운드가 동일한 반복 섹션은 `repeat_of` 필드로 참조만

---

## 2. 섹션별 라벨 스키마

| 필드 | 형식 | 규칙 |
|------|------|------|
| `genres` | 1–3개, 우선순위 순 | Genre Taxonomy v3에서만 선택 |
| `energy` | 정수 1–5 | 아래 앵커 기준 |
| `moods` | 1–3개 | 아래 고정 vocabulary에서만 선택 |
| `confidence` | 0 또는 1 | 확신 없으면 0 → 나중에 재청취 |
| `notes` | 자유 텍스트 (선택) | 특이사항만, 짧게 |

### 장르 우선순위 판단 기준
1. **1순위 = 리듬 패턴**이 지배하는 장르 (드럼/퍼커션 그루브)
2. **2–3순위 = 사운드 텍스처/멜로디**가 가리키는 장르
3. 4개 이상 떠오르면 상위 3개만. 나머지는 버린다 (notes에도 안 씀)

### 에너지 앵커 (1–5)
| 점수 | 기준 |
|------|------|
| 1 | 리듬 거의 없음. 발라드 인트로, 어쿠스틱 솔로 |
| 2 | 차분한 미드템포. 다운된 verse, 어쿠스틱 그루브 |
| 3 | 표준 그루브. 미드템포 chorus, 보통 강도의 verse |
| 4 | 댄스곡 chorus. 드라이브 강함, 풀 프로덕션 |
| 5 | 최대 강도. 드랍, dance break, 마지막 chorus 폭발 |

### Mood Controlled Vocabulary (24개, 초안 — Zoe 확정 필요)
- **밝음**: `bright` `playful` `cheeky` `euphoric` `triumphant`
- **어두움**: `dark` `moody` `melancholic` `bittersweet` `haunting`
- **강도**: `aggressive` `fierce` `gritty` `intense`
- **부드러움**: `dreamy` `tender` `warm` `intimate`
- **스타일**: `sleek` `retro` `nostalgic` `groovy` `hypnotic` `sensual`

규칙: 이 목록 밖의 단어는 절대 사용 금지. 빠진 태그가 필요하면 **라벨링 중단 → vocabulary 개정 → 기존 라벨 재검토** 후 재개.

---

## 3. 일관성 규칙

1. **들리는 것만 라벨링.** 아티스트, 회사, 마케팅 문구, 평론 지식은 배제. Namu Wiki는 섹션 구조 참고용으로만.
2. **하루 최대 10곡.** 귀 피로가 기준을 흔든다.
3. **Calibration round**: 첫 10곡 완료 후 가이드 재점검. 기준 수정이 생기면 그 10곡 재라벨링. (10곡 재작업은 싸고, 100곡 재작업은 비싸다)
4. confidence=0 곡들은 전체 완료 후 별도 세션에서 일괄 재청취.
5. 라벨링 순서는 무작위 (연도순/아티스트순 금지 — 기준 drift 방지).

---

## 4. 선곡 분포 (100곡, 초안)

| 축 | 분포 |
|----|------|
| 연도 | 2025: 25 / 2024: 25 / 2023: 20 / 2022: 15 / 2021: 10 / 2020: 5 |
| 트랙 | 타이틀 60 / B사이드 40 |
| 회사 | 메이저 70 / 인디·중소 30 |
| 장르 | 의도적 쿼터 없음 — 위 분포로 뽑으면 시장 분포가 자연히 반영됨 |

- 음원은 전곡 구매 (고음질, 도메인 갭 방지)
- 선곡 리스트는 라벨링 시작 전 확정 (라벨링 중 교체 금지)

---

## 5. 파일 포맷 (JSONL, 곡당 1줄)

```json
{
  "track_id": "kpop_eval_001",
  "title": "...",
  "artist": "...",
  "year": 2024,
  "track_type": "title",
  "company_size": "major",
  "sections": [
    {
      "type": "Intro",
      "start": 0, "end": 12,
      "genres": ["UK Garage", "Electropop"],
      "energy": 2,
      "moods": ["dreamy", "sleek"],
      "confidence": 1
    },
    {
      "type": "Chorus",
      "start": 45, "end": 73,
      "genres": ["Jersey Club", "Electropop", "Pop R&B"],
      "energy": 4,
      "moods": ["euphoric", "groovy"],
      "confidence": 1
    }
  ]
}
```

---

## 6. 이 평가셋의 용도 (변경 불가)

1. **모든 모델의 유일한 성능 기준** — 학습 데이터의 Val accuracy는 참고치일 뿐
2. 학습에 절대 사용하지 않는다 (hold-out 오염 금지)
3. CLAP 레퍼런스 추천 품질 평가에도 동일 사용
