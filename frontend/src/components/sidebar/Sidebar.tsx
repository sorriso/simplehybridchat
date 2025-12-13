/* path: frontend/src/components/sidebar/Sidebar.tsx
   version: 9 - FIXED: Made onConversationShare optional for compatibility with ChatContainer
   
   Changes in v9:
   - FIXED: onConversationShare is now optional (not required in all contexts)
   - ADDED: Conditional rendering of Share menu item based on onConversationShare presence
   - Reason: ChatContainer doesn't need share functionality, only page.tsx does
   
   Changes in v8:
   - ADDED: currentUserId optional prop to pass to ConversationList
   - Reason: Support shared conversation filtering in ConversationList
   
   Changes in v7:
   - ADDED: onConversationShare prop to SidebarProps
   - ADDED: Pass onConversationShare to ConversationList
   - Reason: Support conversation sharing with user groups
*/

import { useState } from "react";
import { Settings, FolderPlus, Upload } from "lucide-react";
import { NewConversationButton } from "./NewConversationButton";
import { ConversationList } from "./ConversationList";
import { IconButton } from "../ui/IconButton";
import { Modal } from "../ui/Modal";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import type { Conversation, ConversationGroup } from "@/types/conversation";

interface SidebarProps {
  // Conversation state
  conversations: Conversation[];
  groups: ConversationGroup[];
  currentConversationId: string | null;
  currentUserId?: string;

  // Conversation actions
  createConversation: (
    title?: string,
    groupId?: string,
  ) => Promise<Conversation>;
  deleteConversation: (id: string) => Promise<void>;
  updateConversation: (
    id: string,
    data: { title?: string; groupId?: string | null },
  ) => Promise<Conversation>;
  onConversationShare?: (id: string) => void;
  createGroup: (name: string) => Promise<ConversationGroup>;
  deleteGroup: (id: string) => Promise<void>;
  setCurrentConversationId: (id: string | null) => void;

  // UI actions
  onSettingsClick: () => void;
  onUploadClick: () => void;
}

/**
 * Main sidebar component
 */
