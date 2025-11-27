/* path: src/app/layout.tsx
   version: 3 - Added MSWProvider for development mocks */

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { MSWProvider } from "@/components/MSWProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Chatbot",
  description: "Modern AI chatbot interface",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <MSWProvider>{children}</MSWProvider>
      </body>
    </html>
  );
}
