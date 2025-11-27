// path: tests/unit/hooks/useConversations.test.unit.ts
// version: 6 - Fixed removeConversation to removeFromGroup to match API

import { renderHook, act, waitFor } from '@testing-library/react'
import { useConversations } from '@/lib/hooks/useConversations'

// Mock the conversations API
jest.mock('@/lib/api/conversations', () => ({
  conversationsApi: {
    getAll: jest.fn(),
    create: jest.fn(),
    delete: jest.fn(),
    update: jest.fn(),
  },
  groupsApi: {
    getAll: jest.fn(),
    create: jest.fn(),
    delete: jest.fn(),
    addConversation: jest.fn(),
    removeFromGroup: jest.fn(),
  },
}))

// Mock storage
jest.mock('@/lib/utils/storage', () => ({
  storage: {
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
    // Default: APIs return mock data
    mockConversationsApi.getAll.mockResolvedValue(mockConversations)
    mockGroupsApi.getAll.mockResolvedValue(mockGroups)
    mockStorage.get.mockReturnValue(null)
  })

  describe('Initial state', () => {
    it('starts with empty conversations and loading true', () => {
      const { result } = renderHook(() => useConversations())
      
      expect(result.current.conversations).toEqual([])
      expect(result.current.groups).toEqual([])
      expect(result.current.currentConversationId).toBe(null)
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
      
      expect(result.current.conversations).toEqual(mockConversations)
      expect(result.current.groups).toEqual(mockGroups)
      expect(mockConversationsApi.getAll).toHaveBeenCalledTimes(1)
      expect(mockGroupsApi.getAll).toHaveBeenCalledTimes(1)
    })

    it('handles load error', async () => {
      mockConversationsApi.getAll.mockRejectedValue(new Error('Load failed'))
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // The hook uses err.message if err instanceof Error
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
  })

  describe('Create conversation', () => {
    it('creates conversation successfully', async () => {
      const newConversation = {
        id: 'conv-new',
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
      
      let created: typeof newConversation | undefined
      await act(async () => {
        created = await result.current.createConversation('New Conversation')
      })
      
      expect(created).toEqual(newConversation)
      expect(result.current.conversations).toContainEqual(newConversation)
      expect(result.current.currentConversationId).toBe('conv-new')
    })

    it('creates conversation with group', async () => {
      const newConversation = {
        id: 'conv-new',
        title: 'Grouped Conversation',
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
        await result.current.createConversation('Grouped Conversation', 'group-1')
      })
      
      expect(mockConversationsApi.create).toHaveBeenCalledWith({
        title: 'Grouped Conversation',
        groupId: 'group-1',
      })
    })

    it('handles create error', async () => {
      // Mock rejects with an error
      mockConversationsApi.create.mockRejectedValue(new Error('Create failed'))
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      let caughtError: Error | null = null
      await act(async () => {
        try {
          await result.current.createConversation('Test')
        } catch (e) {
          caughtError = e as Error
        }
      })
      
      // Verify an error was thrown
      expect(caughtError).not.toBe(null)
      
      // Wait for error state - the hook sets error from err.message if Error, else default
      // Since the error might be transformed, just check that error is set
      await waitFor(() => {
        expect(result.current.error).not.toBe(null)
      })
    })

  })

  describe('Select conversation', () => {
    it('selects conversation by id', async () => {
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      act(() => {
        result.current.setCurrentConversationId('conv-1')
      })
      
      expect(result.current.currentConversationId).toBe('conv-1')
    })

    it('clears selection with null', async () => {
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      act(() => {
        result.current.setCurrentConversationId('conv-1')
      })
      
      expect(result.current.currentConversationId).toBe('conv-1')
      
      act(() => {
        result.current.setCurrentConversationId(null)
      })
      
      expect(result.current.currentConversationId).toBe(null)
    })
  })

  describe('Delete conversation', () => {
    it('deletes conversation successfully', async () => {
      mockConversationsApi.delete.mockResolvedValue(undefined)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      const initialCount = result.current.conversations.length
      
      await act(async () => {
        await result.current.deleteConversation('conv-1')
      })
      
      expect(result.current.conversations).toHaveLength(initialCount - 1)
      expect(result.current.conversations.find(c => c.id === 'conv-1')).toBeUndefined()
    })

    it('clears selection if deleted conversation was selected', async () => {
      mockConversationsApi.delete.mockResolvedValue(undefined)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Select the conversation first
      act(() => {
        result.current.setCurrentConversationId('conv-1')
      })
      
      expect(result.current.currentConversationId).toBe('conv-1')
      
      // Delete it
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
      
      let caughtError: Error | null = null
      await act(async () => {
        try {
          await result.current.deleteConversation('conv-1')
        } catch (e) {
          caughtError = e as Error
        }
      })
      
      expect(caughtError).not.toBe(null)
      
      // Wait for error state to be set
      await waitFor(() => {
        expect(result.current.error).not.toBe(null)
      })
    })
  })

  describe('Update conversation', () => {
    it('updates conversation title', async () => {
      const updatedConversation = { ...mockConversation, title: 'Updated Title' }
      mockConversationsApi.update.mockResolvedValue(updatedConversation)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.updateConversation('conv-1', { title: 'Updated Title' })
      })
      
      expect(mockConversationsApi.update).toHaveBeenCalledWith('conv-1', { title: 'Updated Title' })
      const updated = result.current.conversations.find(c => c.id === 'conv-1')
      expect(updated?.title).toBe('Updated Title')
    })

    it('updates conversation group', async () => {
      const updatedConversation = { ...mockConversation, groupId: 'group-1' }
      mockConversationsApi.update.mockResolvedValue(updatedConversation)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.updateConversation('conv-1', { groupId: 'group-1' })
      })
      
      const updated = result.current.conversations.find(c => c.id === 'conv-1')
      expect(updated?.groupId).toBe('group-1')
    })
  })

  describe('Group management', () => {
    it('creates group successfully', async () => {
      const newGroup = {
        id: 'group-new',
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
      expect(result.current.groups).toContainEqual(newGroup)
    })

    it('deletes group and ungroups conversations', async () => {
      mockGroupsApi.delete.mockResolvedValue(undefined)
      
      const { result } = renderHook(() => useConversations())
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      await act(async () => {
        await result.current.deleteGroup('group-1')
      })
      
      expect(result.current.groups.find(g => g.id === 'group-1')).toBeUndefined()
      // Conversations that were in the group should be ungrouped
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
      
      expect(mockConversationsApi.getAll).toHaveBeenCalledTimes(1)
      
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
      
      expect(mockConversationsApi.getAll).toHaveBeenCalledTimes(2)
    })
  })
})