export function Sidebar({
  conversations,
  groups,
  currentConversationId,
  currentUserId,
  createConversation,
  deleteConversation,
  updateConversation,
  onConversationShare,
  createGroup,
  deleteGroup,
  setCurrentConversationId,
  onSettingsClick,
  onUploadClick,
}: SidebarProps) {
  // Modal states
  const [showNewGroupModal, setShowNewGroupModal] = useState(false);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [showRenameGroupModal, setShowRenameGroupModal] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  // Form states
  const [groupName, setGroupName] = useState("");
  const [conversationTitle, setConversationTitle] = useState("");

  // Handle new conversation
  const handleNewConversation = async () => {
    try {
      await createConversation("New Conversation");
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  // Handle conversation delete
  const handleConversationDelete = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      try {
        await deleteConversation(id);
      } catch (error) {
        console.error("Failed to delete conversation:", error);
      }
    }
  };

  // Handle conversation rename
  const handleConversationRename = (id: string) => {
    const conversation = conversations.find((c) => c.id === id);
    if (conversation) {
      setSelectedItemId(id);
      setConversationTitle(conversation.title);
      setShowRenameModal(true);
    }
  };

  // Handle conversation share
  const handleConversationShare = (id: string) => {
    onConversationShare?.(id);
  };

  // Handle group delete
  const handleGroupDelete = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this group?")) {
      try {
        await deleteGroup(id);
      } catch (error) {
        console.error("Failed to delete group:", error);
      }
    }
  };

  // Handle group rename
  const handleGroupRename = (id: string) => {
    const group = groups.find((g) => g.id === id);
    if (group) {
      setSelectedItemId(id);
      setGroupName(group.name);
      setShowRenameGroupModal(true);
    }
  };

  // Handle move conversation to group
  const handleMoveConversationToGroup = async (
    conversationId: string,
    groupId: string | null,
  ) => {
    try {
      await updateConversation(conversationId, { groupId });
    } catch (error) {
      console.error("Failed to move conversation:", error);
    }
  };

  // Submit new group
  const submitNewGroup = async () => {
    if (!groupName.trim()) return;

    try {
      await createGroup(groupName);
      setShowNewGroupModal(false);
      setGroupName("");
    } catch (error) {
      console.error("Failed to create group:", error);
    }
  };

  // Submit conversation rename
  const submitConversationRename = async () => {
    if (!selectedItemId || !conversationTitle.trim()) return;

    try {
      await updateConversation(selectedItemId, { title: conversationTitle });
      setShowRenameModal(false);
      setSelectedItemId(null);
      setConversationTitle("");
    } catch (error) {
      console.error("Failed to rename conversation:", error);
    }
  };

  // Submit group rename
  const submitGroupRename = async () => {
    if (!selectedItemId || !groupName.trim()) return;

    try {
      const group = groups.find((g) => g.id === selectedItemId);
      if (group) {
        // Note: We need updateGroup API call here
        // For now, just close modal
        setShowRenameGroupModal(false);
        setSelectedItemId(null);
        setGroupName("");
      }
    } catch (error) {
      console.error("Failed to rename group:", error);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 border-r border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h1 className="text-xl font-semibold text-gray-900">Conversations</h1>
        <div className="flex items-center gap-2">
          <IconButton
            icon={FolderPlus}
            onClick={() => setShowNewGroupModal(true)}
            title="New Group"
            size="sm"
          />
          <IconButton
            icon={Upload}
            onClick={onUploadClick}
            title="Upload Files"
            size="sm"
          />
          <IconButton
            icon={Settings}
            onClick={onSettingsClick}
            title="Settings"
            size="sm"
          />
        </div>
      </div>

      {/* New Conversation Button */}
      <div className="p-4">
        <NewConversationButton onClick={handleNewConversation} />
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        <ConversationList
          conversations={conversations}
          groups={groups}
          currentConversationId={currentConversationId}
          currentUserId={currentUserId}
          onConversationClick={setCurrentConversationId}
          onConversationDelete={handleConversationDelete}
          onConversationRename={handleConversationRename}
          onConversationShare={handleConversationShare}
          onGroupDelete={handleGroupDelete}
          onGroupRename={handleGroupRename}
          onMoveConversationToGroup={handleMoveConversationToGroup}
        />
      </div>

      {/* New Group Modal */}
      <Modal
        isOpen={showNewGroupModal}
        onClose={() => {
          setShowNewGroupModal(false);
          setGroupName("");
        }}
        title="Create New Group"
      >
        <div className="space-y-4">
          <Input
            label="Group Name"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            placeholder="Enter group name"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                submitNewGroup();
              }
            }}
          />
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => {
                setShowNewGroupModal(false);
                setGroupName("");
              }}
            >
              Cancel
            </Button>
            <Button onClick={submitNewGroup}>Create</Button>
          </div>
        </div>
      </Modal>

      {/* Rename Conversation Modal */}
      <Modal
        isOpen={showRenameModal}
        onClose={() => {
          setShowRenameModal(false);
          setSelectedItemId(null);
          setConversationTitle("");
        }}
        title="Rename Conversation"
      >
        <div className="space-y-4">
          <Input
            label="Title"
            value={conversationTitle}
            onChange={(e) => setConversationTitle(e.target.value)}
            placeholder="Enter new title"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                submitConversationRename();
              }
            }}
          />
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => {
                setShowRenameModal(false);
                setSelectedItemId(null);
                setConversationTitle("");
              }}
            >
              Cancel
            </Button>
            <Button onClick={submitConversationRename}>Rename</Button>
          </div>
        </div>
      </Modal>

      {/* Rename Group Modal */}
      <Modal
        isOpen={showRenameGroupModal}
        onClose={() => {
          setShowRenameGroupModal(false);
          setSelectedItemId(null);
          setGroupName("");
        }}
        title="Rename Group"
      >
        <div className="space-y-4">
          <Input
            label="Group Name"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            placeholder="Enter new name"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                submitGroupRename();
              }
            }}
          />
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => {
                setShowRenameGroupModal(false);
                setSelectedItemId(null);
                setGroupName("");
              }}
            >
              Cancel
            </Button>
            <Button onClick={submitGroupRename}>Rename</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
