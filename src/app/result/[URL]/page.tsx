"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import Header from "../../components/Header";
import MeetingSummary from "../../components/MeetingSummary";
import TodoList, { TodoItem } from "../../components/TodoList";
import MeetingTranscript from "../../components/MeetingTranscript";
import DownloadButtons from "../../components/DownloadButtons";

interface PreviousResult {
  id: string;
  title: string;
  date: string;
}

export default function ResultPage() {
  const router = useRouter();
  const [previousResults, setPreviousResults] = useState<PreviousResult[]>([]);

  // 샘플 데이터 - 실제로는 API에서 가져올 데이터
  const todoItems: TodoItem[] = [
    {
      id: "1",
      assignee: "김민수",
      actionItem: "마케팅 계획서 초안 작성",
      deadline: "2025-03-12",
      completed: true,
    },
    {
      id: "2",
      assignee: "김민수",
      actionItem: "마케팅 계획서 초안 작성",
      deadline: "2025-03-12",
    },
    {
      id: "3",
      assignee: "김민수",
      actionItem: "마케팅 계획서 초안 작성",
      deadline: "2025-03-12",
    },
    {
      id: "4",
      assignee: "김민수",
      actionItem: "마케팅 계획서 초안 작성",
      deadline: "2025-03-12",
    },
    {
      id: "5",
      assignee: "김민수",
      actionItem: "마케팅 계획서 초안 작성",
      deadline: "2025-03-12",
    },
  ];

  const meetingSummary = ["3줄 요약", "3줄 요약", "3줄 요약"];

  const meetingTranscript = `
    안녕하세요, 오늘 회의를 시작하겠습니다.

    김민수: 안녕하세요. 오늘은 Q1 마케팅 전략에 대해 논의해보겠습니다.

    박지영: 네, 먼저 현재 진행 중인 프로젝트 현황부터 공유드리겠습니다. UI/UX 디자인 작업이 80% 정도 완료되었고...

    이준호: 개발 측면에서는 일정이 다소 타이트한 상황입니다. 마케팅 일정과 맞추려면 추가 리소스가 필요할 것 같습니다.

    김민수: 그렇다면 예산 재배정을 고려해보겠습니다. 우선순위를 다시 정리해서...

    [회의 내용이 계속됩니다...]
  `;

  useEffect(() => {
    // 이전 결과 샘플 데이터
    setPreviousResults([
      { id: "1", title: "0325 회의", date: "2025년 3월 25일" },
      { id: "2", title: "0326 회의", date: "2025년 3월 26일" },
    ]);
  }, []);

  const handleDownloadPDF = () => {
    console.log("PDF 다운로드");
  };

  const handleDownloadTXT = () => {
    console.log("TXT 다운로드");
  };

  const handleNewMeeting = () => {
    router.push("/");
  };

  const handleLogoClick = () => {
    router.push("/");
  };

  const handleShare = () => {
    // API에서 받아온 shared url로 수정 필요 (현재는 현재 페이지 링크로 복사됨)
    navigator.clipboard
      .writeText(window.location.href)
      .then(() => {
        alert("링크가 클립보드에 복사되었습니다!");
      })
      .catch(() => {
        alert("링크 복사에 실패했습니다.");
      });
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
            <div className="space-y-1">
              {previousResults.map((result) => (
                <div
                  key={result.id}
                  className="p-2 rounded cursor-pointer hover:bg-gray-200 text-sm"
                  onClick={() => router.push(`/result/${result.id}`)}
                >
                  <div className="font-medium text-gray-800">
                    {result.title}
                  </div>
                </div>
              ))}
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
                  회의 이름
                </h1>
                <p className="text-gray-600">2025년 2월 27일</p>
              </div>
              <DownloadButtons
                onDownloadPDF={handleDownloadPDF}
                onDownloadTXT={handleDownloadTXT}
              />
            </div>

            <div className="space-y-8">
              {/* 회의록 요약 */}
              <MeetingSummary summaryItems={meetingSummary} />

              {/* 투두리스트 */}
              <TodoList todoItems={todoItems} />

              {/* 회의 전문 토글 */}
              <MeetingTranscript transcript={meetingTranscript} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
