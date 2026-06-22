# SoundTag v3 — 최종 프로젝트 전략

## 프로젝트 비전

> 데모 하나 넣으면 모든 답이 나오는 K-pop A&R 도구

SoundTag은 K-pop A&R 실무자를 위한 음악 자동 분석 플랫폼이다.
등록되지 않은 데모 상태의 곡이라도 업로드하면:

1. **개별 악기를 10+ stem으로 분리** (자체 모델, LALAL.AI 수준 목표)
2. **세부 장르를 자동 태깅** (trip-hop, trap soul 수준, 6,043개 장르 DB)
3. **발매곡에서 유사곡을 추천** (Musicae + ReccoBeats + CLAP 벡터 검색)
4. **레퍼런스 1곡 기준으로 유사곡 리스트를 확장 탐색** (탐색 트리)

타겟: K-pop A&R 실무자
요구 처리량: 프로젝트당 (3-4개월) 2,000곡
UI 수준: 깔끔하고 직관적인 웹 앱

---

## 핵심 차별점

### 1. Spotify가 막은 기능을 자체 구축
2024.11 Spotify audio features/analysis/recommendations API 전면 폐쇄.
2026.02 Developer Mode에 Premium 필수 + 유저 5명 제한으로 추가 제한.
→ SoundTag은 자체 분석 엔진 + Musicae/ReccoBeats로 이 기능을 완전 대체.

### 2. 미등록 데모 분석 가능
Spotify/Shazam에 없는 곡도 오디오 파일만으로 전체 분석 가능.

### 3. K-pop 특화 10+ stem 분리 (자체 모델)
LALAL.AI의 10-stem 결과를 ground truth로 활용한 knowledge distillation 방식.
자체 모델로 서빙하여 곡당 $0.03 수준의 저비용 운영.

### 4. 레퍼런스 확장 탐색
곡 → 유사곡 리스트 → 선택 → 또 확장하는 탐색 트리 방식 디스커버리.

---

## 핵심 전략: Knowledge Distillation

### 개념
"큰 모델(LALAL.AI)의 지식을 작은 모델(자체 Demucs)에 옮기는 기법"

LALAL.AI를 직접 서비스에 사용하면 2,000곡 × $4.50 = $9,000/프로젝트.
자체 모델을 서비스에 사용하면 2,000곡 × $0.03 = $60/프로젝트.

LALAL.AI는 학습 데이터 생성에만 일회성으로 사용하고,
실서비스는 자체 모델로 운영하여 비용 150배 절감.

### 프로세스

```
Step 1: LALAL.AI로 K-pop 200곡을 10-stem 분리 (일회성 $150)
        → "이 곡의 피아노는 이렇게 들려야 해" = 정답지 (ground truth)

Step 2: 같은 200곡의 원본(믹스) + LALAL.AI stem 쌍을 학습 데이터로 구성
        + Slakh2100 (2,100곡 멀티트랙, 무료)
        + K-pop MIDI → VST 합성 (500곡, 무료)
        = 총 ~2,800곡 학습 데이터

Step 3: Demucs를 base model로 fine-tuning
        → 10+ stem 분리가 가능한 자체 모델 생성

Step 4: LALAL.AI 결과 vs 자체 모델 결과를 SDR로 비교
        → 반복 개선하여 품질 수렴

Step 5: 자체 모델을 Replicate에 배포 → SoundTag 서비스에 통합
```

### 품질 목표
- LALAL.AI 대비 70-80% SDR 달성이 1차 목표
- 프로듀서 멀티트랙 추가 학습으로 점진적 개선
- K-pop 특화 패턴(808, 레이어드 신스, 보컬 프로세싱)에서 LALAL.AI보다 나은 결과 가능

---

## 기술 아키텍처

### 3층 분석 엔진

**Layer 1 — 음원 분리**
- Base: Demucs v4 htdemucs_6s
- 목표: fine-tuning으로 10+ stem 확장
- 학습 데이터: LALAL.AI ground truth + Slakh2100 + K-pop MIDI 합성
- 서빙: Replicate (곡당 ~$0.03)

**Layer 2 — 오디오 분석**
- librosa: BPM, onset, RMS 에너지, spectral features
- Essentia: 키, 댄서빌리티, 무드
- CLAP: 오디오 → 1024차원 벡터 임베딩

**Layer 3 — 레퍼런스 DB + 유사도 매칭**
- Musicae API: Spotify 대체 (audio features, recommendations, related artists)
- ReccoBeats API: 무료, 수백만 곡 DB + 오디오 업로드 분석
- Supabase pgvector: CLAP 임베딩 벡터 검색
- 자체 장르 DB: 6,043개 장르 CLAP 임베딩 (구축 완료)

