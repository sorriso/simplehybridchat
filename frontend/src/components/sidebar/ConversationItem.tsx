/* path: frontend/src/components/sidebar/ConversationItem.tsx
   version: 8.0
   
   Changes in v8.0:
   - COMPACT DESIGN: Reduced padding (py-2.5 → py-1.5)
   - SMALLER FONTS: Title (text-sm → text-xs), Messages count (text-xs → text-[11px])
   - SMALLER ICONS: 18px → 16px (MessageSquare), 16px → 14px (GripVertical)
   - ADDED: onUngroup prop to remove conversation from group
   - ADDED: "Remove from group" option in context menu (only if conversation is in a group)
   - Better space efficiency without losing readability
*/

import {
  MessageSquare,
  Trash2,
  Edit2,
  GripVertical,
  Share2,
  FolderX,
} from "lucide-react";
import { Conversation } from "@/types/conversation";
import { ContextMenu } from "../ui/ContextMenu";
import clsx from "clsx";

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
  onRename: () => void;
  onShare?: () => void;
  onUngroup?: () => void; // NEW: Remove from group
  onDragStart?: (conversationId: string) => void;
  onDragEnd?: () => void;
  isDragging?: boolean;
  readOnly?: boolean;
}

export function ConversationItem({
  conversation,
  isActive,
  onClick,
  onDelete,
  onRename,
  onShare,
  onUngroup,
  onDragStart,
  onDragEnd,
  isDragging = false,
  readOnly = false,
}: ConversationItemProps) {
  // Check if conversation is in a group
  const isInGroup = !!conversation.groupId;

  const contextMenuItems = readOnly
    ? []
    : [
        ...(onShare
          ? [
              {
                label: "Share",
                onClick: onShare,
                icon: <Share2 size={14} />,
              },
            ]
          : []),
        // NEW: Add "Remove from group" if conversation is in a group
        ...(isInGroup && onUngroup
          ? [
              {
                label: "Remove from group",
                onClick: onUngroup,
                icon: <FolderX size={14} />,
              },
            ]
          : []),
        {
          label: "Rename",
          onClick: onRename,
          icon: <Edit2 size={14} />,
        },
        {
          label: "Delete",
          onClick: onDelete,
          icon: <Trash2 size={14} />,
          variant: "danger" as const,
        },
      ];

  const handleDragStart = (e: React.DragEvent) => {
    if (readOnly) return;
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("conversationId", conversation.id);
    onDragStart?.(conversation.id);
  };

  const handleDragEnd = () => {
    if (readOnly) return;
    onDragEnd?.();
  };

  return (
    <ContextMenu items={contextMenuItems}>
      <div
        draggable={!readOnly}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        className={clsx(
          "group relative transition-opacity",
          isDragging && "opacity-50",
        )}
      >
        <button
          onClick={onClick}
          className={clsx(
            "w-full px-2.5 py-1.5 rounded-lg text-left",
            "flex items-center gap-2.5 transition-all duration-150",
            "border-l-4",
            {
              "bg-blue-50 border-blue-400 text-blue-900 shadow-sm ring-1 ring-blue-200": isActive,
              "border-transparent text-gray-700 hover:bg-gray-100": !isActive,
            },
          )}
        >
          {!readOnly && (
            <GripVertical
              size={14}
              className="flex-shrink-0 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing"
            />
          )}

          <MessageSquare
            size={16}
            className={clsx(
              "flex-shrink-0",
              isActive ? "text-blue-500" : "text-gray-600",
            )}
          />
          <div className="flex-1 min-w-0">
            <p
              className={clsx(
                "text-xs font-medium truncate leading-tight",
                isActive && "font-semibold",
              )}
            >
              {conversation.title || "New Conversation"}
            </p>
            <p
              className={clsx(
                "text-[11px] truncate leading-tight mt-0.5",
                isActive ? "text-blue-600" : "text-gray-500",
              )}
            >
              {conversation.messageCount ?? 0} messages
            </p>
          </div>
        </button>
      </div>
    </ContextMenu>
  );
}