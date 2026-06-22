"""
각 장르의 기대 오디오 프로필.
CLAP 매칭 후 2차 검증에 사용.
값이 None이면 해당 feature로 검증하지 않음.
"""

GENRE_PROFILES = {
    # --- Tier 1 (Core) ---
    "Dance Pop": {
        "bpm_range": (110, 135),
        "bass_prominence": (15, 35),
        "drum_pattern": ["Driving (Dance/EDM)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.7
    },
    "Synth Pop": {
        "bpm_range": (100, 130),
        "bass_prominence": (15, 35),
        "drum_pattern": ["Driving (Dance/EDM)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.6
    },
    "Electropop": {
        "bpm_range": (110, 140),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.7
    },
    "Dark Pop": {
        "bpm_range": (70, 130),
        "bass_prominence": (20, 40),
        "drum_pattern": None,
        "danceability_min": 0.4
    },
    "Bubblegum Pop": {
        "bpm_range": (110, 140),
        "bass_prominence": (10, 30),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.7
    },
    "Y2K Pop": {
        "bpm_range": (95, 130),
        "bass_prominence": (15, 35),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.6
    },
    "Trap": {
        "bpm_range": (130, 170),
        "bass_prominence": (30, 50),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.5
    },
    "Drill": {
        "bpm_range": (135, 150),
        "bass_prominence": (30, 50),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)"],
        "danceability_min": 0.4
    },
    "Atlanta Trap": {
        "bpm_range": (130, 170),
        "bass_prominence": (30, 50),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)"],
        "danceability_min": 0.5
    },
    "Pluggnb": {
        "bpm_range": (130, 160),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.5
    },
    "Contemporary R&B": {
        "bpm_range": (70, 120),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Moderate (Pop/R&B)", "Sparse (Trap/Hip-Hop)"],
        "danceability_min": 0.4
    },
    "Alternative R&B": {
        "bpm_range": (60, 120),
        "bass_prominence": (20, 45),
        "drum_pattern": None,
        "danceability_min": 0.3
    },
    "Trap Soul": {
        "bpm_range": (60, 100),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.3
    },
    "House": {
        "bpm_range": (118, 132),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.7
    },
    "Future House": {
        "bpm_range": (124, 132),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.7
    },
    "Future Bass": {
        "bpm_range": (130, 175),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Driving (Dance/EDM)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.6
    },
    "EDM / Big Room": {
        "bpm_range": (126, 132),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.8
    },
    "UK Garage": {
        "bpm_range": (128, 135),
        "bass_prominence": (25, 40),
        "drum_pattern": ["Driving (Dance/EDM)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.7
    },
    "Miami Bass": {
        "bpm_range": (125, 145),
        "bass_prominence": (35, 50),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.7
    },
    "Electro": {
        "bpm_range": (110, 140),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.6
    },
    "Reggaeton": {
        "bpm_range": (85, 100),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.7
    },
    "Pop Rock": {
        "bpm_range": (100, 150),
        "bass_prominence": (15, 35),
        "drum_pattern": ["Moderate (Pop/R&B)", "Driving (Dance/EDM)"],
        "danceability_min": 0.5
    },
    "Pop Ballad": {
        "bpm_range": (55, 85),
        "bass_prominence": (10, 30),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.1
    },
    "R&B Ballad": {
        "bpm_range": (55, 90),
        "bass_prominence": (15, 35),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.1
    },
    "K-Ballad": {
        "bpm_range": (55, 85),
        "bass_prominence": (10, 30),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)"],
        "danceability_min": 0.1
    },
    "Funk": {
        "bpm_range": (95, 130),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Moderate (Pop/R&B)", "Driving (Dance/EDM)"],
        "danceability_min": 0.7
    },
    "Disco": {
        "bpm_range": (110, 135),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.7
    },

    # --- Tier 2 (Adjacent) - 주요 장르만 ---
    "Boom Bap": {
        "bpm_range": (80, 100),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.4
    },
    "Phonk": {
        "bpm_range": (130, 160),
        "bass_prominence": (30, 50),
        "drum_pattern": ["Driving (Dance/EDM)", "Sparse (Trap/Hip-Hop)"],
        "danceability_min": 0.5
    },
    "Cloud Rap": {
        "bpm_range": (60, 90),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)"],
        "danceability_min": 0.3
    },
    "New Jack Swing": {
        "bpm_range": (100, 120),
        "bass_prominence": (20, 35),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.6
    },
    "Neo Soul": {
        "bpm_range": (70, 110),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.4
    },
    "Jersey Club": {
        "bpm_range": (128, 142),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.7
    },
    "Drum and Bass": {
        "bpm_range": (165, 185),
        "bass_prominence": (30, 50),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.6
    },
    "Amapiano": {
        "bpm_range": (108, 122),
        "bass_prominence": (30, 45),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.6
    },
    "Afrobeats": {
        "bpm_range": (95, 120),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.6
    },
    "Afro Swing": {
        "bpm_range": (95, 115),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.6
    },
    "Dancehall": {
        "bpm_range": (90, 110),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Moderate (Pop/R&B)"],
        "danceability_min": 0.6
    },
    "Breakbeat": {
        "bpm_range": (120, 150),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.5
    },
    "Trip-Hop": {
        "bpm_range": (70, 100),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)", "Moderate (Pop/R&B)"],
        "danceability_min": 0.3
    },
    "Bossa Nova": {
        "bpm_range": (60, 90),
        "bass_prominence": (10, 25),
        "drum_pattern": ["Sparse (Trap/Hip-Hop)"],
        "danceability_min": 0.3
    },
    "J-Pop": {
        "bpm_range": (110, 160),
        "bass_prominence": (15, 35),
        "drum_pattern": ["Moderate (Pop/R&B)", "Driving (Dance/EDM)"],
        "danceability_min": 0.5
    },
    "Shoegaze": {
        "bpm_range": (80, 130),
        "bass_prominence": (20, 40),
        "drum_pattern": None,
        "danceability_min": 0.2
    },
    "Eurodance": {
        "bpm_range": (130, 150),
        "bass_prominence": (20, 40),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.7
    },
    "Footwork": {
        "bpm_range": (155, 170),
        "bass_prominence": (25, 45),
        "drum_pattern": ["Driving (Dance/EDM)"],
        "danceability_min": 0.6
    }
}


