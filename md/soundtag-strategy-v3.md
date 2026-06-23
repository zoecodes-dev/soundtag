# SoundTag v3 — 초기 프로젝트 전략 (과거 기록)

> **📌 이 문서는 Day 2 시점의 제품 전략 기록입니다. 이후 방향이 크게 바뀌었습니다.**
> stem 분리는 처음에 상용 도구 기반 distillation도 검토했지만 ToS 문제로 접고
> **Demucs(htdemucs) + Slakh2100**으로 확정했습니다. 장르 분류는
> CLAP+MLP(161 genres)에서 AST를 거쳐 **dual-model(Model A 드럼루프 /
> Model B 풀트랙)**로 진화했고, 본문에 나오는 "6,043개 장르 DB"는 이후
> **161개로 큐레이션한 Taxonomy v3**가 됐습니다. 지금 무엇이 살아있는지는
> [`../README.md`](../README.md)와
> [`../experiments/experiment-log.md`](../experiments/experiment-log.md)를 보시면 됩니다.
> 아래는 그 시점에 무슨 생각을 하고 있었는지 보존하는 기록입니다.

## 한 줄 비전

> 데모 하나 넣으면 모든 답이 나오는 K-pop A&R 도구.

SoundTag은 K-pop A&R 실무자를 위한 음악 자동 분석 플랫폼입니다. 아직 어디에도
등록되지 않은 데모 한 곡을 업로드하면, 시스템이 네 가지를 차례로 해냅니다 —
개별 악기를 stem으로 분리하고(Demucs htdemucs, drums/bass/vocals/other를
기본으로 Slakh2100 ground truth로 10+ stem까지 확장 실험), trip-hop이나
trap soul 수준의 세부 장르를 자동으로 태깅하고(161개로 큐레이션한 Taxonomy v3),
발매곡 풀에서 유사곡을 골라내며(Musicae + ReccoBeats + CLAP 벡터 검색),
레퍼런스 한 곡을 기준으로 비슷한 곡을 계속 펼쳐 들어가는 탐색 트리를 그립니다.

타겟은 명확합니다. K-pop A&R 실무자입니다. 한 프로젝트(3~4개월)당 2,000곡 정도를
처리할 수 있어야 하고, UI는 깔끔하고 직관적인 웹 앱이어야 합니다.

---

## 왜 이 프로젝트가 성립하는가

이 도구가 의미 있으려면, 남들이 못 하거나 안 하는 일을 해야 합니다. 네 가지가
그 자리를 채웁니다.

**Spotify가 닫은 문을 직접 엽니다.** 2024년 11월 Spotify가 audio
features·analysis·recommendations API를 전면 폐쇄했고, 2026년 2월에는
Developer Mode에 Premium 필수 + 유저 5명 제한까지 걸어 추가로 막았습니다. 음악
분석을 Spotify에 기대던 도구들은 이때 전부 발이 묶였습니다. SoundTag은 자체 분석
엔진과 Musicae/ReccoBeats로 이 기능을 통째로 대체합니다.

**미등록 데모도 분석합니다.** Spotify나 Shazam에 존재하지 않는 곡, 즉 아직
세상에 나오지 않은 데모도 오디오 파일 하나만 있으면 전체 분석이 돌아갑니다.
A&R이 실제로 다루는 건 이미 발매된 곡이 아니라 바로 이 데모들입니다.

**K-pop에 특화된 stem 분리를 씁니다.** Demucs(htdemucs)로 stem을 분리하고,
Slakh2100의 멀티트랙 stem을 ground truth로 활용합니다. 초기엔 상용 도구 기반
distillation도 검토했지만 ToS 문제로 배제하고 Demucs + Slakh 조합으로
확정했습니다.

**레퍼런스를 펼쳐 들어갑니다.** 한 곡에서 유사곡 리스트를 뽑고, 그중 하나를
골라 또 펼치는 탐색 트리 방식의 디스커버리입니다. A&R이 머릿속으로 하는 "이 곡과
비슷한 거… 그럼 그것과 비슷한 건…"을 그대로 화면에 옮긴 것입니다.

