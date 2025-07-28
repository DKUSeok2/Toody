#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChromaDB 초기화 스크립트 (키워드 기반 주제 분류)
API 키 없이도 키워드 매칭으로 주제 분류
"""

import json
import uuid
import re
from pathlib import Path
from datetime import datetime

# ChromaDB 및 임베딩 관련
import chromadb
from sentence_transformers import SentenceTransformer

def keyword_classify_topic(meeting_text: str) -> str:
    """키워드 기반 주제 분류"""
    
    # 한국어 키워드 패턴 (더 확장된 버전)
    domain_patterns = {
        "의료": r'의료|병원|수술|환자|의사|간호사|치료|진료|의료진|담당의|수술실|병원|치료제|약물|병원장|의료기기|응급실|입원|외래|검사|진단|처방|수술실|마취|회복|병상',
        "법무": r'법무|계약|법률|소송|변호사|법적|규정|컴플라이언스|계약서|법원|재판|소송|고발|법적책임|법률검토|계약검토|법적분쟁|소송비용',
        "교육": r'교육|학교|수업|학생|교사|강의|커리큘럼|학습|연수|교육과정|교육청|학급|학년|교육프로그램|교육정책|학사일정|교육예산|교육개발',
        "제조": r'제조|생산|공장|품질|생산라인|제품|공정|품질관리|생산성|제조업|생산계획|품질검사|불량률|생산능력|제조원가|생산관리|품질보증',
        "금융": r'금융|은행|투자|대출|펀드|증권|보험|자산|리스크|금융상품|금리|투자수익|자금조달|신용평가|금융시장|투자포트폴리오|금융규제',
        "건설": r'건설|공사|현장|시공|설계|건축|토목|공사현장|건설업|건축물|공사일정|안전관리|건설자재|건축설계|시공업체|공사비용|건축허가',
        "마케팅": r'마케팅|광고|브랜드|캠페인|홍보|콘텐츠|마케팅전략|광고비|브랜딩|마케팅예산|고객획득|브랜드인지도|광고효과|홍보활동|마케팅채널',
        "개발": r'개발|프로그래밍|시스템|API|코딩|소프트웨어|개발팀|시스템개발|프로그램|어플리케이션|웹개발|앱개발|소프트웨어개발|시스템구축',
        "기획": r'기획|전략|로드맵|계획|분석|기획팀|사업계획|전략기획|기획안|프로젝트기획|사업전략|기획서|계획수립|전략수립|기획업무',
        "영업": r'영업|세일즈|고객|클라이언트|계약|매출|영업팀|영업실적|고객관리|영업전략|계약체결|영업목표|고객만족|영업활동|계약서',
        "인사": r'인사|채용|면접|평가|승진|조직|인사팀|인사관리|직원|근무|채용공고|인사평가|조직개편|인사정책|근무조건|급여|복리후생',
        "재무": r'재무|회계|예산|비용|손익|경비|재무팀|회계처리|예산편성|재무분석|손익계산|경비관리|재무제표|회계감사|예산집행|재무계획',
        "운영": r'운영|관리|프로세스|업무|절차|운영팀|업무관리|운영관리|업무프로세스|운영체계|관리시스템|업무절차|운영방침|관리방안|업무개선',
        "IT": r'IT|정보기술|컴퓨터|네트워크|데이터베이스|서버|클라우드|IT시스템|정보시스템|IT인프라|데이터관리|시스템관리|네트워크관리',
        "연구개발": r'연구|개발|R&D|연구소|기술개발|연구개발|기술연구|연구프로젝트|기술혁신|연구성과|개발성과|연구비|기술개발비',
        "품질": r'품질|QA|QC|품질관리|품질보증|품질검사|품질개선|품질시스템|품질기준|품질평가|품질관리팀|품질인증|품질감사|품질향상'
    }
    
    # 각 도메인별 매칭 점수 계산
    scores = {}
    for domain, pattern in domain_patterns.items():
        matches = re.findall(pattern, meeting_text, re.IGNORECASE)
        scores[domain] = len(matches)
    
    # 가장 높은 점수의 도메인 반환
    if scores and max(scores.values()) > 0:
        best_domain = max(scores.items(), key=lambda x: x[1])[0]
        print(f"🎯 키워드 기반 분류: {best_domain} (매칭: {scores[best_domain]}개)")
        return best_domain
    
    print("🤷 분류 불가 - 일반으로 분류")
    return "일반"

def format_todo_from_summary(summary_array):
    """summary 배열을 TODO 형식으로 변환"""
    if not summary_array:
        return "TODO 항목이 없습니다."
    
    formatted_lines = []
    for i, item in enumerate(summary_array, 1):
        if isinstance(item, dict):
            # 실제 JSON 구조에 맞게 수정
            content = item.get('맥락', item.get('내용', '내용 없음'))
            person = item.get('담당자', '담당자 미정')
            deadline = item.get('기한', '기한 미정')
            category = item.get('카테고리', '업무')
            
            formatted_line = f"{i}. [{category}] {content} (담당: {person}) (기한: {deadline})"
        else:
            formatted_line = f"{i}. [업무] {str(item)} (담당: 미정) (기한: 미정)"
        
        formatted_lines.append(formatted_line)
    
    return '\n'.join(formatted_lines)

def extract_core_content_keyword(meeting_text: str, meeting_topic: str) -> str:
    """키워드 기반 핵심 내용 추출"""
    
    core_parts = [f"회의주제: {meeting_topic}"]
    
    # 주제별 핵심 키워드 추출
    topic_keyword_patterns = {
        "의료": r'(환자|수술|진료|치료|의료진|담당의|간호사|병원|수술실|의료기기)',
        "법무": r'(계약|법률|소송|변호사|법적|규정|컴플라이언스|계약서|법원|재판)',
        "교육": r'(교육|학교|수업|학생|교사|강의|커리큘럼|학습|연수|교육과정)',
        "제조": r'(제조|생산|공장|품질|생산라인|제품|공정|품질관리|생산성)',
        "마케팅": r'(브랜드|캠페인|타겟|세그먼트|포지셔닝|채널|광고|홍보|마케팅)',
        "개발": r'(개발|프로그래밍|시스템|API|코딩|소프트웨어|프로그램|어플리케이션)',
        "기획": r'(기획|전략|로드맵|계획|분석|사업계획|전략기획|기획안)',
        "영업": r'(영업|세일즈|고객|클라이언트|계약|매출|영업실적|고객관리)',
        "인사": r'(인사|채용|면접|평가|승진|조직|직원|근무|인사관리)',
        "재무": r'(재무|회계|예산|비용|손익|경비|재무분석|회계처리)',
        "일반": r'(진행|완료|검토|준비|회의|논의|결정|방향|계획|일정)'
    }
    
    pattern = topic_keyword_patterns.get(meeting_topic, topic_keyword_patterns["일반"])
    keywords = re.findall(pattern, meeting_text, re.IGNORECASE)
    
    if keywords:
        unique_keywords = list(set(keywords[:5]))  # 중복 제거 후 최대 5개
        core_parts.append(f"핵심키워드: {' '.join(unique_keywords)}")
    
    # 액션 관련 패턴 추출
    action_patterns = [
        r'(.{10,50}?(?:완료|작성|준비|제출|검토|진행|실행|수행))',
        r'([가-힣]{2,4})\s*(?:가|이)\s*(.{10,50}?(?:하겠습니다|할 예정|진행예정))'
    ]
    
    actions = []
    for pattern in action_patterns:
        matches = re.findall(pattern, meeting_text)
        for match in matches:
            if isinstance(match, tuple):
                actions.append(' '.join(match))
            else:
                actions.append(match)
    
    if actions:
        core_parts.extend(actions[:3])  # 최대 3개
    
    core_content = ' '.join(core_parts)
    if len(core_content) > 500:
        core_content = core_content[:500]
    
    return core_content

def load_json_to_chromadb(json_file_path: str):
    """JSON 파일을 ChromaDB에 로드 (키워드 기반 분류)"""
    
    print("🚀 ChromaDB 초기화 시작 (키워드 기반)")
    print("=" * 50)
    
    # JSON 파일 로드
    print(f"📂 로드할 파일: {json_file_path}")
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ JSON 파일 로드 성공: {len(data)}개 데이터")
    
    # ChromaDB 초기화
    vector_db_path = "data/vectordb"
    collection_name = "meeting_todos"
    embedding_model_name = "jhgan/ko-sroberta-multitask"
    
    # 디렉토리 생성
    Path(vector_db_path).mkdir(parents=True, exist_ok=True)
    
    try:
        client = chromadb.PersistentClient(path=vector_db_path)
        
        try:
            collection = client.get_collection(collection_name)
            print(f"✅ 기존 벡터 DB 컬렉션 로드: {collection_name}")
        except:
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": "회의록-TODO 쌍 저장소"}
            )
            print(f"✅ 새 벡터 DB 컬렉션 생성: {collection_name}")
            
        # 임베딩 모델 초기화
        embedding_model = SentenceTransformer(embedding_model_name)
        print(f"✅ 임베딩 모델 로드: {embedding_model_name}")
        
        print("✅ ChromaDB 연결 성공")
        
        # 기존 데이터 확인
        existing_count = collection.count()
        print(f"📊 기존 ChromaDB 데이터: {existing_count}개")
        
        added_count = 0
        
        # JSON 구조: {"data1": {"original": "...", "summary": [...]}, ...}
        for key, item in data.items():
            try:
                if not isinstance(item, dict):
                    continue
                    
                meeting_text = item.get('original', '')
                summary_array = item.get('summary', [])
                
                if not meeting_text:
                    continue
                
                # 키워드 기반 주제 분류
                meeting_topic = keyword_classify_topic(meeting_text)
                
                # 핵심 내용 추출
                core_content = extract_core_content_keyword(meeting_text, meeting_topic)
                
                # TODO 형식 변환
                todo_list = format_todo_from_summary(summary_array)
                
                # 메타데이터 생성
                doc_id = str(uuid.uuid4())
                metadata = {
                    "meeting_length": len(meeting_text),
                    "todo_count": len([line for line in todo_list.split('\n') if line.strip()]),
                    "doc_id": doc_id,
                    "todo_list": todo_list,
                    "original_meeting_text": meeting_text,
                    "meeting_topic": meeting_topic,
                    "created_at": datetime.now().isoformat(),
                    "source": "json_dataset_keyword_classified"
                }
                
                # 벡터 DB에 추가
                collection.add(
                    documents=[core_content],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
                
                added_count += 1
                print(f"🎓 새로운 지식이 학습되었습니다! ID: {doc_id[:8]}... (주제: {meeting_topic})")
                
                # 진행상황 출력
                if added_count % 10 == 0:
                    print(f"📈 진행상황: {added_count}개 추가됨")
                    
            except Exception as e:
                print(f"❌ 데이터 처리 중 오류: {e}")
                continue
        
        print("=" * 50)
        print(f"🎉 ChromaDB 초기화 완료!")
        print(f"📊 총 추가된 데이터: {added_count}개")
        print(f"💾 벡터 DB 위치: {vector_db_path}")
        print(f"📚 컬렉션명: {collection_name}")
        
        # 주제별 통계
        topic_stats = {}
        for i in range(collection.count()):
            results = collection.get(limit=collection.count())
            for metadata in results['metadatas']:
                topic = metadata.get('meeting_topic', '일반')
                topic_stats[topic] = topic_stats.get(topic, 0) + 1
        
        print("\n📊 주제별 분포:")
        for topic, count in sorted(topic_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {topic}: {count}개")
            
    except Exception as e:
        print(f"❌ ChromaDB 초기화 실패: {e}")
        return False
    
    return True

if __name__ == "__main__":
    json_file = "output_dataset_ver4.json"
    
    if not Path(json_file).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
        exit(1)
    
    try:
        success = load_json_to_chromadb(json_file)
        if success:
            print("\n✅ 모든 작업이 성공적으로 완료되었습니다!")
        else:
            print("\n❌ 초기화 중 오류가 발생했습니다.")
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}") 