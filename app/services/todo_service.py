# app/services/todo_service.py

import uuid
import json
import os
import requests
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class TodoService:
    """회의록에서 TODO 추출하는 RAG 기반 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.vector_db_path = "data/vectordb"
        self.collection_name = "meeting_todos"
        self.embedding_model_name = "jhgan/ko-sroberta-multitask"
        self.similarity_threshold = 0.3
        
        # 디렉토리 생성
        Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
        
        # ChromaDB 초기화
        try:
            self.client = chromadb.PersistentClient(path=self.vector_db_path)
            
            try:
                self.collection = self.client.get_collection(self.collection_name)
                print(f"✅ 기존 벡터 DB 컬렉션 로드: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "회의록-TODO 쌍 저장소"}
                )
                print(f"✅ 새 벡터 DB 컬렉션 생성: {self.collection_name}")
                
            # 임베딩 모델 초기화
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            print(f"✅ 임베딩 모델 로드: {self.embedding_model_name}")
            
        except Exception as e:
            print(f"❌ 벡터 DB 초기화 실패: {e}")
            self.client = None
            self.collection = None
            self.embedding_model = None

    def extract_todo_from_meeting(self, meeting_text: str) -> Dict:
        """
        회의록에서 TODO 추출 (메인 함수)
        
        Args:
            meeting_text: 회의록 텍스트
             
        Returns:
            추출된 TODO와 메타데이터
        """
        if not self.collection:
            # 벡터 DB 없으면 직접 LLM으로 생성
            return self._generate_with_llm_only(meeting_text)
        
        try:
            # 1단계: 유사한 회의록 검색
            similar_meetings = self._search_similar_meetings(meeting_text, top_k=5)
            
            print(f"📊 검색된 유사 사례 수: {len(similar_meetings)}")
            
            if similar_meetings and similar_meetings[0]['similarity_score'] >= self.similarity_threshold:
                # 유사 사례가 있는 경우: RAG 기반 생성
                highest_similarity = similar_meetings[0]['similarity_score']
                print(f"✅ 유사 사례 발견! 최고 유사도: {highest_similarity:.4f}")
                result = self._generate_from_similar_cases(meeting_text, similar_meetings)
                
            else:
                # 유사 사례가 없는 경우: LLM 생성 + 학습
                print("⚠️ 유사 사례 없음 - LLM 생성 후 학습")
                result = self._generate_with_llm_and_learn(meeting_text, similar_meetings)
            
            return result
            
        except Exception as e:
            print(f"❌ TODO 추출 중 오류: {e}")
            return self._generate_with_llm_only(meeting_text)

    def _search_similar_meetings(self, query_meeting: str, top_k: int = 5) -> List[Dict]:
        """유사한 회의록 검색"""
        
        try:
            # 핵심 내용 추출
            core_query = self._extract_core_content(query_meeting)
            
            # ChromaDB에서 검색
            results = self.collection.query(
                query_texts=[core_query],
                n_results=min(top_k, self.collection.count()),
                include=['documents', 'metadatas', 'distances']
            )
            
            similar_meetings = []
            
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    distance = results['distances'][0][i]
                    similarity = max(0, 1 - distance)
                    
                    similar_meetings.append({
                        'id': results['ids'][0][i],
                        'meeting_text': results['metadatas'][0][i].get('original_meeting_text', results['documents'][0][i]),
                        'todo_list': results['metadatas'][0][i].get('todo_list', ''),
                        'similarity_score': similarity,
                        'metadata': results['metadatas'][0][i]
                    })
            
            # 유사도 순으로 정렬
            similar_meetings.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return similar_meetings
            
        except Exception as e:
            print(f"❌ 유사 회의록 검색 실패: {e}")
            return []

    def _extract_core_content(self, meeting_text: str) -> str:
        """주제 기반 핵심 내용 추출"""
        
        # 1단계: 회의 주제/도메인 분류
        meeting_topic = self._classify_meeting_topic(meeting_text)
        
        core_parts = [f"회의주제: {meeting_topic}"]
        
        # 2단계: 해당 주제의 핵심 키워드 추출
        topic_keywords = self._extract_topic_keywords(meeting_text, meeting_topic)
        if topic_keywords:
            core_parts.append(f"핵심키워드: {' '.join(topic_keywords)}")
        
        # 3단계: 액션 아이템 추출 (주제 관련만)
        action_items = self._extract_topic_actions(meeting_text, meeting_topic)
        if action_items:
            core_parts.extend(action_items[:3])  # 최대 3개
        
        # 4단계: 주제별 중요 정보 추출
        topic_specific_info = self._extract_topic_specific_info(meeting_text, meeting_topic)
        if topic_specific_info:
            core_parts.append(topic_specific_info)
        
        core_content = ' '.join(core_parts)
        if len(core_content) > 500:
            core_content = core_content[:500]
        
        return core_content

    def _classify_meeting_topic(self, meeting_text: str) -> str:
        """LLM 기반 동적 회의 주제 분류"""
        
        print("🤖 LLM으로 회의 주제 분류 중...")
        
        # 회의록이 너무 길면 앞부분만 사용 (토큰 절약)
        analysis_text = meeting_text[:1000] if len(meeting_text) > 1000 else meeting_text
        
        topic_prompt = f"""
