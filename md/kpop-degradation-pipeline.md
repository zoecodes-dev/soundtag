# SoundTag — K-pop Production Degradation Pipeline (초기 실험 기록, Day 2 단계)

> **📌 이 문서는 초기 10-stem 분리 비전 시절의 합성 데이터 파이프라인 설계다.**
> 클린 stem에 K-pop 프로덕션 이펙트를 합성해 stem-separation 학습 데이터를 만들려던
> 방향으로, 해당 비전은 현재 **보류** 상태다. 코드 자체는 재사용 가능한 자료로 보존한다.
> **현재 방향은 [`../README.md`](../README.md) 참조.**

## 목적

클린 stem(MIDI→VST 렌더링)에 실제 K-pop 프로덕션 수준의 이펙트를 적용하여
"진짜 K-pop 믹스처럼 들리는" 학습 데이터를 합성한다.

핵심 라이브러리: `pedalboard` (Spotify), `scipy.signal`, `numpy`, `librosa`

```bash
pip install pedalboard pydub scipy numpy librosa
```

---

## 1. 개별 Stem 프로세싱

### 1-1. Lead Vocal Chain

K-pop 보컬의 특징: 밝고 선명, 믹스 최전면, 레이어링 두꺼움.

```python
from pedalboard import (
    Pedalboard, Compressor, HighpassFilter, LowShelfFilter,
    HighShelfFilter, Reverb, Delay, Gain
)
import numpy as np

def process_lead_vocal(audio, sr):
    """K-pop 리드 보컬 프로세싱 체인"""

    board = Pedalboard([
        # 1. High-pass: 숨소리/럼블 제거 (80-120Hz)
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(80, 120)),

        # 2. Subtractive EQ: 200-400Hz 머디니스 컷
        #    (pedalboard에 parametric EQ가 없으므로 LowShelf로 근사)
        LowShelfFilter(
            cutoff_frequency_hz=np.random.uniform(200, 400),
            gain_db=np.random.uniform(-4, -2)
        ),

        # 3. Compression: 1176 스타일 - 빠른 어택, 미디엄 릴리스
        #    K-pop은 보컬 다이나믹을 꽤 눌러서 일정하게 유지
        Compressor(
            threshold_db=np.random.uniform(-25, -15),
            ratio=np.random.uniform(3, 6),
            attack_ms=np.random.uniform(0.5, 5),
            release_ms=np.random.uniform(50, 150)
        ),

        # 4. Additive EQ: 800Hz 미드 프레즌스 + 8-12kHz 에어
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(8000, 12000),
            gain_db=np.random.uniform(2, 5)
        ),

        # 5. De-esser 근사: 고역 컴프레션 (2-8kHz 시빌런스 억제)
        #    실제로는 dynamic EQ지만, 추가 컴프레션으로 근사
        Compressor(
            threshold_db=np.random.uniform(-20, -10),
            ratio=np.random.uniform(2, 4),
            attack_ms=0.5,
            release_ms=30
        ),

        # 6. Plate Reverb: 짧은 디케이, K-pop은 보컬에 리버브 적게
        Reverb(
            room_size=np.random.uniform(0.1, 0.3),
            damping=np.random.uniform(0.5, 0.8),
            wet_level=np.random.uniform(0.05, 0.15),
            dry_level=1.0
        ),

        # 7. Delay: 스테레오 딜레이 (1/8 또는 1/4 노트)
        Delay(
            delay_seconds=np.random.uniform(0.1, 0.25),
            feedback=np.random.uniform(0.1, 0.3),
            mix=np.random.uniform(0.05, 0.15)
        ),

        # 8. 최종 게인 조정
        Gain(gain_db=np.random.uniform(-2, 2))
    ])

    return board(audio, sr)


def process_background_vocal(audio, sr):
    """백보컬/하모니: 더 넓은 스테레오, 더 많은 리버브"""

    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(150, 250)),

        Compressor(
            threshold_db=np.random.uniform(-20, -12),
            ratio=np.random.uniform(3, 5),
            attack_ms=np.random.uniform(5, 15),
            release_ms=np.random.uniform(80, 200)
        ),

        # 백보컬은 리드보다 미드를 덜 부스트 — 뒤로 빠지게
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(6000, 10000),
            gain_db=np.random.uniform(1, 3)
        ),

        # 리버브 더 많이 — 공간감 형성
        Reverb(
            room_size=np.random.uniform(0.3, 0.6),
            damping=np.random.uniform(0.4, 0.7),
            wet_level=np.random.uniform(0.15, 0.35),
            dry_level=1.0
        ),

        Gain(gain_db=np.random.uniform(-6, -2))
    ])

    return board(audio, sr)
```

