FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 컨테이너 내부 포트 개방
EXPOSE 9011
CMD ["python", "jellyfin_downloader.py"]