# SoundTag v3 — 초기 프로젝트 전략 (과거 기록)

> **📌 이 문서는 초기(Day 2 시점) 제품 전략 기록이다. 이후 방향이 크게 바뀌었다.**
> - stem 분리는 **Demucs(htdemucs)**, ground truth 멀티트랙은 **Slakh2100**으로 진행한다.
>   (초기엔 상용 stem 분리 도구 기반 distillation도 검토했으나 ToS 문제로 배제하고,
>   Demucs + Slakh 조합으로 확정했다.)
> - 장르 분류는 **CLAP+MLP(161 genres) → AST → dual-model(Model A 드럼루프 /
>   Model B 풀트랙)**로 진화했다. 본문의 "6,043개 장르 DB"는 **161개로 큐레이션한
>   Taxonomy v3**다.
> - **현재 방향은 [`../README.md`](../README.md)와
>   [`../experiments/experiment-log.md`](../experiments/experiment-log.md)를 참조.**
>   아래는 시점 기록용으로 보존한다.

## 프로젝트 비전

> 데모 하나 넣으면 모든 답이 나오는 K-pop A&R 도구

SoundTag은 K-pop A&R 실무자를 위한 음악 자동 분석 플랫폼이다.
등록되지 않은 데모 상태의 곡이라도 업로드하면:

1. **개별 악기를 stem으로 분리** (Demucs htdemucs — drums/bass/vocals/other, Slakh2100 ground truth로 10+ stem 확장 실험)
2. **세부 장르를 자동 태깅** (trip-hop, trap soul 수준, 161개 큐레이션 장르 DB / Taxonomy v3)
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

### 3. K-pop 특화 stem 분리 (Demucs + Slakh2100)
Demucs(htdemucs)로 stem을 분리하고, Slakh2100의 멀티트랙 stem을 ground truth로
활용한다. (초기엔 상용 도구 기반 distillation도 검토했으나 ToS 문제로 배제하고
Demucs + Slakh 조합으로 확정.)

### 4. 레퍼런스 확장 탐색
곡 → 유사곡 리스트 → 선택 → 또 확장하는 탐색 트리 방식 디스커버리.

---

## 핵심 전략: stem 분리 접근

stem 분리는 **Demucs(htdemucs)** 기반으로 한다. 별도의 멀티트랙 ground truth가
필요한 부분은 **Slakh2100**(2,100곡 멀티트랙, 이미 stem이 분리된 무료 데이터셋)을
그대로 활용한다 — `scripts/test_slakh_mix.py`가 Slakh stem을 불러와 K-pop 믹스를
합성하는 식으로 이미 사용 중이다.

> 초기엔 상용 stem 분리 도구의 10-stem 결과를 ground truth로 한 knowledge
> distillation으로 자체 분리 모델을 만드는 방안도 검토했으나, **해당 도구의 ToS
> 문제로 배제**하고 Demucs + Slakh 조합으로 확정했다. 한편 프로젝트의 ML 핵심은
> stem 분리가 아니라 **장르 분류의 측정 체계 재설계**(source-type leakage 진단)로
> 이동했다 — [`../README.md`](../README.md) 참조.

---

## 기술 아키텍처

### 3층 분석 엔진

**Layer 1 — 음원 분리**
- Base: Demucs v4 htdemucs (Replicate)
- 목표: fine-tuning으로 10+ stem 확장
- ground truth/학습 데이터: Slakh2100 멀티트랙 + K-pop MIDI 합성
- 서빙: Replicate (곡당 ~$0.03)

**Layer 2 — 오디오 분석**
- librosa: BPM, onset, RMS 에너지, spectral features
- Essentia: 키, 댄서빌리티, 무드
- CLAP: 오디오 → 1024차원 벡터 임베딩

**Layer 3 — 레퍼런스 DB + 유사도 매칭**
- Musicae API: Spotify 대체 (audio features, recommendations, related artists)
- ReccoBeats API: 무료, 수백만 곡 DB + 오디오 업로드 분석
- Supabase pgvector: CLAP 임베딩 벡터 검색
- 자체 장르 DB: Every Noise 6,043개를 **161개로 큐레이션(Taxonomy v3)**한 장르 임베딩

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

### 소스 1: Slakh2100 (핵심 ground truth)
- 2,100곡 × 34개 악기 클래스, 145시간
- 이미 stem이 분리된 멀티트랙 → 별도 분리 도구 없이 ground truth로 바로 활용
- MIDI → 프로급 VST 렌더링, Creative Commons 4.0 (무료), Zenodo에서 다운로드
- `scripts/test_slakh_mix.py`에서 K-pop 믹스 합성에 사용 중

### 소스 2: K-pop MIDI → VST 자체 합성
- Slakh 생성 코드 (오픈소스) 활용
- K-pop 스타일 MIDI 확보 → VST 렌더링
- 무한 생산 가능, 비용 $0
- K-pop은 가상악기 기반이라 합성↔실제 격차 작음

