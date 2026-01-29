/* path: frontend/src/components/sidebar/ConversationList.tsx
   version: 9.2
   
   Changes in v9.2:
   - FIX: onGroupRename signature changed to (id: string, currentName: string) => void
   - Reason: Sidebar.handleGroupRename needs the name to prefill the rename modal
   - Updated onGroupRename call to pass group.name
   
   Changes in v9.1:
   - FIX: onConversationRename signature changed to (id: string, currentTitle: string) => void
   - Reason: Sidebar.handleConversationRename needs the title to prefill the rename modal
   - Updated all onRename calls to pass conversation.title
   
   Changes in v9.0:
   - ADDED: Support for ungrouping conversations via onUngroup handler
   - Pass onUngroup to ConversationGroup and ungrouped ConversationItems
   - Ungrouping sets groupId to null
*/

import { useState } from "react";
import { Users2 } from "lucide-react";
import {
  Conversation,
  ConversationGroup as ConversationGroupType,
} from "@/types/conversation";
import { ConversationGroup } from "./ConversationGroup";
import { ConversationItem } from "./ConversationItem";
import clsx from "clsx";

interface ConversationListProps {
  conversations: Conversation[];
  groups: ConversationGroupType[];
  currentConversationId: string | null;
  currentUserId?: string;
  onConversationClick: (id: string) => void;
  onConversationDelete: (id: string) => void;
  onConversationRename: (id: string, currentTitle: string) => void; // FIXED: Added currentTitle
  onConversationShare: (id: string) => void;
  onGroupDelete: (id: string) => void;
  onGroupRename: (id: string, currentName: string) => void; // FIXED: Added currentName
  onMoveConversationToGroup?: (conversationId: string, groupId: string | null) => void;
}

export function ConversationList({
  conversations,
  groups,
  currentConversationId,
  currentUserId,
  onConversationClick,
  onConversationDelete,
  onConversationRename,
  onConversationShare,
  onGroupDelete,
  onGroupRename,
  onMoveConversationToGroup,
}: ConversationListProps) {
  const [draggingConversationId, setDraggingConversationId] = useState<string | null>(null);
  const [isDragOverUngrouped, setIsDragOverUngrouped] = useState(false);

  const safeGroups = groups || [];
  const safeConversations = conversations || [];

  const sharedConversations = safeConversations.filter(
    (c) => c.isShared === true || (currentUserId && c.ownerId !== currentUserId),
  );

  const ownedConversations = safeConversations.filter(
    (c) => !c.isShared && (!currentUserId || c.ownerId === currentUserId),
  );

  const ungroupedConversations = ownedConversations.filter((c) => !c.groupId);

  // NEW: Handle ungrouping - moves conversation to ungrouped
  const handleUngroup = async (conversationId: string) => {
    if (onMoveConversationToGroup) {
      await onMoveConversationToGroup(conversationId, null);
    }
  };

  const handleDragStart = (conversationId: string) => {
    setDraggingConversationId(conversationId);
  };

  const handleDragEnd = () => {
    setDraggingConversationId(null);
  };

  const handleDrop = (conversationId: string, groupId: string | null) => {
    if (onMoveConversationToGroup) {
      onMoveConversationToGroup(conversationId, groupId);
    }
  };

  const handleDragOverUngrouped = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setIsDragOverUngrouped(true);
  };

  const handleDragLeaveUngrouped = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOverUngrouped(false);
  };

  const handleDropUngrouped = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOverUngrouped(false);

    const conversationId = e.dataTransfer.getData("conversationId");
    if (conversationId && onMoveConversationToGroup) {
      onMoveConversationToGroup(conversationId, null);
    }
  };

  return (
    <div className="px-2 space-y-1">
      {/* Shared conversations section */}
      {sharedConversations.length > 0 && (
        <div className="mb-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-gray-500 mb-1">
            <Users2 size={14} />
            <span>Shared with me</span>
            <span className="text-[11px]">({sharedConversations.length})</span>
          </div>
          <div className="space-y-1">
            {sharedConversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === currentConversationId}
                onClick={() => onConversationClick(conversation.id)}
                onDelete={() => onConversationDelete(conversation.id)}
                onRename={() => onConversationRename(conversation.id, conversation.title)}
                readOnly={true}
              />
            ))}
          </div>
        </div>
      )}

      {/* Groups */}
      {safeGroups.map((group) => (
        <ConversationGroup
          key={group.id}
          group={group}
          conversations={ownedConversations}
          currentConversationId={currentConversationId}
          onConversationClick={onConversationClick}
          onConversationDelete={onConversationDelete}
          onConversationRename={onConversationRename}
          onConversationShare={onConversationShare}
          onConversationUngroup={handleUngroup}
          onGroupDelete={() => onGroupDelete(group.id)}
          onGroupRename={() => onGroupRename(group.id, group.name)}
          onConversationDrop={handleDrop}
          draggingConversationId={draggingConversationId}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        />
      ))}

      {/* Ungrouped conversations */}
      {ungroupedConversations.length > 0 && (
        <div>
          <div
            onDragOver={handleDragOverUngrouped}
            onDragLeave={handleDragLeaveUngrouped}
            onDrop={handleDropUngrouped}
            className={clsx(
              "rounded-lg transition-colors mb-1",
              isDragOverUngrouped && "bg-primary-100 ring-2 ring-primary-500",
            )}
          >
            <div className="px-2.5 py-1.5 text-xs font-medium text-gray-500">
              UNGROUPED
            </div>
            {isDragOverUngrouped && draggingConversationId && (
              <div className="px-2.5 py-1">
                <p className="text-[11px] text-primary-600">
                  Drop here to ungroup
                </p>
              </div>
            )}
          </div>
          <div className="space-y-1">
            {ungroupedConversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === currentConversationId}
                onClick={() => onConversationClick(conversation.id)}
                onDelete={() => onConversationDelete(conversation.id)}
                onRename={() => onConversationRename(conversation.id, conversation.title)}
                onShare={() => onConversationShare(conversation.id)}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
                isDragging={conversation.id === draggingConversationId}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {safeConversations.length === 0 && (
        <div className="text-center py-8 text-gray-400">
          <p className="text-xs">No conversations yet</p>
          <p className="text-[11px] mt-1">Click &quot;New Conversation&quot; to start</p>
        </div>
      )}
    </div>
  );
}