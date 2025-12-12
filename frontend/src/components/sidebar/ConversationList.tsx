/* path: frontend/src/components/sidebar/ConversationList.tsx
   version: 8
   
   Changes in v8:
   - ADDED: "Shared with me" section at the top for isShared conversations
   - ADDED: Filter to separate owned vs shared conversations
   - ADDED: currentUserId prop for ownership checking
   - IMPROVED: Better organization (Shared → Groups → Ungrouped)
   - Reason: Display shared conversations in dedicated section
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
  currentUserId?: string; // For checking ownership
  onConversationClick: (id: string) => void;
  onConversationDelete: (id: string) => void;
  onConversationRename: (id: string) => void;
  onConversationShare: (id: string) => void;
  onGroupDelete: (id: string) => void;
  onGroupRename: (id: string) => void;
  onMoveConversationToGroup?: (
    conversationId: string,
    groupId: string | null,
  ) => void;
}

/**
 * List of conversations organized by groups with drag & drop support
 * Now includes "Shared with me" section for conversations shared via user groups
 */
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
  const [draggingConversationId, setDraggingConversationId] = useState<
    string | null
  >(null);
  const [isDragOverUngrouped, setIsDragOverUngrouped] = useState(false);

  // GUARD: Ensure groups is always an array
  const safeGroups = groups || [];
  const safeConversations = conversations || [];

  // Separate shared conversations (not owned by current user OR marked as isShared)
  const sharedConversations = safeConversations.filter(
    (c) =>
      c.isShared === true || (currentUserId && c.ownerId !== currentUserId),
  );

  // Owned conversations
  const ownedConversations = safeConversations.filter(
    (c) => !c.isShared && (!currentUserId || c.ownerId === currentUserId),
  );

  // Ungrouped conversations (owned, no groupId)
  const ungroupedConversations = ownedConversations.filter((c) => !c.groupId);

  const handleDragStart = (conversationId: string) => {
    setDraggingConversationId(conversationId);
  };

  const handleDragEnd = () => {
    setDraggingConversationId(null);
    setIsDragOverUngrouped(false);
  };

  const handleConversationDrop = (conversationId: string, groupId: string) => {
    onMoveConversationToGroup?.(conversationId, groupId);
  };

  const handleUngroupedDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "move";
    setIsDragOverUngrouped(true);
  };

  const handleUngroupedDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    if (
      e.clientX < rect.left ||
      e.clientX >= rect.right ||
      e.clientY < rect.top ||
      e.clientY >= rect.bottom
    ) {
      setIsDragOverUngrouped(false);
    }
  };

  const handleUngroupedDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOverUngrouped(false);

    const conversationId = e.dataTransfer.getData("conversationId");
    if (conversationId && onMoveConversationToGroup) {
      onMoveConversationToGroup(conversationId, null); // null = ungrouped
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
      {/* ============================================================ */}
      {/* SHARED WITH ME SECTION */}
      {/* ============================================================ */}
      {sharedConversations.length > 0 && (
        <div className="pb-2 border-b border-gray-200">
          <div className="flex items-center gap-2 px-3 py-1.5">
            <Users2 className="w-4 h-4 text-blue-600" />
            <p className="text-xs font-medium text-blue-700 uppercase tracking-wide">
              Shared with me
            </p>
            <span className="text-xs text-gray-500">
              ({sharedConversations.length})
            </span>
          </div>
          <div className="space-y-1 px-1 mt-1">
            {sharedConversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === currentConversationId}
                onClick={() => onConversationClick(conversation.id)}
                onDelete={() => onConversationDelete(conversation.id)}
                onRename={() => onConversationRename(conversation.id)}
                onShare={() => onConversationShare(conversation.id)}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
                isDragging={false} // Shared conversations cannot be dragged
                readOnly={true} // Shared conversations are read-only
              />
            ))}
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* GROUPED CONVERSATIONS (OWNED) */}
      {/* ============================================================ */}
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
          onGroupDelete={() => onGroupDelete(group.id)}
          onGroupRename={() => onGroupRename(group.id)}
          onConversationDrop={handleConversationDrop}
          draggingConversationId={draggingConversationId}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        />
      ))}

      {/* ============================================================ */}
      {/* UNGROUPED CONVERSATIONS (OWNED) */}
      {/* ============================================================ */}
      {(ungroupedConversations.length > 0 || draggingConversationId) && (
        <div className="pt-2">
          <div
            onDragOver={handleUngroupedDragOver}
            onDragLeave={handleUngroupedDragLeave}
            onDrop={handleUngroupedDrop}
            className={clsx(
              "rounded-lg transition-all",
              isDragOverUngrouped && "bg-primary-100 ring-2 ring-primary-500",
            )}
          >
            <p className="px-3 py-1.5 text-xs font-medium text-gray-500 uppercase tracking-wide">
              Ungrouped
            </p>

            {/* Drop zone indicator */}
            {draggingConversationId &&
              (isDragOverUngrouped || ungroupedConversations.length === 0) && (
                <div className="px-3 pb-2">
                  <div
                    className={clsx(
                      "border-2 border-dashed rounded-lg p-8 text-center transition-colors min-h-[100px]",
                      isDragOverUngrouped
                        ? "border-primary-500 bg-primary-50"
                        : "border-gray-300 bg-gray-50",
                    )}
                  >
                    <p
                      className={clsx(
                        "text-sm font-medium",
                        isDragOverUngrouped
                          ? "text-primary-700"
                          : "text-gray-500",
                      )}
                    >
                      Drop here to ungroup
                    </p>
                  </div>
                </div>
              )}

            {/* Ungrouped conversations list */}
            {ungroupedConversations.length > 0 && (
              <div className="space-y-1 px-1">
                {ungroupedConversations.map((conversation) => (
                  <ConversationItem
                    key={conversation.id}
                    conversation={conversation}
                    isActive={conversation.id === currentConversationId}
                    onClick={() => onConversationClick(conversation.id)}
                    onDelete={() => onConversationDelete(conversation.id)}
                    onRename={() => onConversationRename(conversation.id)}
                    onShare={() => onConversationShare(conversation.id)}
                    onDragStart={handleDragStart}
                    onDragEnd={handleDragEnd}
                    isDragging={draggingConversationId === conversation.id}
                  />
                ))}
              </div>
            )}

            {/* Empty state */}
            {ungroupedConversations.length === 0 && !draggingConversationId && (
              <div className="px-3 py-2">
                <p className="text-xs text-gray-400 italic text-center">
                  No ungrouped conversations
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* EMPTY STATE (NO CONVERSATIONS AT ALL) */}
      {/* ============================================================ */}
      {safeConversations.length === 0 && (
        <div className="text-center py-8">
          <p className="text-sm text-gray-500">No conversations yet</p>
          <p className="text-xs text-gray-400 mt-1">
            Click "New Chat" to start
          </p>
        </div>
      )}
    </div>
  );
}