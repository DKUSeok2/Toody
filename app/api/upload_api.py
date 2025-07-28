from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime

upload_bp = Blueprint("upload", __name__)
UPLOAD_FOLDER = "uploads"
DATA_FILE = "data/meetings_data.json"

# uploads 폴더가 없으면 생성
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# data 폴더가 없으면 생성
if not os.path.exists("data"):
    os.makedirs("data")

# 사용자 ID 생성 및 관리
def get_or_create_user_id():
    """세션에서 사용자 ID를 가져오거나 새로 생성"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session.permanent = True
        print(f"🆔 새 사용자 ID 생성: {session['user_id']}")
    return session['user_id']

# JSON 파일에서 회의 데이터 로드
def load_meetings_data():
    """JSON 파일에서 회의 데이터 로드"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"❌ 데이터 로드 중 오류: {e}")
        return {}

# JSON 파일에 회의 데이터 저장
def save_meetings_data(meetings_db):
    """JSON 파일에 회의 데이터 저장"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(meetings_db, f, ensure_ascii=False, indent=2)
        print(f"✅ 데이터 저장 완료: {len(meetings_db)}개 회의")
    except Exception as e:
        print(f"❌ 데이터 저장 중 오류: {e}")

# 회의 데이터 로드 (서버 시작 시)
meetings_db = load_meetings_data()
print(f"🚀 서버 시작: {len(meetings_db)}개 회의 데이터 로드됨")

def generate_password():
    """랜덤 8자리 비밀번호 생성"""
    return str(uuid.uuid4())[:8]

@upload_bp.route("/api/upload", methods=["POST"])
def upload_meeting(): 
    # 사용자 ID 획득
    user_id = get_or_create_user_id()
    
    # 파일 받기
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "파일이 없습니다"}), 400

    # 회의 정보 받기
    meeting_name = request.form.get("meeting_name", "회의")
    date = request.form.get("date")
    password_enabled = request.form.get("password_enabled", "false")
    frontend_password = request.form.get("password")  # 프론트엔드에서 전달된 비밀번호
    
    # 연속 회의 정보 받기 (기존 그룹에 추가할 때)
    parent_group_id = request.form.get("parent_group_id")  # 기존 그룹에 추가할 때
    is_additional_upload = parent_group_id is not None

    # 파일 저장
    filename = secure_filename(file.filename)
    meeting_id = str(uuid.uuid4())
    new_filename = f"{meeting_id}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(filepath)

    # 그룹 ID 결정
    if is_additional_upload and parent_group_id in meetings_db:
        # 기존 그룹에 추가 - 기존 그룹의 소유자와 같은지 확인
        parent_meeting = meetings_db[parent_group_id]
        if parent_meeting.get("user_id") != user_id:
            return jsonify({"error": "해당 회의 그룹에 추가할 권한이 없습니다"}), 403
            
        group_id = parent_group_id
        # 같은 그룹의 회의 수 계산 (시퀀스 번호)
        group_meetings = [m for m in meetings_db.values() if m.get("group_id") == group_id]
        sequence_number = len(group_meetings) + 1
        
        # 기존 그룹의 비밀번호 사용
        password = parent_meeting.get("password")
        
        print(f"🔗 기존 그룹에 추가: {group_id}, 시퀀스: {sequence_number}")
    else:
        # 새로운 그룹 생성
        group_id = meeting_id  # 첫 번째 회의의 ID를 그룹 ID로 사용
        sequence_number = 1
        
        # 비밀번호 설정 (프론트엔드에서 전달된 것 우선, 없으면 백엔드에서 생성)
        if password_enabled == "true":
            password = frontend_password if frontend_password else generate_password()
        else:
            password = None
            
        print(f"🆕 새로운 그룹 생성: {group_id}")

    # 회의 데이터 저장 (사용자 ID 포함)
    meetings_db[meeting_id] = {
        "meeting_id": meeting_id,
        "user_id": user_id,  # 사용자 ID 추가
        "group_id": group_id,  # 그룹 ID 추가
        "sequence_number": sequence_number,  # 그룹 내 순서
        "name": meeting_name,
        "date": date,
        "file_path": filepath,
        "password": password,
        "created_at": datetime.now().isoformat(),
        "is_group_main": sequence_number == 1  # 그룹의 대표 회의 여부
    }

    # 바로 요약과 TODO 생성
    original_text = ""  # 원본 텍스트 초기화
    
    try:
        from app.utils.file_utils import extract_text_from_file
        from app.services.summary_service import SummaryService
        
        print(f"📂 파일에서 텍스트 추출 시작: {filepath}")
        
        # 텍스트 추출
        text = extract_text_from_file(filepath)
        original_text = text  # 성공하면 원본 텍스트 저장
        
        print(f"✅ 텍스트 추출 성공 (길이: {len(text)}자)")
        
        # 통합 서비스 사용 (요약 + TODO)
        print("🚀 요약 및 TODO 생성 시작")
        result = SummaryService.summarize_and_extract_todo(text)
        
        # 회의 데이터에 요약과 TODO 결과 저장
        meetings_db[meeting_id]["summary"] = result['summary']
        meetings_db[meeting_id]["todo_result"] = result['todo_result']
        meetings_db[meeting_id]["original_text"] = original_text
        meetings_db[meeting_id]["processing_status"] = "completed"
        
        print("✅ 요약 및 TODO 생성 완료")
        
    except Exception as e:
        print(f"❌ 처리 중 오류 발생: {e}")
        
        # 텍스트 추출이 실패한 경우에도 파일 정보는 저장
        meetings_db[meeting_id]["original_text"] = original_text  # 빈 문자열이라도 저장
        meetings_db[meeting_id]["processing_status"] = "failed"
        meetings_db[meeting_id]["error_message"] = str(e)
        
        # 에러 메시지 설정
        error_msg = str(e)
        meetings_db[meeting_id]["summary"] = f"요약 생성 중 오류가 발생했습니다: {error_msg}"
        meetings_db[meeting_id]["todo_result"] = {
            'generated_todo': f"TODO 추출 중 오류가 발생했습니다: {error_msg}",
            'confidence_score': 0.0,
            'method': 'error',
            'learning_occurred': False,
            'error': error_msg
        }
    
    # 데이터 저장 (처리 완료 후)
    save_meetings_data(meetings_db)
    
    # 실시간 업데이트 브로드캐스트 (회의 생성 완료)
    # broadcast_meeting_update(meeting_id, 'meeting_created', {
    #     'meeting_id': meeting_id,
    #     'name': meeting_name,
    #     'summary': meetings_db[meeting_id].get('summary'),
    #     'todos': meetings_db[meeting_id].get('todo_result')
    # })
    
    # 그룹의 다른 회의들에도 히스토리 업데이트 알림
    for other_meeting_id in meetings_db:
        other_meeting = meetings_db[other_meeting_id]
        if other_meeting.get('group_id') == group_id and other_meeting_id != meeting_id:
            # broadcast_meeting_update(other_meeting_id, 'history_updated', {
            #     'group_id': group_id
            # })
            pass # Socket.IO 브로드캐스트 제거
    
    # 세션에 meeting_id 저장 (회의 생성자는 비밀번호 없이 접근 가능)
    if 'accessible_meetings' not in session:
        session['accessible_meetings'] = []
    session['accessible_meetings'].append(meeting_id)
    
    # 그룹 접근 권한도 세션에 저장
    if 'accessible_groups' not in session:
        session['accessible_groups'] = []
    if group_id not in session['accessible_groups']:
        session['accessible_groups'].append(group_id)

    # JSON 응답으로 변경
    return jsonify({
        "status": "success",
        "message": "회의 업로드 완료",
        "data": {
            "meeting_id": meeting_id,
            "name": meeting_name,
            "date": date,
            "file_url": f"/uploads/{new_filename}",
            "password": password,
            "created_at": meetings_db[meeting_id]["created_at"]
        }
    }), 201

@upload_bp.route("/api/upload/additional", methods=["POST"])
def upload_additional_meeting():
    """기존 회의 그룹에 추가 회의록 업로드"""
    try:
        # 사용자 ID 획득
        user_id = get_or_create_user_id()
        
        # 파일 받기
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "파일이 없습니다"}), 400

        # 회의 정보 받기
        meeting_name = request.form.get("meeting_name", "추가 회의")
        date = request.form.get("date")
        parent_group_id = request.form.get("parent_group_id")  # 필수

        if not parent_group_id:
            return jsonify({"error": "parent_group_id가 필요합니다"}), 400

        if parent_group_id not in meetings_db:
            return jsonify({"error": "원본 회의 그룹을 찾을 수 없습니다"}), 404

        # 파일 저장
        filename = secure_filename(file.filename)
        meeting_id = str(uuid.uuid4())
        new_filename = f"{meeting_id}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, new_filename)
        file.save(filepath)

        # 기존 그룹 정보 가져오기 및 권한 확인
        parent_meeting = meetings_db[parent_group_id]
        if parent_meeting.get("user_id") != user_id:
            return jsonify({"error": "해당 회의 그룹에 추가할 권한이 없습니다"}), 403
            
        group_id = parent_meeting.get("group_id", parent_group_id)
        
        # 같은 그룹의 회의 수 계산 (시퀀스 번호)
        group_meetings = [m for m in meetings_db.values() if m.get("group_id") == group_id]
        sequence_number = len(group_meetings) + 1
        
        print(f"🔗 추가 회의 업로드: 그룹 {group_id}, 시퀀스 {sequence_number}")

        # 회의 데이터 저장 (사용자 ID 포함)
        meetings_db[meeting_id] = {
            "meeting_id": meeting_id,
            "user_id": user_id,  # 사용자 ID 추가
            "group_id": group_id,
            "sequence_number": sequence_number,
            "name": meeting_name,
            "date": date,
            "file_path": filepath,
            "password": parent_meeting.get("password"),  # 부모 회의와 같은 비밀번호
            "created_at": datetime.now().isoformat(),
            "is_group_main": False  # 추가 회의는 메인이 아님
        }
        save_meetings_data(meetings_db) # 데이터 저장

        # 바로 요약과 TODO 생성
        original_text = ""
        try:
            # 필요한 import 추가
            from app.utils.file_utils import extract_text_from_file
            from app.services.summary_service import SummaryService
            
            original_text = extract_text_from_file(filepath)
            meetings_db[meeting_id]["original_text"] = original_text
            
            # 요약과 TODO 자동 생성
            result = SummaryService.summarize_and_extract_todo(original_text)
            meetings_db[meeting_id]["summary"] = result['summary']
            meetings_db[meeting_id]["todo_result"] = result['todo_result']
            meetings_db[meeting_id]["processing_status"] = "completed"
            
            print(f"✅ 추가 회의 처리 완료: {meeting_id}")
            
        except Exception as e:
            print(f"❌ 추가 회의 처리 중 오류: {e}")
            # 오류가 있어도 회의 데이터는 저장
            meetings_db[meeting_id]["original_text"] = ""
            meetings_db[meeting_id]["summary"] = ""
            meetings_db[meeting_id]["todo_result"] = {
                "generated_todo": "텍스트 추출 실패로 TODO를 생성할 수 없습니다.",
                "method": "error"
            }
            meetings_db[meeting_id]["processing_status"] = "failed"
            meetings_db[meeting_id]["error_message"] = str(e)
        save_meetings_data(meetings_db) # 데이터 저장

        # 세션에 접근 권한 추가
        if 'accessible_meetings' not in session:
            session['accessible_meetings'] = []
        if meeting_id not in session['accessible_meetings']:
            session['accessible_meetings'].append(meeting_id)
            
        # 그룹 접근 권한도 세션에 저장
        if 'accessible_groups' not in session:
            session['accessible_groups'] = []
        if group_id not in session['accessible_groups']:
            session['accessible_groups'].append(group_id)
            
        # 실시간 업데이트 브로드캐스트 (추가 회의 생성 완료)
        # broadcast_meeting_update(meeting_id, 'meeting_created', {
        #     'meeting_id': meeting_id,
        #     'name': meeting_name,
        #     'summary': meetings_db[meeting_id].get('summary'),
        #     'todos': meetings_db[meeting_id].get('todo_result')
        # })
        
        # 그룹의 다른 회의들에도 히스토리 업데이트 알림
        for other_meeting_id in meetings_db:
            other_meeting = meetings_db[other_meeting_id]
            if other_meeting.get('group_id') == group_id and other_meeting_id != meeting_id:
                # broadcast_meeting_update(other_meeting_id, 'history_updated', {
                #     'group_id': group_id
                # })
                pass # Socket.IO 브로드캐스트 제거

        return jsonify({
            "status": "success",
            "data": {
                "meeting_id": meeting_id,
                "group_id": group_id,
                "sequence_number": sequence_number,
                "password": parent_meeting.get("password"),
                "redirect_url": f"/result/{meeting_id}?creator=true"
            }
        }), 201

    except Exception as e:
        print(f"❌ 추가 업로드 중 오류 발생: {e}")
        return jsonify({"error": f"업로드 중 오류가 발생했습니다: {str(e)}"}), 500