def verify_genre_match(genre_name, audio_features):
    """
    오디오 feature로 장르 매칭을 검증.
    Returns: score (0.0 ~ 1.0), reasons list
    """
    if genre_name not in GENRE_PROFILES:
        return None, ["프로필 없음 — CLAP 점수만 사용"]

    profile = GENRE_PROFILES[genre_name]
    score = 0.0
    max_score = 0.0
    reasons = []

    # BPM 검증 (drum_bpm 우선, 없으면 bpm)
    bpm = audio_features.get("drum_bpm") or audio_features.get("bpm", 0)
    if profile["bpm_range"]:
        max_score += 1.0
        low, high = profile["bpm_range"]
        if low <= bpm <= high:
            score += 1.0
            reasons.append(f"BPM {bpm} ✓ ({low}-{high})")
        else:
            # 범위 밖이지만 가까우면 부분 점수
            distance = min(abs(bpm - low), abs(bpm - high))
            partial = max(0, 1.0 - distance / 30)
            score += partial
            reasons.append(f"BPM {bpm} △ ({low}-{high}, -{distance})")

    # Bass prominence 검증
    bass = audio_features.get("stems", {}).get("bass", {}).get("prominence", 0)
    if profile["bass_prominence"]:
        max_score += 1.0
        low, high = profile["bass_prominence"]
        if low <= bass <= high:
            score += 1.0
            reasons.append(f"Bass {bass}% ✓ ({low}-{high})")
        else:
            distance = min(abs(bass - low), abs(bass - high))
            partial = max(0, 1.0 - distance / 15)
            score += partial
            reasons.append(f"Bass {bass}% △ ({low}-{high})")

    # Drum pattern 검증
    drum = audio_features.get("drum_pattern", "")
    if profile["drum_pattern"]:
        max_score += 1.0
        if drum in profile["drum_pattern"]:
            score += 1.0
            reasons.append(f"Drum '{drum}' ✓")
        else:
            reasons.append(f"Drum '{drum}' ✗ (expected: {profile['drum_pattern']})")

    # Danceability 검증
    dance = audio_features.get("danceability", 0)
    if profile["danceability_min"] is not None:
        max_score += 1.0
        if dance >= profile["danceability_min"]:
            score += 1.0
            reasons.append(f"Dance {dance:.2f} ✓ (>={profile['danceability_min']})")
        else:
            partial = dance / profile["danceability_min"]
            score += partial
            reasons.append(f"Dance {dance:.2f} △ (>={profile['danceability_min']})")

    final = score / max_score if max_score > 0 else 0.5
    return final, reasons