interface MeetingSummaryProps {
  summaryItems: string[];
}

export default function MeetingSummary({ summaryItems }: MeetingSummaryProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-300 p-6">
      <div className="space-y-3">
        {summaryItems.map((item, index) => (
          <div key={index} className="flex items-start">
            <div className="w-1 h-1 bg-black rounded-full mt-2 mr-3 flex-shrink-0"></div>
            <p className="text-gray-900">{item}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
