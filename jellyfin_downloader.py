import os
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# NAS 마운트 경로
BASE_DIR = "/mnt/nas"

# 유튜브 쿠키 파일
COOKIES_FILE = "/app/cookies.txt"

current_process = None

@app.route('/')
def index():
    return render_template('downloader.html')

@app.route('/list_dir', methods=['POST'])
def list_dir():
    req_data = request.get_json()
    path = req_data.get('path') if req_data and req_data.get('path') else BASE_DIR
    abs_path = os.path.abspath(path)

    if not abs_path.startswith(os.path.abspath(BASE_DIR)):
        abs_path = os.path.abspath(BASE_DIR)

    try:
        if not os.path.exists(abs_path):
            return jsonify({"error": "경로 없음", "items": [], "current_path": abs_path}), 200

        items = []
        if abs_path != os.path.abspath(BASE_DIR):
            parent = os.path.dirname(abs_path)
            items.append({"name": ".. (상위 폴더)", "path": parent, "icon": "⬆️"})

        for name in os.listdir(abs_path):
            full_path = os.path.join(abs_path, name)
            if os.path.isdir(full_path) and not name.startswith(('.', '#', '@')):
                items.append({"name": name, "path": full_path, "icon": "📁"})

        return jsonify({
            "current_path": abs_path,
            "items": sorted(items, key=lambda x: (x['name'] != ".. (상위 폴더)", x['name']))
        })
    except Exception as e:
        return jsonify({"error": str(e), "items": []}), 500

@app.route('/download', methods=['POST'])
def download():
    global current_process
    data = request.get_json()

    url = data.get('url')
    start = data.get('start', 0)
    end = data.get('end', 30)
    target_path = data.get('path')
    use_cookies = data.get('use_cookies', False) # 쿠키 사용 옵션

    if not url or not target_path:
        return jsonify({"status": "error", "msg": "URL 또는 경로가 없습니다."})

    output_file = os.path.join(target_path, "theme.mp3")

    # yt-dlp 명령어 최적화
    # m4a(ba)를 먼저 시도하고 mp3로 변환하는 것이 가장 안정적입니다.
    cmd = [
        "python", "-m", "yt_dlp",
        "-x",                           # 오디오 추출
        "--audio-format", "mp3",        # mp3 변환
        "--audio-quality", "0", 
        "--download-sections", f"*{start}-{end}",
        "--force-overwrites",
        "-f", "ba/best",                # 최고의 오디오 포맷 선택
        "--no-check-certificate",
        "--prefer-free-formats",        # 호환성 높은 포맷 우선
        "-o", output_file,
        url
    ]

    # 사용자가 쿠키 사용을 체크했고, 파일이 실제로 존재할 때만 옵션 추가
    if use_cookies and os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])

    try:
        # 로그 수집 방식 개선 (stderr를 stdout으로 통합)
        current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        stdout, _ = current_process.communicate()

        if current_process.returncode == 0:
            return jsonify({"status": "success", "msg": "성공: theme.mp3 저장 완료!"})
        else:
            return jsonify({"status": "error", "msg": "다운로드 실패", "log": stdout})

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})
    finally:
        current_process = None

@app.route('/stop', methods=['POST'])
def stop_download():
    global current_process
    if current_process and current_process.poll() is None:
        current_process.terminate()
        return jsonify({"status": "success", "msg": "중지 명령을 보냈습니다."})
    return jsonify({"status": "error", "msg": "현재 실행 중인 작업이 없습니다."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9011)