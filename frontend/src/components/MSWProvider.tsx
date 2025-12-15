/* path: frontend/src/components/MSWProvider.tsx
   version: 4 - FIXED: Check NEXT_PUBLIC_DISABLE_MSW variable (was checking wrong env var)
   
   Changes in v4:
   - FIXED: Now checks NEXT_PUBLIC_DISABLE_MSW=true from .env
   - ADDED: Logs to show if MSW is enabled or disabled
   - Reason: Was checking NEXT_PUBLIC_API_MOCKING which doesn't exist in .env
   
   Changes in v3:
   - Can be disabled via env variable */

   "use client";

   import { useEffect, useState } from "react";
   
   export function MSWProvider({ children }: { children: React.ReactNode }) {
     const [mswReady, setMswReady] = useState(false);
   
     useEffect(() => {
       console.log("[MSWProvider] Initializing...");
       console.log("[MSWProvider] NEXT_PUBLIC_DISABLE_MSW:", process.env.NEXT_PUBLIC_DISABLE_MSW);
       console.log("[MSWProvider] NEXT_PUBLIC_API_MOCKING:", process.env.NEXT_PUBLIC_API_MOCKING);
       
       const initMSW = async () => {
         if (typeof window === "undefined") {
           console.log("[MSWProvider] Server-side, skipping MSW");
           setMswReady(true);
           return;
         }
   
         // Check if MSW is disabled (default: disabled unless explicitly enabled)
         const mswDisabled = process.env.NEXT_PUBLIC_DISABLE_MSW === "true";
         const mswEnabled = process.env.NEXT_PUBLIC_API_MOCKING === "enabled";
   
         console.log("[MSWProvider] mswDisabled:", mswDisabled);
         console.log("[MSWProvider] mswEnabled:", mswEnabled);
   
         if (mswDisabled || !mswEnabled) {
           console.log("[MSWProvider] ✅ MSW DISABLED - Using real backend at", process.env.NEXT_PUBLIC_API_URL);
           setMswReady(true);
           return;
         }
   
         console.log("[MSWProvider] ⚠️ MSW ENABLED - Using mock handlers");
         const { worker } = await import("../mocks/browser");
         await worker.start({
           onUnhandledRequest: "bypass",
         });
         console.log("[MSWProvider] MSW worker started");
         setMswReady(true);
       };
   
       initMSW();
     }, []);
   
     if (!mswReady) {
       return <div>Loading...</div>;
     }
   
     return <>{children}</>;
   }