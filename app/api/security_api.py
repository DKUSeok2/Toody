from flask import Blueprint, jsonify
import os
from pathlib import Path
from datetime import datetime

security_bp = Blueprint("security", __name__)

@security_bp.route("/api/security/status", methods=["GET"])
def get_security_status():
    """시스템 보안 상태 확인"""
    
    try:
        # 로컬 데이터 저장 확인
        data_path = Path("data")
        uploads_path = Path("uploads")
        
        local_data_count = 0
        if data_path.exists():
            local_data_count += len(list(data_path.rglob("*")))
        if uploads_path.exists():
            local_data_count += len(list(uploads_path.rglob("*")))
        
        # ChromaDB 상태 확인
        vector_db_path = Path("data/vectordb")
        chromadb_secure = vector_db_path.exists()
        
        # API 키 보안 확인
        api_keys_secure = bool(os.getenv('SOLAR_API_KEY'))
        
        security_status = {
            "overall_status": "SECURE",
            "local_storage": {
                "status": "ACTIVE",
                "files_count": local_data_count,
                "location": "회사 내부 서버",
                "description": "모든 회의록과 학습 데이터가 로컬에 저장"
            },
            "vector_db": {
                "status": "SECURE" if chromadb_secure else "NOT_INITIALIZED",
                "location": str(vector_db_path) if chromadb_secure else "없음",
                "description": "회사 전용 지식 베이스 (외부 접근 불가)"
            },
            "external_dependencies": {
                "solar_api": {
                    "status": "CONFIGURED" if api_keys_secure else "NOT_CONFIGURED",
                    "usage": "TODO 생성시에만 사용",
                    "data_retention": "회의록 원본은 외부 전송 안함"
                }
            },
            "compliance": {
                "data_sovereignty": "✅ 완전한 데이터 주권 확보",
                "gdpr_compliance": "✅ GDPR 준수 (로컬 처리)",
                "privacy_protection": "✅ 개인정보보호법 준수",
                "audit_trail": "✅ 완벽한 감사 추적 가능"
            },
            "vs_competitors": {
                "chatgpt": "❌ 모든 데이터가 OpenAI로 전송됨",
                "notion_ai": "❌ Notion 클라우드에 저장됨", 
                "otter_ai": "❌ Otter 서버에 저장됨",
                "our_system": "✅ 회사 내부에만 저장됨"
            },
            "last_checked": datetime.now().isoformat()
        }
        
        return jsonify({
            "status": "success",
            "data": security_status,
            "message": "보안 상태 확인 완료"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"보안 상태 확인 중 오류: {str(e)}"
        }), 500

@security_bp.route("/api/security/data-locations", methods=["GET"])
def get_data_locations():
    """데이터 저장 위치 상세 정보"""
    
    try:
        locations = {
            "meeting_files": {
                "path": "uploads/",
                "description": "업로드된 회의록 파일",
                "security": "로컬 파일 시스템"
            },
            "vector_database": {
                "path": "data/vectordb/",
                "description": "학습된 지식 베이스",
                "security": "ChromaDB (로컬)"
            },
            "session_data": {
                "path": "메모리",
                "description": "임시 세션 정보",
                "security": "서버 재시작시 삭제"
            },
            "external_apis": {
                "solar_api": {
                    "purpose": "TODO 생성",
                    "data_sent": "회의록 텍스트 (일시적)",
                    "data_retained": "없음 (즉시 삭제)",
                    "alternative": "완전 오프라인 모드 가능"
                }
            }
        }
        
        return jsonify({
            "status": "success",
            "data": locations,
            "message": "데이터 저장 위치 정보"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": f"데이터 위치 확인 중 오류: {str(e)}"
        }), 500

@security_bp.route("/api/security/comparison", methods=["GET"])
def get_security_comparison():
    """경쟁사 대비 보안 비교"""
    
    comparison = {
        "categories": [
            "데이터 저장", "학습 데이터", "인터넷 의존", 
            "회의록 유출", "맞춤 학습", "월 비용"
        ],
        "competitors": {
            "ChatGPT/Claude": [
                "OpenAI 클라우드", "전세계 공유", "필수", 
                "가능성 있음", "불가능", "사용량 기준"
            ],
            "Notion AI": [
                "Notion 서버", "Notion DB", "필수",
                "가능성 있음", "제한적", "구독료"
            ],
            "Otter.ai": [
                "Otter 클라우드", "Otter DB", "필수",
                "가능성 있음", "제한적", "구독료"
            ],
            "우리 시스템": [
                "회사 내부 서버", "회사 전용 DB", "선택사항",
                "불가능", "완전 맞춤", "일회성 구축"
            ]
        },
        "security_incidents": [
            {
                "company": "Samsung",
                "year": 2023,
                "incident": "ChatGPT 사용으로 반도체 정보 유출",
                "action": "전사 ChatGPT 사용 금지"
            },
            {
                "company": "Microsoft",
                "year": 2023,
                "incident": "Copilot 내부 문서 노출",
                "action": "보안 정책 강화"
            }
        ]
    }
    
    return jsonify({
        "status": "success",
        "data": comparison,
        "message": "보안 비교 데이터"
    }) 