### 1-2. Kick Drum Chain

K-pop 킥: 펀치감 + 서브 레이어, 사이드체인의 트리거.

```python
def process_kick(audio, sr):
    """K-pop 킥 드럼: 클릭 + 서브 레이어링"""

    board = Pedalboard([
        # 불필요한 저역 럼블 제거 (30Hz 이하)
        HighpassFilter(cutoff_frequency_hz=30),

        # 50-80Hz 서브 부스트
        LowShelfFilter(
            cutoff_frequency_hz=np.random.uniform(50, 80),
            gain_db=np.random.uniform(2, 5)
        ),

        # 2-5kHz 어택 "클릭" 부스트
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(2000, 5000),
            gain_db=np.random.uniform(2, 4)
        ),

        # 빠른 컴프레션: 펀치감
        Compressor(
            threshold_db=np.random.uniform(-20, -10),
            ratio=np.random.uniform(4, 8),
            attack_ms=np.random.uniform(0.1, 1),
            release_ms=np.random.uniform(30, 80)
        ),

        # 약간의 새추레이션/디스토션 (하모닉 추가)
        Gain(gain_db=np.random.uniform(0, 3))
    ])

    return board(audio, sr)


def process_snare(audio, sr):
    """K-pop 스네어/클랩: 밝고 스냅감 있게"""

    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(80, 150)),

        # 200Hz 바디 + 5kHz 스냅
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(4000, 7000),
            gain_db=np.random.uniform(2, 5)
        ),

        Compressor(
            threshold_db=np.random.uniform(-18, -8),
            ratio=np.random.uniform(3, 6),
            attack_ms=np.random.uniform(1, 5),
            release_ms=np.random.uniform(40, 100)
        ),

        # 짧은 룸 리버브 (타이트한 공간감)
        Reverb(
            room_size=np.random.uniform(0.05, 0.15),
            damping=np.random.uniform(0.6, 0.9),
            wet_level=np.random.uniform(0.05, 0.2),
            dry_level=1.0
        ),

        Gain(gain_db=np.random.uniform(-1, 2))
    ])

    return board(audio, sr)


def process_hihat(audio, sr):
    """하이햇/심벌: 밝지만 귀에 안 걸리게"""

    board = Pedalboard([
        # 저역 완전 제거
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(300, 600)),

        # 10kHz+ 에어 부스트하되 과하지 않게
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(8000, 12000),
            gain_db=np.random.uniform(1, 3)
        ),

        # 가벼운 컴프레션
        Compressor(
            threshold_db=np.random.uniform(-15, -5),
            ratio=np.random.uniform(2, 4),
            attack_ms=np.random.uniform(0.5, 3),
            release_ms=np.random.uniform(20, 60)
        ),

        Gain(gain_db=np.random.uniform(-4, -1))
    ])

    return board(audio, sr)
```

### 1-3. Bass Chain

K-pop 베이스: 대부분 808/신스 베이스. 깊고 펀치감 있게.

```python
def process_bass(audio, sr):
    """808/신스 베이스: 서브 + 하모닉 새추레이션"""

    board = Pedalboard([
        # 30Hz 이하 서브소닉 제거 (스피커 보호)
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(25, 35)),

        # 40-80Hz 서브 부스트
        LowShelfFilter(
            cutoff_frequency_hz=np.random.uniform(40, 80),
            gain_db=np.random.uniform(2, 6)
        ),

        # 컴프레션: 일정한 레벨 유지
        Compressor(
            threshold_db=np.random.uniform(-20, -12),
            ratio=np.random.uniform(4, 8),
            attack_ms=np.random.uniform(5, 15),
            release_ms=np.random.uniform(80, 200)
        ),

        # 고역 롤오프: 다른 악기와 안 겹치게
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(4000, 8000),
            gain_db=np.random.uniform(-6, -2)
        ),

        Gain(gain_db=np.random.uniform(-1, 2))
    ])

    return board(audio, sr)
```

