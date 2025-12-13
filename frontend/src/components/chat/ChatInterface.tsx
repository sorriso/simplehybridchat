/* path: frontend/src/components/chat/ChatInterface.tsx
   version: 12 - ENHANCED: Blue pastel background for visual unity with selected conversation
                Now adapter recreates when switching conversations */

"use client";

import { useState, useEffect } from "react";
import { AiChat } from "@nlux/react";
import { useAsStreamAdapter } from "@nlux/react";
import type { ChatItem } from "@nlux/react";
import "@nlux/themes/nova.css";
import { API_ENDPOINTS, STORAGE_KEYS } from "@/lib/utils/constants";
import { conversationsApi } from "@/lib/api/conversations";

interface ChatInterfaceProps {
  conversationId: string | null;
  promptCustomization?: string;
  onMessageSent?: () => void; // Called after message fully sent
}

/**
 * Get API base URL
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;

  try {
    return window.localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
  } catch (error) {
    console.error("Error reading auth token:", error);
    return null;
  }
}

/**
 * Get current user from localStorage
 */
function getCurrentUser(): { name: string; email: string } | null {
  if (typeof window === "undefined") return null;

  try {
    const userStr = window.localStorage.getItem(STORAGE_KEYS.CURRENT_USER);
    if (!userStr) return null;
    return JSON.parse(userStr);
  } catch (error) {
    console.error("Error reading current user:", error);
    return null;
  }
}

/**
 * Main chat interface using NLUX
 */
export function ChatInterface({
  conversationId,
  promptCustomization,
  onMessageSent,
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
        // Get real token from localStorage
        const token = getAuthToken();
        if (!token) {
          observer.error(new Error("Not authenticated"));
          return;
        }

        // CRITICAL: Use API_BASE_URL for backend
        const response = await fetch(
          `${API_BASE_URL}${API_ENDPOINTS.CHAT_STREAM}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              message,
              conversationId,
              promptCustomization: promptCustomization || "",
            }),
          },
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Read the stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("No response body");
        }

        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            console.log("[ChatInterface] Stream complete");
            observer.complete();
            onMessageSent?.(); // Notify parent that message was sent
            break;
          }

          // Decode chunk
          buffer += decoder.decode(value, { stream: true });

          // Process complete lines
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim() || !line.startsWith("data: ")) {
              continue;
            }

            const data = line.slice(6); // Remove "data: " prefix but KEEP whitespace!
            const dataTrimmed = data.trim(); // Trimmed version for control signals

            // Check for completion signal
            if (dataTrimmed === "[DONE]") {
              console.log("[ChatInterface] Received [DONE]");
              observer.complete();
              onMessageSent?.(); // Notify parent that message was sent
              return;
            }

            // Check for error signal
            if (dataTrimmed.startsWith("[ERROR:")) {
              const errorMsg = dataTrimmed.substring(7, dataTrimmed.length - 1); // Remove [ERROR: and ]
              console.error("[ChatInterface] Received error:", errorMsg);
              observer.error(new Error(errorMsg));
              return;
            }

            // FIXED v9: Preserve whitespace in chunks (don't trim!)
            // Backend sends tokens like " hello" with leading space
            if (data) {
              observer.next(data);
            }
          }
        }
      } catch (error) {
        console.error("[ChatInterface] Stream error:", error);
        observer.error(error as Error);
      }
    },
    [conversationId, promptCustomization, onMessageSent],
  );

  if (!conversationId) {
    console.log("[ChatInterface] No conversationId - showing empty state");
    return (
      <div className="flex h-full items-center justify-center text-gray-500">
        <p>Select or create a conversation to start chatting</p>
      </div>
    );
  }

  // Show loading state while history is loading
  if (loadingHistory) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Loading conversation...</p>
        </div>
      </div>
    );
  }

  // Get current user for persona
  const currentUser = getCurrentUser();
  const userName = currentUser?.name || "User";

  return (
    <div className="h-full bg-blue-50">
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
            name: userName,
            avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=10b981&color=fff`,
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
