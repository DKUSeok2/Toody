from flask import Blueprint, request, jsonify
from app.services.todo_service import TodoService
from datetime import datetime

todo_bp = Blueprint("todo", __name__)

# upload_api에서 meetings_db와 save_meetings_data 가져오기
from app.api.upload_api import meetings_db, save_meetings_data, get_or_create_user_id

@todo_bp.route("/api/todo", methods=["POST"])
def get_or_generate_todos():
    """회의 ID로 TODO 조회 또는 생성"""
    try:
        data = request.get_json()
        meeting_id = data.get("meeting_id")
        
        if not meeting_id:
            return jsonify({"error": "meeting_id가 필요합니다"}), 400
        
        if meeting_id not in meetings_db:
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        meeting_data = meetings_db[meeting_id]
        
        # 이미 생성된 TODO가 있는지 확인
        if meeting_data.get("todo_result"):
            todo_data = meeting_data["todo_result"].get("generated_todo", "")
            todos = []
            if todo_data:
                todo_lines = [line.strip() for line in todo_data.split('\n') if line.strip()]
                
                # 🚫 설명문이나 메타 정보 필터링
                filtered_todo_lines = []
                for line in todo_lines:
                    # 숫자로 시작하는 할 일 항목만 포함
                    if re.match(r'^\d+\.', line.strip()):
                        filtered_todo_lines.append(line)
                    # "이 TODO", "TODO 리스트는", "각 항목은" 등으로 시작하는 설명문 제외
                    elif any(line.startswith(prefix) for prefix in ["이 TODO", "TODO 리스트", "각 항목", "위 항목", "해당 할 일"]):
                        print(f"🚫 설명문 필터링: {line[:50]}...")
                        continue
                    # 100자 이상의 긴 텍스트도 설명문으로 간주하고 제외
                    elif len(line) > 100:
                        print(f"🚫 긴 설명문 필터링: {line[:50]}...")
                        continue
                    else:
                        # 기타 짧은 할 일들도 포함 (숫자 없이 시작하는 경우도 있을 수 있음)
                        filtered_todo_lines.append(line)
                
                todo_lines = filtered_todo_lines
                
                categories = ["수술", "회의", "검토", "준비", "계획", "연구", "일반"]
                
                for todo_line in todo_lines:
                    # 우선순위 결정 (키워드 기반)
                    priority = "보통"
                    if any(word in todo_line for word in ["긴급", "즉시", "급한", "중요한"]):
                        priority = "높음"
                    elif any(word in todo_line for word in ["검토", "확인", "정리"]):
                        priority = "낮음"
                    
                    # 카테고리 결정 (키워드 기반)
                    category = "일반"
                    for cat in categories:
                        if cat in todo_line:
                            category = cat
                            break
                    
                    # 담당자 추출 시도 (이름 패턴)
                    assignee = None
                    import re
                    # 한국어 이름 패턴 찾기
                    name_patterns = re.findall(r'[가-힣]{2,4}(?:\s?(?:님|씨|박사|교수|의사))?', todo_line)
                    if name_patterns:
                        assignee = name_patterns[0]
                    
                    # 기한 추출 시도
                    deadline = ""
                    date_patterns = re.findall(r'(\d{1,2}월\s?\d{1,2}일|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2})', todo_line)
                    if date_patterns:
                        deadline = date_patterns[0]
                    
                    todos.append({
                        "task": todo_line,  # 원래대로 todo_line 그대로 사용
                        "priority": priority,
                        "category": category,
                        "assignee": assignee,
                        "deadline": deadline
                    })
            
            return jsonify({
                "status": "success",
                "data": {"todos": todos}
            })
        
        # TODO가 없으면 원본 텍스트로 새로 생성
        original_text = meeting_data.get("original_text", "")
        if not original_text:
            return jsonify({"error": "원본 텍스트가 없습니다"}), 400
        
        # TODO 서비스로 새로 생성
        todo_service = TodoService()
        result = todo_service.extract_todo_from_meeting(original_text)
        
        # 결과 저장
        meetings_db[meeting_id]["todo_result"] = result
        
        # 데이터 저장
        save_meetings_data(meetings_db)
        
        # 응답 형태로 변환
        todos = []
        if result.get("generated_todo"):
            todo_lines = [line.strip() for line in result["generated_todo"].split('\n') if line.strip()]
            
            # 🚫 설명문이나 메타 정보 필터링
            filtered_todo_lines = []
            for line in todo_lines:
                # 숫자로 시작하는 할 일 항목만 포함
                if re.match(r'^\d+\.', line.strip()):
                    filtered_todo_lines.append(line)
                # "이 TODO", "TODO 리스트는", "각 항목은" 등으로 시작하는 설명문 제외
                elif any(line.startswith(prefix) for prefix in ["이 TODO", "TODO 리스트", "각 항목", "위 항목", "해당 할 일"]):
                    print(f"🚫 설명문 필터링: {line[:50]}...")
                    continue
                # 100자 이상의 긴 텍스트도 설명문으로 간주하고 제외
                elif len(line) > 100:
                    print(f"🚫 긴 설명문 필터링: {line[:50]}...")
                    continue
                else:
                    # 기타 짧은 할 일들도 포함 (숫자 없이 시작하는 경우도 있을 수 있음)
                    filtered_todo_lines.append(line)
            
            todo_lines = filtered_todo_lines
            
            categories = ["수술", "회의", "검토", "준비", "계획", "연구", "일반"]
            
            for todo_line in todo_lines:
                # 우선순위 결정 (키워드 기반)
                priority = "보통"
                if any(word in todo_line for word in ["긴급", "즉시", "급한", "중요한"]):
                    priority = "높음"
                elif any(word in todo_line for word in ["검토", "확인", "정리"]):
                    priority = "낮음"
                
                # 카테고리 결정 (키워드 기반)
                category = "일반"
                for cat in categories:
                    if cat in todo_line:
                        category = cat
                        break
                
                # 담당자 추출 시도 (이름 패턴)
                assignee = None
                import re
                # 한국어 이름 패턴 찾기
                name_patterns = re.findall(r'[가-힣]{2,4}(?:\s?(?:님|씨|박사|교수|의사))?', todo_line)
                if name_patterns:
                    assignee = name_patterns[0]
                
                # 기한 추출 시도
                deadline = ""
                date_patterns = re.findall(r'(\d{1,2}월\s?\d{1,2}일|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2})', todo_line)
                if date_patterns:
                    deadline = date_patterns[0]
                
                todos.append({
                    "task": todo_line,  # 원래대로 todo_line 그대로 사용
                    "priority": priority,
                    "category": category,
                    "assignee": assignee,
                    "deadline": deadline
                })
        
        return jsonify({
            "status": "success",
            "data": {"todos": todos}
        })
        
    except Exception as e:
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500