### 1-4. Synth Chain

```python
def process_lead_synth(audio, sr):
    """리드 신스/멜로디: 밝고 존재감 있게"""

    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(200, 400)),

        # 미드 프레즌스
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(3000, 6000),
            gain_db=np.random.uniform(1, 4)
        ),

        Compressor(
            threshold_db=np.random.uniform(-20, -10),
            ratio=np.random.uniform(2, 4),
            attack_ms=np.random.uniform(5, 20),
            release_ms=np.random.uniform(50, 150)
        ),

        # 스테레오 딜레이 (움직임 추가)
        Delay(
            delay_seconds=np.random.uniform(0.08, 0.2),
            feedback=np.random.uniform(0.1, 0.3),
            mix=np.random.uniform(0.1, 0.25)
        ),

        Gain(gain_db=np.random.uniform(-3, 1))
    ])

    return board(audio, sr)


def process_pad(audio, sr):
    """패드/앰비언스: 넓고 부드럽게, 뒤로"""

    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(150, 300)),

        # 고역 살짝 롤오프 (부드럽게)
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(8000, 12000),
            gain_db=np.random.uniform(-3, -1)
        ),

        # 가벼운 컴프레션
        Compressor(
            threshold_db=np.random.uniform(-15, -8),
            ratio=np.random.uniform(2, 3),
            attack_ms=np.random.uniform(20, 50),
            release_ms=np.random.uniform(100, 300)
        ),

        # 넉넉한 리버브 (넓은 공간감)
        Reverb(
            room_size=np.random.uniform(0.5, 0.8),
            damping=np.random.uniform(0.3, 0.6),
            wet_level=np.random.uniform(0.2, 0.45),
            dry_level=1.0
        ),

        Gain(gain_db=np.random.uniform(-8, -3))
    ])

    return board(audio, sr)


def process_piano(audio, sr):
    """피아노/키보드: 자연스럽게, 살짝 컴프"""

    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(60, 100)),

        # 3-5kHz 프레즌스 (건반 어택)
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(3000, 5000),
            gain_db=np.random.uniform(1, 3)
        ),

        Compressor(
            threshold_db=np.random.uniform(-18, -10),
            ratio=np.random.uniform(2, 4),
            attack_ms=np.random.uniform(10, 30),
            release_ms=np.random.uniform(80, 200)
        ),

        # 플레이트 리버브 (자연스러운 울림)
        Reverb(
            room_size=np.random.uniform(0.2, 0.4),
            damping=np.random.uniform(0.4, 0.7),
            wet_level=np.random.uniform(0.1, 0.25),
            dry_level=1.0
        ),

        Gain(gain_db=np.random.uniform(-4, 0))
    ])

    return board(audio, sr)


def process_guitar(audio, sr):
    """기타: 어쿠스틱/일렉 공통"""

    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(80, 150)),

        # 저역 머디니스 컷
        LowShelfFilter(
            cutoff_frequency_hz=np.random.uniform(200, 400),
            gain_db=np.random.uniform(-3, -1)
        ),

        # 2-4kHz 프레즌스 (픽 어택)
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(2000, 4000),
            gain_db=np.random.uniform(1, 3)
        ),

        Compressor(
            threshold_db=np.random.uniform(-20, -10),
            ratio=np.random.uniform(3, 5),
            attack_ms=np.random.uniform(5, 15),
            release_ms=np.random.uniform(60, 150)
        ),

        # 룸 리버브 또는 스프링 리버브
        Reverb(
            room_size=np.random.uniform(0.15, 0.35),
            damping=np.random.uniform(0.4, 0.7),
            wet_level=np.random.uniform(0.08, 0.2),
            dry_level=1.0
        ),

        Gain(gain_db=np.random.uniform(-3, 1))
    ])

    return board(audio, sr)
```

