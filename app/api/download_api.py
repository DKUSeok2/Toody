from flask import Blueprint, send_file, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import io
import re
import urllib.parse
from datetime import datetime

download_bp = Blueprint("download", __name__)

# upload_api에서 meetings_db 가져오기
from app.api.upload_api import meetings_db

def safe_filename(filename):
    """파일명을 안전하게 처리 (한글 보존)"""
    # 파일 시스템에서 금지된 문자만 제거하고 한글은 보존
    safe_name = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 연속된 공백을 하나로 줄이고 하이픈으로 변경
    safe_name = re.sub(r'\s+', '-', safe_name.strip())
    # 파일명이 너무 길면 줄이기 (확장자 보존)
    if len(safe_name) > 100:
        name_part, ext_part = os.path.splitext(safe_name)
        safe_name = name_part[:95] + ext_part
    return safe_name

def create_content_disposition_header(filename):
    """브라우저 호환성을 위한 Content-Disposition 헤더 생성"""
    # ASCII 안전한 fallback 파일명 
    ascii_filename = re.sub(r'[^\x00-\x7F]+', 'meeting', filename)
    ascii_filename = re.sub(r'[<>:"/\\|?*]', '', ascii_filename)
    ascii_filename = re.sub(r'\s+', '_', ascii_filename.strip())
    
    # UTF-8 인코딩된 파일명 (URL 인코딩)
    try:
        encoded_filename = urllib.parse.quote(filename, safe='')
        # RFC 5987과 RFC 6266 표준을 모두 지원하는 형식
        return f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    except Exception as e:
        print(f"⚠️ UTF-8 인코딩 실패, ASCII fallback 사용: {e}")
        return f'attachment; filename="{ascii_filename}"'

