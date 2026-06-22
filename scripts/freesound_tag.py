"""
Freesound 메타데이터 재수집 + 장르 필터링
저장된 freesound_{id}.mp3에서 id 추출 → API로 태그 가져오기
"""

import requests
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv('FREESOUND_API_KEY')

FREESOUND_DIR = Path("/Volumes/One Touch/freesound_drums/")

# 장르별 필수 태그 키워드
GENRE_TAGS = {
    'Hip_Hop': ['hip-hop', 'hiphop', 'rap', 'hip', 'hop', 'boom', 'bap', 'beat', 'break'],
}

def get_sound_metadata(sound_id):
    url = f"https://freesound.org/apiv2/sounds/{sound_id}/"
    params = {
        'fields': 'id,name,tags,license',
        'token': API_KEY
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json()
    print(f'  API 에러 {sound_id}: {resp.status_code} {resp.text[:100]}')
    return None

results = {}

for genre_dir in sorted(FREESOUND_DIR.iterdir()):
    if not genre_dir.is_dir():
        continue
    
    if genre_dir.name not in ['Hip_Hop']:
        
        continue

    genre = genre_dir.name
    required_tags = GENRE_TAGS.get(genre, [])
    
    files = list(genre_dir.glob('freesound_*.mp3'))
    print(f'\n[{genre}] {len(files)}개 파일 메타데이터 수집 중...')
    
    metadata = []
    keep = []
    remove = []
    
    for f in files:
        sound_id = f.stem.replace('freesound_', '')
        meta = get_sound_metadata(sound_id)
        
        if not meta:
            remove.append(f)
            continue
        
        tags = [t.lower() for t in meta.get('tags', [])]
        name = meta.get('name', '').lower()
        
        # 장르 태그 포함 여부 확인
        matched = any(tag in tags or tag in name for tag in required_tags)
        
        metadata.append({
            'id': sound_id,
            'file': f.name,
            'name': meta.get('name'),
            'tags': meta.get('tags'),
            'keep': matched
        })
        
        if matched:
            keep.append(f)
        else:
            remove.append(f)
        
        time.sleep(0.3)
    
    # 메타데이터 저장
    with open(genre_dir / 'metadata.json', 'w', encoding='utf-8') as fp:
        json.dump(metadata, fp, indent=2, ensure_ascii=False)
    
    print(f'  유지: {len(keep)}개 | 제거: {len(remove)}개')
    results[genre] = {'keep': len(keep), 'remove': len(remove)}
    
    # 제거할 파일 이동 (삭제 말고 quarantine 폴더로)
    quarantine = genre_dir / 'quarantine'
    quarantine.mkdir(exist_ok=True)
    for f in remove:
        f.rename(quarantine / f.name)

print('\n=== 최종 결과 ===')
for genre, r in results.items():
    print(f'  {genre:20s} 유지: {r["keep"]}개 | 제거: {r["remove"]}개')