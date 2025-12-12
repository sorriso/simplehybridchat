// path: frontend/tests/unit/hooks/useConversations.test.unit.ts
// version: 10

import { renderHook, act, waitFor } from '@testing-library/react'
import { useConversations } from '@/lib/hooks/useConversations'

// Mock the conversations API
jest.mock('@/lib/api/conversations', () => ({
  conversationsApi: {
    getAll: jest.fn(),
    getMessages: jest.fn(),
    getSharedConversations: jest.fn(),
    create: jest.fn(),
    delete: jest.fn(),
    update: jest.fn(),
  },
  groupsApi: {
    getAll: jest.fn(),
    create: jest.fn(),
    delete: jest.fn(),
    update: jest.fn(),
    addConversation: jest.fn(),
    removeFromGroup: jest.fn(),
  },
}))

// Mock storage
jest.mock('@/lib/utils/storage', () => ({
  storage: {
    getAuthToken: jest.fn(),
    get: jest.fn(),
    set: jest.fn(),
  },
}))

// Mock constants
jest.mock('@/lib/utils/constants', () => ({
  STORAGE_KEYS: {
    CURRENT_CONVERSATION: 'current_conversation',
  },
}))

// Import mocked modules
import { conversationsApi, groupsApi } from '@/lib/api/conversations'
import { storage } from '@/lib/utils/storage'

const mockConversationsApi = conversationsApi as jest.Mocked<typeof conversationsApi>
const mockGroupsApi = groupsApi as jest.Mocked<typeof groupsApi>
const mockStorage = storage as jest.Mocked<typeof storage>

// Mock data
const mockConversation = {
  id: 'conv-1',
  title: 'Test Conversation',
  groupId: null as string | null | undefined,
  createdAt: new Date('2024-01-15'),
  updatedAt: new Date('2024-01-15'),
  messageCount: 5,
  ownerId: 'user-1',
}

const mockConversations = [
  mockConversation,
  {
    id: 'conv-2',
    title: 'Second Conversation',
    groupId: 'group-1',
    createdAt: new Date('2024-01-14'),
    updatedAt: new Date('2024-01-14'),
    messageCount: 10,
    ownerId: 'user-1',
  },
]

const mockGroup = {
  id: 'group-1',
  name: 'Work Projects',
  conversationIds: ['conv-2'],
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
  ownerId: 'user-1',
}

const mockGroups = [mockGroup]