다음 회의록을 분석하여 가장 적절한 주제를 한 단어 또는 두 단어로 분류해주세요.

회의록:
{analysis_text}

지시사항:
1. 회의의 핵심 주제나 도메인을 파악하세요
2. 구체적이고 명확한 주제명을 제시하세요
3. 한국어로 답변하세요
4. 한 단어 또는 최대 두 단어로만 답변하세요

예시:
- 마케팅, 개발, 기획, 영업, 인사, 재무, 운영
- 의료, 법무, 교육, 제조, 금융, 건설, 디자인
- 의료수술, 법무계약, 제조품질, 교육과정 등

회의 주제:
        """
        
        try:
            # Solar API로 주제 분류 (전용 함수 사용)
            classified_topic = self._call_solar_for_topic_classification(topic_prompt).strip()
            
            # 결과 정리 (특수문자 제거, 길이 제한)
            classified_topic = self._clean_topic_name(classified_topic)
            
            print(f"🎯 LLM 주제 분류 결과: '{classified_topic}'")
            return classified_topic
            
        except Exception as e:
            print(f"❌ LLM 주제 분류 실패: {e}")
            # 백업: 간단한 키워드 기반 분류
            return self._fallback_topic_classification(meeting_text)

    def _clean_topic_name(self, topic: str) -> str:
        """주제명 정리"""
        
        # 불필요한 문자 제거
        topic = re.sub(r'[^\w가-힣\s]', '', topic)
        
        # 공백 정리
        topic = ' '.join(topic.split())
        
        # 길이 제한 (10자 이내)
        if len(topic) > 10:
            topic = topic[:10]
        
        # 빈 값 처리
        if not topic or topic.isspace():
            topic = "일반"
        
        return topic

    def _fallback_topic_classification(self, meeting_text: str) -> str:
        """LLM 실패 시 백업 분류"""
        
        # 주요 도메인 키워드 매칭
        domain_patterns = {
            "의료": r'의료|병원|수술|환자|의사|간호사|치료|진료|의료진|담당의|수술실|병원',
            "법무": r'법무|계약|법률|소송|변호사|법적|규정|컴플라이언스|계약서',
            "교육": r'교육|학교|수업|학생|교사|강의|커리큘럼|학습|연수',
            "제조": r'제조|생산|공장|품질|생산라인|제품|공정|품질관리|생산성',
            "금융": r'금융|은행|투자|대출|펀드|증권|보험|자산|리스크',
            "건설": r'건설|공사|현장|시공|설계|건축|토목|공사현장',
            "마케팅": r'마케팅|광고|브랜드|캠페인|홍보|콘텐츠',
            "개발": r'개발|프로그래밍|시스템|API|코딩|소프트웨어',
            "기획": r'기획|전략|로드맵|계획|분석',
            "영업": r'영업|세일즈|고객|클라이언트|계약|매출',
            "인사": r'인사|채용|면접|평가|승진|조직',
            "재무": r'재무|회계|예산|비용|손익|경비',
            "운영": r'운영|관리|프로세스|업무|절차'
        }
        
        # 각 도메인별 매칭 점수 계산
        scores = {}
        for domain, pattern in domain_patterns.items():
            matches = re.findall(pattern, meeting_text, re.IGNORECASE)
            scores[domain] = len(matches)
        
        # 가장 높은 점수의 도메인 반환
        if scores and max(scores.values()) > 0:
            best_domain = max(scores.items(), key=lambda x: x[1])[0]
            print(f"🔄 백업 분류 결과: {best_domain} (점수: {scores[best_domain]})")
            return best_domain
        
        print("🤷 분류 불가 - 일반으로 분류")
        return "일반"

    def _extract_topic_keywords(self, meeting_text: str, topic: str) -> List[str]:
        """주제별 특화 키워드 추출"""
        
        topic_keyword_patterns = {
            "마케팅": r'(브랜드|캠페인|타겟|세그먼트|포지셔닝|채널|ROI|CTR|노출|클릭|전환)',
            "개발": r'(스프린트|백로그|이슈|커밋|머지|리뷰|리팩토링|아키텍처|스택|프레임워크)',  
            "기획": r'(로드맵|마일스톤|우선순위|요구사항|스펙|가설|검증|피봇|린스타트업)',
            "영업": r'(리드|파이프라인|크로징|B2B|B2C|어카운트|프로스펙|딜|쿼터)',
            "인사": r'(JD|스킬셋|피드백|1on1|성장|커리어|문화|밸류|리텐션)',
            "재무": r'(손익|현금흐름|EBITDA|ROI|IRR|밸류에이션|투자유치|시리즈)',
            "의료": r'(환자|수술|진료|치료|의료진|담당의|간호사|병원|수술실|의료기기)',
            "일반": r'(진행|완료|검토|준비|회의|논의|결정|방향|계획|일정)'
        }
        
        pattern = topic_keyword_patterns.get(topic, topic_keyword_patterns["일반"])
        keywords = re.findall(pattern, meeting_text, re.IGNORECASE)
        
        return list(set(keywords[:5]))  # 중복 제거 후 최대 5개

    def _extract_topic_actions(self, meeting_text: str, topic: str) -> List[str]:
        """주제별 액션 아이템 추출"""
        
        # 주제별 액션 패턴
        if topic == "마케팅":
            action_patterns = [
                r'(.{10,50}?(?:촬영|제작|런칭|게시|송출|배포))',
                r'(.{10,50}?(?:기획서|시나리오|콘티|크리에이티브)\s*(?:작성|준비))',
            ]
        elif topic == "개발":
            action_patterns = [
                r'(.{10,50}?(?:개발|구현|수정|테스트|배포|릴리즈))',
                r'(.{10,50}?(?:API|기능|모듈|컴포넌트)\s*(?:개발|구현))',
            ]
        elif topic == "의료":
            action_patterns = [
                r'(.{10,50}?(?:수술|진료|치료|검사|처방))',
                r'(.{10,50}?(?:환자|의료진|담당의)\s*(?:확인|준비|배정))',
            ]
        else:
            # 일반적인 액션 패턴
            action_patterns = [
                r'(.{10,50}?(?:완료|작성|준비|제출|검토))',
                r'([가-힣]{2,4})\s*(?:가|이)\s*(.{10,50}?(?:하겠습니다|할 예정))'
            ]
        
        actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, meeting_text)
            for match in matches:
                if isinstance(match, tuple):
                    actions.append(' '.join(match))
                else:
                    actions.append(match)
        
        return actions

    def _extract_topic_specific_info(self, meeting_text: str, topic: str) -> str:
        """주제별 특화 정보 추출"""
        
        if topic == "마케팅":
            # 타겟, 예산, 채널 정보 추출
            target_match = re.search(r'타겟[은는]?\s*([^.\n]{10,50})', meeting_text)
            budget_match = re.search(r'예산[은는]?\s*([^.\n]{5,30})', meeting_text)
            
            info_parts = []
            if target_match:
                info_parts.append(f"타겟: {target_match.group(1)}")
            if budget_match:
                info_parts.append(f"예산: {budget_match.group(1)}")
                
            return " | ".join(info_parts) if info_parts else ""
            
        elif topic == "개발":
            # 기술스택, 일정 정보 추출
            tech_match = re.search(r'(React|Vue|Python|Java|Node\.js|Spring|Django)', meeting_text)
            schedule_match = re.search(r'([0-9]+주|[0-9]+개월|[0-9]+일)\s*(?:안에|내에|까지)', meeting_text)
            
            info_parts = []
            if tech_match:
                info_parts.append(f"기술: {tech_match.group(1)}")
            if schedule_match:
                info_parts.append(f"일정: {schedule_match.group(1)}")
                
            return " | ".join(info_parts) if info_parts else ""
            
        elif topic == "의료":
            # 환자, 수술, 담당의 정보 추출
            patient_match = re.search(r'환자[는은]?\s*([^.\n]{5,30})', meeting_text)
            surgery_match = re.search(r'수술[은는]?\s*([^.\n]{10,40})', meeting_text)
            doctor_match = re.search(r'담당의[는은]?\s*([^.\n]{5,20})', meeting_text)
            
            info_parts = []
            if patient_match:
                info_parts.append(f"환자: {patient_match.group(1)}")
            if surgery_match:
                info_parts.append(f"수술: {surgery_match.group(1)}")
            if doctor_match:
                info_parts.append(f"담당의: {doctor_match.group(1)}")
                
            return " | ".join(info_parts) if info_parts else ""
        
        return ""

    def _generate_from_similar_cases(self, meeting_text: str, similar_meetings: List[Dict]) -> Dict:
        """유사 사례 기반 TODO 생성"""
        
        top_case = similar_meetings[0]
        
        # 유사도에 따라 다른 전략 사용
        if top_case['similarity_score'] >= 0.8:
            # 높은 유사도: 기존 사례 참고해서 생성
            generated_todo = self._generate_with_high_similarity_reference(meeting_text, similar_meetings[:3])
            method = "high_similarity_reference"
            
        elif top_case['similarity_score'] >= 0.6:
            # 중간 유사도: LLM으로 개선
            generated_todo = self._improve_with_llm(meeting_text, similar_meetings[:3])
            method = "improved_rag"
            
        else:
            # 낮은 유사도: 패턴 기반 생성
            generated_todo = self._generate_from_patterns(meeting_text, similar_meetings[:3])
            method = "pattern_based"
        
        # 회의 주제 정보 추가
        meeting_topic = self._classify_meeting_topic(meeting_text)
        
        return {
            'generated_todo': generated_todo,
            'confidence_score': top_case['similarity_score'],
            'method': method,
            'similar_cases': similar_meetings[:3],
            'learning_occurred': False,
            'meeting_topic': meeting_topic,
            'timestamp': datetime.now().isoformat()
        }

    def _generate_with_llm_and_learn(self, meeting_text: str, weak_similar_cases: List[Dict]) -> Dict:
        """LLM으로 TODO 생성 (사용자 승인 후 학습)"""
        
        print("🤖 LLM으로 새로운 TODO 생성 중...")
        
        # LLM으로 TODO 생성
        generated_todo = self._generate_todo_with_solar(meeting_text)
        
        # ✅ 자동 학습 비활성화 - 사용자 승인 후에만 학습
        print("⏸️ 자동 학습 비활성화 - 사용자 검증 대기 중")
        
        # 회의 주제 정보 추가
        meeting_topic = self._classify_meeting_topic(meeting_text)
        
        return {
            'generated_todo': generated_todo,
            'confidence_score': 0.5,
            'method': 'llm_generation',
            'similar_cases': weak_similar_cases,
            'learning_occurred': False,  # 아직 학습 안됨
            'needs_user_approval': True,  # 사용자 승인 필요
            'meeting_topic': meeting_topic,
            'timestamp': datetime.now().isoformat()
        }

    def _generate_with_llm_only(self, meeting_text: str) -> Dict:
        """벡터 DB 없이 LLM만으로 TODO 생성"""
        
        generated_todo = self._generate_todo_with_solar(meeting_text)
        
        # 회의 주제 정보 추가
        meeting_topic = self._classify_meeting_topic(meeting_text)
        
        return {
            'generated_todo': generated_todo,
            'confidence_score': 0.5,
            'method': 'llm_only',
            'similar_cases': [],
            'learning_occurred': False,
            'meeting_topic': meeting_topic,
            'timestamp': datetime.now().isoformat()
        }

    def _call_solar_for_topic_classification(self, prompt: str) -> str:
        """주제 분류 전용 Solar API 호출"""
        
        try:
            headers = {
                "Authorization": f"Bearer {os.getenv('SOLAR_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "solar-1-mini-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50,  # 주제 분류용으로 짧게
                "temperature": 0.1,  # 일관성을 위해 더 낮게
                "top_p": 0.8
            }
            
            response = requests.post(
                "https://api.upstage.ai/v1/solar/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                return result.strip()
            else:
                print(f"❌ Solar API 응답 오류: {response.status_code} - {response.text}")
                return "일반"
                
        except Exception as e:
            print(f"❌ Solar API 호출 실패: {e}")
            return "일반"

    def _generate_todo_with_solar(self, meeting_text: str) -> str:
        """Solar API로 TODO 생성"""
        
        prompt = f"""
