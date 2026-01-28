"use client";

/* path: frontend/src/app/page.tsx
   version: 21
   
   Changes in v21:
   - CRITICAL FIX: Pass user to useConversations({ user })
   - Hook now reloads conversations when user changes
   - Fixes stale data after logout/login with different user
   - No more manual reload needed
   
   Changes in v20:
   - REMOVED: Overlay completely (was causing black screen over chat area)
   - Panels have shadow-xl which is sufficient to distinguish them
   - Chat area stays fully visible when panels are open
   - Cleaner UX without overlay interference */

import { useState, useEffect, useRef } from "react";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { FileUploadPanel } from "@/components/upload/FileUploadPanel";
import { SettingsPanel } from "@/components/settings/SettingsPanel";
import { ShareConversationModal } from "@/components/sharing/ShareConversationModal";
import { LoginForm } from "@/components/auth/LoginForm";
import { useAuth } from "@/lib/hooks/useAuth";
import { useConversations } from "@/lib/hooks/useConversations";
import { userManagementApi } from "@/lib/hooks/useAuth";
import type { UserGroup } from "@/types/auth";

export default function Home() {
  const { user, loading, login, error } = useAuth();
  const conversations = useConversations({ user });
  const [showUploadPanel, setShowUploadPanel] = useState(false);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareConversationId, setShareConversationId] = useState<string | null>(
    null,
  );
  const [userGroups, setUserGroups] = useState<UserGroup[]>([]);
  const hasReloaded = useRef(false);

  useEffect(() => {
    if (user) {
      loadUserGroups();
    }
  }, [user]);

  const loadUserGroups = async () => {
    try {
      const groups = await userManagementApi.getAllGroups();
      setUserGroups(groups.filter((g) => g.status === "active"));
    } catch (error) {
      console.error("Failed to load user groups:", error);
    }
  };

  useEffect(() => {
    if (user && !hasReloaded.current) {
      hasReloaded.current = true;
    }
  }, [user]);

  useEffect(() => {
    if (!user) {
      setShowUploadPanel(false);
      setShowSettingsPanel(false);
      setShowShareModal(false);
      hasReloaded.current = false;
    }
  }, [user]);

  const handleShareConversation = (conversationId: string) => {
    setShareConversationId(conversationId);
    setShowShareModal(true);
  };

  const handleShare = async (groupIds: string[]) => {
    if (!shareConversationId) return;
    try {
      await conversations.shareConversation(shareConversationId, groupIds);
      setShowShareModal(false);
      setShareConversationId(null);
    } catch (error) {
      console.error("Failed to share conversation:", error);
    }
  };

  const handleUnshare = async (groupIds: string[]) => {
    if (!shareConversationId) return;
    try {
      await conversations.unshareConversation(shareConversationId, groupIds);
    } catch (error) {
      console.error("Failed to unshare conversation:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <LoginForm onLogin={login} loading={loading} error={error} />
      </div>
    );
  }

  const selectedConversation = conversations.conversations.find(
    (c) => c.id === shareConversationId,
  );

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <div className="w-80 flex-shrink-0">
        <Sidebar
          conversations={conversations.conversations}
          groups={conversations.groups}
          currentConversationId={conversations.currentConversationId}
          currentUserId={user?.id}
          createConversation={conversations.createConversation}
          deleteConversation={conversations.deleteConversation}
          updateConversation={conversations.updateConversation}
          createGroup={conversations.createGroup}
          deleteGroup={conversations.deleteGroup}
          setCurrentConversationId={conversations.setCurrentConversationId}
          onSettingsClick={() => setShowSettingsPanel(true)}
          onUploadClick={() => setShowUploadPanel(true)}
          onConversationShare={handleShareConversation}
        />
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-gray-200 flex items-center px-6">
          <h1 className="text-lg font-semibold text-gray-900">Product CyberSecurity AI Assistant</h1>
        </header>

        <main className="flex-1 overflow-hidden">
          <ChatContainer
            currentConversationId={conversations.currentConversationId}
            onMessageSent={() => {
              if (conversations.currentConversationId) {
                conversations.incrementMessageCount(
                  conversations.currentConversationId,
                );
              }
            }}
          />
        </main>
      </div>

      <FileUploadPanel
        isOpen={showUploadPanel}
        onClose={() => setShowUploadPanel(false)}
        data-testid="upload-panel"
      />

      <SettingsPanel
        isOpen={showSettingsPanel}
        onClose={() => setShowSettingsPanel(false)}
        data-testid="settings-panel"
      />

      {showShareModal && selectedConversation && (
        <ShareConversationModal
          conversation={selectedConversation}
          userGroups={userGroups}
          onShare={handleShare}
          onUnshare={handleUnshare}
          onClose={() => {
            setShowShareModal(false);
            setShareConversationId(null);
          }}
        />
      )}
    </div>
  );
}
