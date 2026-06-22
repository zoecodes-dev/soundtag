# SoundTag Genre Taxonomy — 자동 업데이트 시스템 설계

## 1. 이번 세션에서 실제로 한 일 (수동 프로세스 기록)

### Step 1: 초판 뼈대 생성
- Every Noise at Once 6,043개 장르 리스트를 시작점으로 사용
- 결과: 지역명 노이즈 과다 ("austrian hip hop" 등) → 쓸모없음
- **교훈: 기존 리스트를 그대로 쓰면 안 됨. 큐레이션 필수.**

### Step 2: 트렌드 소스 검색
- 검색 키워드: "emerging music genres 2024 2025", "fastest growing genres Splice Soundtrap"
- 핵심 소스 발견:
  - Splice 연간 트렌드 리포트 (다운로드 기반 성장률 데이터)
  - Soundtrap 장르 트렌드 (샘플팩 사용량 데이터)
  - Synergy FM, Samplesound 등 이머징 장르 리스트
  - IFPI Global Music Report (시장 규모별 국가 순위)
  - Spotify Loud & Clear (언어별 스트리밍 성장)
  - Beatport 장르/서브장르 공식 리스트
  - Rate Your Music 장르 분류 체계
- **교훈: 프로듀서 플랫폼(Splice, Soundtrap) 데이터가 가장 실질적. 리스너 데이터보다 생산자 데이터가 트렌드를 선행함.**

### Step 3: 시장 규모별 갭 분석
- IFPI Top 10 시장 리스트 확인: US, Japan, UK, Germany, China, France, Korea, Canada, Brazil, Mexico
- 최고 성장 지역: Latin America 22.5%, Sub-Saharan Africa 22.6%, MENA 22.8%
- 현재 taxonomy 대비 커버리지 확인 → 일본, 인도, 중국, MENA, 유럽 로컬 완전 누락 발견
- **교훈: 시장 규모로 먼저 걸러내고, 그 시장의 핵심 장르를 채워야 함.**

### Step 4: K-pop 차용 사례 검증
- "kpop songs [장르명] examples" 검색
- 실제 K-pop 곡에서 사용된 증거 확인:
  - aespa "Supernova" → Electro (Planet Rock 샘플링)
  - NewJeans "How Sweet" → Electroclash + Miami Bass
  - ARTMS "Birth" → Breakbeat
  - Infinite "The Chaser" → Freestyle
  - 터보, 클론 → Eurodance
  - ALL(H)OURS → Drift Phonk
- **교훈: 검색 없이 추측하면 안 됨. 실제 차용 사례가 Tier 분류의 근거.**

### Step 5: A&R 관점 필터링 (Zoe 피드백)
- "K-pop은 어떤 장르든 가져다 쓴다" → K-Pop Specific 카테고리 삭제
- "인도 시장은 K-pop 트렌드와 방향성이 다르다" → Tier 3 (Detection Only)
- "일본은 K-pop 진출 시장" → Tier 2 (Adjacent)
- "A&R은 새로운 방향을 고려해야 한다" → Tier 4 (New Horizon) 신설
- "레트로지만 꺼내올 수 있는 장르도 Tier 4" → Crunk, Hyphy 등 재분류
- **교훈: A&R 실무자의 관점이 가장 중요한 필터. 시스템이 자동 수집하되, 최종 Tier 분류는 A&R 피드백 반영.**

### Step 6: 반복 검증
- 힙합이 약하다는 피드백 → 재검색 → 서브장르 대폭 보충
- 브레이크비트 계열 누락 → 검색 → Breakbeat, Breakcore, Baltimore Club 등 추가
- **교훈: 한 번에 완성 불가. 카테고리별 깊이 검증이 반복 필요.**

---

## 2. 자동화 시스템 설계

### 2.1 데이터 수집 파이프라인 (Claude API + Web Search)

```
[월 1회 자동 실행]

Step A: 트렌드 소스 크롤링
├── Splice 연간/분기 리포트 검색
├── Soundtrap 트렌드 리포트 검색  
├── "emerging music genres [현재년도]" 검색
├── "fastest growing music subgenres [현재년도]" 검색
├── Beatport 장르 리스트 변경 확인
└── Rate Your Music 신규 장르 태그 확인

Step B: 시장 동향 검색
├── IFPI Global Music Report 최신판
├── Spotify Loud & Clear 최신 데이터
├── Luminate 연간 리포트
└── 지역별 성장률 변화 확인

Step C: K-pop 차용 사례 검색
├── "kpop [새 장르명] 2025 2026" 검색
├── Billboard K-pop 리스트/리뷰 검색
├── Dazed, Rolling Stone Korea 등 K-pop 비평 검색
└── 실제 곡명 + 장르 매칭 증거 수집

Step D: 결과 종합 → 신규 장르 후보 리스트 생성
├── 기존 taxonomy에 없는 장르명 추출
├── 각 후보에 대해:
│   ├── clap_text 생성 (음악적 설명)
│   ├── insight 생성 (A&R 관점 설명)
│   ├── Tier 제안 (차용 사례 기반)
│   └── 근거 소스 URL 첨부
└── "신규 장르 후보 리포트" 출력
```

