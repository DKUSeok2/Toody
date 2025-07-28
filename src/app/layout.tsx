import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Toody",
  description: "AI 회의록 투두리스트 추출 서비스",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        {/* Socket.io 연결 시도 차단 스크립트 */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Socket.io 연결 시도 차단
              const socket = {
                on: function() { console.log('Socket.io blocked'); },
                emit: function() { console.log('Socket.io blocked'); },
                disconnect: function() { console.log('Socket.io blocked'); }
              };
              
              // io 함수 오버라이드
              window.io = function() {
                console.log('Socket.io connection blocked by client');
                return socket;
              };
              
              // WebSocket 생성자 오버라이드 (추가 보안)
              const OriginalWebSocket = window.WebSocket;
              window.WebSocket = function(url) {
                if (url && url.includes('socket.io')) {
                  console.log('Socket.io WebSocket blocked:', url);
                  return {
                    addEventListener: function() {},
                    removeEventListener: function() {},
                    send: function() {},
                    close: function() {},
                    readyState: 3 // CLOSED
                  };
                }
                return new OriginalWebSocket(url);
              };
            `,
          }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
