FROM python:3.11-slim

# 시스템 패키지 업데이트 및 설치
# yt-dlp의 n-challenge 해결을 위한 nodejs/npm
# 오디오 추출 및 구간 자르기를 위한 ffmpeg (필수!)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 설치 (yt-dlp 최신 버전 보장)
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -U -r requirements.txt

COPY . .

EXPOSE 9011

# 파이썬 출력 버퍼링 해제
ENV PYTHONUNBUFFERED=1

CMD ["python", "jellyfin_downloader.py"]