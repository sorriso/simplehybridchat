/* path: frontend/src/components/chat/ChatInterface.tsx
   version: 5 - Load conversation history on mount */

"use client";

import { useState, useEffect } from "react";
import { AiChat } from "@nlux/react";
import { useAsStreamAdapter } from "@nlux/react";
import type { ChatItem } from "@nlux/react";
import "@nlux/themes/nova.css";
import { API_ENDPOINTS } from "@/lib/utils/constants";
import { MOCK_USER } from "@/lib/utils/constants";
import { conversationsApi } from "@/lib/api/conversations";

interface ChatInterfaceProps {
  conversationId: string | null;
  promptCustomization?: string;
}

/**
 * Main chat interface using NLUX
 */
export function ChatInterface({
  conversationId,
  promptCustomization,
}: ChatInterfaceProps) {
  console.log("[ChatInterface] Rendering with conversationId:", conversationId);

  const [initialMessages, setInitialMessages] = useState<ChatItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Load conversation history when conversationId changes
  useEffect(() => {
    if (!conversationId) {
      setInitialMessages([]);
      return;
    }

    const loadHistory = async () => {
      setLoadingHistory(true);
      console.log(
        "[ChatInterface] Loading history for conversation:",
        conversationId,
      );

      try {
        const messages = await conversationsApi.getMessages(conversationId);
        console.log("[ChatInterface] Loaded", messages.length, "messages");

        // Convert messages to NLUX format
        const chatItems: ChatItem[] = messages.map((msg) => ({
          role: msg.role,
          message: msg.content,
        }));

        setInitialMessages(chatItems);
      } catch (error) {
        console.error("[ChatInterface] Failed to load history:", error);
        setInitialMessages([]);
      } finally {
        setLoadingHistory(false);
      }
    };

    loadHistory();
  }, [conversationId]);

  // Create streaming adapter for FastAPI backend
  const adapter = useAsStreamAdapter(
    async (message: string, observer) => {
      console.log("[ChatInterface] Adapter called with message:", message);

      if (!conversationId) {
        observer.error(new Error("No conversation selected"));
        return;
      }

      try {
        const response = await fetch(API_ENDPOINTS.CHAT_STREAM, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${MOCK_USER.token}`,
          },
          body: JSON.stringify({
            message,
            conversationId,
            promptCustomization: promptCustomization || "",
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Read the stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("No response body");
        }

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            observer.complete();
            break;
          }

          // Decode and send chunks to NLUX
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.substring(6).trim();
              if (data && data !== "[DONE]") {
                observer.next(data);
              }
            }
          }
        }
      } catch (error) {
        console.error("Chat stream error:", error);
        observer.error(
          error instanceof Error ? error : new Error("Unknown error"),
        );
      }
    },
    [conversationId, promptCustomization],
  );

  // Show empty state when no conversation is selected
  if (!conversationId) {
    console.log("[ChatInterface] No conversationId - showing empty state");
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium mb-2">No conversation selected</p>
          <p className="text-sm">
            Create or select a conversation to start chatting
          </p>
        </div>
      </div>
    );
  }

  console.log("[ChatInterface] Rendering AiChat component");

  // Show loading state while fetching history
  if (loadingHistory) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="h-full">
      <AiChat
        key={conversationId}
        adapter={adapter}
        initialConversation={initialMessages}
        personaOptions={{
          assistant: {
            name: "AI Assistant",
            tagline: "How can I help you today?",
            avatar:
              "https://ui-avatars.com/api/?name=AI+Assistant&background=3b82f6&color=fff",
          },
          user: {
            name: MOCK_USER.name,
            avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(MOCK_USER.name)}&background=10b981&color=fff`,
          },
        }}
        conversationOptions={{
          layout: "bubbles",
        }}
        displayOptions={{
          colorScheme: "light",
        }}
        composerOptions={{
          placeholder: "Type your message...",
        }}
      />
    </div>
  );
}