다음 회의록을 분석하여 구체적이고 실행 가능한 TODO 리스트를 추출해주세요.

회의록:
{meeting_text}

지시사항:
1. 회의에서 언급된 구체적인 할 일들을 추출하세요
2. 담당자가 명시된 경우 포함하세요
3. 기한이 언급된 경우 포함하세요
⚠️ 중요: 설명문이나 메타 정보는 절대 생성하지 마세요! 오직 할 일 목록만 출력하세요!

출력 형식:
1. 구체적인 할 일 내용 (담당: 담당자명) (기한: 기한)
2. 구체적인 할 일 내용 (담당: 담당자명) (기한: 기한)
...

할 일 목록만 출력:
        """
        
        try:
            headers = {
                "Authorization": f"Bearer {os.getenv('SOLAR_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "solar-1-mini-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # 일관성을 위해 낮게 설정
                "top_p": 0.8,
                "max_tokens": 1500
            }
            
            response = requests.post(
                "https://api.upstage.ai/v1/solar/chat/completions",
                headers=headers,
                json=data
            )
            
            todo_result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "TODO 추출 실패")
            return todo_result
            
        except Exception as e:
            print(f"❌ Solar API TODO 생성 실패: {e}")
            return f"TODO 생성 실패: {str(e)}"

    def _generate_with_high_similarity_reference(self, meeting_text: str, similar_cases: List[Dict]) -> str:
        """높은 유사도 사례를 참고하여 TODO 생성"""
        
        reference_case = similar_cases[0]
        
        prompt = f"""
