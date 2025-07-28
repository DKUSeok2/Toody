from flask import Blueprint, jsonify, session
from datetime import datetime

sidebar_bp = Blueprint("sidebar", __name__)

# upload_api에서 meetings_db 가져오기
from app.api.upload_api import meetings_db, get_or_create_user_id

@sidebar_bp.route("/api/meetings", methods=["GET"])
def get_meetings():
    """현재 사용자의 회의 그룹 목록을 반환 (공유 링크 접속 시 해당 그룹도 포함)"""
    try:
        # 현재 사용자 ID 획득
        user_id = get_or_create_user_id()
        
        # 현재 사용자의 회의만 필터링
        user_meetings = {
            meeting_id: meeting_data 
            for meeting_id, meeting_data in meetings_db.items() 
            if meeting_data.get("user_id") == user_id
        }
        
        # 공유 링크로 접근한 회의가 있는지 확인
        accessible_meetings = session.get('accessible_meetings', [])
        shared_group_ids = set()
        
        for accessible_id in accessible_meetings:
            if accessible_id in meetings_db:
                accessible_meeting = meetings_db[accessible_id]
                # 현재 사용자 소유가 아닌 회의 (공유 링크로 접근)
                if accessible_meeting.get("user_id") != user_id:
                    group_id = accessible_meeting.get("group_id", accessible_id)
                    shared_group_ids.add(group_id)
        
        # 공유받은 그룹의 모든 회의도 포함
        for meeting_id, meeting_data in meetings_db.items():
            meeting_group_id = meeting_data.get("group_id", meeting_id)
            if meeting_group_id in shared_group_ids:
                user_meetings[meeting_id] = meeting_data
        
        print(f"📋 사용자 {user_id}의 회의 {len(user_meetings)}개 조회 (공유 그룹 {len(shared_group_ids)}개 포함)")
        
        # 그룹별로 회의들을 정리
        groups = {}
        
        for meeting_id, meeting_data in user_meetings.items():
            group_id = meeting_data.get("group_id", meeting_id)
            
            if group_id not in groups:
                groups[group_id] = {
                    "group_id": group_id,
                    "group_name": "",
                    "total_meetings": 0,
                    "latest_date": "",
                    "meetings": [],
                    "is_shared": meeting_data.get("user_id") != user_id  # 공유받은 그룹인지 표시
                }
            
            groups[group_id]["meetings"].append({
                "meeting_id": meeting_id,
                "name": meeting_data["name"],
                "date": meeting_data["date"],
                "created_at": meeting_data.get("created_at", ""),
                "sequence_number": meeting_data.get("sequence_number", 1),
                "is_group_main": meeting_data.get("is_group_main", False)
            })
        
        # 각 그룹 정보 완성
        for group_id, group_data in groups.items():
            # 시간순 정렬 (최신 순)
            group_data["meetings"].sort(key=lambda x: x["created_at"], reverse=True)
            
            # 그룹 이름은 메인 회의 이름 또는 첫 번째 회의 이름 사용
            main_meeting = next((m for m in group_data["meetings"] if m["is_group_main"]), None)
            if main_meeting:
                group_data["group_name"] = main_meeting["name"]
            elif group_data["meetings"]:
                group_data["group_name"] = group_data["meetings"][0]["name"]
            
            # 공유받은 그룹인 경우 이름에 표시
            if group_data["is_shared"]:
                group_data["group_name"] = f"📤 {group_data['group_name']}"
            
            group_data["total_meetings"] = len(group_data["meetings"])
            
            # 최신 날짜
            if group_data["meetings"]:
                group_data["latest_date"] = max([m["date"] for m in group_data["meetings"]])
        
        # 그룹들을 최신 날짜순으로 정렬
        sorted_groups = sorted(groups.values(), key=lambda x: x["latest_date"], reverse=True)
        
        return jsonify({
            "status": "success",
            "groups": sorted_groups
        })
        
    except Exception as e:
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500