/* path: src/types/conversation.ts
   version: 1 */

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  conversationId: string;
}

export interface Conversation {
  id: string;
  title: string;
  groupId?: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  ownerId: string; // User who created the conversation
  sharedWithGroupIds?: string[]; // User groups this conversation is shared with
  isShared?: boolean; // Helper flag
}

export interface ConversationGroup {
  id: string;
  name: string;
  createdAt: Date;
  conversationIds: string[];
}

// API request/response types
export interface CreateConversationRequest {
  title?: string;
  groupId?: string;
}

export interface CreateConversationResponse {
  conversation: Conversation;
}

export interface UpdateConversationRequest {
  title?: string;
  groupId?: string;
}

export interface CreateGroupRequest {
  name: string;
}

export interface CreateGroupResponse {
  group: ConversationGroup;
}

export interface ChatMessageRequest {
  message: string;
  conversationId: string;
}