다음은 매우 유사한 회의록과 그 TODO 리스트입니다. 이를 참고하여 새로운 회의록의 TODO를 정확하게 생성해주세요.

**참고할 유사 회의록:**
{reference_case['meeting_text'][:1000]}...

**참고할 TODO 리스트:**
{reference_case['todo_list']}

**새로운 회의록:**
{meeting_text}

**지시사항:**
1. 위 참고 사례의 TODO 구조와 분류 방식을 따르세요
2. 새로운 회의록의 구체적인 내용에 맞게 TODO를 조정하세요
3. 담당자, 기한를 명확히 표시하세요

**새로운 회의록의 TODO 리스트:**
        """
        
        return self._generate_todo_with_solar(prompt)

    def _improve_with_llm(self, meeting_text: str, similar_cases: List[Dict]) -> str:
        """LLM으로 유사 사례 개선"""
        
        cases_text = ""
        for i, case in enumerate(similar_cases, 1):
            cases_text += f"""
사례 {i} (유사도: {case['similarity_score']:.2f}):
회의: {case['meeting_text'][:300]}...
TODO: {case['todo_list'][:300]}...
"""
        
        prompt = f"""
다음은 비슷한 유형의 회의록들과 각각의 TODO 리스트입니다. 이 패턴들을 참고하여 새로운 회의록의 TODO를 생성해주세요.

