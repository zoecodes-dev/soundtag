# SoundTag — K-pop Production Degradation Pipeline v2
# 핵심 철학: "프로 믹싱은 안 건드린 것처럼 들린다"
# 이펙트는 소리를 바꾸는 게 아니라 살짝 다듬는 것
#
# v1 대비 변경:
#   - 컴프레션: ratio/threshold 대폭 완화 (1-3dB 리덕션)
#   - 리버브: wet level 50% 이상 축소
#   - EQ: 부스트/컷 ±0.5-2dB 범위로 제한
#   - 패럴렐/새추레이션: 비율 대폭 축소
#   - 밸런스: 소스 원본 색채 보존 우선

import numpy as np
import librosa
import soundfile as sf
from pedalboard import (
    Pedalboard, Compressor, HighpassFilter, LowpassFilter,
    LowShelfFilter, HighShelfFilter, Reverb, Delay, Gain,
    Distortion
)
from pathlib import Path


def rand(low, high):
    return np.random.uniform(low, high)

def maybe(probability=0.5):
    return np.random.random() < probability

def normalize(audio, target_peak=0.95):
    peak = np.max(np.abs(audio))
    if peak > 0:
        return audio * (target_peak / peak)
    return audio

def ensure_mono(audio):
    if audio.ndim == 2:
        return np.mean(audio, axis=0)
    return audio

def ensure_stereo(audio):
    if audio.ndim == 1:
        return np.stack([audio, audio])
    return audio

def db_to_linear(db):
    return 10 ** (db / 20)


# ============================================================
# 1. Stem 프로세싱 — 서틀 버전
# ============================================================

def process_lead_vocal(audio, sr):
    """
    리드 보컬 — 거의 안 건드린 것처럼
    원본 색채 보존이 최우선
    """
    audio = ensure_mono(audio)

    chain = Pedalboard([
        # HPF: 럼블만 제거
        HighpassFilter(cutoff_frequency_hz=rand(70, 90)),

        # 머디니스 살짝만 컷
        LowShelfFilter(
            cutoff_frequency_hz=rand(250, 350),
            gain_db=rand(-1.5, -0.5)  # v1: -5~-2 → v2: -1.5~-0.5
        ),

        # 컴프: 1-3dB만 리덕션, 부드럽게
        Compressor(
            threshold_db=rand(-15, -8),   # v1: -25~-12 → 올림
            ratio=rand(2, 3.5),           # v1: 3~8 → 낮춤
            attack_ms=rand(5, 15),        # v1: 0.3~5 → 느리게 (트랜지언트 보존)
            release_ms=rand(80, 200)      # v1: 40~150 → 느리게
        ),

        # 에어 부스트 살짝만
        HighShelfFilter(
            cutoff_frequency_hz=rand(10000, 13000),
            gain_db=rand(0.5, 2)  # v1: 2~5 → 반으로
        ),

        Gain(gain_db=rand(-0.5, 0.5))
    ])

    processed = chain(audio, sr)

    # 리버브: 매우 적게 (K-pop 보컬은 드라이)
    if maybe(0.6):
        reverb = Pedalboard([
            Reverb(
                room_size=rand(0.08, 0.2),
                damping=rand(0.6, 0.8),
                wet_level=rand(0.02, 0.06),  # v1: 0.05~0.15 → 대폭 축소
                dry_level=1.0
            )
        ])
        processed = reverb(processed, sr)

    # 딜레이: 아주 살짝
    if maybe(0.4):
        delay = Pedalboard([
            Delay(
                delay_seconds=rand(0.1, 0.2),
                feedback=rand(0.05, 0.15),  # v1: 0.1~0.3 → 축소
                mix=rand(0.03, 0.08)        # v1: 0.05~0.12 → 축소
            )
        ])
        processed = delay(processed, sr)

    # 패럴렐: 극소량 (20% 확률)
    if maybe(0.2):
        parallel = Pedalboard([
            Compressor(threshold_db=-25, ratio=10, attack_ms=1, release_ms=50)
        ])
        crushed = parallel(audio, sr)
        processed = processed * 0.95 + crushed * 0.05  # v1: 0.7/0.3 → 0.95/0.05

    return normalize(processed)


