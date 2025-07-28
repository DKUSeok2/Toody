import fitz
import os
from pathlib import Path

def extract_text_from_file(filepath):
    """파일에서 텍스트 추출 - 확장자 유연하게 처리"""
    
    print(f"🔍 파일 경로: {filepath}")
    
    # 파일 경로에서 확장자 추출 (대소문자 구분 안함)
    file_extension = Path(filepath).suffix.lower()
    
    # 파일명에 확장자가 없는 경우, 파일명에서 추출 시도
    if not file_extension:
        filename = os.path.basename(filepath)
        if '_txt' in filename:
            file_extension = '.txt'
        elif '_pdf' in filename:
            file_extension = '.pdf'
        else:
            # 파일 내용으로 판단 시도
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    f.read(100)  # 처음 100자 읽기 시도
                file_extension = '.txt'
                print(f"✅ 텍스트 파일로 판단: {filepath}")
            except UnicodeDecodeError:
                try:
                    # PDF 파일인지 확인
                    doc = fitz.open(filepath)
                    doc.close()
                    file_extension = '.pdf'
                    print(f"✅ PDF 파일로 판단: {filepath}")
                except:
                    raise ValueError(f"지원하지 않는 파일 형식입니다: {filepath}")
    
    print(f"📁 감지된 파일 확장자: {file_extension}")
    
    # 파일 타입에 따라 처리
    if file_extension == '.pdf':
        return extract_text_from_pdf(filepath)
    elif file_extension in ['.txt', '.text']:
        return extract_text_from_txt(filepath)
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {file_extension}")

def extract_text_from_txt(filepath):
    """텍스트 파일에서 텍스트 추출"""
    
    encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-16']  # 한국어 인코딩들
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"✅ 텍스트 파일 읽기 성공 (인코딩: {encoding})")
                return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"⚠️ 인코딩 {encoding} 실패: {e}")
            continue
    
    raise ValueError(f"텍스트 파일을 읽을 수 없습니다: {filepath}")
    
def extract_text_from_pdf(filepath):
    """PDF 파일에서 텍스트 추출"""
    
    try:
        doc = fitz.open(filepath)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        print(f"✅ PDF 파일 읽기 성공 (페이지 수: {len(doc)})")
        return full_text
    except Exception as e:
        raise ValueError(f"PDF 파일을 읽을 수 없습니다: {e}")