@download_bp.route("/api/download/txt/<meeting_id>", methods=["GET"])
def download_txt(meeting_id):
    """TXT 파일 다운로드"""
    print(f"🔄 TXT 다운로드 요청: meeting_id={meeting_id}")
    
    try:
        if meeting_id not in meetings_db:
            print(f"❌ 회의 ID {meeting_id}를 찾을 수 없음")
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        meeting_data = meetings_db[meeting_id]
        print(f"✅ 회의 데이터 로드 성공: {meeting_data.get('name', 'Unknown')}")
        
        summary = meeting_data.get("summary", "요약이 생성되지 않았습니다.")
        
        # TODO 항목 추출
        todo_content = ""
        if meeting_data.get("todo_result") and isinstance(meeting_data["todo_result"], dict):
            todo_data = meeting_data["todo_result"].get("generated_todo", "")
            if todo_data:
                print(f"✅ TODO 데이터 발견: {len(todo_data)}자")
                todo_content = f"""

할 일 목록 (TODO)
----------------
{todo_data}"""
            else:
                print("⚠️ TODO 데이터가 비어있음")
        else:
            print("⚠️ TODO 데이터 없음")
        
        # TXT 내용 생성 (비밀번호와 회의 ID 제외)
        txt_content = f"""회의록 요약
================

회의명: {meeting_data['name']}
날짜: {meeting_data['date']}

3줄 요약
--------
{summary}{todo_content}
"""
        
        print(f"✅ TXT 내용 생성 완료: {len(txt_content)}자")
        
        # 메모리에서 파일 생성
        txt_io = io.StringIO()
        txt_io.write(txt_content)
        txt_io.seek(0)
        
        # 바이트로 변환
        txt_bytes = io.BytesIO()
        txt_bytes.write(txt_content.encode('utf-8'))
        txt_bytes.seek(0)
        
        # 파일명: 날짜와 회의 이름만 포함
        filename = safe_filename(f"{meeting_data['date']}_{meeting_data['name']}.txt")
        print(f"✅ 파일명 생성: {filename}")
        
        response = send_file(
            txt_bytes,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
        # 브라우저 호환성을 위한 헤더 설정
        response.headers['Content-Disposition'] = create_content_disposition_header(filename)
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        print(f"✅ Content-Disposition 헤더: {response.headers['Content-Disposition']}")
        
        print(f"✅ TXT 다운로드 응답 준비 완료")
        return response
        
    except Exception as e:
        print(f"❌ TXT 다운로드 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"다운로드 중 오류가 발생했습니다: {str(e)}"}), 500

@download_bp.route("/api/download/pdf/<meeting_id>", methods=["GET"])
def download_pdf(meeting_id):
    """PDF 파일 다운로드"""
    print(f"🔄 PDF 다운로드 요청: meeting_id={meeting_id}")
    
    try:
        if meeting_id not in meetings_db:
            print(f"❌ 회의 ID {meeting_id}를 찾을 수 없음")
            return jsonify({"error": "회의를 찾을 수 없습니다"}), 404
        
        meeting_data = meetings_db[meeting_id]
        print(f"✅ 회의 데이터 로드 성공: {meeting_data.get('name', 'Unknown')}")
        
        summary = meeting_data.get("summary", "요약이 생성되지 않았습니다.")
        
        # 한글 폰트 등록 (assets 폴더의 폰트 사용)
        try:
            font_name = 'Helvetica'  # 기본값
            
            # assets 폰트 경로 (올바른 경로로 수정)
            # 현재 파일: summary_project/app/api/download_api.py
            # 목표 경로: summary_project/assets/fonts/NanumGothic.ttf
            current_dir = os.path.dirname(os.path.abspath(__file__))  # summary_project/app/api/
            project_root = os.path.dirname(os.path.dirname(current_dir))  # summary_project/
            assets_font_path = os.path.join(project_root, 'assets', 'fonts', 'NanumGothic.ttf')
            
            print(f"🔍 폰트 경로 확인: {assets_font_path}")
            print(f"📁 폰트 파일 존재 여부: {os.path.exists(assets_font_path)}")
            
            if os.path.exists(assets_font_path):
                try:
                    pdfmetrics.registerFont(TTFont('NanumGothic', assets_font_path))
                    font_name = 'NanumGothic'
                    print(f"✅ assets 폰트 로드 성공: NanumGothic")
                except Exception as font_error:
                    print(f"❌ assets 폰트 로드 실패: {font_error}")
                    # 폴백: 시스템 폰트 시도
                    pass
            else:
                print(f"❌ assets 폰트 파일을 찾을 수 없음: {assets_font_path}")
            
            # assets 폰트 실패 시 시스템 폰트 시도
            if font_name == 'Helvetica':
                # macOS 시스템 폰트 확인
                macos_fonts = [
                    "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # Apple SD Gothic Neo
                    "/System/Library/Fonts/Helvetica.ttc",  # Helvetica
                    "/Library/Fonts/Arial Unicode MS.ttf"  # Arial Unicode MS
                ]
                
                for font_path in macos_fonts:
                    if os.path.exists(font_path):
                        try:
                            if "AppleSDGothicNeo" in font_path:
                                pdfmetrics.registerFont(TTFont('AppleGothic', font_path))
                                font_name = 'AppleGothic'
                                print(f"✅ macOS 폰트 로드: AppleGothic")
                                break
                            elif "Arial" in font_path:
                                pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))
                                font_name = 'ArialUnicode'
                                print(f"✅ macOS 폰트 로드: ArialUnicode")
                                break
                        except:
                            continue
                
                # Windows 시스템 폰트 확인 (macOS에서 실패한 경우)
                if font_name == 'Helvetica':
                    windows_fonts = [
                        "C:/Windows/Fonts/malgun.ttf",  # 맑은 고딕
                        "C:/Windows/Fonts/gulim.ttc"    # 굴림
                    ]
                    
                    for font_path in windows_fonts:
                        if os.path.exists(font_path):
                            try:
                                if "malgun" in font_path:
                                    pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
                                    font_name = 'MalgunGothic'
                                    print(f"✅ Windows 폰트 로드: MalgunGothic")
                                    break
                                elif "gulim" in font_path:
                                    pdfmetrics.registerFont(TTFont('Gulim', font_path))
                                    font_name = 'Gulim'
                                    print(f"✅ Windows 폰트 로드: Gulim")
                                    break
                            except:
                                continue
                            
        except Exception as e:
            print(f"폰트 설정 중 오류: {e}")
            font_name = 'Helvetica'
        
        print(f"✅ 사용할 폰트: {font_name}")
        
        # PDF 생성
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        
        # 스타일 설정 (한글 폰트 적용)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # PDF 내용 구성
        story = []
        
        # 제목
        story.append(Paragraph("회의록 요약", title_style))
        story.append(Spacer(1, 20))
        
        # 회의 정보 (비밀번호 제외)
        story.append(Paragraph("회의 정보", heading_style))
        story.append(Paragraph(f"<b>회의명:</b> {meeting_data['name']}", normal_style))
        story.append(Paragraph(f"<b>날짜:</b> {meeting_data['date']}", normal_style))
        story.append(Spacer(1, 20))
        
        # 요약
        story.append(Paragraph("3줄 요약", heading_style))
        
        # 요약 내용을 줄별로 나누어 처리
        summary_lines = summary.split('\n')
        for line in summary_lines:
            if line.strip():
                story.append(Paragraph(line, normal_style))
                story.append(Spacer(1, 6))
        
        # TODO 항목 추가
        if meeting_data.get("todo_result") and isinstance(meeting_data["todo_result"], dict):
            todo_data = meeting_data["todo_result"].get("generated_todo", "")
            if todo_data:
                print(f"✅ TODO 데이터 발견: {len(todo_data)}자")
                story.append(Spacer(1, 20))
                story.append(Paragraph("할 일 목록 (TODO)", heading_style))
                
                # TODO 내용을 줄별로 나누어 처리
                todo_lines = todo_data.split('\n')
                for line in todo_lines:
                    if line.strip():
                        story.append(Paragraph(line, normal_style))
                        story.append(Spacer(1, 6))
            else:
                print("⚠️ TODO 데이터가 비어있음")
        else:
            print("⚠️ TODO 데이터 없음")
        
        # 회의 ID 제거 (세션 ID 불포함)
        
        print(f"✅ PDF 내용 구성 완료")
        
        # PDF 빌드
        doc.build(story)
        pdf_buffer.seek(0)
        
        # 파일명: 날짜와 회의 이름만 포함
        filename = safe_filename(f"{meeting_data['date']}_{meeting_data['name']}.pdf")
        print(f"✅ 파일명 생성: {filename}")
        
        response = send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
        # 브라우저 호환성을 위한 헤더 설정
        response.headers['Content-Disposition'] = create_content_disposition_header(filename)
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        print(f"✅ Content-Disposition 헤더: {response.headers['Content-Disposition']}")
        
        print(f"✅ PDF 다운로드 응답 준비 완료")
        return response
        
    except Exception as e:
        print(f"❌ PDF 다운로드 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"다운로드 중 오류가 발생했습니다: {str(e)}"}), 500