---

## stem 분리를 어떻게 풀 것인가

stem 분리는 **Demucs(htdemucs)**를 기반으로 갑니다. 별도의 멀티트랙 ground
truth가 필요한 부분은 **Slakh2100**으로 채웁니다 — 2,100곡 멀티트랙이 이미
stem 단위로 분리돼 있는 무료 데이터셋이고, `scripts/test_slakh_mix.py`가
이 stem을 불러와 K-pop 믹스를 합성하는 식으로 이미 쓰고 있습니다.

> 처음엔 상용 stem 분리 도구의 10-stem 결과를 ground truth로 삼아 knowledge
> distillation으로 자체 분리 모델을 만드는 그림도 그렸습니다. 하지만 해당 도구의
> **ToS 문제**가 걸려 접고 Demucs + Slakh 조합으로 확정했습니다. 그리고 이
> 프로젝트의 ML 무게중심은 이후 stem 분리가 아니라 **장르 분류의 측정 체계를
> 다시 설계하는 일**(source-type leakage 진단)로 옮겨갔습니다 —
> [`../README.md`](../README.md)에 그 이야기가 있습니다.

---

## 기술 아키텍처 — 3층 분석 엔진

분석 엔진은 세 겹으로 쌓습니다.

**1층, 음원 분리.** Demucs v4 htdemucs를 베이스로 Replicate에서 서빙하고
(곡당 ~$0.03), fine-tuning으로 10+ stem 확장을 노립니다. 학습 데이터는
Slakh2100 멀티트랙에 K-pop MIDI 합성을 더해 만듭니다.

**2층, 오디오 분석.** librosa가 BPM·onset·RMS 에너지·spectral feature를 뽑고,
Essentia가 키·댄서빌리티·무드를 잡습니다. CLAP은 오디오를 1024차원 벡터
임베딩으로 바꿔 이후 검색의 재료가 됩니다.

**3층, 레퍼런스 DB + 유사도 매칭.** Musicae API가 Spotify를 대체해 audio
features·recommendations·related artists를 채우고, 무료인 ReccoBeats API가
수백만 곡 DB와 오디오 업로드 분석을 보탭니다. CLAP 임베딩은 Supabase pgvector에
넣어 벡터 검색을 돌리고, 자체 장르 DB는 Every Noise 6,043개를
**161개로 큐레이션한 Taxonomy v3** 임베딩으로 씁니다.

확장하려는 10+ stem의 목표 분류는 다음과 같습니다 — Lead Vocal, Background
Vocal/Harmony, Kick Drum, Snare/Clap, Hi-hat/Cymbal, 808/Sub Bass, Bass
Guitar/Synth Bass, Lead Synth/Melody, Pad/Atmosphere, Piano/Keys,
Guitar(Acoustic/Electric), String/Brass. K-pop 믹스의 결을 살리려면 드럼을
킥·스네어·하이햇으로, 베이스를 808과 신스 베이스로 갈라낼 수 있어야 합니다.

---

## 학습 데이터는 어디서 오는가

데이터는 세 소스에서 들어오고, 무게중심은 무료·합성 쪽에 둡니다.

**Slakh2100이 핵심 ground truth입니다.** 2,100곡 × 34개 악기 클래스, 145시간.
이미 stem이 분리된 멀티트랙이라 별도 분리 도구 없이 ground truth로 바로 씁니다.
MIDI를 프로급 VST로 렌더링한 데이터이고, Creative Commons 4.0(무료)으로
Zenodo에서 받습니다. 앞서 말한 `scripts/test_slakh_mix.py`가 이걸로 K-pop 믹스를
합성하는 데 이미 쓰고 있습니다.

**K-pop MIDI를 VST로 직접 합성합니다.** Slakh 생성 코드(오픈소스)를 가져다
K-pop 스타일 MIDI를 VST로 렌더링합니다. 무한 생산이 가능하고 비용은 $0입니다.
K-pop은 애초에 가상악기 기반이라 합성과 실제 사이의 격차가 작다는 점이 여기서
유리하게 작동합니다.

