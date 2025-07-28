"use client";

import { useState } from "react";

interface MeetingInfo {
  name: string;
  date: string;
  usePassword: boolean;
  password: string;
}

interface MeetingInfoFormProps {
  onSubmit?: (meetingInfo: MeetingInfo) => void;
}

export default function MeetingInfoForm({ onSubmit }: MeetingInfoFormProps) {
  const [meetingInfo, setMeetingInfo] = useState<MeetingInfo>({
    name: "",
    date: "",
    usePassword: false,
    password: "",
  });

  // 복사 성공 상태를 위한 state 추가
  const [copySuccess, setCopySuccess] = useState(false);

  // 복사 함수
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(meetingInfo.password);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000); // 2초 후 상태 초기화
    } catch (err) {
      console.error("복사 실패:", err);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(meetingInfo);
  };

  const handleInputChange = (
    field: keyof MeetingInfo,
    value: string | boolean
  ) => {
    setMeetingInfo((prev) => {
      if (field === "usePassword") {
        if (value) {
          // 임시 비밀번호 설정 (추후 API 호출로 변경 예정)
          const tempPassword = "temp1234";
          return {
            ...prev,
            usePassword: true,
            password: tempPassword,
          };
        } else {
          // 비밀번호 사용 안 할 경우 비밀번호 초기화
          return {
            ...prev,
            usePassword: false,
            password: "",
          };
        }
      }
      return {
        ...prev,
        [field]: value,
      };
    });
  };

  return (
    <div className="w-full max-w-lg mx-auto">
      <h3 className="text-xl font-semibold mb-8 text-gray-800 text-left">
        회의 정보를 입력해주세요
      </h3>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 회의 이름 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            회의 이름
          </label>
          <input
            type="text"
            value={meetingInfo.name}
            onChange={(e) => handleInputChange("name", e.target.value)}
            placeholder="회의 이름을 입력해주세요"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#667AFF] focus:border-transparent"
            required
          />
        </div>

        {/* 회의 날짜 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            회의 날짜
          </label>
          <input
            type="date"
            value={meetingInfo.date}
            onChange={(e) => handleInputChange("date", e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#667AFF] focus:border-transparent"
            required
          />
        </div>

        {/* 비밀번호 사용 여부 */}
        <div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={meetingInfo.usePassword}
              onChange={(e) =>
                handleInputChange("usePassword", e.target.checked)
              }
              className="w-5 h-5 text-[#667AFF] border-gray-300 rounded focus:ring-[#667AFF] focus:ring-2"
            />
            <span className="text-sm font-medium text-gray-700">
              비밀번호 사용 (결과 페이지 접근 시 필요)
            </span>
          </label>
        </div>

        {/* 생성된 비밀번호 표시 (조건부 렌더링) */}
        {meetingInfo.usePassword && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              아래 생성된 비밀번호를 복사해주세요
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={meetingInfo.password}
                readOnly
                className="flex-1 px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-gray-700"
                placeholder="비밀번호가 생성됩니다"
              />
              <button
                type="button"
                onClick={copyToClipboard}
                className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                  copySuccess
                    ? "bg-green-500 text-white"
                    : "bg-[#667AFF] hover:bg-[#5A6BFF] text-white"
                }`}
              >
                {copySuccess ? "복사됨!" : "복사"}
              </button>
            </div>
          </div>
        )}

        {/* 제출 버튼 */}
        <button
          type="submit"
          className="w-full bg-black text-white py-3 rounded-lg hover:bg-[#667AFF] transition-colors font-medium"
        >
          할 일 목록 생성하기
        </button>
      </form>
    </div>
  );
}
