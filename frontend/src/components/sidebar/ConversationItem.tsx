/* path: frontend/src/components/sidebar/ConversationItem.tsx
   version: 4 - Enhanced selected item visibility */

import { MessageSquare, Trash2, Edit2, GripVertical } from "lucide-react";
import { Conversation } from "@/types/conversation";
import { ContextMenu } from "../ui/ContextMenu";
import clsx from "clsx";

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
  onRename: () => void;
  onDragStart?: (conversationId: string) => void;
  onDragEnd?: () => void;
  isDragging?: boolean;
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
  onDragStart,
  onDragEnd,
  isDragging = false,
}: ConversationItemProps) {
  const contextMenuItems = [
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
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("conversationId", conversation.id);
    onDragStart?.(conversation.id);
  };

  const handleDragEnd = () => {
    onDragEnd?.();
  };

  const handleClick = () => {
    console.log("[ConversationItem] Clicked:", conversation.id);
    onClick();
  };

  return (
    <ContextMenu items={contextMenuItems}>
      <div
        draggable
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        className={clsx(
          "group relative transition-opacity",
          isDragging && "opacity-50",
        )}
      >
        <button
          onClick={handleClick}
          className={clsx(
            "w-full px-3 py-2.5 rounded-lg text-left",
            "flex items-center gap-3 transition-all duration-150",
            "border-l-4",
            {
              // Active state - much more visible
              "bg-primary-100 border-primary-600 text-primary-900 shadow-sm":
                isActive,
              // Inactive state
              "border-transparent text-gray-700 hover:bg-gray-100": !isActive,
            },
          )}
        >
          {/* Drag handle */}
          <GripVertical
            size={16}
            className="flex-shrink-0 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing"
          />

          <MessageSquare
            size={18}
            className={clsx(
              "flex-shrink-0",
              isActive ? "text-primary-600" : "text-gray-600",
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
                isActive ? "text-primary-700" : "text-gray-500",
              )}
            >
              {conversation.messageCount} messages
            </p>
          </div>
        </button>
      </div>
    </ContextMenu>
  );
}
