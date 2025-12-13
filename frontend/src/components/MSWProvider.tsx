/* path: frontend/src/components/MSWProvider.tsx
   version: 3 - Can be disabled via env variable */

"use client";

import { useEffect, useState } from "react";

export function MSWProvider({ children }: { children: React.ReactNode }) {
  const [mswReady, setMswReady] = useState(false);

  useEffect(() => {
    const initMSW = async () => {
      if (typeof window === "undefined") {
        setMswReady(true);
        return;
      }

      if (process.env.NEXT_PUBLIC_API_MOCKING !== "enabled") {
        setMswReady(true);
        return;
      }

      const { worker } = await import("../mocks/browser");
      await worker.start({
        onUnhandledRequest: "bypass",
      });
      setMswReady(true);
    };

    initMSW();
  }, []);

  if (!mswReady) {
    return <div>Loading...</div>;
  }

  return <>{children}</>;
}
