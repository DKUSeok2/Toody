# app/services/summary_service.py

import os
import requests
from app.services.todo_service import TodoService

class SummaryService:
    @staticmethod
    def summarize_meeting(text):
        prompt = (
            "다음 회의록을 읽고, 반드시 다음 형식을 유지해서 요약해줘:\n\n"
            "1) 이 회의는 무엇에 대해 논의했는가?\n"
            "2) 어떤 문제가 있었거나 분석된 내용은?\n"
            "3) 결과적으로 어떤 방향으로 결정됐는가?\n\n"
            "요약은 반드시 3개의 문장으로 나누고, 각 문장 앞에 '1)', '2)'. 3)' 형식을 붙여서 출력해줘.\n"
            f"회의록:\n{text}\n\n요약:"
        )

        headers = {
            "Authorization": f"Bearer {os.getenv('SOLAR_API_KEY')}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "solar-1-mini-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # 일관성을 위해 낮게 설정
            "top_p": 0.8,
            "max_tokens": 1000
        }

        response = requests.post(
            "https://api.upstage.ai/v1/solar/chat/completions",
            headers=headers,
            json=data
        )

        summary = response.json().get("choices", [{}])[0].get("message", {}).get("content", "요약 실패")
        return summary
    
    @staticmethod
    def summarize_and_extract_todo(text):
        """요약과 TODO를 동시에 생성하는 통합 서비스"""
        
        # 기존 요약 생성
        summary = SummaryService.summarize_meeting(text)
        
        # TODO 추출
        try:
            todo_service = TodoService()
            todo_result = todo_service.extract_todo_from_meeting(text)
            
            return {
                'success': True,
                'summary': summary,
                'todo_result': todo_result,
                'message': '요약과 TODO 추출이 완료되었습니다.'
            }
            
        except Exception as e:
            print(f"❌ TODO 추출 중 오류: {e}")
            return {
                'success': True,
                'summary': summary,
                'todo_result': {
                    'generated_todo': f"TODO 추출 중 오류가 발생했습니다: {str(e)}",
                    'confidence_score': 0.0,
                    'method': 'error',
                    'learning_occurred': False
                },
                'message': '요약은 완료되었으나 TODO 추출에 오류가 발생했습니다.'
            }
