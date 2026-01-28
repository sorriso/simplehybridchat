/* path: frontend/src/components/sidebar/Sidebar.tsx
   version: 10.0
   
   Changes in v10.0:
   - ADDED: Resizable sidebar with drag handle
   - Default width: 280px → 320px (wider)
   - Min width: 240px, Max width: 480px
   - Persist width in localStorage
   - Modern resize handle with hover effect
*/

import { useState, useEffect } from "react";
import { Settings, FolderPlus, Upload } from "lucide-react";
import { NewConversationButton } from "./NewConversationButton";
import { ConversationList } from "./ConversationList";
import { IconButton } from "../ui/IconButton";
import { Modal } from "../ui/Modal";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import type { Conversation, ConversationGroup } from "@/types/conversation";

interface SidebarProps {
  conversations: Conversation[];
  groups: ConversationGroup[];
  currentConversationId: string | null;
  currentUserId?: string;
  createConversation: (title?: string, groupId?: string) => Promise<Conversation>;
  deleteConversation: (id: string) => Promise<void>;
  updateConversation: (id: string, data: { title?: string; groupId?: string | null }) => Promise<Conversation>;
  onConversationShare?: (id: string) => void;
  createGroup: (name: string) => Promise<ConversationGroup>;
  deleteGroup: (id: string) => Promise<void>;
  setCurrentConversationId: (id: string | null) => void;
  onSettingsClick: () => void;
  onUploadClick: () => void;
}

const SIDEBAR_WIDTH_KEY = 'sidebar-width';
const DEFAULT_WIDTH = 320;
const MIN_WIDTH = 240;
const MAX_WIDTH = 480;

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
  const [showNewGroupModal, setShowNewGroupModal] = useState(false);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [showRenameGroupModal, setShowRenameGroupModal] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [newGroupName, setNewGroupName] = useState("");
  const [renameValue, setRenameValue] = useState("");
  const [isResizing, setIsResizing] = useState(false);
  const [width, setWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(SIDEBAR_WIDTH_KEY);
      return saved ? parseInt(saved, 10) : DEFAULT_WIDTH;
    }
    return DEFAULT_WIDTH;
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(SIDEBAR_WIDTH_KEY, width.toString());
    }
  }, [width]);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.min(Math.max(e.clientX, MIN_WIDTH), MAX_WIDTH);
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const handleNewConversation = async () => {
    const newConv = await createConversation();
    setCurrentConversationId(newConv.id);
  };

  const handleConversationDelete = async (id: string) => {
    if (window.confirm("Delete this conversation?")) {
      await deleteConversation(id);
      if (currentConversationId === id) {
        setCurrentConversationId(null);
      }
    }
  };

  const handleConversationRename = (id: string, currentTitle: string) => {
    setSelectedItemId(id);
    setRenameValue(currentTitle || "New Conversation");
    setShowRenameModal(true);
  };

  const handleConversationShare = (id: string) => {
    onConversationShare?.(id);
  };

  const handleGroupDelete = async (id: string) => {
    if (window.confirm("Delete this group? Conversations will be ungrouped.")) {
      await deleteGroup(id);
    }
  };

  const handleGroupRename = (id: string, currentName: string) => {
    setSelectedItemId(id);
    setRenameValue(currentName);
    setShowRenameGroupModal(true);
  };

  const handleMoveConversationToGroup = async (conversationId: string, groupId: string | null) => {
    await updateConversation(conversationId, { groupId });
  };

  const submitNewGroup = async () => {
    if (newGroupName.trim()) {
      await createGroup(newGroupName.trim());
      setNewGroupName("");
      setShowNewGroupModal(false);
    }
  };

  const submitRename = async () => {
    if (selectedItemId && renameValue.trim()) {
      await updateConversation(selectedItemId, { title: renameValue.trim() });
      setShowRenameModal(false);
      setSelectedItemId(null);
      setRenameValue("");
    }
  };

  const submitGroupRename = async () => {
    if (selectedItemId && renameValue.trim()) {
      const group = groups.find((g) => g.id === selectedItemId);
      if (group) {
        await updateConversation(selectedItemId, { title: renameValue.trim() });
        setShowRenameGroupModal(false);
        setSelectedItemId(null);
        setRenameValue("");
      }
    }
  };

  return (
    <div 
      className="flex-shrink-0 bg-gray-50 border-r border-gray-200 flex relative"
      style={{ width: `${width}px` }}
    >
      <div className="flex flex-col h-full w-full">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2.5 border-b border-gray-200 bg-white">
          <h1 className="text-base font-semibold text-gray-900">Conversations</h1>
          <div className="flex items-center gap-1">
            <IconButton icon={FolderPlus} onClick={() => setShowNewGroupModal(true)} title="New Group" size="sm" />
            <IconButton icon={Upload} onClick={onUploadClick} title="Upload Files" size="sm" />
            <IconButton icon={Settings} onClick={onSettingsClick} title="Settings" size="sm" />
          </div>
        </div>

        {/* New Conversation Button */}
        <div className="px-3 py-2">
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

        {/* Modals */}
        <Modal isOpen={showNewGroupModal} onClose={() => { setShowNewGroupModal(false); setNewGroupName(""); }} title="Create New Group">
          <div className="space-y-4">
            <Input label="Group Name" value={newGroupName} onChange={(e) => setNewGroupName(e.target.value)} placeholder="Enter group name" autoFocus />
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => { setShowNewGroupModal(false); setNewGroupName(""); }} fullWidth>
                Cancel
              </Button>
              <Button variant="primary" onClick={submitNewGroup} disabled={!newGroupName.trim()} fullWidth>
                Create
              </Button>
            </div>
          </div>
        </Modal>

        <Modal isOpen={showRenameModal} onClose={() => { setShowRenameModal(false); setRenameValue(""); setSelectedItemId(null); }} title="Rename Conversation">
          <div className="space-y-4">
            <Input label="Conversation Title" value={renameValue} onChange={(e) => setRenameValue(e.target.value)} placeholder="Enter new title" autoFocus />
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => { setShowRenameModal(false); setRenameValue(""); setSelectedItemId(null); }} fullWidth>
                Cancel
              </Button>
              <Button variant="primary" onClick={submitRename} disabled={!renameValue.trim()} fullWidth>
                Rename
              </Button>
            </div>
          </div>
        </Modal>

        <Modal isOpen={showRenameGroupModal} onClose={() => { setShowRenameGroupModal(false); setRenameValue(""); setSelectedItemId(null); }} title="Rename Group">
          <div className="space-y-4">
            <Input label="Group Name" value={renameValue} onChange={(e) => setRenameValue(e.target.value)} placeholder="Enter new name" autoFocus />
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => { setShowRenameGroupModal(false); setRenameValue(""); setSelectedItemId(null); }} fullWidth>
                Cancel
              </Button>
              <Button variant="primary" onClick={submitGroupRename} disabled={!renameValue.trim()} fullWidth>
                Rename
              </Button>
            </div>
          </div>
        </Modal>
      </div>

      {/* Resize Handle */}
      <div
        onMouseDown={() => setIsResizing(true)}
        className={`absolute right-0 top-0 h-full w-1 cursor-ew-resize bg-transparent hover:bg-blue-400 transition-colors ${isResizing ? 'bg-blue-500' : ''}`}
        style={{ zIndex: 10 }}
      />
    </div>
  );
}