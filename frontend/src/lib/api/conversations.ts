/* path: frontend/src/lib/api/conversations.ts
   version: 1 */

import { apiClient } from "./client";
import { API_ENDPOINTS } from "../utils/constants";
import type {
  Conversation,
  ConversationGroup,
  CreateConversationRequest,
  CreateConversationResponse,
  UpdateConversationRequest,
  CreateGroupRequest,
  CreateGroupResponse,
  Message,
} from "@/types/conversation";

/**
 * API functions for conversation management
 */
export const conversationsApi = {
  /**
   * Get all conversations for the current user
   */
  getAll: async (): Promise<Conversation[]> => {
    const response = await apiClient.get<{ conversations: Conversation[] }>(
      API_ENDPOINTS.CONVERSATIONS,
    );
    return response.conversations;
  },

  /**
   * Get a single conversation by ID
   */
  getById: async (id: string): Promise<Conversation> => {
    const response = await apiClient.get<{ conversation: Conversation }>(
      API_ENDPOINTS.CONVERSATION_BY_ID(id),
    );
    return response.conversation;
  },

  /**
   * Get messages for a conversation
   */
  getMessages: async (conversationId: string): Promise<Message[]> => {
    const response = await apiClient.get<{ messages: Message[] }>(
      `${API_ENDPOINTS.CONVERSATION_BY_ID(conversationId)}/messages`,
    );
    return response.messages;
  },

  /**
   * Create a new conversation
   */
  create: async (data: CreateConversationRequest): Promise<Conversation> => {
    const response = await apiClient.post<CreateConversationResponse>(
      API_ENDPOINTS.CONVERSATIONS,
      data,
    );
    return response.conversation;
  },

  /**
   * Update a conversation
   */
  update: async (
    id: string,
    data: UpdateConversationRequest,
  ): Promise<Conversation> => {
    const response = await apiClient.put<{ conversation: Conversation }>(
      API_ENDPOINTS.CONVERSATION_BY_ID(id),
      data,
    );
    return response.conversation;
  },

  /**
   * Delete a conversation
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.CONVERSATION_BY_ID(id));
  },
};

/**
 * API functions for conversation groups management
 */
export const groupsApi = {
  /**
   * Get all groups for the current user
   */
  getAll: async (): Promise<ConversationGroup[]> => {
    const response = await apiClient.get<{ groups: ConversationGroup[] }>(
      API_ENDPOINTS.GROUPS,
    );
    return response.groups;
  },

  /**
   * Get a single group by ID
   */
  getById: async (id: string): Promise<ConversationGroup> => {
    const response = await apiClient.get<{ group: ConversationGroup }>(
      API_ENDPOINTS.GROUP_BY_ID(id),
    );
    return response.group;
  },

  /**
   * Create a new group
   */
  create: async (data: CreateGroupRequest): Promise<ConversationGroup> => {
    const response = await apiClient.post<CreateGroupResponse>(
      API_ENDPOINTS.GROUPS,
      data,
    );
    return response.group;
  },

  /**
   * Update a group name
   */
  update: async (id: string, name: string): Promise<ConversationGroup> => {
    const response = await apiClient.put<{ group: ConversationGroup }>(
      API_ENDPOINTS.GROUP_BY_ID(id),
      { name },
    );
    return response.group;
  },

  /**
   * Delete a group
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.GROUP_BY_ID(id));
  },

  /**
   * Add a conversation to a group
   */
  addConversation: async (
    groupId: string,
    conversationId: string,
  ): Promise<ConversationGroup> => {
    const response = await apiClient.post<{ group: ConversationGroup }>(
      `${API_ENDPOINTS.GROUP_BY_ID(groupId)}/conversations`,
      { conversationId },
    );
    return response.group;
  },

  /**
   * Remove conversation from group
   */
  removeFromGroup: async (
    groupId: string,
    conversationId: string,
  ): Promise<ConversationGroup> => {
    const response = await apiClient.delete<{ group: ConversationGroup }>(
      `${API_ENDPOINTS.GROUP_BY_ID(groupId)}/conversations/${conversationId}`,
    );
    return response.group;
  },

  /**
   * Share conversation with user groups
   */
  shareConversation: async (
    conversationId: string,
    groupIds: string[],
  ): Promise<Conversation> => {
    const response = await apiClient.post<{ conversation: Conversation }>(
      `${API_ENDPOINTS.CONVERSATION_BY_ID(conversationId)}/share`,
      { groupIds },
    );
    return response.conversation;
  },

  /**
   * Unshare conversation (remove from user groups)
   */
  unshareConversation: async (
    conversationId: string,
    groupIds: string[],
  ): Promise<Conversation> => {
    const response = await apiClient.post<{ conversation: Conversation }>(
      `${API_ENDPOINTS.CONVERSATION_BY_ID(conversationId)}/unshare`,
      { groupIds },
    );
    return response.conversation;
  },

  /**
   * Get conversations shared with user
   */
  getSharedConversations: async (): Promise<Conversation[]> => {
    const response = await apiClient.get<{ conversations: Conversation[] }>(
      "/api/conversations/shared",
    );
    return response.conversations;
  },
};