---

## 2. 사이드체인 컴프레션

K-pop의 핵심 — 킥이 칠 때 베이스/신스가 살짝 빠지는 "펌핑" 이펙트.

```python
def apply_sidechain(target_audio, trigger_audio, sr,
                    threshold=0.3, ratio=0.4, attack_ms=1, release_ms=80):
    """
    사이드체인 컴프레션 시뮬레이션

    target_audio: 사이드체인 걸릴 대상 (베이스, 패드 등)
    trigger_audio: 트리거 소스 (보통 킥 드럼)
    threshold: 트리거 레벨 (이 이상이면 작동)
    ratio: 얼마나 줄일지 (0.4 = 60% 줄임)
    attack_ms: 얼마나 빨리 줄일지
    release_ms: 얼마나 빨리 복원할지
    """
    # 트리거의 엔벨로프 추출
    trigger_env = np.abs(trigger_audio)

    # 스무딩 (어택/릴리스)
    attack_samples = int(sr * attack_ms / 1000)
    release_samples = int(sr * release_ms / 1000)

    envelope = np.zeros_like(trigger_env)
    for i in range(1, len(trigger_env)):
        if trigger_env[i] > envelope[i-1]:
            # 어택: 빠르게 올라감
            coeff = 1 - np.exp(-1 / max(attack_samples, 1))
            envelope[i] = envelope[i-1] + coeff * (trigger_env[i] - envelope[i-1])
        else:
            # 릴리스: 천천히 내려감
            coeff = 1 - np.exp(-1 / max(release_samples, 1))
            envelope[i] = envelope[i-1] + coeff * (trigger_env[i] - envelope[i-1])

    # 게인 리덕션 계산
    gain = np.ones_like(envelope)
    mask = envelope > threshold
    gain[mask] = 1 - ratio * (envelope[mask] - threshold) / (1 - threshold + 1e-8)
    gain = np.clip(gain, 1 - ratio, 1.0)

    # 적용
    if target_audio.ndim == 1:
        return target_audio * gain
    else:
        # 스테레오
        return target_audio * gain[np.newaxis, :]
```

---

## 3. 버스 프로세싱 (그룹 이펙트)

실제 믹싱에서는 개별 트랙 → 버스(그룹) → 마스터로 흐른다.

```python
def process_drum_bus(mixed_drums, sr):
    """드럼 버스: 전체 드럼에 글루 컴프레션 + 새추레이션"""

    board = Pedalboard([
        # 글루 컴프레션: 드럼 전체를 하나로 묶어줌
        Compressor(
            threshold_db=np.random.uniform(-15, -8),
            ratio=np.random.uniform(2, 4),
            attack_ms=np.random.uniform(10, 30),
            release_ms=np.random.uniform(80, 200)
        ),

        # 고역 부스트: 전체 드럼 밝기
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(8000, 12000),
            gain_db=np.random.uniform(1, 3)
        ),

        Gain(gain_db=np.random.uniform(-1, 1))
    ])

    return board(mixed_drums, sr)


def process_instrument_bus(mixed_instruments, sr):
    """악기 버스: 신스+피아노+기타 그룹"""

    board = Pedalboard([
        # 가벼운 글루 컴프
        Compressor(
            threshold_db=np.random.uniform(-12, -6),
            ratio=np.random.uniform(1.5, 3),
            attack_ms=np.random.uniform(15, 40),
            release_ms=np.random.uniform(100, 250)
        ),

        # 공유 리버브 (공간 일관성)
        Reverb(
            room_size=np.random.uniform(0.3, 0.5),
            damping=np.random.uniform(0.4, 0.6),
            wet_level=np.random.uniform(0.08, 0.15),
            dry_level=1.0
        ),

        Gain(gain_db=np.random.uniform(-2, 1))
    ])

    return board(mixed_instruments, sr)
```

---

## 4. 마스터링 체인