@todo_bp.route("/api/todo/extract", methods=["POST"])
def extract_todo():
    """회의록에서 TODO 추출"""
    
    try:
        data = request.get_json()
        meeting_text = data.get("meeting_text")
        
        if not meeting_text:
            return jsonify({
                "error": "meeting_text가 필요합니다"
            }), 400
        
        # TODO 서비스 초기화
        todo_service = TodoService()
        
        # TODO 추출
        result = todo_service.extract_todo_from_meeting(meeting_text)
        
        return jsonify({
            "status": "success",
            "data": result,
            "message": "TODO 추출이 완료되었습니다"
        })
        
    except Exception as e:
        return jsonify({
            "error": f"TODO 추출 중 오류가 발생했습니다: {str(e)}"
        }), 500

@todo_bp.route("/api/todo/status", methods=["GET"])
def get_todo_system_status():
    """TODO 시스템 상태 확인"""
    
    try:
        todo_service = TodoService()
        status = todo_service.get_system_status()
        
        return jsonify({
            "status": "success",
            "data": status,
            "message": "시스템 상태 조회 완료"
        })
        
    except Exception as e:
        return jsonify({
            "error": f"상태 조회 중 오류가 발생했습니다: {str(e)}"
        }), 500

@todo_bp.route("/api/meeting/<meeting_id>/regenerate-todo", methods=["POST"])
def regenerate_todo(meeting_id):
    """특정 회의의 TODO 재생성"""
    
    try:
        from app.api.upload_api import meetings_db
        
        print(f"🔄 TODO 재생성 요청: {meeting_id}")
        
        if meeting_id not in meetings_db:
            print(f"❌ 회의를 찾을 수 없음: {meeting_id}")
            return jsonify({
                "error": "회의를 찾을 수 없습니다"
            }), 404
        
        meeting_data = meetings_db[meeting_id]
        original_text = meeting_data.get("original_text", "")
        processing_status = meeting_data.get("processing_status", "unknown")
        
        print(f"📊 회의 데이터 상태: {processing_status}")
        print(f"📝 원본 텍스트 길이: {len(original_text)}")
        
        # 원본 텍스트가 없거나 비어있는 경우
        if not original_text or original_text.strip() == "":
            error_message = meeting_data.get("error_message", "원본 텍스트 없음")
            
            # 파일 재추출 시도
            if meeting_data.get("file_path"):
                try:
                    print(f"🔄 파일에서 텍스트 재추출 시도: {meeting_data['file_path']}")
                    from app.utils.file_utils import extract_text_from_file
                    
                    original_text = extract_text_from_file(meeting_data["file_path"])
                    
                    # 성공하면 저장
                    meetings_db[meeting_id]["original_text"] = original_text
                    
                    # 데이터 저장
                    save_meetings_data(meetings_db)
                    
                    print(f"✅ 파일 재추출 성공 (길이: {len(original_text)}자)")
                    
                except Exception as file_error:
                    print(f"❌ 파일 재추출 실패: {file_error}")
                    return jsonify({
                        "error": f"원본 텍스트를 찾을 수 없습니다. 파일 처리 오류: {error_message}",
                        "details": f"재추출 시도 실패: {str(file_error)}"
                    }), 400
            else:
                return jsonify({
                    "error": f"원본 텍스트를 찾을 수 없습니다. 오류: {error_message}",
                    "details": "파일 경로 정보도 없습니다."
                }), 400
        
        # TODO 재생성
        print("🤖 TODO 재생성 시작")
        todo_service = TodoService()
        new_todo_result = todo_service.extract_todo_from_meeting(original_text)
        
        # 회의 데이터 업데이트
        meetings_db[meeting_id]["todo_result"] = new_todo_result
        meetings_db[meeting_id]["last_regenerated"] = datetime.now().isoformat()
        
        # 데이터 저장
        save_meetings_data(meetings_db)
        
        print("✅ TODO 재생성 완료")
        
        return jsonify({
            "status": "success",
            "data": new_todo_result,
            "message": "TODO가 재생성되었습니다"
        })
        
    except Exception as e:
        print(f"❌ TODO 재생성 중 예외 발생: {e}")
        return jsonify({
            "error": f"TODO 재생성 중 오류가 발생했습니다: {str(e)}"
        }), 500 

