import Image from "next/image";

interface HeaderProps {
  onLogoClick: () => void;
  onNewMeeting: () => void;
  onShare?: () => void;
}

export default function Header({
  onLogoClick,
  onNewMeeting,
  onShare,
}: HeaderProps) {
  return (
    <header className="flex justify-between border-b border-gray-100 items-center p-6 md:p-8">
      <div className="flex items-center cursor-pointer" onClick={onLogoClick}>
        <Image src="/logo.png" alt="Toody Logo" width={110} height={110} />
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onNewMeeting}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          새로 회의 요약하기
        </button>
        {onShare && (
          <button
            onClick={onShare}
            className="px-4 py-2 bg-[#191A23] hover:bg-[#5A6BFF] text-white rounded-lg transition-colors"
          >
            공유하기
          </button>
        )}
      </div>
    </header>
  );
}
