/* path: frontend/src/components/sidebar/ConversationItem.tsx
   version: 7
   
   Changes in v7:
   - ADDED: onShare prop for sharing conversations
   - ADDED: readOnly prop to disable drag/delete/rename for shared conversations
   - ADDED: Share option in context menu (when not readOnly)
   - Reason: Support shared conversations display with proper restrictions
*/

import {
  MessageSquare,
  Trash2,
  Edit2,
  GripVertical,
  Share2,
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
  onDragStart?: (conversationId: string) => void;
  onDragEnd?: () => void;
  isDragging?: boolean;
  readOnly?: boolean;
}

/**
 * Single conversation item in the sidebar with drag functionality
 */
export function ConversationItem({
  conversation,
  isActive,
  onClick,
  onDelete,
  onRename,
  onShare,
  onDragStart,
  onDragEnd,
  isDragging = false,
  readOnly = false,
}: ConversationItemProps) {
  // Build context menu items based on readOnly state
  const contextMenuItems = readOnly
    ? [] // No context menu for read-only conversations
    : [
        ...(onShare
          ? [
              {
                label: "Share",
                onClick: onShare,
                icon: <Share2 size={16} />,
              },
            ]
          : []),
        {
          label: "Rename",
          onClick: onRename,
          icon: <Edit2 size={16} />,
        },
        {
          label: "Delete",
          onClick: onDelete,
          icon: <Trash2 size={16} />,
          variant: "danger" as const,
        },
      ];

  const handleDragStart = (e: React.DragEvent) => {
    if (readOnly) return; // Prevent dragging read-only conversations
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
            "w-full px-3 py-2.5 rounded-lg text-left",
            "flex items-center gap-3 transition-all duration-150",
            "border-l-4",
            {
              // Active state - bleu pastel visible
              "bg-blue-50 border-blue-400 text-blue-900 shadow-md ring-1 ring-blue-200":
                isActive,
              // Inactive state
              "border-transparent text-gray-700 hover:bg-gray-100": !isActive,
            },
          )}
        >
          {/* Drag handle - hidden for read-only */}
          {!readOnly && (
            <GripVertical
              size={16}
              className="flex-shrink-0 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing"
            />
          )}

          <MessageSquare
            size={18}
            className={clsx(
              "flex-shrink-0",
              isActive ? "text-blue-500" : "text-gray-600",
            )}
          />
          <div className="flex-1 min-w-0">
            <p
              className={clsx(
                "text-sm font-medium truncate",
                isActive && "font-semibold",
              )}
            >
              {conversation.title || "New Conversation"}
            </p>
            <p
              className={clsx(
                "text-xs truncate",
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
