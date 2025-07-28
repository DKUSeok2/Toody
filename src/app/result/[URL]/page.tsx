"use client";

import { useRouter, useParams } from "next/navigation";
import { useState, useEffect, useRef } from "react"; // useRef 추가
import Header from "../../components/Header";
import MeetingSummary from "../../components/MeetingSummary";
import TodoList, { TodoItem } from "../../components/TodoList";
import MeetingTranscript from "../../components/MeetingTranscript";
import DownloadButtons from "../../components/DownloadButtons";
import AdditionalUpload from "../../components/AdditionalUpload";
import { getMeetingData, generateSummary, extractTodos, downloadPDF, downloadTXT, getSidebarMeetings, MeetingGroup, updateMeetingName, deleteMeeting } from "../../lib/api";

interface PreviousResult {
  id: string;
  title: string;
  date: string;
}

interface MeetingData {
  meeting_id: string;
  name: string;
  date: string;
  summary?: string;
  todos?: Array<{
    task: string;
    priority: string;
    category: string;
    assignee?: string; // 추가
    deadline?: string; // 추가
  }>;
  transcript?: string;
}

export default function ResultPage() {
  const router = useRouter();
  const params = useParams();
  const meetingId = params.URL as string;

  // 🚫 중복 호출 방지를 위한 ref
  const isLoadingRef = useRef(false);

  const [previousResults, setPreviousResults] = useState<PreviousResult[]>([]);
  const [meetingData, setMeetingData] = useState<MeetingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingTodos, setLoadingTodos] = useState(false);

  // 비밀번호 입력 상태
  const [showPasswordInput, setShowPasswordInput] = useState(false);
  const [password, setPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");

  // 사이드바 관련 상태
  const [sidebarGroups, setSidebarGroups] = useState<MeetingGroup[]>([]);
  const [loadingSidebar, setLoadingSidebar] = useState(false);

  // 추가 업로드 모달 상태
  const [showAdditionalUpload, setShowAdditionalUpload] = useState(false);

  // 편집 관련 상태
  const [editingMeetingId, setEditingMeetingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");

  // 삭제 확인 모달 상태
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletingMeetingId, setDeletingMeetingId] = useState<string | null>(null);
  const [deletingMeetingName, setDeletingMeetingName] = useState("");

  // 사이드바 데이터 로드 함수 (useEffect보다 먼저 정의)
  const loadSidebarData = async () => {
    setLoadingSidebar(true);
    try {
      const result = await getSidebarMeetings();
      
      if (result.success && result.data) {
        setSidebarGroups(result.data.groups);
        console.log('✅ 사이드바 데이터 로드 성공:', result.data.groups);
      } else {
        console.warn('⚠️ 사이드바 로드 실패:', result.error);
      }
    } catch (error) {
      console.error('❌ 사이드바 로드 중 오류:', error);
    } finally {
      setLoadingSidebar(false);
    }
  };

  useEffect(() => {
    if (meetingId) {
      loadMeetingData();
    }
  }, [meetingId]);

  // 컴포넌트 마운트 시 사이드바 로드
  useEffect(() => {
    loadSidebarData();
  }, []);

  const loadMeetingData = async (inputPassword?: string) => {
    // 🚫 이미 로딩 중이면 중복 요청 방지
    if (isLoadingRef.current) {
      console.log("🚫 중복 API 호출 방지");
      return;
    }

    try {
      isLoadingRef.current = true; // 로딩 시작
      setLoading(true);
      setError(null);
      setPasswordError("");

      console.log("📡 API 호출 중...", meetingId);
      const response = await getMeetingData(meetingId, inputPassword);
      
      if (response.success && response.data) {
        setMeetingData(response.data);
        setShowPasswordInput(false);
        console.log("✅ API 호출 성공");
      } else {
        if (response.error?.includes("비밀번호") || response.error?.includes("password")) {
          setShowPasswordInput(true);
          setPasswordError(response.error);
        } else {
          setError(response.error || "회의 데이터를 불러올 수 없습니다.");
        }
      }
    } catch (error) {
      setError("네트워크 오류가 발생했습니다.");
      console.error("Load meeting data error:", error);
    } finally {
      setLoading(false);
      setTimeout(() => {
        isLoadingRef.current = false; // 로딩 완료 (약간의 지연으로 중복 호출 방지)
      }, 100);
    }
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password.trim()) {
      loadMeetingData(password);
    }
  };

  const handleGenerateSummary = async () => {
    if (!meetingData) return;
    
    try {
      setLoadingSummary(true);
      const response = await generateSummary(meetingData.meeting_id);
      
      if (response.success && response.data?.summary) {
        setMeetingData(prev => prev ? {
          ...prev,
          summary: response.data!.summary
        } : null);
      }
    } catch (error) {
      console.error("Summary generation error:", error);
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleExtractTodos = async () => {
    if (!meetingData) return;
    
    try {
      setLoadingTodos(true);
      const response = await extractTodos(meetingData.meeting_id);
      
      if (response.success && response.data?.todos) {
        setMeetingData(prev => prev ? {
          ...prev,
          todos: response.data!.todos
        } : null);
      }
    } catch (error) {
      console.error("Todo extraction error:", error);
    } finally {
      setLoadingTodos(false);
    }
  };

  const handleTodoUpdate = async () => {
    // todo 업데이트 후 최신 데이터 다시 로드
    if (meetingData?.meeting_id) {
      try {
        const response = await getMeetingData(meetingData.meeting_id);
        if (response.success && response.data) {
          setMeetingData(response.data);
        }
      } catch (error) {
        console.error("데이터 새로고침 오류:", error);
      }
    }
  };

  // 비밀번호 입력 화면
  if (showPasswordInput) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-center mb-6">비밀번호 입력</h2>
          <form onSubmit={handlePasswordSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                회의 접근 비밀번호
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="비밀번호를 입력하세요"
                required
              />
              {passwordError && (
                <p className="mt-2 text-sm text-red-600">{passwordError}</p>
              )}
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
              disabled={loading}
            >
              {loading ? "확인 중..." : "확인"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // 로딩 화면
  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">회의 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 화면
  if (error) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  if (!meetingData) {
    return null;
  }

  // TodoItem 형식으로 변환
  const todoItems: TodoItem[] = meetingData.todos?.map((todo, index) => ({
    id: (index + 1).toString(),
    assignee: todo.assignee || "담당자 미지정", // 백엔드에서 추출된 담당자 사용
    actionItem: todo.task,
    deadline: todo.deadline || "", // 백엔드에서 추출된 기한 사용
    priority: todo.priority,
    category: todo.category,
  })) || [];

  const summaryItems = meetingData.summary 
    ? meetingData.summary.split('\n').filter(item => item.trim()) 
    : [];

  const handleDownloadPDF = async () => {
    if (!meetingData?.meeting_id) {
      alert("회의 데이터를 찾을 수 없습니다.");
      return;
    }

    try {
      console.log("📄 PDF 다운로드 시작...");
      const success = await downloadPDF(meetingData.meeting_id);
      
      if (!success) {
        alert("PDF 다운로드에 실패했습니다. 다시 시도해주세요.");
      }
    } catch (error) {
      console.error("PDF 다운로드 오류:", error);
      alert("PDF 다운로드 중 오류가 발생했습니다.");
    }
  };

  const handleDownloadTXT = async () => {
    if (!meetingData?.meeting_id) {
      alert("회의 데이터를 찾을 수 없습니다.");
      return;
    }

    try {
      console.log("📝 TXT 다운로드 시작...");
      const success = await downloadTXT(meetingData.meeting_id);
      
      if (!success) {
        alert("TXT 다운로드에 실패했습니다. 다시 시도해주세요.");
      }
    } catch (error) {
      console.error("TXT 다운로드 오류:", error);
      alert("TXT 다운로드 중 오류가 발생했습니다.");
    }
  };



  // 히스토리에서 다른 회의로 이동
  const handleMeetingClick = (targetMeetingId: string) => {
    if (targetMeetingId !== meetingId) {
      router.push(`/result/${targetMeetingId}`);
    }
  };

  // 추가 업로드 성공 처리
  const handleAdditionalUploadSuccess = async (newMeetingId: string) => {
    console.log("🎉 추가 업로드 성공, 새 회의 ID:", newMeetingId);
    
    // 사이드바 다시 로드 (새로운 회의가 추가되었으므로)
    await loadSidebarData();
    
    // 성공 메시지 표시 (선택사항)
    alert("추가 회의록이 성공적으로 업로드되었습니다!");
  };

  const handleNewMeeting = () => {
    router.push("/");
  };

  const handleLogoClick = () => {
    router.push("/");
  };

  const handleShare = () => {
    // 공유용 URL 생성 (creator 파라미터 제거)
    const shareUrl = window.location.origin + window.location.pathname;
    
    navigator.clipboard
      .writeText(shareUrl)
      .then(() => {
        alert("공유 링크가 클립보드에 복사되었습니다!");
      })
      .catch(() => {
        alert("링크 복사에 실패했습니다.");
      });
  };

  // 회의 이름 편집 시작
  const handleStartEdit = (meetingId: string, currentName: string) => {
    setEditingMeetingId(meetingId);
    setEditingName(currentName);
  };

  // 회의 이름 편집 취소
  const handleCancelEdit = () => {
    setEditingMeetingId(null);
    setEditingName("");
  };

  // 회의 이름 저장
  const handleSaveEdit = async () => {
    if (!editingMeetingId || !editingName.trim()) return;

    try {
      const response = await updateMeetingName(editingMeetingId, editingName.trim());
      
      if (response.success) {
        // 사이드바 데이터 새로고침
        await loadSidebarData();
        
        // 현재 회의가 편집된 회의라면 meetingData도 업데이트
        if (editingMeetingId === meetingId && meetingData) {
          setMeetingData({
            ...meetingData,
            name: editingName.trim()
          });
        }
        
        alert("회의 이름이 성공적으로 수정되었습니다!");
      } else {
        alert(response.error || "회의 이름 수정에 실패했습니다.");
      }
    } catch (error) {
      console.error("회의 이름 수정 오류:", error);
      alert("회의 이름 수정 중 오류가 발생했습니다.");
    } finally {
      setEditingMeetingId(null);
      setEditingName("");
    }
  };

  // 삭제 확인 모달 열기
  const handleStartDelete = (meetingId: string, meetingName: string) => {
    setDeletingMeetingId(meetingId);
    setDeletingMeetingName(meetingName);
    setShowDeleteConfirm(true);
  };

  // 삭제 확인 모달 닫기
  const handleCancelDelete = () => {
    setDeletingMeetingId(null);
    setDeletingMeetingName("");
    setShowDeleteConfirm(false);
  };

  // 회의 삭제 실행
  const handleConfirmDelete = async () => {
    if (!deletingMeetingId) return;

    try {
      const response = await deleteMeeting(deletingMeetingId);
      
      if (response.success) {
        // 삭제된 회의가 현재 보고 있는 회의라면 홈으로 이동
        if (deletingMeetingId === meetingId) {
          alert("회의가 삭제되었습니다. 홈페이지로 이동합니다.");
          router.push("/");
          return;
        }
        
        // 사이드바 데이터 새로고침
        await loadSidebarData();
        alert("회의가 성공적으로 삭제되었습니다!");
      } else {
        alert(response.error || "회의 삭제에 실패했습니다.");
      }
    } catch (error) {
      console.error("회의 삭제 오류:", error);
      alert("회의 삭제 중 오류가 발생했습니다.");
    } finally {
      handleCancelDelete();
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* 헤더 */}
      <Header
        onLogoClick={handleLogoClick}
        onNewMeeting={handleNewMeeting}
        onShare={handleShare}
      />

      <div className="flex">
        {/* 사이드바 */}
        <div className="w-60 bg-gray-50 min-h-screen p-4">
                      <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                이전 기록
              </h3>
              <div className="space-y-3">
                {sidebarGroups.map((group) => (
                  <div key={group.group_id} className="space-y-1">
                    {/* 그룹 헤더 */}
                    <div className="text-xs font-medium text-gray-500 px-2">
                      {group.group_name} 
                      {group.total_meetings > 1 && (
                        <span className="ml-1">({group.total_meetings}차)</span>
                      )}
                    </div>
                    
                    {/* 그룹 내 회의들 */}
                    {group.meetings.map((meeting) => (
                      <div
                        key={meeting.meeting_id}
                        className={`relative group p-2 rounded text-sm ml-2 ${
                          meeting.meeting_id === meetingId 
                            ? 'bg-blue-100 border border-blue-300' 
                            : 'hover:bg-gray-200'
                        }`}
                      >
                        {editingMeetingId === meeting.meeting_id ? (
                          // 편집 모드
                          <div className="space-y-2">
                            <input
                              type="text"
                              value={editingName}
                              onChange={(e) => setEditingName(e.target.value)}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleSaveEdit();
                                } else if (e.key === 'Escape') {
                                  handleCancelEdit();
                                }
                              }}
                              autoFocus
                            />
                            <div className="flex gap-1">
                              <button
                                onClick={handleSaveEdit}
                                className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                              >
                                저장
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
                              >
                                취소
                              </button>
                            </div>
                          </div>
                        ) : (
                          // 일반 모드
                          <>
                            <div
                              className="cursor-pointer"
                              onClick={() => handleMeetingClick(meeting.meeting_id)}
                            >
                              <div className="font-medium text-gray-800">
                                {group.total_meetings > 1 
                                  ? `${meeting.sequence_number}차: ${meeting.name}`
                                  : meeting.name
                                }
                              </div>
                              <div className="text-xs text-gray-500">
                                {meeting.date}
                              </div>
                            </div>
                            
                            {/* 편집/삭제 버튼 (호버 시에만 표시) */}
                            <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStartEdit(meeting.meeting_id, meeting.name);
                                }}
                                className="p-1 text-gray-400 hover:text-blue-500 hover:bg-white rounded"
                                title="이름 수정"
                              >
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStartDelete(meeting.meeting_id, meeting.name);
                                }}
                                className="p-1 text-gray-400 hover:text-red-500 hover:bg-white rounded"
                                title="회의 삭제"
                              >
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
                
                {sidebarGroups.length === 0 && !loadingSidebar && (
                  <div className="text-xs text-gray-500 px-2">
                    아직 회의 기록이 없습니다.
                  </div>
                )}
                
                {loadingSidebar && (
                  <div className="text-xs text-gray-500 px-2">
                    로딩 중...
                  </div>
                )}
              </div>
            </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="flex-1 p-8">
          <div className="max-w-4xl mx-auto">
            {/* 페이지 헤더 */}
            <div className="flex justify-between items-start mb-8">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 mb-2">
                  {meetingData.name}
                </h1>
                <p className="text-gray-600">{meetingData.date}</p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowAdditionalUpload(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  추가 회의록
                </button>
                <DownloadButtons
                  onDownloadPDF={handleDownloadPDF}
                  onDownloadTXT={handleDownloadTXT}
                />
              </div>
            </div>



            <div className="space-y-8">
              {/* 회의록 요약 */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">회의록 요약</h2>
                  {!meetingData.summary && (
                    <button
                      onClick={handleGenerateSummary}
                      disabled={loadingSummary}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                      {loadingSummary ? "생성 중..." : "요약 생성"}
                    </button>
                  )}
                </div>
                {meetingData.summary ? (
                  <MeetingSummary summaryItems={summaryItems} />
                ) : (
                  <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-600">
                    요약을 생성하려면 "요약 생성" 버튼을 클릭하세요.
                  </div>
                )}
              </div>

              {/* 투두리스트 */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">할 일 목록</h2>
                  {(!meetingData.todos || meetingData.todos.length === 0) && (
                    <button
                      onClick={handleExtractTodos}
                      disabled={loadingTodos}
                      className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
                    >
                      {loadingTodos ? "추출 중..." : "할 일 추출"}
                    </button>
                  )}
                </div>
                {meetingData.todos && meetingData.todos.length > 0 ? (
                  <TodoList 
                    todoItems={todoItems} 
                    meetingId={meetingData.meeting_id}
                    onTodoUpdate={handleTodoUpdate}
                  />
                ) : (
                  <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-600">
                    할 일을 추출하려면 "할 일 추출" 버튼을 클릭하세요.
                  </div>
                )}
              </div>

              {/* 회의 전문 토글 */}
              {meetingData?.transcript && (
                <MeetingTranscript transcript={meetingData.transcript} />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 추가 업로드 모달 */}
      {meetingData && (
        <AdditionalUpload
          isOpen={showAdditionalUpload}
          onClose={() => setShowAdditionalUpload(false)}
          parentGroupId={meetingData.meeting_id}
          onUploadSuccess={handleAdditionalUploadSuccess}
        />
      )}

      {/* 삭제 확인 모달 */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              회의 삭제 확인
            </h3>
            <p className="text-gray-600 mb-6">
              <span className="font-medium">"{deletingMeetingName}"</span> 회의를 삭제하시겠습니까?
              <br />
              <span className="text-sm text-red-500">
                이 작업은 되돌릴 수 없으며, 회의 파일과 모든 데이터가 영구적으로 삭제됩니다.
              </span>
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={handleCancelDelete}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleConfirmDelete}
                className="px-4 py-2 text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
