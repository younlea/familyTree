import http.server
import socketserver
import json
import os
import argparse
import sys

# 기본 설정
PORT = 8000
DB_FILE = "db.json"
EDIT_MODE = False  # 기본은 수정 불가 (View Mode)

# 인자 파싱 (Launch Arguments)
parser = argparse.ArgumentParser(description='침교택파 족보 서버')
parser.add_argument('--edit', action='store_true', help='수정 모드로 실행 (좌표 따기 기능 활성화)')
parser.add_argument('--port', type=int, default=8000, help='서버 포트 설정 (기본: 8000)')
args = parser.parse_args()

EDIT_MODE = args.edit
PORT = args.port

class ThreadingSimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """동시 접속을 처리하기 위한 멀티스레드 서버"""
    pass

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # [API] 현재 서버가 수정 모드인지 확인
        if self.path == '/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            config_data = {"edit_mode": EDIT_MODE}
            self.wfile.write(json.dumps(config_data).encode('utf-8'))
        else:
            # 나머지는 일반 파일 서빙 (html, image 등)
            super().do_GET()

    def do_POST(self):
        if self.path == '/add_coordinate':
            # [보안] 수정 모드가 아니면 요청 거부
            if not EDIT_MODE:
                self.send_error(403, "Forbidden: Server is in View-Only mode.")
                return

            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                new_data = json.loads(post_data.decode('utf-8'))
                
                # 기존 DB 로드
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, 'r', encoding='utf-8') as f:
                        try:
                            current_db = json.load(f)
                        except json.JSONDecodeError:
                            current_db = []
                else:
                    current_db = []

                current_db.append(new_data)
                
                # 저장
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(current_db, f, indent=4, ensure_ascii=False)

                print(f"✅ [저장됨] {new_data['n']}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ 오류: {e}")
                self.send_error(500, str(e))
        else:
            self.send_error(404)

print("="*40)
print(f"🚀 침교택파 족보 서버 가동")
print(f"📡 주소: http://localhost:{PORT}")
print(f"👥 모드: {'[🛠 관리자 수정 모드]' if EDIT_MODE else '[👁 가족용 뷰어 모드]'}")
if not EDIT_MODE:
    print("   (수정하려면 'python server.py --edit' 으로 실행하세요)")
print("="*40)

# 멀티스레드 서버 실행
with ThreadingSimpleServer(("", PORT), RequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 서버를 종료합니다.")
        sys.exit(0)