def process_background_vocal(audio, sr):
    """백보컬: 리드보다 살짝 뒤에, 약간만 더 리버브"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(120, 200)),

        Compressor(
            threshold_db=rand(-15, -8),
            ratio=rand(2, 3),
            attack_ms=rand(8, 20),
            release_ms=rand(100, 250)
        ),

        HighShelfFilter(
            cutoff_frequency_hz=rand(8000, 11000),
            gain_db=rand(0.5, 1.5)
        ),

        Reverb(
            room_size=rand(0.15, 0.3),
            damping=rand(0.5, 0.7),
            wet_level=rand(0.05, 0.12),  # v1: 0.15~0.35 → 대폭 축소
            dry_level=1.0
        ),

        Gain(gain_db=rand(-4, -1))
    ])

    return normalize(chain(audio, sr))


def process_kick(audio, sr):
    """킥: 원본 펀치감 보존, EQ 미세 조정만"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(25, 30)),

        # 서브 살짝 부스트
        LowShelfFilter(
            cutoff_frequency_hz=rand(50, 70),
            gain_db=rand(1, 2.5)  # v1: 2~6 → 축소
        ),

        # 어택 클릭 살짝
        HighShelfFilter(
            cutoff_frequency_hz=rand(3000, 5000),
            gain_db=rand(0.5, 2)  # v1: 2~5 → 축소
        ),

        # 컴프: 트랜지언트 보존! 느린 어택
        Compressor(
            threshold_db=rand(-12, -6),
            ratio=rand(2, 4),      # v1: 4~10 → 낮춤
            attack_ms=rand(5, 15), # v1: 0.1~2 → 느리게 (펀치 보존)
            release_ms=rand(30, 60)
        ),

        Gain(gain_db=rand(0, 1))
    ])

    return normalize(chain(audio, sr))


def process_snare(audio, sr):
    """스네어: 스냅감 보존"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(80, 120)),

        HighShelfFilter(
            cutoff_frequency_hz=rand(4000, 6000),
            gain_db=rand(0.5, 2)  # v1: 2~5
        ),

        Compressor(
            threshold_db=rand(-12, -6),
            ratio=rand(2, 4),
            attack_ms=rand(3, 10),
            release_ms=rand(30, 70)
        ),

        # 리버브: 극소량
        Reverb(
            room_size=rand(0.03, 0.08),
            damping=rand(0.7, 0.9),
            wet_level=rand(0.02, 0.06),  # v1: 0.05~0.2
            dry_level=1.0
        ),

        Gain(gain_db=rand(-0.5, 1))
    ])

    return normalize(chain(audio, sr))


def process_hihat(audio, sr):
    """하이햇: 거의 안 건드림"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(300, 500)),

        HighShelfFilter(
            cutoff_frequency_hz=rand(10000, 13000),
            gain_db=rand(0.5, 1.5)
        ),

        # 아주 가벼운 컴프
        Compressor(
            threshold_db=rand(-10, -4),
            ratio=rand(1.5, 2.5),
            attack_ms=rand(1, 5),
            release_ms=rand(20, 50)
        ),

        Gain(gain_db=rand(-3, -1))
    ])

    return normalize(chain(audio, sr))


def process_bass(audio, sr):
    """베이스: 서브 존재감 유지, 고역만 살짝 정리"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(25, 30)),

        LowShelfFilter(
            cutoff_frequency_hz=rand(50, 70),
            gain_db=rand(1, 2.5)
        ),

        Compressor(
            threshold_db=rand(-15, -8),
            ratio=rand(2, 4),
            attack_ms=rand(5, 15),
            release_ms=rand(80, 180)
        ),

        # 고역 살짝만 롤오프
        HighShelfFilter(
            cutoff_frequency_hz=rand(4000, 7000),
            gain_db=rand(-2, -0.5)  # v1: -6~-2
        ),

        Gain(gain_db=rand(-0.5, 1))
    ])

    return normalize(chain(audio, sr))


def process_lead_synth(audio, sr):
    """리드 신스: 원본 색채 보존, 딜레이만 살짝"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(150, 300)),

        HighShelfFilter(
            cutoff_frequency_hz=rand(4000, 7000),
            gain_db=rand(0.5, 1.5)
        ),

        Compressor(
            threshold_db=rand(-12, -6),
            ratio=rand(1.5, 3),
            attack_ms=rand(5, 15),
            release_ms=rand(60, 150)
        ),

        # 딜레이: 살짝만 움직임
        Delay(
            delay_seconds=rand(0.08, 0.15),
            feedback=rand(0.05, 0.15),
            mix=rand(0.05, 0.1)  # v1: 0.1~0.25
        ),

        Gain(gain_db=rand(-2, 0))
    ])

    return normalize(chain(audio, sr))