@todo_bp.route("/api/meeting/<meeting_id>/todo/<int:todo_index>", methods=["PUT"])
def update_todo(meeting_id, todo_index):
    """특정 회의의 특정 TODO 항목 수정"""
    
    try:
        from app.api.upload_api import meetings_db
        
        if meeting_id not in meetings_db:
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "수정할 데이터가 필요합니다"}), 400
        
        meeting_data = meetings_db[meeting_id]
        
        # 현재 todo_result에서 todos 가져오기
        if not meeting_data.get("todo_result"):
            return jsonify({"error": "TODO 데이터를 찾을 수 없습니다"}), 404
        
        todo_data = meeting_data["todo_result"].get("generated_todo", "")
        if not todo_data:
            return jsonify({"error": "TODO 데이터가 비어있습니다"}), 404
        
        # TODO 라인들을 분리
        todo_lines = [line.strip() for line in todo_data.split('\n') if line.strip()]
        
        # 인덱스 검증
        if todo_index < 0 or todo_index >= len(todo_lines):
            return jsonify({"error": "잘못된 TODO 인덱스입니다"}), 400
        
        # 수정된 데이터 가져오기
        updated_task = data.get("task", "").strip()
        updated_assignee = data.get("assignee", "").strip()
        updated_deadline = data.get("deadline", "").strip()
        updated_priority = data.get("priority", "보통")
        updated_category = data.get("category", "일반")
        
        if not updated_task:
            return jsonify({"error": "할 일 내용은 필수입니다"}), 400
        
        # 새로운 TODO 라인 생성
        new_todo_line = updated_task
        
        # 담당자와 기한 정보 추가
        additional_info = []
        if updated_assignee and updated_assignee != "담당자 미지정":
            additional_info.append(f"담당: {updated_assignee}")
        if updated_deadline:
            additional_info.append(f"기한: {updated_deadline}")
        
        if additional_info:
            new_todo_line += f" ({', '.join(additional_info)})"
        
        # 기존 TODO 라인 업데이트
        todo_lines[todo_index] = new_todo_line
        
        # 업데이트된 TODO 문자열 생성
        updated_todo_data = '\n'.join(todo_lines)
        
        # 회의 데이터 업데이트
        meetings_db[meeting_id]["todo_result"]["generated_todo"] = updated_todo_data
        meetings_db[meeting_id]["todo_result"]["last_modified"] = datetime.now().isoformat()
        
        # 데이터 저장
        save_meetings_data(meetings_db)
        
        print(f"✅ TODO 수정 완료: meeting_id={meeting_id}, index={todo_index}")
        
        return jsonify({
            "status": "success",
            "message": "TODO가 성공적으로 수정되었습니다",
            "data": {
                "updated_todo": {
                    "task": updated_task,
                    "assignee": updated_assignee if updated_assignee != "담당자 미지정" else None,
                    "deadline": updated_deadline,
                    "priority": updated_priority,
                    "category": updated_category
                }
            }
        })
        
    except Exception as e:
        print(f"❌ TODO 수정 중 오류: {e}")
        return jsonify({
            "error": f"TODO 수정 중 오류가 발생했습니다: {str(e)}"
        }), 500