### 목표 stem 분류 (10+ stems)
1. Lead Vocal
2. Background Vocal / Harmony
3. Kick Drum
4. Snare / Clap
5. Hi-hat / Cymbal
6. 808 / Sub Bass
7. Bass Guitar / Synth Bass
8. Lead Synth / Melody
9. Pad / Atmosphere
10. Piano / Keys
11. Guitar (Acoustic/Electric)
12. String / Brass

---

## 데이터 확보 전략

### 소스 1: LALAL.AI Ground Truth (핵심)
- K-pop 200곡을 10-stem 분리
- 비용: ~$150 (일회성)
- 가장 높은 품질의 학습 타겟
- 이 200곡은 신중하게 선정 (장르 다양성, 악기 구성 다양성)

### 소스 2: Slakh2100 (즉시 사용)
- 2,100곡 × 34개 악기 클래스, 145시간
- MIDI → 프로급 VST 렌더링
- Creative Commons 4.0 (무료)
- Zenodo에서 다운로드

### 소스 3: K-pop MIDI → VST 자체 합성
- Slakh 생성 코드 (오픈소스) 활용
- K-pop 스타일 MIDI 확보 → VST 렌더링
- 무한 생산 가능, 비용 $0
- K-pop은 가상악기 기반이라 합성↔실제 격차 작음

### 소스 4: 프로듀서 멀티트랙 (장기)
- A&R 네트워크로 미계약 곡 멀티트랙 수집
- 사용 동의서 필수
- 목표: 100-300곡
- 이 데이터로 최종 품질 개선

### 총 학습 데이터 예상
- LALAL.AI ground truth: 200곡
- Slakh2100: 2,100곡
- K-pop MIDI 합성: 500곡
- 프로듀서 멀티트랙: 100곡 (점진적)
- **총 ~2,900곡**

---

## 서비스 기능 명세

### 기능 1: 웹 업로드 + 자동 분석 대시보드
- 드래그앤드롭 업로드
- 분석 진행률 표시
- BPM, 키, 에너지, 댄서빌리티, stem prominence 차트

### 기능 2: 세부 장르 자동 태깅
- CLAP 오디오 임베딩 × 6,043개 장르 DB
- 상위 10-20개 장르를 유사도 %와 함께 표시

### 기능 3: 유사곡 추천
- Musicae API + ReccoBeats + CLAP 벡터 유사도
- 발매곡 DB에서 가장 비슷한 곡 매칭

### 기능 4: 레퍼런스 확장 탐색
- 기준곡 → 유사곡 리스트 → 선택 → 또 확장
- 탐색 히스토리 시각화 (트리 형태)

### 기능 5: 10+ Stem 플레이어
- 개별 stem solo/mute 토글
- 파형 시각화
- A/B 비교

---

## 비용 구조

### 초기 투자 (일회성)
| 항목 | 비용 |
|------|------|
| LALAL.AI 200곡 10-stem (학습 데이터) | ~$150 |
| Google Colab Pro 2개월 (학습) | $20 |
| **총 초기 투자** | **~$170** |

### 월 운영비
| 항목 | 비용 |
|------|------|
| Replicate (자체 모델 서빙) | ~$10-20 |
| Supabase | $0-25 |
| Railway (백엔드) | $5 |
| Vercel (프론트엔드) | $0 |
| Musicae/ReccoBeats API | Free tier |
| **월 운영비** | **~$15-50** |

### 처리 비용 비교
| 방식 | 2,000곡 비용 |
|------|-------------|
| LALAL.AI 직접 사용 | ~$9,000 |
| 자체 모델 (Replicate) | ~$60 |
| **절감율** | **99.3%** |

---

## 개발 로드맵

### Phase 0: 데이터 확보 + 모델 학습 (6주)

**Week 1-2: 데이터 준비**
- [ ] LALAL.AI 계정 생성 + API 연동
- [ ] K-pop 200곡 선정 (장르/악기 다양성 기준)
- [ ] LALAL.AI로 200곡 10-stem 분리 실행
- [ ] Slakh2100 다운로드 (Zenodo)
- [ ] 학습 데이터 포맷 통일

**Week 3-4: 모델 학습 환경 + 첫 실험**
- [ ] Google Colab Pro 셋업 (A100 GPU)
- [ ] Demucs 학습 코드 셋업 (Dora)
- [ ] Slakh2100으로 6→10 stem 확장 첫 실험
- [ ] LALAL.AI ground truth로 fine-tuning 실행

**Week 5-6: 벤치마크 + 개선**
- [ ] 자체 모델 vs LALAL.AI SDR 비교
- [ ] K-pop MIDI → VST 합성 파이프라인 구축
- [ ] 합성 데이터 추가 후 재학습
- [ ] 모델 export + Replicate 배포 테스트

