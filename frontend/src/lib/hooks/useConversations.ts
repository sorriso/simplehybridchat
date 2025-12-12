/* path: frontend/src/lib/hooks/useConversations.ts
   version: 5 - Only load data when authenticated */

   import { useState, useEffect, useCallback } from "react";
   import { conversationsApi, groupsApi } from "../api/conversations";
   import type { Conversation, ConversationGroup } from "@/types/conversation";
   import { storage } from "../utils/storage";
   import { STORAGE_KEYS } from "../utils/constants";
   import { useAuth } from "./useAuth";
   
   /**
    * Hook for managing conversations and groups
    */
   export function useConversations() {
     const { isAuthenticated, loading: authLoading } = useAuth();
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
   
     // v5.0: Load conversations and groups ONLY when authenticated
     useEffect(() => {
       // Wait for auth to complete
       if (authLoading) {
         return;
       }
   
       // Only load data if authenticated
       if (isAuthenticated) {
         loadData();
       } else {
         // Not authenticated - reset state
         setConversations([]);
         setGroups([]);
         setCurrentConversationIdState(null);
         setLoading(false);
       }
     }, [isAuthenticated, authLoading]);
   
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
       async (title?: string): Promise<Conversation> => {
         const newConversation = await conversationsApi.create(title);
         setConversations((prev) => [newConversation, ...prev]);
         setCurrentConversationIdState(newConversation.id);
         return newConversation;
       },
       [],
     );
   
     /**
      * Update conversation
      */
     const updateConversation = useCallback(
       async (id: string, updates: Partial<Conversation>): Promise<void> => {
         const updated = await conversationsApi.update(id, updates);
         setConversations((prev) =>
           prev.map((c) => (c.id === id ? { ...c, ...updated } : c)),
         );
       },
       [],
     );
   
     /**
      * Delete conversation
      */
     const deleteConversation = useCallback(
       async (id: string): Promise<void> => {
         await conversationsApi.delete(id);
         setConversations((prev) => prev.filter((c) => c.id !== id));
   
         // Clear current conversation if it was deleted
         if (currentConversationId === id) {
           setCurrentConversationIdState(null);
           storage.remove(STORAGE_KEYS.CURRENT_CONVERSATION);
         }
       },
       [currentConversationId],
     );
   
     /**
      * Share conversation
      */
     const shareConversation = useCallback(
       async (
         conversationId: string,
         shareWith: string[],
       ): Promise<Conversation> => {
         const updated = await conversationsApi.share(conversationId, shareWith);
         setConversations((prev) =>
           prev.map((c) => (c.id === conversationId ? updated : c)),
         );
         return updated;
       },
       [],
     );
   
     /**
      * Get conversation by ID
      */
     const getConversation = useCallback(
       (id: string): Conversation | undefined => {
         return conversations.find((c) => c.id === id);
       },
       [conversations],
     );
   
     /**
      * Get conversations in a group
      */
     const getConversationsByGroup = useCallback(
       (groupId: string): Conversation[] => {
         return conversations.filter((c) => c.groupId === groupId);
       },
       [conversations],
     );
   
     /**
      * Get conversations without a group
      */
     const getUngroupedConversations = useCallback((): Conversation[] => {
       return conversations.filter((c) => !c.groupId);
     }, [conversations]);
   
     /**
      * Create a new group
      */
     const createGroup = useCallback(async (name: string) => {
       const newGroup = await groupsApi.create(name);
       setGroups((prev) => [...prev, newGroup]);
       return newGroup;
     }, []);
   
     /**
      * Update group
      */
     const updateGroup = useCallback(
       async (id: string, updates: Partial<ConversationGroup>) => {
         const updated = await groupsApi.update(id, updates);
         setGroups((prev) => prev.map((g) => (g.id === id ? updated : g)));
       },
       [],
     );
   
     /**
      * Delete group
      */
     const deleteGroup = useCallback(async (id: string) => {
       await groupsApi.delete(id);
       setGroups((prev) => prev.filter((g) => g.id !== id));
   
       // Ungroup conversations in this group
       setConversations((prev) =>
         prev.map((c) => (c.groupId === id ? { ...c, groupId: undefined } : c)),
       );
     }, []);
   
     /**
      * Move conversation to group
      */
     const moveToGroup = useCallback(
       async (conversationId: string, groupId: string | null) => {
         const updated = await conversationsApi.update(conversationId, { groupId });
         setConversations((prev) =>
           prev.map((c) => (c.id === conversationId ? { ...c, groupId } : c)),
         );
       },
       [],
     );
   
     return {
       // State
       conversations,
       groups,
       currentConversationId,
       loading: loading || authLoading, // v5.0: Include auth loading
       error,
   
       // Conversation actions
       createConversation,
       updateConversation,
       deleteConversation,
       shareConversation,
       getConversation,
       getConversationsByGroup,
       getUngroupedConversations,
       setCurrentConversationId,
   
       // Group actions
       createGroup,
       updateGroup,
       deleteGroup,
       moveToGroup,
   
       // Utility
       reload: loadData,
     };
   }