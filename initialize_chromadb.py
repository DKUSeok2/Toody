#!/usr/bin/env python3
"""
ChromaDB 초기화 스크립트
output_dataset_ver4.json 데이터를 ChromaDB에 로드
"""

import json
import sys
from pathlib import Path
from app.services.todo_service import TodoService

def format_todo_from_summary(summary_list):
    """
    JSON의 summary 배열을 TODO 텍스트로 변환
    """
    
    if not summary_list:
        return "TODO 없음"
    
    todo_lines = []
    
    for i, item in enumerate(summary_list, 1):
        todo_line = f"{i}. "
        
        # 카테고리 추가
        if item.get("카테고리"):
            todo_line += f"[{item['카테고리']}] "
        
        # 맥락 추가 (TODO 내용)
        if item.get("맥락"):
            todo_line += item["맥락"]
        
        # 담당자 추가
        if item.get("담당자") and item["담당자"] != "공통":
            todo_line += f" (담당: {item['담당자']})"
        
        # 기한 추가
        if item.get("기한") and item["기한"] != "미정":
            todo_line += f" (기한: {item['기한']})"
        
        # 중요도 추가
        if item.get("중요도"):
            todo_line += f" (중요도: {item['중요도']})"
        
        todo_lines.append(todo_line)
    
    return "\n".join(todo_lines)

def load_json_to_chromadb(json_file_path):
    """
    JSON 파일을 ChromaDB에 로드
    """
    
    print(f"📂 JSON 파일 로드 시작: {json_file_path}")
    
    # JSON 파일 읽기
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON 파일 로드 성공: {len(data)}개 데이터")
    
    except Exception as e:
        print(f"❌ JSON 파일 로드 실패: {e}")
        return False
    
    # TodoService 초기화
    try:
        todo_service = TodoService()
        
        if not todo_service.collection:
            print("❌ ChromaDB 초기화 실패")
            return False
        
        print(f"✅ ChromaDB 연결 성공")
        
    except Exception as e:
        print(f"❌ TodoService 초기화 실패: {e}")
        return False
    
    # 기존 데이터 확인
    existing_count = todo_service.collection.count()
    print(f"📊 기존 ChromaDB 데이터: {existing_count}개")
    
    # 데이터 추가
    added_count = 0
    failed_count = 0
    
    for key, item in data.items():
        try:
            original_text = item.get("original", "")
            summary_list = item.get("summary", [])
            
            if not original_text:
                print(f"⚠️ 빈 텍스트 건너뜀: {key}")
                continue
            
            # TODO 텍스트 변환
            todo_text = format_todo_from_summary(summary_list)
            
            # ChromaDB에 추가
            success = todo_service._save_to_knowledge_base(
                meeting_text=original_text,
                todo_list=todo_text
            )
            
            if success:
                added_count += 1
                if added_count % 10 == 0:  # 10개마다 진행상황 출력
                    print(f"📈 진행상황: {added_count}개 추가됨")
            else:
                failed_count += 1
                print(f"❌ 데이터 추가 실패: {key}")
                
        except Exception as e:
            failed_count += 1
            print(f"❌ 데이터 처리 실패 ({key}): {e}")
    
    # 결과 출력
    final_count = todo_service.collection.count()
    
    print("\n" + "="*50)
    print("📊 ChromaDB 초기화 완료")
    print("="*50)
    print(f"📥 처리된 JSON 데이터: {len(data)}개")
    print(f"✅ 성공적으로 추가: {added_count}개")
    print(f"❌ 추가 실패: {failed_count}개")
    print(f"📊 기존 데이터: {existing_count}개")
    print(f"📈 최종 데이터: {final_count}개")
    print(f"🎯 실제 증가: {final_count - existing_count}개")
    print("="*50)
    
    return True

def main():
    """메인 함수"""
    
    print("🚀 ChromaDB 초기화 시작")
    print("="*50)
    
    # JSON 파일 경로
    json_file = Path("output_dataset_ver4.json")
    
    if not json_file.exists():
        print(f"❌ JSON 파일을 찾을 수 없습니다: {json_file}")
        sys.exit(1)
    
    # 확인 메시지
    print(f"📂 로드할 파일: {json_file}")
    response = input("계속 진행하시겠습니까? (y/N): ")
    
    if response.lower() not in ['y', 'yes']:
        print("❌ 사용자가 취소했습니다.")
        sys.exit(0)
    
    # ChromaDB 초기화 실행
    success = load_json_to_chromadb(json_file)
    
    if success:
        print("\n🎉 ChromaDB 초기화가 성공적으로 완료되었습니다!")
        print("💡 이제 파일을 업로드하면 유사 사례를 기반으로 TODO를 생성합니다.")
    else:
        print("\n❌ ChromaDB 초기화 중 오류가 발생했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main() 