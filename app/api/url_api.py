from flask import Blueprint, request, jsonify, session
import uuid
import secrets
from app.api.upload_api import meetings_db

url_bp = Blueprint("url", __name__)

# URL 공유 데이터 저장 (실제로는 MongoDB에 저장)
shared_urls = {}

@url_bp.route("/api/url/generate/<meeting_id>", methods=["POST"])
def generate_share_url(meeting_id):
    """공유 URL 생성"""
    if meeting_id not in meetings_db:
        return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
    
    meeting_data = meetings_db[meeting_id]
    
    # 공유용 고유 토큰 생성
    share_token = str(uuid.uuid4())
    
    # 공유 데이터 저장 (인증키는 회의 원래 비밀번호 사용)
    shared_urls[share_token] = {
        "meeting_id": meeting_id,
        "requires_password": meeting_data.get("password") is not None,
        "created_at": meeting_data["created_at"],
        "expires_at": None  # 필요시 만료 시간 설정
    }
    
    # 공유 URL 생성
    share_url = f"/shared/{share_token}"
    
    return jsonify({
        "status": "success",
        "message": "공유 URL 생성 완료",
        "data": {
            "share_url": share_url,
            "meeting_id": meeting_id,
            "meeting_name": meeting_data["name"],
            "requires_password": meeting_data.get("password") is not None
        }
    })

@url_bp.route("/shared/<share_token>", methods=["GET"])
def view_shared_meeting(share_token):
    """공유된 회의 보기 (비밀번호 입력 페이지 또는 바로 접근)"""
    if share_token not in shared_urls:
        return "유효하지 않은 공유 링크입니다.", 404
    
    shared_data = shared_urls[share_token]
    meeting_id = shared_data["meeting_id"]
    
    if meeting_id not in meetings_db:
        return "회의 데이터를 찾을 수 없습니다.", 404
    
    meeting_data = meetings_db[meeting_id]
    
    # 비밀번호가 필요하지 않은 경우 바로 회의 페이지로 리다이렉트
    if not shared_data["requires_password"]:
        from flask import redirect
        return redirect(f"/result/{meeting_id}")
    
    # 비밀번호가 필요한 경우 인증 페이지 렌더링
    return f'''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>회의 접근 - {meeting_data["name"]}</title>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background-color: #f8f9fa;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            .auth-container {{
                background-color: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                text-align: center;
                max-width: 400px;
                width: 100%;
            }}
            h2 {{
                color: #007bff;
                margin-bottom: 30px;
            }}
            .meeting-info {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 4px;
                margin-bottom: 30px;
            }}
            .notice {{
                background-color: #fff3cd;
                padding: 15px;
                border-radius: 4px;
                border-left: 4px solid #ffc107;
                margin-bottom: 30px;
                font-size: 14px;
            }}
            input[type="password"] {{
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
                margin-bottom: 20px;
                box-sizing: border-box;
            }}
            button {{
                background-color: #007bff;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
            }}
            button:hover {{
                background-color: #0056b3;
            }}
            .error {{
                color: #dc3545;
                margin-top: 10px;
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="auth-container">
            <h2>회의 접근</h2>
            <div class="meeting-info">
                <strong>{meeting_data["name"]}</strong><br>
                <small>{meeting_data["date"]}</small>
            </div>
            <div class="notice">
                이 회의는 비밀번호로 보호되어 있습니다.<br>
                회의 생성 시 설정된 비밀번호를 입력해주세요.
            </div>
            <form id="authForm">
                <input type="password" id="password" placeholder="회의 비밀번호를 입력하세요" required>
                <button type="submit">회의 보기</button>
            </form>
            <div class="error" id="errorMsg">비밀번호가 올바르지 않습니다.</div>
        </div>
        
        <script>
            document.getElementById('authForm').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                const password = document.getElementById('password').value;
                const errorMsg = document.getElementById('errorMsg');
                
                try {{
                    const response = await fetch('/api/url/verify/{share_token}', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ password: password }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {{
                        window.location.href = `/result/${{data.data.meeting_id}}`;
                    }} else {{
                        errorMsg.style.display = 'block';
                    }}
                }} catch (error) {{
                    errorMsg.style.display = 'block';
                }}
            }});
        </script>
    </body>
    </html>
    '''

@url_bp.route("/api/url/verify/<share_token>", methods=["POST"])
def verify_auth_key(share_token):
    """비밀번호 검증"""
    if share_token not in shared_urls:
        return jsonify({"error": "유효하지 않은 공유 링크입니다"}), 404
    
    data = request.get_json()
    password = data.get("password")
    
    if not password:
        return jsonify({"error": "비밀번호가 필요합니다"}), 400
    
    shared_data = shared_urls[share_token]
    meeting_id = shared_data["meeting_id"]
    
    if meeting_id not in meetings_db:
        return jsonify({"error": "회의 데이터를 찾을 수 없습니다"}), 404
    
    meeting_data = meetings_db[meeting_id]
    
    # 회의 원래 비밀번호와 비교
    if password == meeting_data.get("password"):
        # 세션에 인증 상태 저장
        auth_key = f"meeting_auth_{meeting_id}"
        session[auth_key] = True
        
        return jsonify({
            "status": "success",
            "message": "인증 성공",
            "data": {
                "meeting_id": meeting_id
            }
        })
    else:
        return jsonify({
            "status": "error", 
            "message": "비밀번호가 올바르지 않습니다"
        }), 401