### 2.2 Tier 자동 분류 로직

```python
def suggest_tier(genre_name, search_results):
    """
    K-pop 차용 사례 검색 결과를 기반으로 Tier 제안
    """
    kpop_direct_use = search_kpop_examples(genre_name)
    
    if kpop_direct_use["title_track_count"] >= 3:
        return 1  # Core: 타이틀곡에서 3회 이상 직접 차용
    
    elif kpop_direct_use["bside_count"] >= 1 or kpop_direct_use["element_use"]:
        return 2  # Adjacent: B사이드나 프로덕션 요소로 차용
    
    elif is_in_top10_market(genre_name) and not kpop_relevant(genre_name):
        return 3  # Detection: 시장 규모는 크지만 K-pop과 거리
    
    elif is_trending(genre_name) or has_revival_potential(genre_name):
        return 4  # Horizon: 트렌딩 중이거나 리바이벌 잠재력
    
    else:
        return 3  # Default: Detection
```

### 2.3 A&R 피드백 루프

```
[서비스 내 기능]

1. 분석 결과에서 "이 장르 분류가 틀림" 버튼
2. "이 장르가 목록에 없음" → 장르 제안 기능
3. "이 Tier가 맞지 않음" → Tier 조정 제안
4. 피드백이 N건 이상 쌓이면 → taxonomy 업데이트 검토 트리거
```

### 2.4 업데이트 승인 플로우

```
자동 수집 → 신규 후보 리포트 → [사람 검토] → 승인 시 taxonomy 반영
                                    ↑
                              A&R 피드백 ─┘
```

핵심: **완전 자동이 아니라 "자동 수집 + 사람 승인" 하이브리드.**
장르 분류는 문화적 판단이 필요하기 때문에 사람(A&R)이 최종 결정.

---

## 3. 필요한 구성 요소

| 구성 요소 | 역할 | 구현 방법 |
|-----------|------|-----------|
| 스케줄러 | 월 1회 자동 실행 | cron job / Cloud Scheduler |
| 웹 검색 | 트렌드 소스 수집 | Claude API (web search tool) |
| 장르 매칭 | 기존 taxonomy 대비 신규 확인 | Python 문자열 매칭 + CLAP 유사도 |
| 리포트 생성 | 신규 후보 정리 | Claude API (structured output) |
| A&R 피드백 UI | 유저 인풋 수집 | React 웹앱 내 피드백 버튼 |
| 승인 대시보드 | 최종 반영 결정 | 관리자 웹 UI |

---

## 4. 검색 쿼리 템플릿 (Claude API용)

### 트렌드 수집용
```
"emerging music genres {year}"
"fastest growing genres Splice Beatport {year}"  
"new music subgenres TikTok viral {year}"
"underground genres breaking mainstream {year}"
"{region} music market growth genres {year}"
```

### K-pop 차용 검증용
```
"kpop songs {genre_name} examples {year}"
"K-pop {genre_name} influence"
"kpop {genre_name} title track"
```

### 시장 규모용
```
"IFPI global music report {year} top markets"
"Spotify Loud Clear {year} fastest growing languages"
"Luminate year end report {year} streaming"
```

---

## 5. 현재 taxonomy 버전 히스토리

| 버전 | 날짜 | 장르 수 | 주요 변경 |
|------|------|---------|----------|
| v1 | 2026-03-18 | ~185 (Every Noise 기반) | 초안. 지역명 노이즈 과다 |
| v2 | 2026-03-18 | 185 | 자체 큐레이션. 14개 대분류, clap_text + insight |
| v3 | 2026-03-18 | 161 | Tier 시스템(1-4), 글로벌 시장 커버리지, 힙합/EDM 대폭 보강 |

---

## 6. 핵심 원칙

1. **프로듀서 데이터 > 리스너 데이터**: Splice/Soundtrap 다운로드가 Spotify 스트리밍보다 트렌드를 선행함
2. **실제 차용 사례가 Tier의 근거**: 추측이 아니라 검색 증거 기반
3. **A&R 관점이 최종 필터**: 시장 규모가 크다고 중요한 게 아님. K-pop 방향성과의 관련성이 기준
4. **한 번에 완성 불가**: 카테고리별 깊이 검증을 반복해야 함
5. **"빠진 것"을 찾는 게 핵심**: 있는 것을 정리하는 것보다, 없는 것을 발견하는 것이 A&R에게 더 큰 가치