### 소스 3: 프로듀서 멀티트랙 (장기)
- A&R 네트워크로 미계약 곡 멀티트랙 수집
- 사용 동의서 필수
- 목표: 100-300곡
- 이 데이터로 최종 품질 개선

### 총 학습 데이터 예상
- Slakh2100: 2,100곡
- K-pop MIDI 합성: 500곡
- 프로듀서 멀티트랙: 100곡 (점진적)
- **총 ~2,700곡**

---

## 서비스 기능 명세

### 기능 1: 웹 업로드 + 자동 분석 대시보드
- 드래그앤드롭 업로드
- 분석 진행률 표시
- BPM, 키, 에너지, 댄서빌리티, stem prominence 차트

### 기능 2: 세부 장르 자동 태깅
- CLAP 오디오 임베딩 × 161개 큐레이션 장르 DB (Taxonomy v3)
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
| Google Colab Pro 2개월 (학습) | $20 |
| **총 초기 투자** | **~$20** |

### 월 운영비
| 항목 | 비용 |
|------|------|
| Replicate (자체 모델 서빙) | ~$10-20 |
| Supabase | $0-25 |
| Railway (백엔드) | $5 |
| Vercel (프론트엔드) | $0 |
| Musicae/ReccoBeats API | Free tier |
| **월 운영비** | **~$15-50** |

### 처리 비용
2,000곡 처리 시 Replicate(Demucs) 기준 ~$60 수준. (Slakh2100·MIDI 합성 데이터는
무료이므로 학습 데이터 비용은 사실상 $0.)

---

## 개발 로드맵

### Phase 0: 데이터 확보 + 모델 학습 (6주)

**Week 1-2: 데이터 준비**
- [ ] Slakh2100 다운로드 (Zenodo)
- [ ] K-pop 스타일 MIDI 확보
- [ ] 학습 데이터 포맷 통일

**Week 3-4: 모델 학습 환경 + 첫 실험**
- [ ] Google Colab Pro 셋업 (A100 GPU)
- [ ] Demucs 학습 코드 셋업 (Dora)
- [ ] Slakh2100으로 6→10 stem 확장 첫 실험

**Week 5-6: 벤치마크 + 개선**
- [ ] 자체 모델 SDR 측정
- [ ] K-pop MIDI → VST 합성 파이프라인 구축
- [ ] 합성 데이터 추가 후 재학습
- [ ] 모델 export + Replicate 배포 테스트

### Phase 1: 분석 엔진 통합 (3주)

**Week 7-8:**
- [x] Demucs 4-stem 분리 파이프라인 (완료)
- [x] librosa/Essentia 기본 분석 (완료)
- [x] CLAP 임베딩 + 161개 큐레이션 장르 DB (Taxonomy v3)
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
- [x] 장르 임베딩 DB 구축 (이후 161개로 큐레이션 → Taxonomy v3)
- [x] 레퍼런스 DB 전략 확정
- [x] stem 분리 접근 확정 (Demucs + Slakh2100)

### Day 3 예정
- [ ] 161개 큐레이션 장르 × GOT7 Python 매칭 테스트
- [ ] soundtag.py에 장르 매칭 통합

---

## 외부 API 의존성 정리

| API | 용도 | 비용 | 상태 |
|-----|------|------|------|
| Replicate | Demucs 분리 서빙 | 곡당 ~$0.03 | 사용 중 |
| Musicae | Spotify 대체 (audio features, recs) | Free tier | RapidAPI (2026.03 출시) |
| ReccoBeats | audio features + 추천 | 무료 | 사용 가능 |
| Spotify | 아티스트 장르 태그 | 무료 | 제한적 사용 가능 |

---

## 리스크 & 대응

### 자체 모델 품질이 기대 이하일 경우
→ Demucs 기본 모델(htdemucs)을 그대로 폴백으로 사용. 10+ stem 확장은 점진 과제로 두고,
대량 처리는 자체 파이프라인으로 운영.

### Musicae/ReccoBeats 서비스 중단
→ 자체 CLAP 벡터 검색이 백업. Supabase pgvector에 자체 DB 점진적 구축.

### GPU 학습 비용 초과
→ Google Colab 무료 티어로 실험, Pro ($10/월)로 본 학습. 필요시 Kaggle 무료 GPU 활용.

---

## 포트폴리오 임팩트

1. **측정 체계 재설계**: validation 77.6%가 source-type leakage에 의한 가짜 신호임을 진단하고 방법론을 재설계 (현재 핵심 서사 — [`../README.md`](../README.md) 참조)
2. **전체 ML 파이프라인**: 데이터 수집 → 학습 → leakage 진단 → measurement-first 재설계
3. **저비용 아키텍처**: 상용 API 의존 대신 Demucs/오픈 모델·무료 데이터셋(Slakh2100) 기반으로 운영비 최소화
4. **실사용자 피드백**: A&R 현업이 실제 사용하는 프로덕션 서비스
5. **도메인 전문성**: K-pop A&R 경험 × ML 엔지니어링의 유일한 교차점
6. **시장 타이밍**: Spotify API 폐쇄 시점에 대체 인프라 구축