describe('useConversations', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock auth token to enable data loading
    mockStorage.getAuthToken.mockReturnValue('test-token')
    // Default: APIs return mock data
    mockConversationsApi.getAll.mockResolvedValue(mockConversations)
    mockConversationsApi.getSharedConversations.mockResolvedValue([])
    // Mock getMessages to return empty array for message count computation
    mockConversationsApi.getMessages.mockResolvedValue([])
    mockGroupsApi.getAll.mockResolvedValue(mockGroups)
    mockStorage.get.mockReturnValue(null)
  })

  describe('Initial state', () => {
    it('starts with empty conversations and loading true', () => {
      const { result } = renderHook(() => useConversations())
      
      expect(result.current.conversations).toEqual([])
      expect(result.current.groups).toEqual([])
      expect(result.current.currentConversationId).toBe(null)
      // Loading starts true but becomes false quickly due to async
      expect(result.current.loading).toBe(true)
      expect(result.current.error).toBe(null)
    })
  })

  describe('Load conversations', () => {
    it('loads conversations and groups successfully', async () => {
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.conversations).toHaveLength(2)
      expect(result.current.groups).toEqual(mockGroups)
      expect(mockConversationsApi.getAll).toHaveBeenCalled()
      expect(mockGroupsApi.getAll).toHaveBeenCalled()
    })

    it('handles load error', async () => {
      mockConversationsApi.getAll.mockRejectedValue(new Error('Load failed'))
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.error).toBe('Load failed')
      expect(result.current.conversations).toEqual([])
    })

    it('restores current conversation from storage', async () => {
      mockStorage.get.mockReturnValue('conv-1')
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.currentConversationId).toBe('conv-1')
    })

    it('does not restore invalid conversation from storage', async () => {
      mockStorage.get.mockReturnValue('non-existent-conv')
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.currentConversationId).toBe(null)
    })

    it('skips loading if no auth token', async () => {
      mockStorage.getAuthToken.mockReturnValue(null)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(mockConversationsApi.getAll).not.toHaveBeenCalled()
      expect(result.current.conversations).toEqual([])
    })
  })

  describe('Create conversation', () => {
    it('creates new conversation', async () => {
      const newConversation = {
        id: 'conv-3',
        title: 'New Conversation',
        groupId: null,
        createdAt: new Date(),
        updatedAt: new Date(),
        messageCount: 0,
        ownerId: 'user-1',
      }
      mockConversationsApi.create.mockResolvedValue(newConversation)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      let createdConv: any
      await act(async () => {
        createdConv = await result.current.createConversation('New Conversation')
      })
      
      expect(mockConversationsApi.create).toHaveBeenCalledWith({ title: 'New Conversation', groupId: undefined })
      expect(createdConv).toEqual(newConversation)
    })

    it('creates conversation with group', async () => {
      const newConversation = {
        id: 'conv-3',
        title: 'New Conversation',
        groupId: 'group-1',
        createdAt: new Date(),
        updatedAt: new Date(),
        messageCount: 0,
        ownerId: 'user-1',
      }
      mockConversationsApi.create.mockResolvedValue(newConversation)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.createConversation('New Conversation', 'group-1')
      })
      
      expect(mockConversationsApi.create).toHaveBeenCalledWith({ 
        title: 'New Conversation', 
        groupId: 'group-1' 
      })
    })

    it('handles create error', async () => {
      mockConversationsApi.create.mockRejectedValue(new Error('Create failed'))
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await expect(async () => {
        await act(async () => {
          await result.current.createConversation('New Conversation')
        })
      }).rejects.toThrow('Create failed')
      
      // List should remain unchanged
      expect(result.current.conversations).toHaveLength(2)
    })
  })

  describe('Delete conversation', () => {
    it('deletes conversation and updates list', async () => {
      mockConversationsApi.delete.mockResolvedValue()
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.deleteConversation('conv-1')
      })
      
      expect(mockConversationsApi.delete).toHaveBeenCalledWith('conv-1')
      expect(result.current.conversations).toHaveLength(1)
    })

    it('clears current selection when deleting current conversation', async () => {
      mockConversationsApi.delete.mockResolvedValue()
      mockStorage.get.mockReturnValue('conv-1')
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.currentConversationId).toBe('conv-1')
      
      await act(async () => {
        await result.current.deleteConversation('conv-1')
      })
      
      expect(result.current.currentConversationId).toBe(null)
    })

    it('handles delete error', async () => {
      mockConversationsApi.delete.mockRejectedValue(new Error('Delete failed'))
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await expect(async () => {
        await act(async () => {
          await result.current.deleteConversation('conv-1')
        })
      }).rejects.toThrow('Delete failed')
      
      // List should remain unchanged
      expect(result.current.conversations).toHaveLength(2)
    })
  })

  describe('Update conversation', () => {
    it('updates conversation title', async () => {
      const updated = { ...mockConversation, title: 'Updated Title' }
      mockConversationsApi.update.mockResolvedValue(updated)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.updateConversation('conv-1', { title: 'Updated Title' })
      })
      
      expect(mockConversationsApi.update).toHaveBeenCalledWith('conv-1', { title: 'Updated Title' })
      const updatedConv = result.current.conversations.find(c => c.id === 'conv-1')
      expect(updatedConv?.title).toBe('Updated Title')
    })

    it('increments message count', async () => {
      // Mock getMessages to return 5 messages for conv-1 so the recompute gives messageCount = 5
      mockConversationsApi.getMessages.mockImplementation((id: string) => {
        if (id === 'conv-1') {
          return Promise.resolve([
            { id: '1', role: 'user', content: 'msg1' },
            { id: '2', role: 'assistant', content: 'msg2' },
            { id: '3', role: 'user', content: 'msg3' },
            { id: '4', role: 'assistant', content: 'msg4' },
            { id: '5', role: 'user', content: 'msg5' },
          ] as any);
        }
        return Promise.resolve([]);
      });
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Wait for conversations to be loaded and recomputed (should have messageCount = 5)
      await waitFor(() => {
        const conv = result.current.conversations.find(c => c.id === 'conv-1')
        expect(conv?.messageCount).toBe(5)
      })
      
      await act(async () => {
        result.current.incrementMessageCount('conv-1')
      })
      
      const updated = result.current.conversations.find(c => c.id === 'conv-1')
      // Increments by 2 (user + assistant): 5 + 2 = 7
      expect(updated?.messageCount).toBe(7)
    })
  })

  describe('Groups', () => {
    it('creates new group', async () => {
      const newGroup = {
        id: 'group-2',
        name: 'New Group',
        conversationIds: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        ownerId: 'user-1',
      }
      mockGroupsApi.create.mockResolvedValue(newGroup)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.createGroup('New Group')
      })
      
      expect(mockGroupsApi.create).toHaveBeenCalledWith({ name: 'New Group' })
    })

    it('deletes group', async () => {
      mockGroupsApi.delete.mockResolvedValue()
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.deleteGroup('group-1')
      })
      
      expect(mockGroupsApi.delete).toHaveBeenCalledWith('group-1')
      expect(result.current.groups).toHaveLength(0)
      
      // The group should be ungrouped
      const ungrouped = result.current.conversations.find(c => c.id === 'conv-2')
      expect(ungrouped?.groupId).toBeUndefined()
    })

    it('adds conversation to group', async () => {
      mockGroupsApi.addConversation.mockResolvedValue(mockGroup)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.addToGroup('conv-1', 'group-1')
      })
      
      expect(mockGroupsApi.addConversation).toHaveBeenCalledWith('group-1', 'conv-1')
    })

    it('removes conversation from group', async () => {
      mockGroupsApi.removeFromGroup.mockResolvedValue(mockGroup)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.removeFromGroup('conv-2', 'group-1')
      })
      
      expect(mockGroupsApi.removeFromGroup).toHaveBeenCalledWith('group-1', 'conv-2')
    })
  })

  describe('Reload', () => {
    it('reloads data from API', async () => {
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Track initial call counts
      const initialGetAllCalls = mockConversationsApi.getAll.mock.calls.length
      const initialGroupsCalls = mockGroupsApi.getAll.mock.calls.length
      
      // Update mock to return different data
      const newConversations = [
        ...mockConversations,
        {
          id: 'conv-3',
          title: 'New Loaded',
          groupId: null,
          createdAt: new Date(),
          updatedAt: new Date(),
          messageCount: 0,
          ownerId: 'user-1',
        },
      ]
      mockConversationsApi.getAll.mockResolvedValue(newConversations)
      
      await act(async () => {
        result.current.reload()
      })
      
      await waitFor(() => {
        expect(result.current.conversations).toHaveLength(3)
      })
      
      expect(mockConversationsApi.getAll).toHaveBeenCalledTimes(initialGetAllCalls + 1)
      expect(mockGroupsApi.getAll).toHaveBeenCalledTimes(initialGroupsCalls + 1)
    })
  })
})