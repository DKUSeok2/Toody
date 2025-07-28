import { useState } from "react";
import { ChevronDownIcon } from "@heroicons/react/24/outline";

interface DownloadButtonsProps {
  onDownloadPDF: () => void;
  onDownloadTXT: () => void;
}

export default function DownloadButtons({
  onDownloadPDF,
  onDownloadTXT,
}: DownloadButtonsProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-center gap-2.5 px-9 py-5 bg-[#191A23] hover:bg-[#2a2b36] text-white rounded-lg font-medium transition-colors min-w-[100px] h-[48px]"
      >
        파일 다운로드
        <ChevronDownIcon
          className={`h-4 w-4 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[150px]">
          <button
            onClick={() => {
              onDownloadPDF();
              setIsOpen(false);
            }}
            className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-t-lg transition-colors"
          >
            pdf 파일로 다운받기
          </button>
          <button
            onClick={() => {
              onDownloadTXT();
              setIsOpen(false);
            }}
            className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-b-lg transition-colors border-t border-gray-100"
          >
            txt 파일로 다운받기
          </button>
        </div>
      )}
    </div>
  );
}
