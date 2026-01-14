FROM python:3.11-slim

# ffmpeg(변환), nodejs 및 npm(JS 챌린지 해결용) 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# yt-dlp가 'node' 명령어를 찾을 수 있도록 심볼릭 링크 생성
RUN ln -s /usr/bin/nodejs /usr/bin/node || true

WORKDIR /app

# 의존성 설치 및 yt-dlp 최신 버전 강제 업데이트
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --upgrade yt-dlp

COPY . .

EXPOSE 9011

CMD ["python", "jellyfin_downloader.py"]