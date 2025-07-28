const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://your-backend-url.com';

// API 응답 타입 정의
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadResponse {
  meeting_id: string;
  password?: string;
  redirect_url: string;
}

export interface MeetingData {
  meeting_id: string;
  name: string;
  date: string;
  summary?: string;
  todos?: Array<{
    task: string;
    priority: string;
    category: string;
    assignee?: string;
    deadline?: string;
  }>;
  group_id?: string;
  sequence_number?: number;
  is_group_main?: boolean;
}

export interface MeetingHistory {
  group_id: string;
  group_name: string;
  current_meeting_id: string;
  total_meetings: number;
  meetings: Array<{
    meeting_id: string;
    name: string;
    date: string;
    summary?: string;
    todo_summary?: string[];
    todo_count?: number;
    sequence_number: number;
    created_at: string;
  }>;
}

export interface MeetingGroup {
  group_id: string;
  group_name: string;
  total_meetings: number;
  latest_date: string;
  meetings: Array<{
    meeting_id: string;
    name: string;
    date: string;
    created_at: string;
    sequence_number: number;
    is_group_main: boolean;
  }>;
}

export interface SidebarResponse {
  status: string;
  groups: MeetingGroup[];
}

// API 호출 헬퍼 함수
async function apiCall<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      credentials: 'include', // 세션 쿠키 포함
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || 'API 호출 실패',
      };
    }

    // 백엔드 응답 형태: {status: "success", data: {...}}
    return {
      success: true,
      data: data.data || data, // data.data가 있으면 추출, 없으면 그대로
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '네트워크 오류',
    };
  }
}

// 파일 업로드 API
export async function uploadMeeting(
  file: File,
  meetingName: string,
  date: string,
  passwordEnabled: boolean = false,
  password?: string
): Promise<ApiResponse<UploadResponse>> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('meeting_name', meetingName);
  formData.append('date', date);
  formData.append('password_enabled', passwordEnabled.toString());
  if (password && passwordEnabled) {
    formData.append('password', password);
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      credentials: 'include', // 세션 쿠키 포함
      body: formData,
    });

    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || '업로드 실패',
      };
    }

    // 백엔드 응답에서 실제 데이터 부분만 추출
    return {
      success: true,
      data: data.data, // data.data로 실제 meeting_id가 들어있는 부분 추출
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '네트워크 오류',
    };
  }
}

// 회의 데이터 조회 API
export async function getMeetingData(
  meetingId: string,
  password?: string
): Promise<ApiResponse<MeetingData>> {
  const params = new URLSearchParams({ meeting_id: meetingId });
  if (password) {
    params.append('password', password);
  }

  return apiCall<MeetingData>(`/api/meeting/${meetingId}?${params}`);
}

// 요약 생성 API
export async function generateSummary(
  meetingId: string
): Promise<ApiResponse<{ summary: string }>> {
  return apiCall<{ summary: string }>(`/api/summary`, {
    method: 'POST',
    body: JSON.stringify({ meeting_id: meetingId }),
  });
}

// TODO 추출 API
export async function extractTodos(
  meetingId: string
): Promise<ApiResponse<{ todos: Array<{ task: string; priority: string; category: string }> }>> {
  return apiCall<{ todos: Array<{ task: string; priority: string; category: string }> }>(`/api/todo`, {
    method: 'POST',
    body: JSON.stringify({ meeting_id: meetingId }),
  });
} 

// TODO 수정
export async function updateTodo(
  meetingId: string,
  todoIndex: number,
  updatedTodo: {
    task: string;
    assignee?: string;
    deadline?: string;
    priority?: string;
    category?: string;
  }
): Promise<ApiResponse<any>> {
  return apiCall(`/api/meeting/${meetingId}/todo/${todoIndex}`, {
    method: 'PUT',
    body: JSON.stringify(updatedTodo),
  });
}

// TODO 삭제
export async function deleteTodo(
  meetingId: string,
  todoIndex: number
): Promise<ApiResponse<any>> {
  return apiCall(`/api/meeting/${meetingId}/todo/${todoIndex}`, {
    method: 'DELETE',
  });
} 

