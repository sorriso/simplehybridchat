/* path: frontend/src/components/sidebar/ConversationGroup.tsx
   version: 2 */

import { useState } from "react";
import { ChevronDown, ChevronRight, Folder, Trash2, Edit2 } from "lucide-react";
import {
  ConversationGroup as ConversationGroupType,
  Conversation,
} from "@/types/conversation";
import { ConversationItem } from "./ConversationItem";
import { ContextMenu } from "../ui/ContextMenu";
import clsx from "clsx";

interface ConversationGroupProps {
  group: ConversationGroupType;
  conversations: Conversation[];
  currentConversationId: string | null;
  onConversationClick: (id: string) => void;
  onConversationDelete: (id: string) => void;
  onConversationRename: (id: string) => void;
  onGroupDelete: () => void;
  onGroupRename: () => void;
  onConversationDrop?: (conversationId: string, groupId: string) => void;
  draggingConversationId?: string | null;
  onDragStart?: (conversationId: string) => void;
  onDragEnd?: () => void;
}

/**
 * Collapsible group of conversations with drop zone functionality
 */
export function ConversationGroup({
  group,
  conversations,
  currentConversationId,
  onConversationClick,
  onConversationDelete,
  onConversationRename,
  onGroupDelete,
  onGroupRename,
  onConversationDrop,
  draggingConversationId,
  onDragStart,
  onDragEnd,
}: ConversationGroupProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isDragOver, setIsDragOver] = useState(false);

  // Filter conversations that belong to this group
  const groupConversations = conversations.filter(
    (c) => c.groupId === group.id,
  );

  const contextMenuItems = [
    {
      label: "Rename",
      onClick: onGroupRename,
      icon: <Edit2 size={16} />,
    },
    {
      label: "Delete",
      onClick: onGroupDelete,
      icon: <Trash2 size={16} />,
      variant: "danger" as const,
    },
  ];

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const conversationId = e.dataTransfer.getData("conversationId");
    if (conversationId && onConversationDrop) {
      onConversationDrop(conversationId, group.id);
    }
  };

  return (
    <div className="mb-1">
      {/* Group header */}
      <ContextMenu items={contextMenuItems}>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={clsx(
            "rounded-lg transition-colors",
            isDragOver && "bg-primary-100 ring-2 ring-primary-500",
          )}
        >
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={clsx(
              "w-full px-3 py-2 rounded-lg text-left",
              "flex items-center gap-2 transition-colors",
              "hover:bg-gray-100 text-gray-700",
            )}
          >
            {isExpanded ? (
              <ChevronDown size={16} className="flex-shrink-0" />
            ) : (
              <ChevronRight size={16} className="flex-shrink-0" />
            )}
            <Folder size={16} className="flex-shrink-0" />
            <span className="text-sm font-medium truncate">{group.name}</span>
            <span className="text-xs text-gray-500 ml-auto">
              ({groupConversations.length})
            </span>
          </button>

          {/* Drop zone indicator */}
          {isDragOver && draggingConversationId && (
            <div className="px-3 pb-2">
              <div className="border-2 border-dashed border-primary-500 rounded-lg p-4 text-center">
                <p className="text-sm text-primary-700 font-medium">
                  Drop here to move to {group.name}
                </p>
              </div>
            </div>
          )}
        </div>
      </ContextMenu>

      {/* Group conversations */}
      {isExpanded && (
        <div className="ml-4 mt-1 space-y-1">
          {groupConversations.map((conversation) => (
            <ConversationItem
              key={conversation.id}
              conversation={conversation}
              isActive={conversation.id === currentConversationId}
              onClick={() => onConversationClick(conversation.id)}
              onDelete={() => onConversationDelete(conversation.id)}
              onRename={() => onConversationRename(conversation.id)}
              onDragStart={onDragStart}
              onDragEnd={onDragEnd}
              isDragging={draggingConversationId === conversation.id}
            />
          ))}
          {groupConversations.length === 0 && (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={clsx(
                "px-3 py-4 rounded-lg transition-colors",
                isDragOver
                  ? "bg-primary-50 border-2 border-dashed border-primary-500"
                  : "bg-gray-50",
              )}
            >
              <p className="text-xs text-gray-500 italic text-center">
                {isDragOver ? "Drop conversation here" : "No conversations"}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
