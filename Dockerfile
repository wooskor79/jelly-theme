FROM python:3.11-slim

# 시스템 패키지 업데이트 및 Node.js(JS 런타임) 설치
# yt-dlp가 n-challenge를 해결하기 위해 반드시 필요합니다.
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 설치 (yt-dlp 최신 버전 보장)
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -U -r requirements.txt

COPY . .

EXPOSE 9011

# 파이통 출력 버퍼링 해제
ENV PYTHONUNBUFFERED=1

CMD ["python", "jellyfin_downloader.py"]