**프로듀서 멀티트랙은 장기 과제입니다.** A&R 네트워크로 미계약 곡 멀티트랙을
모으는 길인데, 사용 동의서가 필수이고 목표는 100~300곡 정도입니다. 이 데이터가
최종 품질을 끌어올리는 마지막 한 겹이 됩니다.

다 합치면 Slakh2100 2,100곡 + K-pop MIDI 합성 500곡 + 프로듀서 멀티트랙
100곡(점진적), **대략 2,700곡** 규모를 예상합니다.

---

## 서비스가 제공하는 것

화면에서 사용자가 만나는 기능은 다섯 가지입니다.

웹 업로드 후 곧장 펼쳐지는 **자동 분석 대시보드**가 첫 화면입니다 — 드래그앤드롭
업로드, 분석 진행률, 그리고 BPM·키·에너지·댄서빌리티·stem prominence 차트.
그 위에서 CLAP 오디오 임베딩과 161개 큐레이션 장르 DB(Taxonomy v3)를 맞붙여
**세부 장르를 자동 태깅**하고, 상위 10~20개 장르를 유사도 %와 함께 보여줍니다.
**유사곡 추천**은 Musicae + ReccoBeats + CLAP 벡터 유사도로 발매곡 DB에서 가장
가까운 곡을 찾아주고, 거기서 한 발 더 들어가는 게 **레퍼런스 확장 탐색**입니다 —
기준곡에서 유사곡 리스트로, 그중 하나를 골라 또 확장하며, 그 경로를 트리로
시각화합니다. 마지막으로 **10+ Stem 플레이어**가 개별 stem을 solo/mute로
토글하고 파형을 보여주며 A/B 비교를 받습니다.

---

## 돈은 얼마나 드는가

핵심은 학습 데이터가 사실상 공짜라는 점입니다. Slakh2100도 MIDI 합성도 비용이
없어서, 돈이 드는 곳은 서빙과 인프라뿐입니다.

초기 투자는 학습용 Google Colab Pro 2개월치 **~$20**가 거의 전부입니다. 월
운영비는 Replicate 자체 모델 서빙 ~$10-20, Supabase $0-25, Railway 백엔드 $5,
Vercel 프론트엔드 $0, Musicae/ReccoBeats는 Free tier로 묶어 **월 ~$15-50**
수준입니다. 실제 처리 비용은 2,000곡을 Replicate(Demucs)로 돌릴 때 ~$60
정도인데, 앞서 말했듯 학습 데이터 비용이 $0이라 여기서 더 새는 돈은 없습니다.

---

## 개발 로드맵

전체는 약 15주(4개월)로 잡고, 네 단계로 나눕니다.

**Phase 0 — 데이터 확보 + 모델 학습 (6주).** 1~2주차에 Slakh2100을 받고
K-pop 스타일 MIDI를 확보해 학습 데이터 포맷을 통일합니다. 3~4주차에 Google
Colab Pro(A100 GPU)를 셋업하고 Demucs 학습 코드(Dora)를 올려 Slakh2100으로
6→10 stem 확장 첫 실험을 돌립니다. 5~6주차에 자체 모델 SDR을 측정하고, K-pop
MIDI→VST 합성 파이프라인을 세워 합성 데이터를 더한 뒤 재학습하고, export해서
Replicate 배포까지 테스트합니다.

**Phase 1 — 분석 엔진 통합 (3주).** 7~8주차에 Demucs 4-stem 분리 파이프라인,
librosa/Essentia 기본 분석, CLAP 임베딩 + 161개 큐레이션 장르 DB까지는 이미
끝나 있고(완료), 남은 건 자체 10-stem 모델을 `soundtag.py`에 통합하고 장르
매칭·prominence 분석을 10-stem 기준으로 업데이트하는 일입니다. 9주차에 Musicae와
ReccoBeats를 연동하고 Supabase 스키마 + pgvector를 셋업합니다.

