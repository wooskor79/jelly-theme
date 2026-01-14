import os
import subprocess
import signal
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 도커 내부 마운트 경로 설정
BASE_DIR = "/mnt/nas" 
COOKIES_FILE = "/app/cookies.txt"

# 현재 실행 중인 다운로드 프로세스를 저장할 전역 변수
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
    
    output_file = os.path.join(target_path, "theme.mp3")
    
    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3",
        "--download-sections", f"*{start}-{end}",
        "--force-overwrites"
    ]

    if os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
    
    cmd.extend(["-o", output_file, url])
    
    try:
        # 프로세스 비동기 실행
        current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = current_process.communicate()
        
        if current_process.returncode == 0:
            return jsonify({"status": "success", "msg": "성공, theme.mp3 저장 완료!"})
        else:
            # SIGTERM(-15) 등으로 중지된 경우
            if current_process.returncode == -15:
                return jsonify({"status": "stopped", "msg": "사용자에 의해 작업이 강제 중지되었습니다."})
            return jsonify({"status": "error", "msg": "다운로드 실패", "log": stderr})
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