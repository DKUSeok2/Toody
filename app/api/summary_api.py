from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from app.services.summary_service import SummaryService
from app.utils.file_utils import extract_text_from_file
import re
import os
from datetime import datetime

summary_bp = Blueprint("summary", __name__)

# upload_api에서 meetings_db와 save_meetings_data 가져오기
from app.api.upload_api import meetings_db, save_meetings_data, get_or_create_user_id

# 요약 생성 API 엔드포인트
@summary_bp.route("/api/summary", methods=["POST"])
def generate_summary():
    """회의 ID로 요약 조회 또는 생성"""
    try:
        data = request.get_json()
        meeting_id = data.get("meeting_id")
        
        if not meeting_id:
            return jsonify({"error": "meeting_id가 필요합니다"}), 400
        
        if meeting_id not in meetings_db:
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        meeting_data = meetings_db[meeting_id]
        
        # 이미 생성된 요약이 있는지 확인
        if meeting_data.get("summary"):
            return jsonify({
                "status": "success",
                "data": {"summary": meeting_data["summary"]}
            })
        
        # 요약이 없으면 원본 텍스트로 새로 생성
        original_text = meeting_data.get("original_text", "")
        if not original_text:
            return jsonify({"error": "원본 텍스트가 없습니다"}), 400
        
        # 요약 서비스로 새로 생성
        result = SummaryService.summarize_and_extract_todo(original_text)
        
        # 결과 저장
        meetings_db[meeting_id]["summary"] = result['summary']
        if not meeting_data.get("todo_result"):
            meetings_db[meeting_id]["todo_result"] = result['todo_result']
        
        # 데이터 저장
        save_meetings_data(meetings_db)
        
        return jsonify({
            "status": "success",
            "data": {"summary": result['summary']}
        })
        
    except Exception as e:
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500

# 새로운 JSON API 엔드포인트 추가
@summary_bp.route("/api/meeting/<meeting_id>", methods=["GET"])
def get_meeting_data(meeting_id):
    """회의 데이터를 JSON으로 반환 (프론트엔드용)"""
    try:
        if meeting_id not in meetings_db:
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        meeting_data = meetings_db[meeting_id]
        
        # 1단계: 생성자 확인 (세션 + URL 파라미터 + 그룹 접근 권한)
        accessible_meetings = session.get('accessible_meetings', [])
        accessible_groups = session.get('accessible_groups', [])
        is_creator_by_session = meeting_id in accessible_meetings
        is_creator_by_param = request.args.get('creator') == 'true'
        
        # 같은 그룹 내 다른 회의에 접근 권한이 있는지 확인
        group_id = meeting_data.get("group_id", meeting_id)
        has_group_access = group_id in accessible_groups
        
        # 또는 같은 그룹의 다른 회의에 접근 권한이 있는지 확인
        has_indirect_group_access = False
        for accessible_id in accessible_meetings:
            if accessible_id in meetings_db:
                accessible_group_id = meetings_db[accessible_id].get("group_id", accessible_id)
                if accessible_group_id == group_id:
                    has_indirect_group_access = True
                    break
        
        is_creator = is_creator_by_session or is_creator_by_param or has_group_access or has_indirect_group_access
        
        # 2단계: 비밀번호가 설정된 회의인지 확인
        password_authenticated = False
        if meeting_data.get("password") and not is_creator:
            # 외부 접근자는 비밀번호 필요
            password = request.args.get("password")
            stored_password = meeting_data["password"]
            
            if not password or password != stored_password:
                return jsonify({"error": "올바른 비밀번호를 입력해주세요"}), 401
            else:
                password_authenticated = True

        # 접근 권한이 있는 경우 세션에 추가 (다음 접근을 위해)
        if is_creator and meeting_id not in accessible_meetings:
            session['accessible_meetings'] = accessible_meetings + [meeting_id]
            session.modified = True
        
        # 그룹 접근 권한도 세션에 추가
        if is_creator and group_id not in accessible_groups:
            session['accessible_groups'] = accessible_groups + [group_id]
            session.modified = True
        
        # 공유 링크로 접속해서 비밀번호를 입력한 경우, 같은 그룹의 모든 회의에 접근 권한 부여
        if password_authenticated:
            # 같은 그룹의 모든 회의를 accessible_meetings에 추가
            group_meeting_ids = []
            for other_meeting_id, other_meeting_data in meetings_db.items():
                if other_meeting_data.get("group_id") == group_id:
                    group_meeting_ids.append(other_meeting_id)
            
            # 세션에 그룹의 모든 회의 접근 권한 추가
            session['accessible_meetings'] = list(set(accessible_meetings + group_meeting_ids))
            if group_id not in accessible_groups:
                session['accessible_groups'] = accessible_groups + [group_id]
            session.modified = True
            print(f"🔑 공유 링크 비밀번호 인증 완료: 그룹 {group_id}의 {len(group_meeting_ids)}개 회의 접근 권한 부여")
        
        # 반환할 데이터 준비 (다른 API와 일관성 맞추기)
        # todo_result를 todos 형태로 변환
        todos = []
        if meeting_data.get("todo_result"):
            todo_result = meeting_data["todo_result"]
            
            if isinstance(todo_result, dict):
                generated_todo = todo_result.get("generated_todo", "")
                
                # 생성된 TODO 문자열을 파싱하여 구조화된  형태로 변환
                import re
                lines = [line.strip() for line in generated_todo.split('\n') if line.strip()]
                
                for line in lines:
                    # "1. 작업 내용 (담당자: 홍길동, 기한: 2024-01-01)" 형태 파싱
                    match = re.match(r'^(\d+)\.\s*(.+?)(?:\s*\(담당자:\s*([^,)]+)(?:,\s*기한:\s*([^)]+))?\))?$', line)
                    if match:
                        task_num, task_desc, assignee, deadline = match.groups()
                        todos.append({
                            "task": task_desc.strip(),
                            "assignee": assignee.strip() if assignee else "",
                            "deadline": deadline.strip() if deadline else "",
                            "priority": "보통",  # 기본값
                            "category": "일반"   # 기본값
                        })
                    elif re.match(r'^\d+\.', line):  # 번호가 있는 경우
                        task_desc = re.sub(r'^\d+\.\s*', '', line)
                        todos.append({
                            "task": task_desc.strip(),
                            "assignee": "",
                            "deadline": "",
                            "priority": "보통",
                            "category": "일반"
                        })
        
        response_data = {
            "meeting_id": meeting_id,
            "name": meeting_data["name"],
            "date": meeting_data["date"],
            "summary": meeting_data.get("summary"),
            "todos": todos,
            "transcript": meeting_data.get("original_text")  # 원본 텍스트가 있다면
        }
        
        return jsonify({
            "status": "success",
            "data": response_data
        })
        
    except Exception as e:
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500

