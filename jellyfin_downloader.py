import os
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BASE_DIR = "/mnt/nas"
COOKIES_FILE = "/app/cookies.txt"

# 컨테이너 내부 Python (Flask 실행 Python과 동일)
PYTHON_BIN = "python"

current_process = None


@app.route('/')
def index():
    return render_template('downloader.html')


@app.route('/list_dir', methods=['POST'])
def list_dir():
    req_data = request.get_json()
    path = req_data.get('path') if req_data and req_data.get('path') else BASE_DIR
    abs_path = os.path.realpath(path)

    if not abs_path.startswith(os.path.realpath(BASE_DIR)):
        abs_path = os.path.realpath(BASE_DIR)

    try:
        if not os.path.exists(abs_path):
            return jsonify({"error": "경로 없음", "items": [], "current_path": abs_path}), 200

        items = []
        if abs_path != os.path.realpath(BASE_DIR):
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
    target_path = data.get('path')
    use_cookies = data.get('use_cookies', False)

    try:
        start = int(data.get('start', 0))
        end = int(data.get('end', 30))
    except ValueError:
        return jsonify({"status": "error", "msg": "시작/종료 값은 숫자여야 합니다."})

    if start < 0 or end <= start:
        return jsonify({"status": "error", "msg": "구간 값이 올바르지 않습니다."})

    if not url or not target_path:
        return jsonify({"status": "error", "msg": "URL 또는 경로가 없습니다."})

    output_file = os.path.join(target_path, "theme.mp3")

    cmd = [
        PYTHON_BIN, "-m", "yt_dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--download-sections", f"*{start}-{end}",
        "--force-overwrites",
        "-f", "ba/best",
        "-o", output_file,
        url
    ]

    if use_cookies and os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])

    try:
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