**Phase 2 — 웹 서비스 (4주).** 10~11주차에 FastAPI 백엔드(업로드→분리→분석→결과
API), Supabase Storage, 비동기 처리 큐(BackgroundTasks)를 세웁니다. 12~13주차에
React 프론트엔드와 10-stem 플레이어(Web Audio API, solo/mute), 유사곡 리스트 +
레퍼런스 확장 탐색 UI, 장르 태깅 시각화를 붙입니다.

**Phase 3 — 테스트 + 런칭 (2주).** 14~15주차에 A&R 친구 3~5명에게 베타
테스트를 돌려 피드백을 반영하고, 프로듀서 멀티트랙을 추가 학습해 모델 품질을
끌어올린 뒤 Vercel + Railway + Supabase로 배포합니다.

---

## 지금까지 한 일 (Day 2 완료 시점)

여기까지 끝냈습니다 — Python 3.12 + 가상환경 셋업, Replicate + Demucs 4-stem
분리 성공, librosa 드럼 분석(BPM·onset·에너지), Essentia 키/댄서빌리티 분석,
전체 stem prominence 비교, 원커맨드 파이프라인(`soundtag.py`), CLAP 임베딩 +
텍스트-오디오 유사도 테스트, 장르 임베딩 DB 구축(이후 161개로 큐레이션 →
Taxonomy v3), 레퍼런스 DB 전략 확정, 그리고 stem 분리 접근 확정(Demucs +
Slakh2100).

Day 3에는 161개 큐레이션 장르로 GOT7을 Python에서 매칭하는 테스트를 돌려보고,
그 매칭을 `soundtag.py`에 통합하는 데까지 가볼 생각이었습니다.

---

## 외부 API 의존성

| API | 용도 | 비용 | 상태 |
|-----|------|------|------|
| Replicate | Demucs 분리 서빙 | 곡당 ~$0.03 | 사용 중 |
| Musicae | Spotify 대체 (audio features, recs) | Free tier | RapidAPI (2026.03 출시) |
| ReccoBeats | audio features + 추천 | 무료 | 사용 가능 |
| Spotify | 아티스트 장르 태그 | 무료 | 제한적 사용 가능 |

---

## 무엇이 어긋날 수 있나

세 군데가 약점이고, 각각 폴백을 미리 정해뒀습니다.

자체 모델 품질이 기대 이하면, Demucs 기본 모델(htdemucs)을 그대로 폴백으로
쓰고 10+ stem 확장은 점진 과제로 미룬 채 대량 처리만 자체 파이프라인으로
돌립니다. Musicae나 ReccoBeats가 서비스를 멈추면, 자체 CLAP 벡터 검색이
받쳐주도록 Supabase pgvector에 자체 DB를 점진적으로 쌓아둡니다. GPU 학습 비용이
넘치면, Colab 무료 티어로 실험하고 본 학습만 Pro($10/월)로 돌리되 필요하면
Kaggle 무료 GPU까지 끌어옵니다.

---

## 이 프로젝트가 남기는 것

포트폴리오 관점에서 이 작업이 증명하는 건 여섯 가지입니다. **측정 체계를 다시
설계**한 경험(validation 77.6%가 source-type leakage에 의한 가짜 신호임을
진단하고 방법론을 갈아엎은 것 — 지금의 핵심 서사, [`../README.md`](../README.md)
참조), 데이터 수집부터 학습·leakage 진단·measurement-first 재설계까지
이어지는 **전체 ML 파이프라인**, 상용 API 대신 Demucs/오픈 모델과 무료
데이터셋(Slakh2100)으로 운영비를 최소화한 **저비용 아키텍처**, A&R 현업이 실제로
쓰는 **실사용자 피드백** 루프, K-pop A&R 경험과 ML 엔지니어링이 만나는
**도메인 전문성**, 그리고 Spotify가 API를 닫은 바로 그 시점에 대체 인프라를
세운 **시장 타이밍**입니다.
