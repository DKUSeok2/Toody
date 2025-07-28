"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { uploadMeeting } from "../lib/api";

interface MeetingInfo {
  name: string;
  date: string;
  usePassword: boolean;
  password: string;
}

interface MeetingInfoFormProps {
  onSubmit?: (meetingInfo: MeetingInfo) => void;
  uploadedFile?: File | null;
}

export default function MeetingInfoForm({ onSubmit, uploadedFile }: MeetingInfoFormProps) {
  const router = useRouter();
  const [meetingInfo, setMeetingInfo] = useState<MeetingInfo>({
    name: "",
    date: "",
    usePassword: false,
    password: "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  // 복사 함수
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(meetingInfo.password);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error("복사 실패:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!uploadedFile) {
      setError("업로드된 파일이 없습니다.");
      return;
    }

    if (!meetingInfo.name.trim()) {
      setError("회의명을 입력해주세요.");
      return;
    }

    if (!meetingInfo.date) {
      setError("날짜를 선택해주세요.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await uploadMeeting(
        uploadedFile,
        meetingInfo.name,
        meetingInfo.date,
        meetingInfo.usePassword,
        meetingInfo.usePassword ? meetingInfo.password : undefined
      );

      if (response.success && response.data) {
        // 업로드 성공시 결과 페이지로 이동 (생성자 플래그 포함)
        const meetingId = response.data!.meeting_id;
        router.push(`/result/${meetingId}?creator=true`);
      } else {
        setError(response.error || "업로드에 실패했습니다.");
      }
    } catch (error) {
      setError("네트워크 오류가 발생했습니다.");
      console.error("Upload error:", error);
    } finally {
      setIsSubmitting(false);
    }

    // 기존 onSubmit 콜백도 호출
    onSubmit?.(meetingInfo);
  };

  const handleInputChange = (field: string, value: string) => {
    setMeetingInfo((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePasswordToggle = (checked: boolean) => {
    setMeetingInfo((prev) => ({
      ...prev,
      usePassword: checked,
      password: checked ? Math.random().toString(36).slice(-8) : "", // 즉시 비밀번호 생성
    }));
  };

  return (
    <div className="w-full max-w-md mx-auto bg-white p-8 rounded-2xl border border-gray-200 shadow-sm">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
        회의 정보 입력
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            회의명
          </label>
          <input
            type="text"
            value={meetingInfo.name}
            onChange={(e) => handleInputChange("name", e.target.value)}
            placeholder="회의명을 입력하세요"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isSubmitting}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            날짜
          </label>
          <input
            type="date"
            value={meetingInfo.date}
            onChange={(e) => handleInputChange("date", e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isSubmitting}
            required
          />
        </div>

        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="usePassword"
              checked={meetingInfo.usePassword}
              onChange={(e) => handlePasswordToggle(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={isSubmitting}
            />
            <label
              htmlFor="usePassword"
              className="ml-2 block text-sm text-gray-700"
            >
              비밀번호 설정
            </label>
          </div>

          {meetingInfo.usePassword && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                생성된 비밀번호
              </label>
              <div className="flex">
                <input
                  type="text"
                  value={meetingInfo.password}
                  readOnly
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-l-lg bg-gray-50 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className={`px-4 py-3 border border-l-0 border-gray-300 rounded-r-lg transition-colors ${
                    copySuccess
                      ? "bg-green-500 text-white"
                      : "bg-gray-50 text-gray-700 hover:bg-gray-100"
                  }`}
                  disabled={isSubmitting}
                >
                  {copySuccess ? "복사됨!" : "복사"}
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                이 비밀번호로 결과를 확인할 수 있습니다.
              </p>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            isSubmitting
              ? "bg-gray-400 text-white cursor-not-allowed"
              : "bg-black text-white hover:bg-gray-800"
          }`}
        >
          {isSubmitting ? "업로드 중..." : "분석 시작"}
        </button>
      </form>
    </div>
  );
}
