/* path: src/lib/hooks/useConversations.ts
   version: 4 - Added debug logging for conversation selection */

import { useState, useEffect, useCallback } from "react";
import { conversationsApi, groupsApi } from "../api/conversations";
import type { Conversation, ConversationGroup } from "@/types/conversation";
import { storage } from "../utils/storage";
import { STORAGE_KEYS } from "../utils/constants";

/**
 * Hook for managing conversations and groups
 */
export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [groups, setGroups] = useState<ConversationGroup[]>([]);
  const [currentConversationId, setCurrentConversationIdState] = useState<
    string | null
  >(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Wrapper with debug logging
  const setCurrentConversationId = useCallback((id: string | null) => {
    console.log("[useConversations] setCurrentConversationId called with:", id);
    setCurrentConversationIdState(id);
    console.log("[useConversations] State update dispatched");
  }, []);

  // Load conversations and groups on mount
  useEffect(() => {
    loadData();
  }, []);

  // Persist current conversation ID
  useEffect(() => {
    console.log(
      "[useConversations] useEffect - currentConversationId changed to:",
      currentConversationId,
    );
    if (currentConversationId) {
      storage.set(STORAGE_KEYS.CURRENT_CONVERSATION, currentConversationId);
    }
  }, [currentConversationId]);

  /**
   * Load all conversations and groups
   */
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [conversationsData, groupsData] = await Promise.all([
        conversationsApi.getAll(),
        groupsApi.getAll(),
      ]);

      setConversations(conversationsData);
      setGroups(groupsData);

      // Restore current conversation from storage
      const savedConversationId = storage.get<string>(
        STORAGE_KEYS.CURRENT_CONVERSATION,
      );
      if (
        savedConversationId &&
        conversationsData.find((c) => c.id === savedConversationId)
      ) {
        setCurrentConversationIdState(savedConversationId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
      console.error("Error loading conversations:", err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Create a new conversation
   */
  const createConversation = useCallback(
    async (title?: string, groupId?: string) => {
      try {
        const newConversation = await conversationsApi.create({
          title,
          groupId,
        });
        setConversations((prev) => [newConversation, ...prev]);
        setCurrentConversationIdState(newConversation.id);
        return newConversation;
      } catch (err) {
        const errorMessage = "Failed to create conversation";
        setError(errorMessage);
        throw err;
      }
    },
    [],
  );

  /**
   * Delete a conversation
   */
  const deleteConversation = useCallback(
    async (id: string) => {
      try {
        await conversationsApi.delete(id);
        setConversations((prev) => prev.filter((c) => c.id !== id));

        // If deleting current conversation, clear selection
        if (currentConversationId === id) {
          setCurrentConversationIdState(null);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to delete conversation",
        );
        throw err;
      }
    },
    [currentConversationId],
  );

  /**
   * Update conversation (e.g., change title or group)
   */
  const updateConversation = useCallback(
    async (id: string, data: { title?: string; groupId?: string }) => {
      try {
        const updated = await conversationsApi.update(id, data);
        setConversations((prev) =>
          prev.map((c) => (c.id === id ? updated : c)),
        );
        return updated;
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to update conversation",
        );
        throw err;
      }
    },
    [],
  );

  /**
   * Create a new group
   */
  const createGroup = useCallback(async (name: string) => {
    try {
      const newGroup = await groupsApi.create({ name });
      setGroups((prev) => [...prev, newGroup]);
      return newGroup;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create group");
      throw err;
    }
  }, []);

  /**
   * Delete a group
   */
  const deleteGroup = useCallback(async (id: string) => {
    try {
      await groupsApi.delete(id);
      setGroups((prev) => prev.filter((g) => g.id !== id));

      // Remove group association from conversations
      setConversations((prev) =>
        prev.map((c) => (c.groupId === id ? { ...c, groupId: undefined } : c)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete group");
      throw err;
    }
  }, []);

  /**
   * Add conversation to group
   */
  const addToGroup = useCallback(
    async (conversationId: string, groupId: string) => {
      try {
        await groupsApi.addConversation(groupId, conversationId);
        await loadData(); // Reload to get updated state
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add to group");
        throw err;
      }
    },
    [],
  );

  /**
   * Remove conversation from group
   */
  const removeFromGroup = useCallback(
    async (conversationId: string, groupId: string) => {
      try {
        await groupsApi.removeFromGroup(groupId, conversationId);
        await loadData(); // Reload to get updated state
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to remove from group",
        );
        throw err;
      }
    },
    [],
  );

  return {
    // State
    conversations,
    groups,
    currentConversationId,
    loading,
    error,

    // Actions
    setCurrentConversationId,
    createConversation,
    deleteConversation,
    updateConversation,
    createGroup,
    deleteGroup,
    addToGroup,
    removeFromGroup,
    reload: loadData,
  };
}
