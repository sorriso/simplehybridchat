/* path: src/components/sidebar/Sidebar.tsx
   version: 4 - Fixed null groupId handling for ungrouping */

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

  // Conversation actions
  createConversation: (
    title?: string,
    groupId?: string,
  ) => Promise<Conversation>;
  deleteConversation: (id: string) => Promise<void>;
  updateConversation: (
    id: string,
    data: { title?: string; groupId?: string },
  ) => Promise<Conversation>;
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
  createConversation,
  deleteConversation,
  updateConversation,
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

  // Submit conversation rename
  const submitConversationRename = async () => {
    if (!selectedItemId || !conversationTitle.trim()) return;

    try {
      await updateConversation(selectedItemId, { title: conversationTitle });
      setShowRenameModal(false);
      setConversationTitle("");
      setSelectedItemId(null);
    } catch (error) {
      console.error("Failed to rename conversation:", error);
    }
  };

  // Handle new group
  const handleNewGroup = () => {
    setGroupName("");
    setShowNewGroupModal(true);
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

  // Handle group delete
  const handleGroupDelete = async (id: string) => {
    if (
      window.confirm(
        "Are you sure you want to delete this group? Conversations will not be deleted.",
      )
    ) {
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

  // Handle move conversation to group (drag & drop)
  const handleMoveConversationToGroup = async (
    conversationId: string,
    groupId: string | null,
  ) => {
    console.log(
      "[Sidebar] Moving conversation",
      conversationId,
      "to group",
      groupId,
    );
    try {
      // Convert null to undefined for API compatibility
      await updateConversation(conversationId, {
        groupId: groupId ?? undefined,
      });
      console.log("[Sidebar] Conversation moved successfully");
    } catch (error) {
      console.error("Failed to move conversation:", error);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <NewConversationButton onClick={handleNewConversation} />
      </div>

      {/* Actions bar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-200">
        <IconButton
          icon={FolderPlus}
          onClick={handleNewGroup}
          title="New Group"
        />
        <IconButton
          icon={Upload}
          onClick={onUploadClick}
          title="Upload Files"
        />
        <div className="flex-1" />
        <IconButton
          icon={Settings}
          onClick={onSettingsClick}
          title="Settings"
        />
      </div>

      {/* Conversations list */}
      <div className="flex-1 overflow-y-auto p-2">
        <ConversationList
          conversations={conversations}
          groups={groups}
          currentConversationId={currentConversationId}
          onConversationClick={setCurrentConversationId}
          onConversationDelete={handleConversationDelete}
          onConversationRename={handleConversationRename}
          onGroupDelete={handleGroupDelete}
          onGroupRename={handleGroupRename}
          onMoveConversationToGroup={handleMoveConversationToGroup}
        />
      </div>

      {/* New Group Modal */}
      <Modal
        isOpen={showNewGroupModal}
        onClose={() => setShowNewGroupModal(false)}
        title="Create New Group"
        size="sm"
      >
        <div className="space-y-4">
          <Input
            label="Group Name"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            placeholder="Enter group name"
            fullWidth
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") submitNewGroup();
            }}
          />
          <div className="flex gap-2 justify-end">
            <Button
              variant="secondary"
              onClick={() => setShowNewGroupModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={submitNewGroup}
              disabled={!groupName.trim()}
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>

      {/* Rename Conversation Modal */}
      <Modal
        isOpen={showRenameModal}
        onClose={() => setShowRenameModal(false)}
        title="Rename Conversation"
        size="sm"
      >
        <div className="space-y-4">
          <Input
            label="Conversation Title"
            value={conversationTitle}
            onChange={(e) => setConversationTitle(e.target.value)}
            placeholder="Enter title"
            fullWidth
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") submitConversationRename();
            }}
          />
          <div className="flex gap-2 justify-end">
            <Button
              variant="secondary"
              onClick={() => setShowRenameModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={submitConversationRename}
              disabled={!conversationTitle.trim()}
            >
              Save
            </Button>
          </div>
        </div>
      </Modal>

      {/* Rename Group Modal */}
      <Modal
        isOpen={showRenameGroupModal}
        onClose={() => setShowRenameGroupModal(false)}
        title="Rename Group"
        size="sm"
      >
        <div className="space-y-4">
          <Input
            label="Group Name"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            placeholder="Enter group name"
            fullWidth
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") submitConversationRename();
            }}
          />
          <div className="flex gap-2 justify-end">
            <Button
              variant="secondary"
              onClick={() => setShowRenameGroupModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={submitConversationRename}
              disabled={!groupName.trim()}
            >
              Save
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
