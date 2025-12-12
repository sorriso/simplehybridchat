/* path: frontend/src/components/chat/ChatContainer.tsx
   version: 2 - Accept currentConversationId as prop */

"use client";

import { ChatInterface } from "./ChatInterface";
import { useSettings } from "@/lib/hooks/useSettings";

interface ChatContainerProps {
  currentConversationId: string | null;
}

/**
 * Container component that wraps ChatInterface with data
 */
export function ChatContainer({ currentConversationId }: ChatContainerProps) {
  const { settings } = useSettings();

  return (
    <div className="h-full flex flex-col">
      <ChatInterface
        conversationId={currentConversationId}
        promptCustomization={settings?.promptCustomization}
      />
    </div>
  );
}