**유사 사례들의 패턴:**
{cases_text}

**새로운 회의록:**
{meeting_text}

**지시사항:**
1. 위 유사 사례들의 공통 패턴을 파악하여 활용하세요
2. TODO의 구조와 형식을 일관성 있게 유지하세요
3. 새로운 회의록의 내용에 맞게 구체적으로 작성하세요

**새로운 회의록의 TODO 리스트:**
        """
        
        return self._generate_todo_with_solar(prompt)

    def _generate_from_patterns(self, meeting_text: str, similar_cases: List[Dict]) -> str:
        """패턴 기반 TODO 생성"""
        
        return self._improve_with_llm(meeting_text, similar_cases)

    def _save_to_knowledge_base(self, meeting_text: str, todo_list: str) -> bool:
        """지식 베이스에 새로운 학습 데이터 저장"""
        
        try:
            doc_id = str(uuid.uuid4())
            
            metadata = {
                "meeting_length": len(meeting_text),
                "todo_count": len([line for line in todo_list.split('\n') if line.strip()]),
                "doc_id": doc_id,
                "todo_list": todo_list,
                "original_meeting_text": meeting_text,
                "created_at": datetime.now().isoformat(),
                "source": "llm_generated"
            }
            
            # 핵심 내용 추출
            core_content = self._extract_core_content(meeting_text)
            
            # 벡터 DB에 추가
            self.collection.add(
                documents=[core_content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            print(f"🎓 새로운 지식이 학습되었습니다! ID: {doc_id[:8]}...")
            return True
            
        except Exception as e:
            print(f"❌ 학습 저장 중 오류: {e}")
            return False

    def get_system_status(self) -> Dict:
        """시스템 상태 반환"""
        
        if not self.collection:
            return {
                'vector_db_size': 0,
                'system_health': 'no_vector_db'
            }
        
        try:
            vector_db_size = self.collection.count()
            
            return {
                'vector_db_size': vector_db_size,
                'system_health': 'healthy' if vector_db_size > 0 else 'initializing'
            }
            
        except:
            return {
                'vector_db_size': 0,
                'system_health': 'error'
            } 