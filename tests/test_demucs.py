import replicate
import os
from dotenv import load_dotenv

load_dotenv()  # .env 에서 REPLICATE_API_TOKEN 로드

print("1. 파일 업로드 중...")
client = replicate.Client(
    api_token=os.environ["REPLICATE_API_TOKEN"],
    timeout=300
)

print("2. Demucs 실행 요청 중...")
prediction = client.predictions.create(
    version="25a173108cff36ef9f80f854c162d01df9e6528be175794b81158fa03836d953",
    input={
        "audio": open("test_song.webm", "rb"),
        "model_name": "htdemucs",
        "output_format": "mp3",
        "mp3_bitrate": 320,
    }
)

print(f"3. 처리 중... (ID: {prediction.id})")
prediction.wait()

print(f"4. 상태: {prediction.status}")
print(f"결과: {prediction.output}")