@todo_bp.route("/api/meeting/<meeting_id>/todo/<int:todo_index>", methods=["DELETE"])
def delete_todo(meeting_id, todo_index):
    """특정 회의의 특정 TODO 항목 삭제"""
    
    try:
        from app.api.upload_api import meetings_db
        
        if meeting_id not in meetings_db:
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        meeting_data = meetings_db[meeting_id]
        
        # 현재 todo_result에서 todos 가져오기
        if not meeting_data.get("todo_result"):
            return jsonify({"error": "TODO 데이터를 찾을 수 없습니다"}), 404
        
        todo_data = meeting_data["todo_result"].get("generated_todo", "")
        if not todo_data:
            return jsonify({"error": "TODO 데이터가 비어있습니다"}), 404
        
        # TODO 라인들을 분리
        todo_lines = [line.strip() for line in todo_data.split('\n') if line.strip()]
        
        # 인덱스 검증
        if todo_index < 0 or todo_index >= len(todo_lines):
            return jsonify({"error": "잘못된 TODO 인덱스입니다"}), 400
        
        # TODO 항목 삭제
        deleted_todo = todo_lines.pop(todo_index)
        
        # 업데이트된 TODO 문자열 생성
        updated_todo_data = '\n'.join(todo_lines)
        
        # 회의 데이터 업데이트
        meetings_db[meeting_id]["todo_result"]["generated_todo"] = updated_todo_data
        meetings_db[meeting_id]["todo_result"]["last_modified"] = datetime.now().isoformat()
        
        # 데이터 저장
        save_meetings_data(meetings_db)
        
        print(f"🗑️ TODO 삭제 완료: meeting_id={meeting_id}, index={todo_index}")
        
        return jsonify({
            "status": "success",
            "message": "TODO가 성공적으로 삭제되었습니다",
            "data": {
                "deleted_todo": deleted_todo
            }
        })
        
    except Exception as e:
        print(f"❌ TODO 삭제 중 오류: {e}")
        return jsonify({
            "error": f"TODO 삭제 중 오류가 발생했습니다: {str(e)}"
        }), 500 