@summary_bp.route("/api/meeting/<meeting_id>/history", methods=["GET"])
def get_meeting_group_history(meeting_id):
    """회의 그룹의 전체 히스토리 조회"""
    try:
        if meeting_id not in meetings_db:
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        current_meeting = meetings_db[meeting_id]
        group_id = current_meeting.get("group_id", meeting_id)
        
        # 같은 그룹의 모든 회의 찾기
        group_meetings = []
        for mid, meeting_data in meetings_db.items():
            if meeting_data.get("group_id") == group_id:
                # 비밀번호 제거 후 추가
                meeting_copy = meeting_data.copy()
                if "password" in meeting_copy:
                    del meeting_copy["password"]
                
                # TODO 데이터 간소화
                if meeting_copy.get("todo_result") and isinstance(meeting_copy["todo_result"], dict):
                    todo_data = meeting_copy["todo_result"].get("generated_todo", "")
                    if todo_data:
                        # TODO를 간단한 리스트로 변환
                        todo_lines = [line.strip() for line in todo_data.split('\n') if line.strip() and not line.startswith('이 TODO')]
                        meeting_copy["todo_summary"] = todo_lines[:3]  # 상위 3개만
                        meeting_copy["todo_count"] = len([line for line in todo_data.split('\n') if line.strip() and re.match(r'^\d+\.', line.strip())])
                
                group_meetings.append(meeting_copy)
        
        # 시간순 정렬 (오래된 것부터)
        group_meetings.sort(key=lambda x: x.get("created_at", ""))
        
        # 그룹 정보
        main_meeting = next((m for m in group_meetings if m.get("is_group_main", False)), group_meetings[0] if group_meetings else None)
        
        return jsonify({
            "status": "success",
            "data": {
                "group_id": group_id,
                "group_name": main_meeting.get("name", "회의 그룹") if main_meeting else "회의 그룹",
                "current_meeting_id": meeting_id,
                "total_meetings": len(group_meetings),
                "meetings": group_meetings
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500

def render_password_form(meeting_id, meeting_data):
    """비밀번호 입력 폼 렌더링"""
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
                    const response = await fetch('/api/meeting/verify/{meeting_id}', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ password: password }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {{
                        window.location.href = `/result/{meeting_id}`;
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

@summary_bp.route("/", methods=["GET"])
def upload_page():
    return render_template("upload.html")

@summary_bp.route("/result/<meeting_id>", methods=["GET"])
def show_result(meeting_id):
    """결과 페이지 표시"""
    if meeting_id not in meetings_db:
        return "회의를 찾을 수 없습니다.", 404
    
    meeting_data = meetings_db[meeting_id]
    
    # 비밀번호가 설정된 회의인지 확인
    if meeting_data.get("password"):
        # 세션에서 인증 상태 확인
        auth_key = f"meeting_auth_{meeting_id}"
        
        if not session.get(auth_key):
            # 인증되지 않은 경우 비밀번호 입력 페이지 표시
            return render_password_form(meeting_id, meeting_data)
    
    summary = meeting_data.get("summary", "요약이 아직 생성되지 않았습니다.")
    
    return render_template("result.html", meeting_data=meeting_data, summary=summary)

@summary_bp.route("/api/meeting/verify/<meeting_id>", methods=["POST"])
def verify_meeting_password(meeting_id):
    """회의 비밀번호 검증"""
    if meeting_id not in meetings_db:
        return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
    
    data = request.get_json()
    password = data.get("password")
    
    if not password:
        return jsonify({"error": "비밀번호가 필요합니다"}), 400
    
    meeting_data = meetings_db[meeting_id]
    
    # 회의 비밀번호와 비교
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

@summary_bp.route("/api/meeting/<meeting_id>/name", methods=["PUT"])
def update_meeting_name(meeting_id):
    """회의 이름 수정"""
    try:
        if meeting_id not in meetings_db:
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        data = request.get_json()
        new_name = data.get("name", "").strip()
        
        if not new_name:
            return jsonify({"error": "회의명이 필요합니다"}), 400
        
        # 현재 사용자 ID 획득
        user_id = get_or_create_user_id()
        meeting_data = meetings_db[meeting_id]
        
        # 접근 권한 확인 (회의 소유자만 수정 가능)
        accessible_meetings = session.get('accessible_meetings', [])
        accessible_groups = session.get('accessible_groups', [])
        
        group_id = meeting_data.get("group_id", meeting_id)
        
        # 사용자 소유 회의인지 확인
        is_owner = meeting_data.get("user_id") == user_id
        
        # 세션 기반 접근 권한 (생성자나 공유 링크 접근자)
        has_session_access = (meeting_id in accessible_meetings or 
                             group_id in accessible_groups or
                             request.args.get('creator') == 'true')
        
        if not (is_owner or has_session_access):
            return jsonify({"error": "수정 권한이 없습니다"}), 403
        
        # 이름 수정
        old_name = meetings_db[meeting_id]["name"]
        meetings_db[meeting_id]["name"] = new_name
        
        # 데이터 저장
        save_meetings_data(meetings_db)
        
        print(f"✅ 회의 이름 수정: {old_name} → {new_name}")
        
        return jsonify({
            "status": "success",
            "message": "회의 이름이 성공적으로 수정되었습니다",
            "data": {
                "meeting_id": meeting_id,
                "old_name": old_name,
                "new_name": new_name
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500

@summary_bp.route("/api/meeting/<meeting_id>", methods=["DELETE"])
def delete_meeting(meeting_id):
    """회의 삭제"""
    try:
        if meeting_id not in meetings_db:
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        # 현재 사용자 ID 획득
        user_id = get_or_create_user_id()
        meeting_data = meetings_db[meeting_id]
        
        # 접근 권한 확인 (회의 소유자만 삭제 가능)
        accessible_meetings = session.get('accessible_meetings', [])
        accessible_groups = session.get('accessible_groups', [])
        
        group_id = meeting_data.get("group_id", meeting_id)
        
        # 사용자 소유 회의인지 확인
        is_owner = meeting_data.get("user_id") == user_id
        
        # 세션 기반 접근 권한 (생성자나 공유 링크 접근자)
        has_session_access = (meeting_id in accessible_meetings or 
                             group_id in accessible_groups or
                             request.args.get('creator') == 'true')
        
        if not (is_owner or has_session_access):
            return jsonify({"error": "삭제 권한이 없습니다"}), 403
        
        # 파일 삭제 (존재하는 경우)
        file_path = meeting_data.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️ 파일 삭제: {file_path}")
            except Exception as e:
                print(f"⚠️ 파일 삭제 실패: {e}")
        
        # 회의 데이터 삭제
        deleted_meeting = meetings_db.pop(meeting_id)
        
        # 세션에서 제거
        if 'accessible_meetings' in session and meeting_id in session['accessible_meetings']:
            session['accessible_meetings'].remove(meeting_id)
            session.modified = True
        
        # 그룹에 다른 회의가 없으면 그룹도 세션에서 제거
        group_meetings = [m for m in meetings_db.values() if m.get("group_id") == group_id]
        if not group_meetings and 'accessible_groups' in session and group_id in session['accessible_groups']:
            session['accessible_groups'].remove(group_id)
            session.modified = True
        
        # 데이터 저장
        save_meetings_data(meetings_db)
        
        print(f"🗑️ 회의 삭제 완료: {deleted_meeting['name']} ({meeting_id})")
        
        return jsonify({
            "status": "success",
            "message": "회의가 성공적으로 삭제되었습니다",
            "data": {
                "deleted_meeting": {
                    "meeting_id": meeting_id,
                    "name": deleted_meeting["name"],
                    "date": deleted_meeting["date"]
                }
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500