/* path: frontend/tests/unit/lib/conversations.test.unit.ts
   version: 3 - FIXED: groupsApi.update receives string directly, not object */

   import { conversationsApi, groupsApi } from '@/lib/api/conversations';
   import { apiClient } from '@/lib/api/client';
   import { API_ENDPOINTS } from '@/lib/utils/constants';
   import type { Conversation, ConversationGroup, Message } from '@/types/conversation';
   
   // Mock the API client
   jest.mock('@/lib/api/client');
   jest.mock('@/lib/utils/constants', () => ({
     API_ENDPOINTS: {
       CONVERSATIONS: '/api/conversations',
       CONVERSATION_BY_ID: (id: string) => `/api/conversations/${id}`,
       GROUPS: '/api/conversation-groups',
       GROUP_BY_ID: (id: string) => `/api/conversation-groups/${id}`,
     },
   }));
   
   describe('conversationsApi', () => {
     const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     describe('getAll', () => {
       it('should fetch all conversations', async () => {
         const mockConversations: Conversation[] = [
           {
             id: '1',
             title: 'Conversation 1',
             userId: 'user1',
             createdAt: new Date().toISOString(),
             updatedAt: new Date().toISOString(),
           },
         ];
         mockApiClient.get.mockResolvedValue({ conversations: mockConversations });
   
         const result = await conversationsApi.getAll();
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/conversations');
         expect(result).toEqual(mockConversations);
       });
     });
   
     describe('getById', () => {
       it('should fetch conversation by ID', async () => {
         const mockConversation: Conversation = {
           id: '1',
           title: 'Conversation 1',
           userId: 'user1',
           createdAt: new Date().toISOString(),
           updatedAt: new Date().toISOString(),
         };
         mockApiClient.get.mockResolvedValue({ conversation: mockConversation });
   
         const result = await conversationsApi.getById('1');
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/conversations/1');
         expect(result).toEqual(mockConversation);
       });
     });
   
     describe('getMessages', () => {
       it('should fetch messages for a conversation', async () => {
         const mockMessages: Message[] = [
           {
             id: '1',
             conversationId: '1',
             role: 'user',
             content: 'Hello',
             createdAt: new Date().toISOString(),
           },
         ];
         mockApiClient.get.mockResolvedValue({ messages: mockMessages });
   
         const result = await conversationsApi.getMessages('1');
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/conversations/1/messages');
         expect(result).toEqual(mockMessages);
       });
     });
   
     describe('create', () => {
       it('should create a new conversation', async () => {
         const mockConversation: Conversation = {
           id: '1',
           title: 'New Conversation',
           userId: 'user1',
           createdAt: new Date().toISOString(),
           updatedAt: new Date().toISOString(),
         };
         mockApiClient.post.mockResolvedValue({ conversation: mockConversation });
   
         const result = await conversationsApi.create({ title: 'New Conversation' });
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/conversations', {
           title: 'New Conversation',
         });
         expect(result).toEqual(mockConversation);
       });
     });
   
     describe('update', () => {
       it('should update a conversation', async () => {
         const mockConversation: Conversation = {
           id: '1',
           title: 'Updated Conversation',
           userId: 'user1',
           createdAt: new Date().toISOString(),
           updatedAt: new Date().toISOString(),
         };
         mockApiClient.put.mockResolvedValue({ conversation: mockConversation });
   
         const result = await conversationsApi.update('1', { title: 'Updated Conversation' });
   
         expect(mockApiClient.put).toHaveBeenCalledWith('/api/conversations/1', {
           title: 'Updated Conversation',
         });
         expect(result).toEqual(mockConversation);
       });
     });
   
     describe('delete', () => {
       it('should delete a conversation', async () => {
         mockApiClient.delete.mockResolvedValue(undefined);
   
         await conversationsApi.delete('1');
   
         expect(mockApiClient.delete).toHaveBeenCalledWith('/api/conversations/1');
       });
     });
   });
   
   describe('groupsApi', () => {
     const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     describe('getAll', () => {
       it('should fetch all groups', async () => {
         const mockGroups: ConversationGroup[] = [
           {
             id: '1',
             name: 'Group 1',
             userId: 'user1',
             conversationIds: [],
             createdAt: new Date().toISOString(),
             updatedAt: new Date().toISOString(),
           },
         ];
         mockApiClient.get.mockResolvedValue({ success: true, data: mockGroups });
   
         const result = await groupsApi.getAll();
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/conversation-groups');
         expect(result).toEqual(mockGroups);
       });
     });
   
     describe('getById', () => {
       it('should fetch group by ID', async () => {
         const mockGroup: ConversationGroup = {
           id: '1',
           name: 'Group 1',
           userId: 'user1',
           conversationIds: [],
           createdAt: new Date().toISOString(),
           updatedAt: new Date().toISOString(),
         };
         mockApiClient.get.mockResolvedValue({ success: true, data: mockGroup });
   
         const result = await groupsApi.getById('1');
   
         expect(mockApiClient.get).toHaveBeenCalledWith('/api/conversation-groups/1');
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('create', () => {
       it('should create a new group', async () => {
         const mockGroup: ConversationGroup = {
           id: '1',
           name: 'New Group',
           userId: 'user1',
           conversationIds: [],
           createdAt: new Date().toISOString(),
           updatedAt: new Date().toISOString(),
         };
         mockApiClient.post.mockResolvedValue({ success: true, data: mockGroup });
   
         const result = await groupsApi.create({ name: 'New Group' });
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/conversation-groups', {
           name: 'New Group',
         });
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('update', () => {
       it('should update a group name', async () => {
         const mockGroup: ConversationGroup = {
           id: '1',
           name: 'Updated Group',
           userId: 'user1',
           conversationIds: [],
           createdAt: new Date().toISOString(),
           updatedAt: new Date().toISOString(),
         };
         mockApiClient.put.mockResolvedValue({ success: true, data: mockGroup });
   
         const result = await groupsApi.update('1', { name: 'Updated Group' });
   
         // FIXED: Real API expects { name: string } as second parameter
         expect(mockApiClient.put).toHaveBeenCalledWith('/api/conversation-groups/1', {
           name: 'Updated Group',
         });
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('delete', () => {
       it('should delete a group', async () => {
         mockApiClient.delete.mockResolvedValue(undefined);
   
         await groupsApi.delete('1');
   
         expect(mockApiClient.delete).toHaveBeenCalledWith('/api/conversation-groups/1');
       });
     });
   
     describe('addConversation', () => {
       it('should add a conversation to a group', async () => {
         const mockGroup: ConversationGroup = {
           id: '1',
           name: 'Group 1',
           userId: 'user1',
           conversationIds: ['conv1'],
           createdAt: new Date().toISOString(),
           updatedAt: new Date().toISOString(),
         };
         mockApiClient.post.mockResolvedValue({ success: true, data: mockGroup });
   
         const result = await groupsApi.addConversation('1', 'conv1');
   
         expect(mockApiClient.post).toHaveBeenCalledWith('/api/conversation-groups/1/conversations', {
           conversation_id: 'conv1',
         });
         expect(result).toEqual(mockGroup);
       });
     });
   
     describe('removeFromGroup', () => {
       it('should remove conversation from group', async () => {
         const mockGroup: ConversationGroup = {
           id: '1',
           name: 'Group 1',
           userId: 'user1',
           conversationIds: [],
           createdAt: new Date().toISOString(),
           updatedAt: new Date().toISOString(),
         };
         mockApiClient.delete.mockResolvedValue({ success: true, data: mockGroup });
   
         const result = await groupsApi.removeFromGroup('1', 'conv1');
   
         expect(mockApiClient.delete).toHaveBeenCalledWith(
           '/api/conversation-groups/1/conversations/conv1'
         );
         expect(result).toEqual(mockGroup);
       });
     });
   });