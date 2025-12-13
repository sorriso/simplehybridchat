/* path: frontend/src/components/chat/ChatContainer.tsx
   version: 4 - FIXED: Type compatibility for conversationId (undefined → null)
   
   Changes in v4:
   - FIXED: Convert undefined to null for conversationId (currentConversationId ?? null)
   - Reason: ChatInterface expects string | null, not string | null | undefined
   
   Changes in v3:
   - REMOVED: Sidebar component (displayed in page.tsx)
   - REMOVED: SettingsPanel and FileUploadPanel (displayed in page.tsx)
   - REMOVED: useConversations hook (already in page.tsx)
   - SIMPLIFIED: Now only displays ChatInterface
   - Props: currentConversationId and onMessageSent from parent */

"use client";

import { ChatInterface } from "./ChatInterface";
import { useSettings } from "@/lib/hooks/useSettings";

interface ChatContainerProps {
  currentConversationId?: string | null;
  onMessageSent?: () => void;
}

/**
 * Container for the chat interface
 * Sidebar, panels, and conversation management are handled in page.tsx
 */
export function ChatContainer({
  currentConversationId,
  onMessageSent,
}: ChatContainerProps) {
  const { settings } = useSettings();

  return (
    <ChatInterface
      conversationId={currentConversationId ?? null}
      promptCustomization={settings?.promptCustomization}
      onMessageSent={onMessageSent}
    />
  );
}
