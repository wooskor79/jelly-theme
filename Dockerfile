# Python 3.11 기반 (이미 컨테이너가 3.11 계열이었음)
FROM python:3.11-slim

# 환경 변수
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ffmpeg 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# requirements 먼저 복사 (캐시 활용)
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY jellyfin_downloader.py .
COPY templates ./templates

# (선택) 쿠키 파일이 있다면 사용
# COPY cookies.txt /app/cookies.txt

# 포트
EXPOSE 9011

# Flask 실행
CMD ["python", "jellyfin_downloader.py"]
