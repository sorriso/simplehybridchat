"use client";

/* path: frontend/src/app/page.tsx
   version: 6 - Fixed conversation selection by removing closure issue */

import { useState } from "react";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { FileUploadPanel } from "@/components/upload/FileUploadPanel";
import { SettingsPanel } from "@/components/settings/SettingsPanel";
import { LoginForm } from "@/components/auth/LoginForm";
import { useAuth } from "@/lib/hooks/useAuth";
import { useConversations } from "@/lib/hooks/useConversations";

/**
 * Main application page
 */
export default function Home() {
  const { user, loading, login, error } = useAuth();
  const conversations = useConversations();
  const [showUploadPanel, setShowUploadPanel] = useState(false);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);

  // Show loading state
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

  // Show login form if not authenticated
  if (!user) {
    return <LoginForm onLogin={login} loading={loading} error={error} />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0">
        <Sidebar
          conversations={conversations.conversations}
          groups={conversations.groups}
          currentConversationId={conversations.currentConversationId}
          createConversation={conversations.createConversation}
          deleteConversation={conversations.deleteConversation}
          updateConversation={conversations.updateConversation}
          createGroup={conversations.createGroup}
          deleteGroup={conversations.deleteGroup}
          setCurrentConversationId={conversations.setCurrentConversationId}
          onSettingsClick={() => setShowSettingsPanel(true)}
          onUploadClick={() => setShowUploadPanel(true)}
        />
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-14 border-b border-gray-200 flex items-center px-6">
          <h1 className="text-lg font-semibold text-gray-900">AI Assistant</h1>
        </header>

        {/* Chat interface */}
        <main className="flex-1 overflow-hidden">
          <ChatContainer
            currentConversationId={conversations.currentConversationId}
          />
        </main>
      </div>

      {/* File upload panel (overlay) */}
      <FileUploadPanel
        isOpen={showUploadPanel}
        onClose={() => setShowUploadPanel(false)}
      />

      {/* Settings panel (overlay) */}
      <SettingsPanel
        isOpen={showSettingsPanel}
        onClose={() => setShowSettingsPanel(false)}
      />

      {/* Overlay backdrop when panels are open */}
      {(showUploadPanel || showSettingsPanel) && (
        <div
          className="fixed inset-0 bg-black bg-opacity-30 z-30"
          onClick={() => {
            setShowUploadPanel(false);
            setShowSettingsPanel(false);
          }}
        />
      )}
    </div>
  );
}
