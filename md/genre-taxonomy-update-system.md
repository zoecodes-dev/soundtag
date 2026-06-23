# SoundTag Genre Taxonomy — 자동 업데이트 시스템 설계 (과거 기록, 2026-03-18)

> **📌 Taxonomy v3(161 genres)를 큐레이션하던 시점의 설계 기록입니다.** 여기
> 담긴 큐레이션 방법론과 A&R 필터링 원칙은 지금도 유효합니다. 다만 이후 분류
> 모델이 **dual-model(Model A 드럼루프 / Model B 풀트랙)**로 바뀌었으니, 이
> 택소노미가 정확히 어디에 어떻게 쓰이는지는 [`../README.md`](../README.md)를
> 기준으로 봅니다.

## 이번 세션에서 실제로 한 일

자동화 시스템을 설계하기 전에, 먼저 그 일을 손으로 한 번 해봤습니다. 무엇을
자동화해야 하는지는 직접 해보지 않으면 알 수 없기 때문입니다. 여섯 단계로
진행했고, 각 단계마다 시스템 설계로 남길 교훈이 하나씩 떨어졌습니다.

**시작은 뼈대를 잘못 잡는 데서 출발했습니다.** Every Noise at Once의 6,043개
장르 리스트를 시작점으로 썼더니, "austrian hip hop" 같은 지역명 노이즈가
과다해서 그대로는 쓸모가 없었습니다. 첫 교훈은 분명했습니다 — **기존 리스트를
그대로 쓰면 안 됩니다. 큐레이션이 필수입니다.**

**그래서 트렌드 소스를 직접 찾아 나섰습니다.** "emerging music genres 2024
2025", "fastest growing genres Splice Soundtrap" 같은 키워드로 검색하면서 핵심
소스들을 건졌습니다 — Splice 연간 트렌드 리포트(다운로드 기반 성장률), Soundtrap
장르 트렌드(샘플팩 사용량), Synergy FM·Samplesound 같은 이머징 장르 리스트,
IFPI Global Music Report(시장 규모별 국가 순위), Spotify Loud & Clear(언어별
스트리밍 성장), Beatport 공식 장르/서브장르 리스트, Rate Your Music 분류 체계.
여기서 두 번째 교훈이 나왔습니다 — **프로듀서 플랫폼(Splice, Soundtrap)
데이터가 가장 실질적입니다. 리스너 데이터보다 생산자 데이터가 트렌드를
선행합니다.**

**다음은 시장 규모로 갭을 분석했습니다.** IFPI Top 10 시장(US, Japan, UK,
Germany, China, France, Korea, Canada, Brazil, Mexico)을 확인하고, 성장률이
가장 높은 지역(Latin America 22.5%, Sub-Saharan Africa 22.6%, MENA 22.8%)을
짚었습니다. 현재 taxonomy와 대조하니 일본·인도·중국·MENA·유럽 로컬이 통째로
빠져 있었습니다. 세 번째 교훈 — **시장 규모로 먼저 거르고, 그 시장의 핵심
장르를 채워 넣어야 합니다.**

**그다음 K-pop이 실제로 그 장르를 쓴 적이 있는지 검증했습니다.** "kpop songs
[장르명] examples"로 검색해 증거를 모았습니다 — aespa "Supernova"는
Electro(Planet Rock 샘플링), NewJeans "How Sweet"는 Electroclash + Miami Bass,
ARTMS "Birth"는 Breakbeat, Infinite "The Chaser"는 Freestyle, 터보·클론은
Eurodance, ALL(H)OURS는 Drift Phonk. 네 번째 교훈 — **검색 없이 추측하면 안
됩니다. 실제 차용 사례가 Tier 분류의 근거입니다.**

**그리고 A&R 관점으로 걸러냈습니다(Zoe 피드백).** "K-pop은 어떤 장르든 가져다
쓴다"는 말에 따라 K-Pop Specific 카테고리를 삭제했고, "인도 시장은 K-pop
트렌드와 방향성이 다르다"며 Tier 3(Detection Only)로, "일본은 K-pop 진출
시장"이라 Tier 2(Adjacent)로 옮겼습니다. "A&R은 새로운 방향을 고려해야 한다"는
판단에서 Tier 4(New Horizon)를 신설하고, "레트로지만 꺼내올 수 있는 장르"인
Crunk·Hyphy 등을 거기로 재분류했습니다. 다섯 번째 교훈 — **A&R 실무자의 관점이
가장 중요한 필터입니다. 시스템이 자동으로 수집하되, 최종 Tier 분류는 A&R
피드백을 반영합니다.**

**마지막은 반복 검증이었습니다.** 힙합이 약하다는 피드백에 재검색해 서브장르를
대폭 보충했고, 브레이크비트 계열이 빠졌다는 지적에 Breakbeat·Breakcore·Baltimore
Club 등을 추가했습니다. 여섯 번째 교훈 — **한 번에 완성되지 않습니다.
카테고리별로 깊이를 다시 파는 검증을 반복해야 합니다.**

---

## 이걸 어떻게 자동화하나

