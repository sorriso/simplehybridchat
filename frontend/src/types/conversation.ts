/* path: frontend/src/types/conversation.ts
   version: 4 - FIXED: Renamed sharedWith to sharedWithGroupIds for consistency with backend and useConversations */

/**
 * Conversation metadata
 */
export interface Conversation {
  id: string;
  title: string;
  ownerId: string;
  groupId?: string;
  sharedWithGroupIds?: string[];
  isShared?: boolean;
  messageCount?: number; // Number of messages in conversation (optional for backward compatibility)
  createdAt: string;
  updatedAt: string;
}

/**
 * Conversation group (for sidebar organization)
 */
export interface ConversationGroup {
  id: string;
  name: string;
  ownerId: string;
  conversationIds: string[];
  createdAt: string;
}

/**
 * Message in a conversation
 */
export interface Message {
  id: string;
  conversationId: string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: string;
}

/**
 * API request types
 */
export interface CreateConversationRequest {
  title?: string;
  groupId?: string;
}

export interface UpdateConversationRequest {
  title?: string;
  groupId?: string | null;
}

export interface CreateGroupRequest {
  name: string;
}

/**
 * API response types
 */
export interface CreateConversationResponse {
  conversation: Conversation;
}

/**
 * FIXED v2: Backend returns {success: true, data: {...}}
 * Not {group: {...}}
 */
export interface CreateGroupResponse {
  success: boolean;
  data: ConversationGroup;
}
