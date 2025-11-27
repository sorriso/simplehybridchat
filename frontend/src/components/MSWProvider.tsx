// path: src/components/MSWProvider.tsx
// version: 2 - Only active in development

"use client";

import { useEffect, useState } from "react";

export function MSWProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(process.env.NODE_ENV === "production");

  useEffect(() => {
    async function init() {
      // Skip MSW in production
      if (process.env.NODE_ENV === "production") {
        setReady(true);
        return;
      }

      if (typeof window === "undefined") return;

      const { worker } = await import("@/mocks/browser");
      await worker.start({ onUnhandledRequest: "bypass" });

      setReady(true);
    }

    init();
  }, []);

  if (!ready) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
      </div>
    );
  }

  return <>{children}</>;
}