손으로 한 여섯 단계 중 반복되는 부분(수집·검색·후보 추출)은 자동화하고,
판단이 필요한 부분(Tier 확정)은 사람에게 남깁니다. 핵심은 **완전 자동이 아니라
"자동 수집 + 사람 승인" 하이브리드**라는 점입니다.

### 데이터 수집 파이프라인 (Claude API + Web Search)

월 1회 자동 실행으로, 위 Step 2~5를 그대로 코드로 옮긴 흐름입니다.

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

### Tier 자동 분류 로직

Step 4(차용 사례 검증)와 Step 5(A&R 필터링)에서 정한 기준을 함수로 굳힌
것입니다. 타이틀곡에서 3회 이상 직접 차용했으면 Core, B사이드나 프로덕션
요소로 썼으면 Adjacent, 시장은 크지만 K-pop과 거리가 있으면 Detection,
트렌딩 중이거나 리바이벌 잠재력이 있으면 Horizon으로 제안합니다.

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

### A&R 피드백 루프

자동 수집만으로는 부족합니다. 서비스 안에서 실무자가 직접 신호를 보낼 수 있어야
합니다. 분석 결과에 "이 장르 분류가 틀림" 버튼을 두고, 목록에 없는 장르를
제안받고, Tier가 맞지 않으면 조정 제안을 받습니다. 이런 피드백이 N건 이상
쌓이면 taxonomy 업데이트를 검토하는 트리거가 걸립니다.

```
[서비스 내 기능]

1. 분석 결과에서 "이 장르 분류가 틀림" 버튼
2. "이 장르가 목록에 없음" → 장르 제안 기능
3. "이 Tier가 맞지 않음" → Tier 조정 제안
4. 피드백이 N건 이상 쌓이면 → taxonomy 업데이트 검토 트리거
```

### 승인 플로우

자동 수집과 사람 판단이 만나는 지점입니다. 수집한 신규 후보 리포트를 사람이
검토하고, A&R 피드백을 함께 얹어, 승인된 것만 taxonomy에 반영합니다.

```
자동 수집 → 신규 후보 리포트 → [사람 검토] → 승인 시 taxonomy 반영
                                    ↑
                              A&R 피드백 ─┘
```

장르 분류는 문화적 판단이 필요한 일이라, 최종 결정은 끝까지 사람(A&R)이 쥡니다.

---

## 필요한 구성 요소

이 시스템을 굴리려면 여섯 가지가 맞물려야 합니다. 월 1회 자동 실행을 거는
**스케줄러**(cron job / Cloud Scheduler), 트렌드 소스를 수집하는 **웹
검색**(Claude API web search tool), 기존 taxonomy와 대조해 신규를 가려내는
**장르 매칭**(Python 문자열 매칭 + CLAP 유사도), 신규 후보를 정리하는 **리포트
생성**(Claude API structured output), 유저 인풋을 받는 **A&R 피드백 UI**(React
웹앱 내 피드백 버튼), 그리고 최종 반영을 결정하는 **승인 대시보드**(관리자 웹
UI)입니다.

---

## 검색 쿼리 템플릿 (Claude API용)

트렌드 수집용:

```
"emerging music genres {year}"
"fastest growing genres Splice Beatport {year}"  
"new music subgenres TikTok viral {year}"
"underground genres breaking mainstream {year}"
"{region} music market growth genres {year}"
```

K-pop 차용 검증용:

```
"kpop songs {genre_name} examples {year}"
"K-pop {genre_name} influence"
"kpop {genre_name} title track"
```

시장 규모용:

```
"IFPI global music report {year} top markets"
"Spotify Loud Clear {year} fastest growing languages"
"Luminate year end report {year} streaming"
```

---

## Taxonomy 버전 히스토리

택소노미는 하루 만에 세 번 갈아엎혔습니다(2026-03-18). **v1**은 Every Noise
기반 ~185개 초안이었고, 앞서 말한 지역명 노이즈가 과다했습니다. **v2**는 그걸
자체 큐레이션해 14개 대분류로 정리하고 각 장르에 clap_text + insight를 붙인
185개입니다. **v3**은 여기에 Tier 시스템(1~4)을 도입하고 글로벌 시장 커버리지를
채우며 힙합/EDM을 대폭 보강해 161개로 추렸습니다 — 이게 지금 쓰는 버전입니다.

---

## 결국 다섯 원칙으로 수렴합니다

여섯 단계의 실습과 자동화 설계가 남긴 건 결국 다섯 개의 원칙입니다.
**프로듀서 데이터가 리스너 데이터보다 앞섭니다** — Splice/Soundtrap 다운로드가
Spotify 스트리밍보다 트렌드를 선행합니다. **실제 차용 사례가 Tier의
근거입니다** — 추측이 아니라 검색으로 확인한 증거로만 분류합니다. **A&R 관점이
최종 필터입니다** — 시장이 크다고 중요한 게 아니라, K-pop 방향성과 얼마나
관련되는지가 기준입니다. **한 번에 완성되지 않습니다** — 카테고리별 깊이 검증을
반복해야 합니다. 그리고 무엇보다, **"빠진 것"을 찾는 게 핵심입니다** — 있는
것을 정리하는 일보다, 없는 것을 발견하는 일이 A&R에게 훨씬 큰 가치입니다.
