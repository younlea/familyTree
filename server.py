import http.server
import socketserver
import json
import os
import argparse
import sys

# 설정
PORT = 8000
DB_FILE = "db.json"
EDIT_MODE = False

# 실행 인자 파싱
parser = argparse.ArgumentParser()
parser.add_argument('--edit', action='store_true', help='수정 모드 활성화')
parser.add_argument('--port', type=int, default=8000, help='포트 번호 설정')
args = parser.parse_args()

EDIT_MODE = args.edit
PORT = args.port

# [핵심 수정] 재실행 시 'Address already in use' 에러 방지
class ReusableThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True  # <-- 이 줄이 에러를 막아줍니다!
    daemon_threads = True

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"edit_mode": EDIT_MODE}).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/add_coordinate':
            if not EDIT_MODE:
                self.send_error(403, "수정 모드가 아닙니다.")
                return

            try:
                length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(length).decode('utf-8'))
                
                # DB 로드 및 업데이트
                current_db = []
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, 'r', encoding='utf-8') as f:
                        try: current_db = json.load(f)
                        except: pass

                # 같은 이름이 있으면 덮어쓰기 (수정 기능), 없으면 추가
                updated = False
                for item in current_db:
                    if item['n'] == data['n']:
                        item.update(data) # 좌표 갱신
                        updated = True
                        break
                if not updated:
                    current_db.append(data)
                
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(current_db, f, indent=4, ensure_ascii=False)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                print(f"✅ 저장됨: {data['n']}")
                
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

print(f"🚀 족보 서버 가동 (http://localhost:{PORT})")
print(f"🔧 모드: {'관리자(수정 가능)' if EDIT_MODE else '뷰어(조회 전용)'}")

with ReusableThreadingServer(("", PORT), RequestHandler) as httpd:
    try: httpd.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