K-pop 마스터링: 밝고, 라우드하고, 펀치감 있게.

```python
def master_chain(mix, sr):
    """K-pop 마스터링 체인"""

    board = Pedalboard([
        # 1. Surgical EQ: 문제 주파수 컷
        HighpassFilter(cutoff_frequency_hz=np.random.uniform(25, 35)),
        LowShelfFilter(
            cutoff_frequency_hz=np.random.uniform(200, 350),
            gain_db=np.random.uniform(-2, -0.5)  # 머디니스 살짝 컷
        ),

        # 2. 글루 컴프레션: 전체 믹스를 하나로
        Compressor(
            threshold_db=np.random.uniform(-12, -6),
            ratio=np.random.uniform(1.5, 2.5),
            attack_ms=np.random.uniform(10, 30),
            release_ms=np.random.uniform(100, 250)
        ),

        # 3. Additive EQ: 에어 부스트
        HighShelfFilter(
            cutoff_frequency_hz=np.random.uniform(10000, 14000),
            gain_db=np.random.uniform(1, 3)
        ),

        # 4. 스테레오 이미징 — pedalboard에는 없으므로
        #    Mid/Side 프로세싱은 별도 구현 (아래 참고)

        # 5. 리미터: 최종 라우드니스
        #    pedalboard에 리미터가 없으므로 강한 컴프레션으로 근사
        Compressor(
            threshold_db=np.random.uniform(-3, -1),
            ratio=20,  # 사실상 리미터
            attack_ms=0.1,
            release_ms=np.random.uniform(30, 80)
        ),

        # 최종 출력 레벨
        Gain(gain_db=np.random.uniform(-0.5, 0))
    ])

    return board(mix, sr)
```

---

## 5. Mid/Side 스테레오 프로세싱

K-pop은 보컬(센터)은 모노로 단단하게, 신스/패드(사이드)는 넓게.

```python
def mid_side_encode(stereo_audio):
    """스테레오 → Mid/Side 변환"""
    left = stereo_audio[0]
    right = stereo_audio[1]
    mid = (left + right) / 2
    side = (left - right) / 2
    return mid, side

def mid_side_decode(mid, side):
    """Mid/Side → 스테레오 변환"""
    left = mid + side
    right = mid - side
    return np.array([left, right])

def stereo_widen(stereo_audio, width=1.3):
    """
    스테레오 이미징
    width=1.0: 원래 그대로
    width>1.0: 더 넓게 (사이드 부스트)
    width<1.0: 더 좁게 (모노 쪽으로)
    """
    mid, side = mid_side_encode(stereo_audio)
    side = side * width
    return mid_side_decode(mid, side)
```

---

## 6. 전체 파이프라인: 클린 stems → K-pop 믹스

