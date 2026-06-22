"""
Freesound 드럼루프 수집기
FSLD 중복 제외 + 장르별 세부 검색
"""

import requests
import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('FREESOUND_API_KEY')

# FSLD Freesound ID 추출 (중복 제외용)
FSLD_DIR = Path("/Volumes/One Touch/audio/wav/")
fsld_ids = set()
for f in FSLD_DIR.glob("*.wav"):
    parts = f.stem.replace('.wav', '').split('_')
    if len(parts) >= 2:
        fsld_ids.add(parts[1])
print(f'FSLD 기존 ID: {len(fsld_ids)}개')

# 장르별 검색어
GENRE_QUERIES = {
    'Disco': [
        'disco drum loop', 'disco beat', 'disco funk drums',
        '4-on-the-floor', 'funky drum loop', 'groovy drum loop',
        'funk drum beat', 'classic disco', 'disco groove'
    ],
    'Electropop': [
        'electropop drum loop', 'synth pop beat', 'electronic pop drums',
        'synthpop drums', '80s drum loop', 'electronic beat loop',
        'new wave drum', 'pop electronic drums', 'indie electronic beat'
    ],
    'Boom_Bap': [
        'boom bap drum loop', 'hip hop drums', 'old school hip hop beat',
        'classic hip hop loop', 'rap drum loop', 'breakbeat hip hop',
        '90s hip hop drums', 'golden era hip hop', 'lo fi hip hop beat'
    ],
}

TARGET_PER_GENRE = 300
OUTPUT_DIR = Path("/Volumes/One Touch/freesound_drums/")
OUTPUT_DIR.mkdir(exist_ok=True)

def search_sounds(query, page=1):
    url = "https://freesound.org/apiv2/search/text/"
    params = {
        'query': query,
        'filter': 'tag:loop tag:drum duration:[1 TO 30]',
        'fields': 'id,name,tags,license,previews,duration',  # previews 추가
        'page_size': 150,
        'page': page,
        'token': API_KEY
    }
    resp = requests.get(url, params=params)
    return resp.json() if resp.status_code == 200 else None

def download_sound(sound, filepath):
    # preview mp3 사용 (인증 불필요)
    preview_url = sound.get('previews', {}).get('preview-hq-mp3')
    if not preview_url:
        return False
    
    resp = requests.get(preview_url, stream=True)
    if resp.status_code == 200:
        mp3_path = str(filepath).replace('.wav', '.mp3')
        with open(mp3_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False

# 수집 실행
results = {}
for genre, queries in GENRE_QUERIES.items():
    genre_dir = OUTPUT_DIR / genre
    genre_dir.mkdir(exist_ok=True)
    
    existing = set(
    f.stem for f in genre_dir.glob('*.mp3')
    if not f.name.startswith('._')
    )
    quarantine = genre_dir / 'quarantine'
    existing.update(
        f.stem for f in quarantine.glob('*.mp3')
        if quarantine.exists() and not f.name.startswith('._')
    )
    collected = len(existing)
    print(f'\n[{genre}] 목표: {TARGET_PER_GENRE}개 | 기존: {collected}개')
    
    for query in queries:
        if collected >= TARGET_PER_GENRE:
            break
        
        data = search_sounds(query)
        if not data:
            continue
            
        for sound in data.get('results', []):
            if collected >= TARGET_PER_GENRE:
                break
            
            sid = str(sound['id'])
            
            # FSLD 중복 제외
            if sid in fsld_ids:
                continue
            
            # CC 라이선스 확인
            license = sound.get('license', '')
            if 'creativecommons' not in license:
                continue
            
            filename = f"freesound_{sid}.wav"
            if filename.replace('.wav', '') in existing:
                continue
            
            filepath = genre_dir / filename
            if download_sound(sound, filepath):
                collected += 1
                existing.add(filename.replace('.wav', ''))
                print(f'  [{collected}/{TARGET_PER_GENRE}] {sound["name"][:50]}')
                time.sleep(0.5)  # rate limit
    
    results[genre] = collected
    print(f'[{genre}] 완료: {collected}개')

# 결과 저장
with open(OUTPUT_DIR / 'collection_results.json', 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print('\n=== 최종 결과 ===')
for genre, count in results.items():
    print(f'  {genre:20s} {count}개')
    
    # 테스트용 — 맨 아래에 추가
data = search_sounds('disco drum loop')
if data and data.get('results'):
    sound = data['results'][0]
    print(f'테스트 곡: {sound["id"]} - {sound["name"]}')
    download_sound(sound['id'], Path('/tmp/test_disco.wav'))
    