def process_pad(audio, sr):
    """패드: 넓지만 과하지 않게"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(100, 200)),

        HighShelfFilter(
            cutoff_frequency_hz=rand(9000, 12000),
            gain_db=rand(-1.5, -0.5)
        ),

        Compressor(
            threshold_db=rand(-10, -5),
            ratio=rand(1.5, 2.5),
            attack_ms=rand(15, 35),
            release_ms=rand(120, 280)
        ),

        # 리버브: 있되 과하지 않게
        Reverb(
            room_size=rand(0.3, 0.5),
            damping=rand(0.4, 0.6),
            wet_level=rand(0.08, 0.15),  # v1: 0.2~0.45 → 반 이하
            dry_level=1.0
        ),

        Gain(gain_db=rand(-5, -2))
    ])

    return normalize(chain(audio, sr))


def process_piano(audio, sr):
    """피아노: 자연스럽게"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(50, 80)),

        HighShelfFilter(
            cutoff_frequency_hz=rand(3000, 5000),
            gain_db=rand(0.5, 1.5)
        ),

        Compressor(
            threshold_db=rand(-12, -6),
            ratio=rand(1.5, 3),
            attack_ms=rand(10, 25),
            release_ms=rand(100, 200)
        ),

        Reverb(
            room_size=rand(0.15, 0.25),
            damping=rand(0.5, 0.7),
            wet_level=rand(0.04, 0.1),  # v1: 0.1~0.25
            dry_level=1.0
        ),

        Gain(gain_db=rand(-3, 0))
    ])

    return normalize(chain(audio, sr))