```python
import soundfile as sf

def create_kpop_mix(stems_dict, sr):
    """
    stems_dict: {
        "lead_vocal": np.array,
        "bg_vocal": np.array,
        "kick": np.array,
        "snare": np.array,
        "hihat": np.array,
        "bass": np.array,
        "lead_synth": np.array,
        "pad": np.array,
        "piano": np.array,
        "guitar": np.array
    }

    Returns: (processed_mix, processed_stems_dict)
    """

    processors = {
        "lead_vocal": process_lead_vocal,
        "bg_vocal": process_background_vocal,
        "kick": process_kick,
        "snare": process_snare,
        "hihat": process_hihat,
        "bass": process_bass,
        "lead_synth": process_lead_synth,
        "pad": process_pad,
        "piano": process_piano,
        "guitar": process_guitar,
    }

    # Step 1: 개별 stem 프로세싱
    processed = {}
    for name, audio in stems_dict.items():
        if name in processors:
            processed[name] = processors[name](audio, sr)
        else:
            processed[name] = audio

    # Step 2: 사이드체인 (킥 → 베이스, 패드)
    if "kick" in processed and "bass" in processed:
        processed["bass"] = apply_sidechain(
            processed["bass"], processed["kick"], sr,
            threshold=np.random.uniform(0.2, 0.4),
            ratio=np.random.uniform(0.3, 0.6),
            release_ms=np.random.uniform(60, 120)
        )

    if "kick" in processed and "pad" in processed:
        processed["pad"] = apply_sidechain(
            processed["pad"], processed["kick"], sr,
            threshold=np.random.uniform(0.2, 0.4),
            ratio=np.random.uniform(0.2, 0.4),
            release_ms=np.random.uniform(80, 150)
        )

    # Step 3: 버스 그룹
    drum_names = ["kick", "snare", "hihat"]
    drum_stems = [processed[n] for n in drum_names if n in processed]
    if drum_stems:
        drum_bus = sum(drum_stems)
        drum_bus = process_drum_bus(drum_bus, sr)
    else:
        drum_bus = np.zeros_like(list(processed.values())[0])

    inst_names = ["lead_synth", "pad", "piano", "guitar"]
    inst_stems = [processed[n] for n in inst_names if n in processed]
    if inst_stems:
        inst_bus = sum(inst_stems)
        inst_bus = process_instrument_bus(inst_bus, sr)
    else:
        inst_bus = np.zeros_like(list(processed.values())[0])

    vocal_stems = [processed[n] for n in ["lead_vocal", "bg_vocal"] if n in processed]
    vocal_bus = sum(vocal_stems) if vocal_stems else np.zeros_like(list(processed.values())[0])

    bass_stem = processed.get("bass", np.zeros_like(list(processed.values())[0]))

    # Step 4: 믹스 밸런스 (K-pop 전형적 밸런스)
    mix = (
        vocal_bus * np.random.uniform(0.85, 1.0) +    # 보컬 최전면
        drum_bus * np.random.uniform(0.7, 0.85) +     # 드럼 강하게
        bass_stem * np.random.uniform(0.65, 0.8) +    # 베이스 두껍게
        inst_bus * np.random.uniform(0.4, 0.6)        # 악기는 뒤로
    )

    # Step 5: 마스터링
    mix = master_chain(mix, sr)

    # Step 6: 정규화 (클리핑 방지)
    peak = np.max(np.abs(mix))
    if peak > 0.95:
        mix = mix * (0.95 / peak)

    return mix, processed
```

---

## 7. 학습 데이터 생성 루프

```python
def generate_training_pair(clean_stems_dict, sr):
    """
    클린 stems → (degraded_mix, clean_stems) 쌍 생성
    매 호출마다 랜덤 파라미터로 다른 결과
    """

    degraded_mix, processed_stems = create_kpop_mix(clean_stems_dict, sr)

    return {
        "mix": degraded_mix,           # 모델 입력: "실제처럼 들리는 믹스"
        "clean_stems": clean_stems_dict # 모델 타겟: "이걸 분리해내야 해"
    }


# 사용 예시: Slakh2100 한 곡에서 100개 변형 생성
for variant in range(100):
    pair = generate_training_pair(slakh_track_stems, sr=44100)
    sf.write(f"train/mix_{track_id}_{variant}.wav", pair["mix"], 44100)
    for stem_name, audio in pair["clean_stems"].items():
        sf.write(f"train/{stem_name}_{track_id}_{variant}.wav", audio, 44100)
```

---

## 핵심 포인트

1. **모든 파라미터가 랜덤 범위**: 매번 다른 이펙트 세팅 → 모델이 다양한 프로덕션 스타일에 일반화
2. **K-pop 특화 밸런스**: 보컬 최전면, 드럼 강하게, 베이스 두껍게, 악기는 뒤
3. **사이드체인 시뮬레이션**: 킥 → 베이스/패드 펌핑 (K-pop 핵심)
4. **버스 프로세싱**: 개별 stem → 그룹 → 마스터 3단계 (실제 믹싱 흐름)
5. **Mid/Side**: 센터 단단하게, 사이드 넓게 (K-pop 스테레오 이미지)
6. **마스터링**: 밝고 라우드한 K-pop 최종 사운드

이 파이프라인으로 Slakh2100 한 곡에서 수십-수백 개의 변형을 만들 수 있어,
2,100곡 × 100변형 = 210,000개 학습 샘플.
