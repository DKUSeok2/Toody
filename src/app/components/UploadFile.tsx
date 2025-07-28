"use client";

import { useState, useRef } from "react";
import Image from "next/image";

interface UploadedFile {
  name: string;
  size: number;
  id: string;
}

interface UploadFileProps {
  onFileUpload?: (file: UploadedFile | null) => void;
}

export default function UploadFile({ onFileUpload }: UploadFileProps) {
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentUploadingFile, setCurrentUploadingFile] = useState<File | null>(
    null
  );
  const fileAddedRef = useRef(false);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const generateUniqueId = () => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setCurrentUploadingFile(file);
    fileAddedRef.current = false;

    // 업로드 진행 상황 시뮬레이션
    const uploadInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(uploadInterval);
          setIsUploading(false);
          setCurrentUploadingFile(null);

          // 파일이 아직 추가되지 않았을 때만 추가
          if (!fileAddedRef.current) {
            fileAddedRef.current = true;
            const newFile: UploadedFile = {
              name: file.name,
              size: file.size,
              id: generateUniqueId(),
            };

            setUploadedFile(newFile);

            setTimeout(() => {
              onFileUpload?.(newFile);
            }, 0);

            setUploadProgress(0);
            return 100;
          }

          setUploadProgress(0);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const handleFileDelete = () => {
    setUploadedFile(null);

    setTimeout(() => {
      onFileUpload?.(null);
    }, 0);
  };

  return (
    <div className="w-full">
      <div className="flex flex-col items-start">
        <input
          type="file"
          id="fileInput"
          className="hidden"
          accept=".pdf,.doc,.docx,.txt,.rtf,.odt,.pages,.hwp"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              handleFileUpload(file);
            }
          }}
        />
        {/* 업로드 버튼 - 업로드 중이거나 파일이 있을 때 숨김 */}
        <div className="w-full max-w-md flex flex-col items-start">
          {!isUploading && uploadedFile === null && (
            <button
              onClick={() => {
                document.getElementById("fileInput")?.click();
              }}
              className="bg-black text-white px-8 py-4 rounded-lg hover:bg-[#667AFF] transition-colors flex items-center gap-2 text-lg font-medium"
            >
              <Image src="/upload.png" alt="upload" width={20} height={20} />
              회의록 업로드
            </button>
          )}

          {/* 업로드 진행 상황 */}
          {isUploading && currentUploadingFile && (
            <div className="w-full">
              <div className="bg-black rounded-lg p-4 text-white">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-[#667AFF] rounded flex items-center justify-center">
                    <span className="text-white text-sm">📄</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm truncate">
                      {currentUploadingFile.name}
                    </div>
                    <div className="mt-1">
                      <div className="w-full bg-gray-600 rounded-full h-2">
                        <div
                          className="bg-white h-2 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-300">{uploadProgress}%</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 파일 업로드 완료 후 */}
      {uploadedFile !== null && (
        <div className="flex flex-row items-start w-full">
          {/* 업로드된 파일 목록 */}
          <div className="flex-shrink-0">
            <div className="w-full max-w-md space-y-2">
              <div
                key={uploadedFile.id}
                className="bg-black rounded-lg p-4 text-white"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-[#667AFF] rounded flex items-center justify-center">
                    <span className="text-white text-sm">📄</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm truncate">{uploadedFile.name}</div>
                    <div className="text-xs text-gray-300">
                      {formatFileSize(uploadedFile.size)}
                    </div>
                  </div>
                  <button
                    onClick={handleFileDelete}
                    className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center hover:bg-gray-500 transition-colors"
                  >
                    <span className="text-white text-xs">✕</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
