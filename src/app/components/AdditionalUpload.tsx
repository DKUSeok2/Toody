import { useState } from "react";
import { XMarkIcon, DocumentArrowUpIcon } from "@heroicons/react/24/outline";
import { uploadAdditionalMeeting } from "../lib/api";

interface AdditionalUploadProps {
  isOpen: boolean;
  onClose: () => void;
  parentGroupId: string;
  onUploadSuccess: (meetingId: string) => void;
}

export default function AdditionalUpload({
  isOpen,
  onClose,
  parentGroupId,
  onUploadSuccess,
}: AdditionalUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [meetingName, setMeetingName] = useState("");
  const [meetingDate, setMeetingDate] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile) {
      setError("파일을 선택해주세요.");
      return;
    }

    if (!meetingName.trim()) {
      setError("회의명을 입력해주세요.");
      return;
    }

    if (!meetingDate) {
      setError("회의 날짜를 선택해주세요.");
      return;
    }

    setIsUploading(true);
    setError("");

    try {
      console.log("🔄 추가 회의록 업로드 시작:", {
        file: selectedFile.name,
        meetingName,
        meetingDate,
        parentGroupId
      });

      const result = await uploadAdditionalMeeting(
        selectedFile,
        meetingName,
        meetingDate,
        parentGroupId
      );

      if (result.success && result.data) {
        console.log("✅ 추가 업로드 성공:", result.data);
        
        // 성공 시 모달 닫고 페이지 새로고침을 위해 새 meeting_id 전달
        onUploadSuccess(result.data.meeting_id);
        
        // 폼 초기화
        setSelectedFile(null);
        setMeetingName("");
        setMeetingDate("");
        onClose();
      } else {
        setError(result.error || "업로드에 실패했습니다.");
      }
    } catch (error) {
      console.error("❌ 추가 업로드 중 오류:", error);
      setError("업로드 중 오류가 발생했습니다.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    if (!isUploading) {
      setSelectedFile(null);
      setMeetingName("");
      setMeetingDate("");
      setError("");
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            추가 회의록 업로드
          </h3>
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* 파일 업로드 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              회의록 파일 *
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
              <input
                type="file"
                accept=".pdf,.txt,.doc,.docx"
                onChange={handleFileChange}
                disabled={isUploading}
                className="hidden"
                id="additional-file-upload"
              />
              <label
                htmlFor="additional-file-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                <DocumentArrowUpIcon className="h-8 w-8 text-gray-400 mb-2" />
                {selectedFile ? (
                  <div className="text-sm">
                    <p className="font-medium text-gray-900">{selectedFile.name}</p>
                    <p className="text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div className="text-sm text-gray-600">
                    <p className="font-medium">파일을 선택하거나 드래그하세요</p>
                    <p>PDF, TXT, DOC, DOCX 파일 지원</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          {/* 회의명 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              회의명 *
            </label>
            <input
              type="text"
              value={meetingName}
              onChange={(e) => setMeetingName(e.target.value)}
              disabled={isUploading}
              placeholder="예: 2차 마케팅 전략 회의"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
          </div>

          {/* 회의 날짜 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              회의 날짜 *
            </label>
            <input
              type="date"
              value={meetingDate}
              onChange={(e) => setMeetingDate(e.target.value)}
              disabled={isUploading}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* 버튼들 */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={isUploading}
              className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isUploading || !selectedFile || !meetingName.trim() || !meetingDate}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isUploading ? "업로드 중..." : "업로드"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 