"use client";

import Image from "next/image";
import { useState } from "react";
import UploadFile from "./components/UploadFile";
import MeetingInfoForm from "./components/MeetingInfoForm";
import { useRouter } from "next/navigation";

interface UploadedFile {
  name: string;
  size: number;
  id: string;
  file?: File; // 실제 File 객체 추가
}

export default function Home() {
  const router = useRouter();
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [actualFile, setActualFile] = useState<File | null>(null); // 실제 파일 객체 저장

  const handleFileUpload = (file: UploadedFile | null, actualFileObj?: File) => {
    setUploadedFile(file);
    setActualFile(actualFileObj || null);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="flex justify-between items-center p-4 md:p-6">
        <div className="flex items-center cursor-pointer">
          <Image
            src="/logo.png"
            alt="Toody Logo"
            width={110}
            height={110}
            onClick={() => {
              router.push("/");
            }}
          />
        </div>
        <button
          onClick={() => {
            document.getElementById("contact")?.scrollIntoView({
              behavior: "smooth",
            });
          }}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Contact Us
        </button>
      </header>

      {/* Main Section */}
      <main
        className="flex items-center justify-between px-8 md:px-16 py-12 md:py-20 max-w-7xl mx-auto"
        style={{ minHeight: "calc(100vh - 90px)" }}
      >
        {/* 좌측 영역 */}
        <div className="flex flex-col items-start flex-1 pr-4">
          <h2 className="text-3xl md:text-4xl font-semibold mb-12 text-gray-800 max-w-2xl leading-relaxed">
            회의록을 업로드하고,
            <br />할 일 목록을 바로 받아보세요
          </h2>
          <UploadFile onFileUpload={handleFileUpload} />
        </div>

        {/* 우측 영역 */}
        {uploadedFile == null && (
          <div className="flex-shrink-0 hidden md:block pl-4">
            <Image
              src="/illustration.png"
              alt="Toody Illustration"
              width={500}
              height={500}
              className="object-contain"
            />
          </div>
        )}

        {/* 회의 정보 입력 폼 */}
        {uploadedFile != null && (
          <div className="flex-1 max-w-lg pl-4 flex justify-center">
            <div className="w-full max-w-xl">
              <MeetingInfoForm uploadedFile={actualFile} />
            </div>
          </div>
        )}
      </main>

      {/* Contact Section */}
      <section id="contact" className="bg-gray-50 py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center gap-2 mb-12">
            <Image src="/contact.png" alt="Toody Logo" width={28} height={28} />
            <h2 className="text-3xl font-medium">Contact Us</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
            {/* Contact Form */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name
                </label>
                <input
                  type="text"
                  placeholder="이름을 입력해주세요"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email*
                </label>
                <input
                  type="email"
                  placeholder="이메일을 입력해주세요"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Message*
                </label>
                <textarea
                  placeholder="메시지를 입력해주세요"
                  rows={6}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent resize-none"
                />
              </div>

              <button className="w-full bg-black text-white py-3 rounded-lg hover:bg-gray-800 transition-colors font-medium">
                메시지 보내기
              </button>
            </div>

            {/* Support Section */}
            <div className="flex flex-col items-center justify-center text-center">
              <div className="mb-8">
                <h3 className="text-xl font-semibold mb-4">
                  Toody가 도움이 되었나요?
                </h3>
                <p className="text-gray-600 mb-6">
                  원하시면 응원의 마음을 보내주세요!
                </p>
                <button className="bg-black text-white px-8 py-3 rounded-lg hover:bg-gray-800 transition-colors font-medium">
                  후원하기
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