### Phase 1: 분석 엔진 통합 (3주)

**Week 7-8:**
- [x] Demucs 4-stem 분리 파이프라인 (완료)
- [x] librosa/Essentia 기본 분석 (완료)
- [x] CLAP 임베딩 + 6,043 장르 DB (완료)
- [ ] 자체 10-stem 모델을 soundtag.py에 통합
- [ ] 장르 매칭 + prominence 분석 업데이트 (10-stem 기반)

**Week 9:**
- [ ] Musicae API 연동 (유사곡 추천)
- [ ] ReccoBeats API 연동 (audio features)
- [ ] Supabase DB 스키마 설계 + pgvector 셋업

### Phase 2: 웹 서비스 (4주)

**Week 10-11:**
- [ ] FastAPI 백엔드 (업로드 → 분리 → 분석 → 결과 API)
- [ ] Supabase Storage (음원 + stem 파일 저장)
- [ ] 비동기 처리 큐 (BackgroundTasks)

**Week 12-13:**
- [ ] React 프론트엔드 (깔끔한 대시보드)
- [ ] 10-stem 플레이어 (Web Audio API, solo/mute)
- [ ] 유사곡 리스트 + 레퍼런스 확장 탐색 UI
- [ ] 장르 태깅 시각화

### Phase 3: 테스트 + 런칭 (2주)

**Week 14-15:**
- [ ] A&R 친구들 베타 테스트 (3-5명)
- [ ] 피드백 반영
- [ ] 모델 품질 개선 (프로듀서 멀티트랙 추가 학습)
- [ ] 배포 (Vercel + Railway + Supabase)

**총 예상: 15주 (약 4개월)**

---

## 현재 진행 상태 (Day 2 완료)

### 완료
- [x] Python 3.12 + 가상환경 셋업
- [x] Replicate + Demucs 4-stem 분리 성공
- [x] librosa 드럼 분석 (BPM, onset, 에너지)
- [x] Essentia 키/댄서빌리티 분석
- [x] 전체 stem prominence 비교
- [x] 원커맨드 파이프라인 (soundtag.py)
- [x] CLAP 임베딩 + 텍스트-오디오 유사도 테스트
- [x] 6,043개 장르 임베딩 DB 구축
- [x] 레퍼런스 DB 전략 확정
- [x] Knowledge distillation 전략 확정

### Day 3 예정
- [ ] 6,043개 장르 × GOT7 Python 매칭 테스트
- [ ] soundtag.py에 장르 매칭 통합

---

## 외부 API 의존성 정리

| API | 용도 | 비용 | 상태 |
|-----|------|------|------|
| LALAL.AI | 학습 데이터 생성 (일회성) | ~$150 | API v1 출시 (2026.02) |
| Replicate | 자체 모델 서빙 | 곡당 ~$0.03 | 사용 중 |
| Musicae | Spotify 대체 (audio features, recs) | Free tier | RapidAPI (2026.03 출시) |
| ReccoBeats | audio features + 추천 | 무료 | 사용 가능 |
| Spotify | 아티스트 장르 태그 | 무료 | 제한적 사용 가능 |

---

## 리스크 & 대응

### 자체 모델 품질이 기대 이하일 경우
→ LALAL.AI API를 fallback으로 유지. 중요한 곡만 LALAL.AI로, 대량 처리는 자체 모델로 하이브리드 운영.

### LALAL.AI API 비용 변동
→ 학습 데이터는 일회성이라 이미 확보하면 의존 없음. 추가 학습이 필요하면 Slakh + MIDI 합성으로 보완.

### Musicae/ReccoBeats 서비스 중단
→ 자체 CLAP 벡터 검색이 백업. Supabase pgvector에 자체 DB 점진적 구축.

### GPU 학습 비용 초과
→ Google Colab 무료 티어로 실험, Pro ($10/월)로 본 학습. 필요시 Kaggle 무료 GPU 활용.

---

## 포트폴리오 임팩트

1. **Knowledge Distillation 실전 적용**: 상용 모델의 지식을 자체 모델로 이전하는 ML 기법
2. **전체 ML 파이프라인**: 데이터 수집 → 합성 → 학습 → 벤치마크 → 서빙
3. **비용 최적화 설계**: $9,000 → $60으로 99.3% 비용 절감 아키텍처
4. **실사용자 피드백**: A&R 현업이 실제 사용하는 프로덕션 서비스
5. **도메인 전문성**: K-pop A&R 경험 × ML 엔지니어링의 유일한 교차점
6. **시장 타이밍**: Spotify API 폐쇄 시점에 대체 인프라 구축
