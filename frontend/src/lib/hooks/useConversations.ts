/* path: frontend/src/lib/hooks/useConversations.ts
   version: 19
   
   Changes in v19:
   - FIXED: Removed duplicate keys in return statement (incrementMessageCount, computeMessageCount)
   - FIXED: Removed console.log statements (ESLint no-console rule)
   - Kept only console.error for actual error logging
   
   Changes in v18:
   - CRITICAL FIX: Preserve messageCount when sharing/unsharing conversations
   - FIXED: shareConversation() now keeps existing messageCount
   - FIXED: unshareConversation() now keeps existing messageCount
   - Reason: Backend doesn't return messageCount, was being reset to 0
   
   Changes in v17:
   - ADDED: Load shared conversations in loadData()
   - ADDED: Merge owned + shared conversations
   - ADDED: shareConversation() method
   - ADDED: unshareConversation() method
   - Reason: Support viewing and managing shared conversations
*/

import { useState, useEffect, useCallback } from "react";
import { conversationsApi, groupsApi } from "../api/conversations";
import type { Conversation, ConversationGroup } from "@/types/conversation";
import { storage } from "../utils/storage";
import { STORAGE_KEYS } from "../utils/constants";

// Cache key for message counts in localStorage
const MESSAGE_COUNTS_CACHE_KEY = "message_counts_cache";

/**
 * Message counts cache structure: { [conversationId]: count }
 */
type MessageCountsCache = Record<string, number>;

/**
 * Load message counts from localStorage cache
 */
function loadMessageCountsCache(): MessageCountsCache {
  try {
    const cached = localStorage.getItem(MESSAGE_COUNTS_CACHE_KEY);
    return cached ? JSON.parse(cached) : {};
  } catch (error) {
    console.error("[useConversations] Failed to load message counts cache:", error);
    return {};
  }
}

/**
 * Save message counts to localStorage cache
 */