// 파일명 추출 함수 개선
function extractFilenameFromContentDisposition(contentDisposition: string): string | null {
  if (!contentDisposition) return null;
  
  console.log('📋 Content-Disposition 헤더:', contentDisposition);
  
  // 1순위: filename*=UTF-8''인코딩된파일명 형식 시도
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match) {
    try {
      const decoded = decodeURIComponent(utf8Match[1]);
      console.log('✅ UTF-8 파일명 추출 성공:', decoded);
      return decoded;
    } catch (e) {
      console.warn('⚠️ UTF-8 파일명 디코딩 실패:', e);
    }
  }
  
  // 2순위: filename="파일명" 형식 시도
  const quotedMatch = contentDisposition.match(/filename="([^"]+)"/i);
  if (quotedMatch) {
    console.log('✅ 따옴표 파일명 추출 성공:', quotedMatch[1]);
    return quotedMatch[1];
  }
  
  // 3순위: filename=파일명 형식 시도
  const simpleMatch = contentDisposition.match(/filename=([^;]+)/i);
  if (simpleMatch) {
    const filename = simpleMatch[1].trim();
    console.log('✅ 단순 파일명 추출 성공:', filename);
    return filename;
  }
  
  console.warn('❌ 파일명 추출 실패');
  return null;
}

// PDF 파일 다운로드
export async function downloadPDF(meetingId: string): Promise<boolean> {
  try {
    console.log('📄 PDF 다운로드 요청 시작:', meetingId);
    
    const response = await fetch(`${API_BASE_URL}/api/download/pdf/${meetingId}`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      console.error('PDF 다운로드 실패:', response.statusText);
      return false;
    }

    // 파일명 추출
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `meeting_${meetingId}_summary.pdf`; // 기본값
    
    const extractedFilename = extractFilenameFromContentDisposition(contentDisposition || '');
    if (extractedFilename) {
      filename = extractedFilename;
    }

    // Blob으로 변환
    const blob = await response.blob();
    console.log('📦 PDF Blob 생성 완료, 크기:', blob.size);
    
    // 다운로드 실행
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    console.log('✅ PDF 다운로드 성공:', filename);
    return true;
  } catch (error) {
    console.error('❌ PDF 다운로드 중 오류:', error);
    return false;
  }
}

// TXT 파일 다운로드
export async function downloadTXT(meetingId: string): Promise<boolean> {
  try {
    console.log('📝 TXT 다운로드 요청 시작:', meetingId);
    
    const response = await fetch(`${API_BASE_URL}/api/download/txt/${meetingId}`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      console.error('TXT 다운로드 실패:', response.statusText);
      return false;
    }

    // 파일명 추출
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `meeting_${meetingId}_summary.txt`; // 기본값
    
    const extractedFilename = extractFilenameFromContentDisposition(contentDisposition || '');
    if (extractedFilename) {
      filename = extractedFilename;
    }

    // Blob으로 변환
    const blob = await response.blob();
    console.log('📦 TXT Blob 생성 완료, 크기:', blob.size);
    
    // 다운로드 실행
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    console.log('✅ TXT 다운로드 성공:', filename);
    return true;
  } catch (error) {
    console.error('❌ TXT 다운로드 중 오류:', error);
    return false;
  }
} 

// 추가 회의 업로드 API
export async function uploadAdditionalMeeting(
  file: File,
  meetingName: string,
  date: string,
  parentGroupId: string
): Promise<ApiResponse<UploadResponse>> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('meeting_name', meetingName);
  formData.append('date', date);
  formData.append('parent_group_id', parentGroupId);

  try {
    const response = await fetch(`${API_BASE_URL}/api/upload/additional`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || '추가 업로드 실패',
      };
    }

    return {
      success: true,
      data: data.data,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '네트워크 오류',
    };
  }
}

// 회의 그룹 히스토리 조회 API
export async function getMeetingHistory(
  meetingId: string
): Promise<ApiResponse<MeetingHistory>> {
  return apiCall<MeetingHistory>(`/api/meeting/${meetingId}/history`);
} 

// 사이드바용 회의 그룹 목록 조회 API
export async function getSidebarMeetings(): Promise<ApiResponse<SidebarResponse>> {
  return apiCall<SidebarResponse>(`/api/meetings`);
} 

// 회의 이름 수정 API
export async function updateMeetingName(
  meetingId: string,
  newName: string
): Promise<ApiResponse<{ meeting_id: string; old_name: string; new_name: string }>> {
  return apiCall(`/api/meeting/${meetingId}/name`, {
    method: 'PUT',
    body: JSON.stringify({ name: newName }),
  });
}

// 회의 삭제 API
export async function deleteMeeting(
  meetingId: string
): Promise<ApiResponse<{ deleted_meeting: { meeting_id: string; name: string; date: string } }>> {
  return apiCall(`/api/meeting/${meetingId}`, {
    method: 'DELETE',
  });
} 