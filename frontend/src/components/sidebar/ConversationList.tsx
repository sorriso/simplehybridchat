/* path: frontend/src/components/sidebar/ConversationList.tsx
   version: 5 - Fixed: groups undefined guard */

   import { useState } from "react";
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
     onConversationClick: (id: string) => void;
     onConversationDelete: (id: string) => void;
     onConversationRename: (id: string) => void;
     onGroupDelete: (id: string) => void;
     onGroupRename: (id: string) => void;
     onMoveConversationToGroup?: (
       conversationId: string,
       groupId: string | null,
     ) => void;
   }
   
   /**
    * List of conversations organized by groups with drag & drop support
    */
   export function ConversationList({
     conversations,
     groups,
     currentConversationId,
     onConversationClick,
     onConversationDelete,
     onConversationRename,
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
   
     // Ungrouped conversations (no groupId)
     const ungroupedConversations = safeConversations.filter((c) => !c.groupId);
   
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
       console.log("[ConversationList] Drag over UNGROUPED");
       setIsDragOverUngrouped(true);
     };
   
     const handleUngroupedDragLeave = (e: React.DragEvent) => {
       e.preventDefault();
       e.stopPropagation();
       // Only set to false if we're leaving the container entirely
       const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
       if (
         e.clientX < rect.left ||
         e.clientX >= rect.right ||
         e.clientY < rect.top ||
         e.clientY >= rect.bottom
       ) {
         console.log("[ConversationList] Drag leave UNGROUPED");
         setIsDragOverUngrouped(false);
       }
     };
   
     const handleUngroupedDrop = (e: React.DragEvent) => {
       e.preventDefault();
       e.stopPropagation();
       setIsDragOverUngrouped(false);
   
       const conversationId = e.dataTransfer.getData("conversationId");
       console.log(
         "[ConversationList] Drop on UNGROUPED, conversationId:",
         conversationId,
       );
   
       if (conversationId && onMoveConversationToGroup) {
         console.log(
           "[ConversationList] Calling onMoveConversationToGroup with null",
         );
         onMoveConversationToGroup(conversationId, null); // null = ungrouped
       }
     };
   
     return (
       <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
         {/* Grouped conversations */}
         {safeGroups.map((group) => (
           <ConversationGroup
             key={group.id}
             group={group}
             conversations={safeConversations}
             currentConversationId={currentConversationId}
             onConversationClick={onConversationClick}
             onConversationDelete={onConversationDelete}
             onConversationRename={onConversationRename}
             onGroupDelete={() => onGroupDelete(group.id)}
             onGroupRename={() => onGroupRename(group.id)}
             onConversationDrop={handleConversationDrop}
             draggingConversationId={draggingConversationId}
             onDragStart={handleDragStart}
             onDragEnd={handleDragEnd}
           />
         ))}
   
         {/* Ungrouped conversations section - show when has items OR when dragging */}
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
   
               {/* Drop zone indicator when dragging and zone is empty or hovered */}
               {draggingConversationId &&
                 (isDragOverUngrouped || ungroupedConversations.length === 0) && (
                   <div className="px-3 pb-2">
                     <div
                       className={clsx(
                         "border-2 border-dashed rounded-lg p-6 text-center transition-colors",
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
                       onDragStart={handleDragStart}
                       onDragEnd={handleDragEnd}
                       isDragging={draggingConversationId === conversation.id}
                     />
                   ))}
                 </div>
               )}
   
               {/* Empty state when no ungrouped conversations and not dragging */}
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
   
         {/* Empty state */}
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