function saveMessageCountsCache(cache: MessageCountsCache): void {
  try {
    localStorage.setItem(MESSAGE_COUNTS_CACHE_KEY, JSON.stringify(cache));
  } catch (error) {
    console.error("[useConversations] Failed to save message counts cache:", error);
  }
}

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

  // Wrapper to trigger state update
  const setCurrentConversationId = useCallback((id: string | null) => {
    setCurrentConversationIdState(id);
  }, []);

  // Load conversations and groups on mount - but only if authenticated
  useEffect(() => {
    // Check if auth token exists before loading
    const token = storage.getAuthToken();
    if (token) {
      loadData();
    } else {
      setLoading(false);
    }
  }, []);

  // Persist current conversation ID
  useEffect(() => {
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

     // Load owned conversations, shared conversations, and groups in parallel
     const [conversationsData, sharedConversationsData, groupsData] = await Promise.all([
       conversationsApi.getAll(),
       conversationsApi.getSharedConversations(),
       groupsApi.getAll(),
     ]);

     // Merge owned and shared conversations (shared ones marked with isShared flag)
     const allConversations = [
       ...conversationsData,
       ...sharedConversationsData.map(conv => ({ ...conv, isShared: true }))
     ];
      // Restore message counts from localStorage cache (temporary display)
      const cache = loadMessageCountsCache();
      const conversationsWithCounts = allConversations.map(conv => ({
        ...conv,
        messageCount: cache[conv.id] ?? conv.messageCount ?? 0
      }));

      setConversations(conversationsWithCounts);
      setGroups(groupsData);

      // Restore current conversation from storage
      const savedConversationId = storage.get<string>(
        STORAGE_KEYS.CURRENT_CONVERSATION,
      );
      if (
        savedConversationId &&
        allConversations.find((c) => c.id === savedConversationId)
      ) {
        setCurrentConversationIdState(savedConversationId);
      }
      
      // Recompute real message counts in background (after initial display)
      const countPromises = allConversations.map(async (conv) => {
        try {
          const messages = await conversationsApi.getMessages(conv.id);
          return { id: conv.id, count: messages.length };
        } catch (error) {
          console.error(`[useConversations] Failed to count messages for ${conv.id}:`, error);
          return { id: conv.id, count: cache[conv.id] ?? 0 }; // Fallback to cache
        }
      });
      
      const counts = await Promise.all(countPromises);
      
      // Update state with real counts
      setConversations(prev =>
        prev.map(conv => {
          const realCount = counts.find(c => c.id === conv.id);
          return realCount ? { ...conv, messageCount: realCount.count } : conv;
        })
      );
      
      // Update cache with real counts
      const newCache = { ...cache };
      counts.forEach(({ id, count }) => {
        newCache[id] = count;
      });
      saveMessageCountsCache(newCache);
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
        const requestData = {
          title,
          groupId,
        };
        
        const newConversation = await conversationsApi.create(requestData);
        
        // Initialize message count to 0 for new conversation
        const conversationWithCount = { ...newConversation, messageCount: 0 };
        setConversations((prev) => [conversationWithCount, ...prev]);
        
        // Save to cache
        const cache = loadMessageCountsCache();
        cache[newConversation.id] = 0;
        saveMessageCountsCache(cache);
        
        setCurrentConversationIdState(newConversation.id);
        return conversationWithCount;
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
    async (id: string, data: { title?: string; groupId?: string | null }) => {
      try {
        const updated = await conversationsApi.update(id, data);
        // Preserve messageCount from current state when updating
        setConversations((prev) =>
          prev.map((c) => 
            c.id === id 
              ? { ...updated, messageCount: c.messageCount } 
              : c
          ),
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
        
        // Optimistic update: preserve message counts
        setConversations(prev =>
          prev.map(conv =>
            conv.id === conversationId
              ? { ...conv, groupId }
              : conv
          )
        );
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
        
        // Optimistic update: preserve message counts
        setConversations(prev =>
          prev.map(conv =>
            conv.id === conversationId
              ? { ...conv, groupId: undefined }
              : conv
          )
        );
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to remove from group",
        );
        throw err;
      }
    },
    [],
  );

  /**
   * Increment message count locally (optimistic update)
   * Called after each message is sent to update UI immediately
   * @param conversationId - ID of conversation to update
   */
  const incrementMessageCount = useCallback((conversationId: string) => {
    setConversations(prev => {
      const updated = prev.map(conv => 
        conv.id === conversationId 
          ? { ...conv, messageCount: (conv.messageCount || 0) + 2 }  // +2 (user + assistant)
          : conv
      );
      
      // Update cache in localStorage
      const cache = loadMessageCountsCache();
      const updatedConv = updated.find(c => c.id === conversationId);
      if (updatedConv && updatedConv.messageCount !== undefined) {
        cache[conversationId] = updatedConv.messageCount;
        saveMessageCountsCache(cache);
      }
      
      return updated;
    });
  }, []);

  /**
   * Compute real message count from messages API
   * Fetches messages and updates both state and cache
   * @param conversationId - ID of conversation to compute
   */
  const computeMessageCount = useCallback(async (conversationId: string) => {
    try {
      const messages = await conversationsApi.getMessages(conversationId);
      const count = messages.length;
      
      // Update state
      setConversations(prev =>
        prev.map(conv =>
          conv.id === conversationId
            ? { ...conv, messageCount: count }
            : conv
        )
      );
      
      // Update cache
      const cache = loadMessageCountsCache();
      cache[conversationId] = count;
      saveMessageCountsCache(cache);
      
      return count;
    } catch (error) {
      console.error(`[useConversations] Failed to compute message count for ${conversationId}:`, error);
      return 0;
    }
  }, []);


 /**
  * Share conversation with user groups
  */
 const shareConversation = useCallback(async (
   conversationId: string,
   groupIds: string[]
 ) => {
   try {
     const updated = await conversationsApi.shareConversation(conversationId, groupIds);
     setConversations(prev =>
       prev.map(conv =>
         conv.id === conversationId
           ? { 
               ...conv,  // Keep existing fields (especially messageCount)
               ...updated,  // Apply backend updates
               messageCount: conv.messageCount ?? updated.messageCount ?? 0,  // Preserve count
               isShared: (updated.sharedWithGroupIds?.length ?? 0) > 0
             }
           : conv
       )
     );
   } catch (error) {
     console.error("[useConversations] Failed to share conversation:", error);
     throw error;
   }
 }, []);

 /**
  * Unshare conversation from user groups
  */
 const unshareConversation = useCallback(async (
   conversationId: string,
   groupIds: string[]
 ) => {
   try {
     const updated = await conversationsApi.unshareConversation(conversationId, groupIds);
     setConversations(prev =>
       prev.map(conv =>
         conv.id === conversationId
           ? { 
               ...conv,  // Keep existing fields (especially messageCount)
               ...updated,  // Apply backend updates
               messageCount: conv.messageCount ?? updated.messageCount ?? 0,  // Preserve count
               isShared: (updated.sharedWithGroupIds?.length ?? 0) > 0
             }
           : conv
       )
     );
   } catch (error) {
     console.error("[useConversations] Failed to unshare conversation:", error);
     throw error;
   }
 }, []);

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
    incrementMessageCount,
    computeMessageCount,
    shareConversation,
    unshareConversation,
    reload: loadData,
  };
}