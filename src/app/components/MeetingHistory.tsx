import { useState } from "react";
import { ChevronRightIcon, CalendarIcon, DocumentTextIcon, CheckIcon } from "@heroicons/react/24/outline";

interface MeetingHistoryItem {
  meeting_id: string;
  name: string;
  date: string;
  summary?: string;
  todo_summary?: string[];
  todo_count?: number;
  sequence_number: number;
  created_at: string;
}

interface MeetingHistoryProps {
  groupName: string;
  currentMeetingId: string;
  totalMeetings: number;
  meetings: MeetingHistoryItem[];
  onMeetingClick: (meetingId: string) => void;
}

export default function MeetingHistory({
  groupName,
  currentMeetingId,
  totalMeetings,
  meetings,
  onMeetingClick,
}: MeetingHistoryProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (totalMeetings <= 1) {
    return null; // 단일 회의면 히스토리 표시 안함
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg p-6 mb-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {groupName} - 회의 히스토리
          </h3>
          <p className="text-sm text-gray-600">
            총 {totalMeetings}개의 회의가 진행되었습니다
          </p>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-white rounded-md transition-colors"
        >
          {isExpanded ? '접기' : '전체 보기'}
          <ChevronRightIcon
            className={`h-4 w-4 transition-transform ${
              isExpanded ? 'rotate-90' : ''
            }`}
          />
        </button>
      </div>

      {/* 요약 보기 */}
      {!isExpanded && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {meetings.slice(0, 3).map((meeting, index) => (
            <div
              key={meeting.meeting_id}
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                meeting.meeting_id === currentMeetingId
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
              onClick={() => onMeetingClick(meeting.meeting_id)}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-medium text-gray-500">
                  {index + 1}차 회의
                </span>
                {meeting.meeting_id === currentMeetingId && (
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    현재
                  </span>
                )}
              </div>
              <h4 className="font-medium text-gray-900 mb-1">{meeting.name}</h4>
              <p className="text-sm text-gray-600 flex items-center gap-1">
                <CalendarIcon className="h-3 w-3" />
                {meeting.date}
              </p>
              {meeting.todo_count && (
                <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                  <CheckIcon className="h-3 w-3" />
                  {meeting.todo_count}개 할 일
                </p>
              )}
            </div>
          ))}
          {meetings.length > 3 && (
            <div className="p-4 rounded-lg border border-dashed border-gray-300 flex items-center justify-center text-gray-500">
              <span className="text-sm">+{meetings.length - 3}개 더 보기</span>
            </div>
          )}
        </div>
      )}

      {/* 전체 보기 */}
      {isExpanded && (
        <div className="space-y-4">
          {meetings.map((meeting, index) => (
            <div
              key={meeting.meeting_id}
              className={`p-6 rounded-lg border cursor-pointer transition-all ${
                meeting.meeting_id === currentMeetingId
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
              onClick={() => onMeetingClick(meeting.meeting_id)}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium text-gray-600">
                    {index + 1}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">{meeting.name}</h4>
                    <p className="text-sm text-gray-600 flex items-center gap-1">
                      <CalendarIcon className="h-3 w-3" />
                      {meeting.date}
                    </p>
                  </div>
                </div>
                {meeting.meeting_id === currentMeetingId && (
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                    현재 회의
                  </span>
                )}
              </div>

              {meeting.summary && (
                <div className="mb-3">
                  <p className="text-sm text-gray-700 line-clamp-2">
                    {meeting.summary.split('\n')[0]}
                  </p>
                </div>
              )}

              {meeting.todo_summary && meeting.todo_summary.length > 0 && (
                <div className="space-y-1">
                  <h5 className="text-xs font-medium text-gray-500 flex items-center gap-1">
                    <CheckIcon className="h-3 w-3" />
                    주요 할 일
                  </h5>
                  <ul className="text-xs text-gray-600 space-y-1">
                    {meeting.todo_summary.slice(0, 2).map((todo, idx) => (
                      <li key={idx} className="flex items-start gap-1">
                        <span className="text-gray-400">•</span>
                        <span className="line-clamp-1">{todo}</span>
                      </li>
                    ))}
                    {meeting.todo_count && meeting.todo_count > 2 && (
                      <li className="text-gray-400">
                        +{meeting.todo_count - 2}개 더
                      </li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 