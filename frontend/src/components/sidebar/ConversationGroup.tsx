/* path: frontend/src/components/sidebar/ConversationGroup.tsx
   version: 4.1
   
   Changes in v4.1:
   - FIX: onConversationRename signature changed to (id: string, currentTitle: string) => void
   - Reason: Sidebar.handleConversationRename needs the title to prefill the rename modal
   - Updated onRename call to pass conversation.title
   
   Changes in v4.0:
   - ADDED: onConversationUngroup prop to remove conversations from group
   - ADDED: Pass onUngroup to ConversationItem components
   - COMPACT: Reduced padding on group header (py-2 → py-1.5)
   - SMALLER: Group font (text-sm → text-xs)
*/

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
  onConversationRename: (id: string, currentTitle: string) => void; // FIXED: Added currentTitle
  onConversationShare: (id: string) => void;
  onConversationUngroup: (id: string) => void;
  onGroupDelete: () => void;
  onGroupRename: () => void;
  onConversationDrop?: (conversationId: string, groupId: string) => void;
  draggingConversationId?: string | null;
  onDragStart?: (conversationId: string) => void;
  onDragEnd?: () => void;
}

export function ConversationGroup({
  group,
  conversations,
  currentConversationId,
  onConversationClick,
  onConversationDelete,
  onConversationRename,
  onConversationShare,
  onConversationUngroup,
  onGroupDelete,
  onGroupRename,
  onConversationDrop,
  draggingConversationId,
  onDragStart,
  onDragEnd,
}: ConversationGroupProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isDragOver, setIsDragOver] = useState(false);

  const groupConversations = conversations.filter((c) => c.groupId === group.id);

  const contextMenuItems = [
    {
      label: "Rename",
      onClick: onGroupRename,
      icon: <Edit2 size={14} />,
    },
    {
      label: "Delete",
      onClick: onGroupDelete,
      icon: <Trash2 size={14} />,
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
              "w-full px-2.5 py-1.5 rounded-lg text-left",
              "flex items-center gap-2 transition-colors",
              "hover:bg-gray-100 text-gray-700",
            )}
          >
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <Folder size={14} />
            <span className="text-xs font-medium flex-1">{group.name}</span>
            <span className="text-[11px] text-gray-500">
              {groupConversations.length}
            </span>
          </button>

          {isDragOver && draggingConversationId && (
            <div className="px-2.5 py-1">
              <p className="text-[11px] text-primary-600">
                Drop here to move to {group.name}
              </p>
            </div>
          )}
        </div>
      </ContextMenu>

      {isExpanded && (
        <div className="ml-3 mt-1 space-y-1">
          {groupConversations.length === 0 ? (
            <p className="text-[11px] text-gray-400 italic px-2.5 py-1.5">
              No conversations in this group
            </p>
          ) : (
            groupConversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === currentConversationId}
                onClick={() => onConversationClick(conversation.id)}
                onDelete={() => onConversationDelete(conversation.id)}
                onRename={() => onConversationRename(conversation.id, conversation.title)}
                onShare={() => onConversationShare(conversation.id)}
                onUngroup={() => onConversationUngroup(conversation.id)}
                onDragStart={onDragStart}
                onDragEnd={onDragEnd}
                isDragging={conversation.id === draggingConversationId}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}