def process_guitar(audio, sr):
    """기타: 최소한의 프로세싱"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(80, 120)),

        LowShelfFilter(
            cutoff_frequency_hz=rand(250, 400),
            gain_db=rand(-1, -0.3)
        ),

        HighShelfFilter(
            cutoff_frequency_hz=rand(3000, 5000),
            gain_db=rand(0.5, 1.5)
        ),

        Compressor(
            threshold_db=rand(-12, -6),
            ratio=rand(2, 3),
            attack_ms=rand(5, 12),
            release_ms=rand(60, 130)
        ),

        Reverb(
            room_size=rand(0.1, 0.2),
            damping=rand(0.5, 0.7),
            wet_level=rand(0.03, 0.08),
            dry_level=1.0
        ),

        Gain(gain_db=rand(-2, 0))
    ])

    return normalize(chain(audio, sr))


def process_strings(audio, sr):
    """스트링/브라스"""
    audio = ensure_mono(audio)

    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(80, 120)),

        Compressor(
            threshold_db=rand(-10, -5),
            ratio=rand(1.5, 2.5),
            attack_ms=rand(20, 45),
            release_ms=rand(150, 350)
        ),

        Reverb(
            room_size=rand(0.35, 0.55),
            damping=rand(0.3, 0.5),
            wet_level=rand(0.1, 0.18),  # v1: 0.25~0.5
            dry_level=1.0
        ),

        Gain(gain_db=rand(-5, -2))
    ])

    return normalize(chain(audio, sr))


# ============================================================
# 2. 사이드체인 — 부드럽게
# ============================================================

def apply_sidechain(target, trigger, sr,
                    threshold=0.3, ratio=0.3,
                    attack_ms=2, release_ms=100):
    """사이드체인: ratio 줄여서 펌핑이 과하지 않게"""
    trigger_mono = ensure_mono(trigger)
    trigger_env = np.abs(trigger_mono)

    attack_coeff = 1 - np.exp(-1 / max(int(sr * attack_ms / 1000), 1))
    release_coeff = 1 - np.exp(-1 / max(int(sr * release_ms / 1000), 1))

    envelope = np.zeros_like(trigger_env)
    for i in range(1, len(trigger_env)):
        coeff = attack_coeff if trigger_env[i] > envelope[i-1] else release_coeff
        envelope[i] = envelope[i-1] + coeff * (trigger_env[i] - envelope[i-1])

    gain = np.ones_like(envelope)
    mask = envelope > threshold
    gain[mask] = 1 - ratio * (envelope[mask] - threshold) / (1 - threshold + 1e-8)
    gain = np.clip(gain, 1 - ratio, 1.0)

    return target * gain


# ============================================================
# 3. 스테레오
# ============================================================

def mid_side_encode(stereo):
    mid = (stereo[0] + stereo[1]) / 2
    side = (stereo[0] - stereo[1]) / 2
    return mid, side

def mid_side_decode(mid, side):
    return np.array([mid + side, mid - side])

def stereo_widen(audio, width=1.15):
    """스테레오 와이드닝 — v1보다 보수적"""
    stereo = ensure_stereo(audio)
    mid, side = mid_side_encode(stereo)
    return mid_side_decode(mid, side * width)


# ============================================================
# 4. 버스 프로세싱 — 가볍게
# ============================================================

def process_drum_bus(drums_mix, sr):
    """드럼 버스: 글루만 살짝"""
    chain = Pedalboard([
        Compressor(
            threshold_db=rand(-6, -2),    # 이전: -10~-4 → 거의 안 건드림
            ratio=rand(1.2, 1.8),         # 이전: 1.5~2.5 → 더 낮춤
            attack_ms=rand(20, 40),       # 느리게 → 트랜지언트 보존
            release_ms=rand(60, 120)
        ),
        HighShelfFilter(
            cutoff_frequency_hz=rand(10000, 13000),
            gain_db=rand(0.5, 1.5)
        ),
    ])
    return normalize(chain(drums_mix, sr))

def process_instrument_bus(inst_mix, sr):
    """악기 버스: 최소한의 글루"""
    chain = Pedalboard([
        Compressor(
            threshold_db=rand(-6, -2),
            ratio=rand(1.2, 1.5),
            attack_ms=rand(20, 40),
            release_ms=rand(120, 250)
        ),
        # 리버브 유지하되 볼륨 자체를 더 낮춤
        Reverb(
            room_size=rand(0.2, 0.35),
            damping=rand(0.5, 0.7),
            wet_level=rand(0.02, 0.06),
            dry_level=1.0
        ),
        Gain(gain_db=rand(-3, -1))  # 악기 버스 전체 볼륨 다운
    ])
    return normalize(chain(inst_mix, sr))


# ============================================================
# 5. 마스터링 — 투명하게
# ============================================================

def master_chain(mix, sr):
    """
    마스터링: 투명하고 깨끗하게
    "마스터링은 안 한 것처럼 들려야 한다"
    """
    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=rand(25, 30)),

        # 머디니스 컷: 아주 살짝
        LowShelfFilter(
            cutoff_frequency_hz=rand(250, 350),
            gain_db=rand(-1, -0.3)  # v1: -2.5~-0.5
        ),

        # 글루 컴프: 1-2dB만
        Compressor(
            threshold_db=rand(-8, -3),
            ratio=rand(1.2, 1.8),  # v1: 1.5~2.5
            attack_ms=rand(15, 30),
            release_ms=rand(120, 250)
        ),

        # 에어: 극소량
        HighShelfFilter(
            cutoff_frequency_hz=rand(12000, 15000),
            gain_db=rand(0.3, 1.2)  # v1: 1~3
        ),

        # 리미터: 피크만 잡기
        Compressor(
            threshold_db=rand(-2, -0.5),  # v1: -4~-1
            ratio=15,
            attack_ms=0.1,
            release_ms=rand(40, 80)
        ),
    ])

    return normalize(chain(mix, sr), target_peak=0.95)


# ============================================================
# 6. 전체 파이프라인
# ============================================================

STEM_PROCESSORS = {
    "lead_vocal": process_lead_vocal,
    "bg_vocal": process_background_vocal,
    # "kick": process_kick,
    #"snare": process_snare,
    #"hihat": process_hihat,
    #"bass": process_bass,
    "lead_synth": process_lead_synth,
    "pad": process_pad,
    "piano": process_piano,
    "guitar": process_guitar,
    "strings": process_strings,
}

# 밸런스: 리듬 섹션 살림
MIX_BALANCE = {
    "lead_vocal": (0.80, 0.90),
    "bg_vocal":   (0.35, 0.50),
    "kick":       (0.90, 1.0),    # 이전: 0.80~0.95
    "snare":      (0.80, 0.92),   # 이전: 0.70~0.85
    "hihat":      (0.50, 0.62),   # 이전: 0.45~0.55
    "bass":       (0.85, 0.95),   # 이전: 0.75~0.90
    "lead_synth": (0.45, 0.58),
    "pad":        (0.20, 0.32),
    "piano":      (0.35, 0.48),   # 이전: 0.40~0.52
    "guitar":     (0.30, 0.42),   # 이전: 0.40~0.52 → 내림
    "strings":    (0.25, 0.35),
}

# 스테레오: 보수적으로
STEREO_WIDTH = {
    "lead_vocal": 1.0,
    "bg_vocal":   1.4,   # v1: 1.8
    "kick":       1.0,
    "snare":      1.05,  # v1: 1.1
    "hihat":      1.25,  # v1: 1.5
    "bass":       1.05,  # v1: 1.1
    "lead_synth": 1.15,  # v1: 1.3
    "pad":        1.5,   # v1: 2.0
    "piano":      1.2,   # v1: 1.4
    "guitar":     1.25,  # v1: 1.5
    "strings":    1.4,   # v1: 1.8
}


def create_kpop_mix(stems_dict, sr):
    """클린 stems → 서틀한 K-pop 믹스"""

    # 길이 맞추기
    max_len = max(len(ensure_mono(s)) for s in stems_dict.values())
    padded = {}
    for name, audio in stems_dict.items():
        mono = ensure_mono(audio)
        if len(mono) < max_len:
            mono = np.pad(mono, (0, max_len - len(mono)))
        padded[name] = mono[:max_len]

    # 개별 프로세싱
    processed = {}
    for name, audio in padded.items():
        if name in STEM_PROCESSORS:
            processed[name] = STEM_PROCESSORS[name](audio, sr)
        else:
            processed[name] = audio

    # 사이드체인: 부드럽게
    if "kick" in processed and "bass" in processed:
        processed["bass"] = apply_sidechain(
            processed["bass"], processed["kick"], sr,
            threshold=rand(0.3, 0.5),
            ratio=rand(0.15, 0.3),   # v1: 0.3~0.6 → 반으로
            release_ms=rand(80, 140)
        )

    if "kick" in processed and "pad" in processed:
        processed["pad"] = apply_sidechain(
            processed["pad"], processed["kick"], sr,
            threshold=rand(0.3, 0.5),
            ratio=rand(0.1, 0.2),    # v1: 0.2~0.4 → 반으로
            release_ms=rand(100, 170)
        )

    # 스테레오 배치
    stereo_stems = {}
    for name, audio in processed.items():
        stereo = ensure_stereo(audio)
        width = STEREO_WIDTH.get(name, 1.1)
        width *= rand(0.95, 1.05)
        stereo_stems[name] = stereo_widen(stereo, width)

    # 버스
    drum_names = ["kick", "snare", "hihat"]
    drum_stems = [stereo_stems[n] for n in drum_names if n in stereo_stems]
    drum_bus = process_drum_bus(ensure_mono(sum(drum_stems)), sr) if drum_stems else np.zeros(max_len)
    drum_bus = ensure_stereo(drum_bus)

    inst_names = ["lead_synth", "pad", "piano", "guitar", "strings"]
    inst_stems = [stereo_stems[n] for n in inst_names if n in stereo_stems]
    inst_bus = process_instrument_bus(ensure_mono(sum(inst_stems)), sr) if inst_stems else np.zeros(max_len)
    inst_bus = ensure_stereo(inst_bus)

    vocal_names = ["lead_vocal", "bg_vocal"]
    vocal_stems = [stereo_stems[n] for n in vocal_names if n in stereo_stems]
    vocal_bus = sum(vocal_stems) if vocal_stems else np.zeros((2, max_len))

    bass_bus = stereo_stems.get("bass", np.zeros((2, max_len)))

    # 믹스: 리듬 섹션 살림
    mix = (
        vocal_bus * rand(0.65, 0.75) +     # 보컬 내림
        drum_bus * rand(1.0, 1.15) +       # 드럼 최대
        bass_bus * rand(0.95, 1.1) +       # 베이스 최대
        inst_bus * rand(0.20, 0.30)        # 악기 확 내림
    )

    # 마스터링
    mix_mono = ensure_mono(mix)
    mix_mono = master_chain(mix_mono, sr)

    # 마스터 스테레오: 보수적
    mix = ensure_stereo(mix_mono)
    mix = stereo_widen(mix, rand(1.05, 1.15))  # v1: 1.1~1.3

    return normalize(mix), processed


# ============================================================
# 테스트
# ============================================================

def quick_test(audio_dir="audio", output_dir="test_output"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    stems = {}
    stem_files = {
        "lead_vocal": "stems_vocals.mp3",
        "kick": "stems_drums.mp3",
        "bass": "stems_bass.mp3",
        "lead_synth": "stems_other.mp3",
    }

    for name, filename in stem_files.items():
        filepath = Path(audio_dir) / filename
        if filepath.exists():
            audio, sr = librosa.load(str(filepath), sr=44100)
            stems[name] = audio
            print(f"  로드: {name} ({len(audio)/sr:.1f}초)")

    if not stems:
        print("stem 파일을 찾을 수 없습니다!")
        print(f"  {audio_dir}/ 폴더에 stems_vocals.mp3 등이 있어야 합니다")
        return

    for v in range(3):
        print(f"\n변형 {v+1}/3 생성 중...")
        mix, _ = create_kpop_mix(stems, 44100)
        mix_mono = ensure_mono(mix)
        sf.write(str(output_path / f"mix_v{v}.wav"), mix_mono, 44100)
        print(f"  저장: mix_v{v}.wav")

    print(f"\n완료! {output_dir}/ 에서 확인")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        print("사용법: python kpop_mixer.py test")
