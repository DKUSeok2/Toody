import { useState } from "react";
import { ChevronDownIcon } from "@heroicons/react/24/outline";

interface MeetingTranscriptProps {
  transcript: string;
}

export default function MeetingTranscript({
  transcript,
}: MeetingTranscriptProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-white rounded-lg border border-gray-300">
      <div
        className="p-6 cursor-pointer flex justify-between items-center"
        onClick={() => setIsOpen(!isOpen)}
      >
        <h2 className="text-xl font-bold text-gray-900">회의 전문</h2>
        <div className="flex items-center gap-1 text-gray-500 text-sm">
          <ChevronDownIcon
            className={`h-4 w-4 transition-transform ${
              isOpen ? "rotate-180" : ""
            }`}
          />
          {isOpen ? "닫기" : "더보기"}
        </div>
      </div>

      {isOpen && (
        <div className="px-6 pb-6 border-t border-gray-200">
          <div className="pt-4">
            <pre className="whitespace-pre-wrap text-gray-700 text-sm leading-relaxed">
              {transcript}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
